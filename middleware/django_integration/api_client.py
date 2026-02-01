"""
Django API client for Observer Eye Middleware.
Provides HTTP client for communicating with Django backend APIs.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import json

import structlog
import httpx
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .models import (
    DjangoAppConfig, APIEndpoint, APIResponse, HTTPMethod, HealthCheck
)
from .error_handler import DjangoErrorHandler
from crud.exceptions import NetworkError, DatabaseOperationError

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class DjangoAPIClient:
    """
    HTTP client for Django backend API communication.
    Provides comprehensive API interaction with error handling and monitoring.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        enable_tracing: bool = True
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.enable_tracing = enable_tracing
        
        # HTTP client configuration
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            follow_redirects=True
        )
        
        # Error handler
        self.error_handler = DjangoErrorHandler()
        
        # App configurations
        self._app_configs: Dict[str, DjangoAppConfig] = {}
        
        # API endpoints registry
        self._endpoints: Dict[str, APIEndpoint] = {}
        
        # Request metrics
        self._request_count = 0
        self._failed_request_count = 0
        self._total_request_time = 0.0
        
        logger.info(
            "Django API client initialized",
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries
        )
    
    def register_app_config(self, config: DjangoAppConfig) -> None:
        """Register Django app configuration"""
        self._app_configs[config.app_name] = config
        
        # Auto-generate standard CRUD endpoints
        if config.enable_crud:
            self._generate_crud_endpoints(config)
        
        logger.info(
            "Django app configuration registered",
            app_name=config.app_name,
            models_count=len(config.models),
            enable_crud=config.enable_crud
        )
    
    def register_endpoint(self, endpoint: APIEndpoint) -> None:
        """Register API endpoint"""
        endpoint_key = f"{endpoint.method.value}:{endpoint.path}"
        self._endpoints[endpoint_key] = endpoint
        
        logger.debug(
            "API endpoint registered",
            method=endpoint.method.value,
            path=endpoint.path,
            app_name=endpoint.app_name
        )
    
    async def request(
        self,
        method: HTTPMethod,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None
    ) -> APIResponse:
        """
        Make HTTP request to Django backend.
        
        Args:
            method: HTTP method
            path: API path
            data: Request body data
            params: Query parameters
            headers: Request headers
            auth_token: Authentication token
        
        Returns:
            APIResponse: Standardized API response
        """
        with tracer.start_as_current_span("django_api_request") as span:
            start_time = time.time()
            request_id = f"req_{int(time.time() * 1000)}"
            
            try:
                # Build full URL
                url = f"{self.base_url}{path}"
                
                # Prepare headers
                request_headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Request-ID": request_id
                }
                
                if headers:
                    request_headers.update(headers)
                
                if auth_token:
                    request_headers["Authorization"] = f"Bearer {auth_token}"
                
                # Set span attributes
                span.set_attribute("http.method", method.value)
                span.set_attribute("http.url", url)
                span.set_attribute("http.request_id", request_id)
                
                # Make request with retries
                response = await self._make_request_with_retries(
                    method, url, data, params, request_headers
                )
                
                # Process response
                api_response = await self._process_response(response, request_id)
                
                # Update metrics
                execution_time = (time.time() - start_time) * 1000
                self._request_count += 1
                self._total_request_time += execution_time
                
                # Set span attributes
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_time_ms", execution_time)
                span.set_status(Status(StatusCode.OK))
                
                logger.info(
                    "Django API request completed",
                    method=method.value,
                    path=path,
                    status_code=response.status_code,
                    response_time_ms=execution_time,
                    request_id=request_id
                )
                
                return api_response
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self._failed_request_count += 1
                
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                
                logger.error(
                    "Django API request failed",
                    method=method.value,
                    path=path,
                    error=str(e),
                    response_time_ms=execution_time,
                    request_id=request_id
                )
                
                # Return error response
                return APIResponse(
                    success=False,
                    message=f"Request failed: {str(e)}",
                    errors=[{
                        "code": "REQUEST_FAILED",
                        "message": str(e),
                        "details": {"method": method.value, "path": path}
                    }],
                    request_id=request_id
                )
    
    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> APIResponse:
        """Make GET request"""
        return await self.request(HTTPMethod.GET, path, params=params, auth_token=auth_token)
    
    async def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> APIResponse:
        """Make POST request"""
        return await self.request(HTTPMethod.POST, path, data=data, auth_token=auth_token)
    
    async def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> APIResponse:
        """Make PUT request"""
        return await self.request(HTTPMethod.PUT, path, data=data, auth_token=auth_token)
    
    async def patch(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> APIResponse:
        """Make PATCH request"""
        return await self.request(HTTPMethod.PATCH, path, data=data, auth_token=auth_token)
    
    async def delete(
        self,
        path: str,
        auth_token: Optional[str] = None
    ) -> APIResponse:
        """Make DELETE request"""
        return await self.request(HTTPMethod.DELETE, path, auth_token=auth_token)
    
    async def _make_request_with_retries(
        self,
        method: HTTPMethod,
        url: str,
        data: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
        headers: Dict[str, str]
    ) -> httpx.Response:
        """Make HTTP request with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Prepare request kwargs
                kwargs = {
                    "headers": headers,
                    "params": params or {}
                }
                
                if data is not None and method in [HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH]:
                    kwargs["json"] = data
                
                # Make request
                response = await self.http_client.request(
                    method.value,
                    url,
                    **kwargs
                )
                
                # Check if we should retry based on status code
                if response.status_code >= 500 and attempt < self.max_retries:
                    logger.warning(
                        "Server error, retrying request",
                        attempt=attempt + 1,
                        status_code=response.status_code,
                        url=url
                    )
                    await asyncio.sleep(self.retry_delay_seconds * (attempt + 1))
                    continue
                
                return response
                
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    logger.warning(
                        "Request failed, retrying",
                        attempt=attempt + 1,
                        error=str(e),
                        url=url
                    )
                    await asyncio.sleep(self.retry_delay_seconds * (attempt + 1))
                    continue
                
                break
        
        # All retries exhausted
        raise NetworkError(
            message=f"Request failed after {self.max_retries + 1} attempts: {str(last_exception)}",
            url=url
        )
    
    async def _process_response(
        self,
        response: httpx.Response,
        request_id: str
    ) -> APIResponse:
        """Process HTTP response into APIResponse"""
        try:
            # Try to parse JSON response
            if response.headers.get("content-type", "").startswith("application/json"):
                response_data = response.json()
            else:
                response_data = {"message": response.text}
            
            # Handle different response formats
            if isinstance(response_data, dict):
                # Django REST framework format
                if "results" in response_data:
                    # Paginated response
                    return APIResponse(
                        success=response.status_code < 400,
                        data=response_data["results"],
                        pagination={
                            "count": response_data.get("count"),
                            "next": response_data.get("next"),
                            "previous": response_data.get("previous")
                        },
                        request_id=request_id
                    )
                else:
                    # Standard response
                    return APIResponse(
                        success=response.status_code < 400,
                        data=response_data,
                        request_id=request_id
                    )
            else:
                # Non-dict response
                return APIResponse(
                    success=response.status_code < 400,
                    data=response_data,
                    request_id=request_id
                )
                
        except json.JSONDecodeError:
            # Non-JSON response
            return APIResponse(
                success=response.status_code < 400,
                data={"raw_response": response.text},
                message=f"Non-JSON response: {response.status_code}",
                request_id=request_id
            )
        except Exception as e:
            # Error processing response
            return APIResponse(
                success=False,
                message=f"Error processing response: {str(e)}",
                errors=[{
                    "code": "RESPONSE_PROCESSING_ERROR",
                    "message": str(e)
                }],
                request_id=request_id
            )
    
    def _generate_crud_endpoints(self, config: DjangoAppConfig) -> None:
        """Generate standard CRUD endpoints for Django app"""
        for model_name in config.models:
            model_name_lower = model_name.lower()
            base_path = f"{config.api_prefix}/{config.app_name}/{model_name_lower}"
            
            # List endpoint
            if "read" in config.allowed_operations:
                self.register_endpoint(APIEndpoint(
                    path=f"{base_path}/",
                    method=HTTPMethod.GET,
                    app_name=config.app_name,
                    model_name=model_name,
                    view_name=f"{model_name}ListView",
                    supports_pagination=config.enable_pagination,
                    supports_filtering=config.enable_filtering,
                    supports_ordering=True,
                    requires_auth=config.require_authentication,
                    cacheable=config.enable_caching,
                    cache_ttl=config.cache_ttl_seconds
                ))
            
            # Detail endpoint
            if "read" in config.allowed_operations:
                self.register_endpoint(APIEndpoint(
                    path=f"{base_path}/{{id}}/",
                    method=HTTPMethod.GET,
                    app_name=config.app_name,
                    model_name=model_name,
                    view_name=f"{model_name}DetailView",
                    requires_auth=config.require_authentication,
                    cacheable=config.enable_caching,
                    cache_ttl=config.cache_ttl_seconds
                ))
            
            # Create endpoint
            if "create" in config.allowed_operations:
                self.register_endpoint(APIEndpoint(
                    path=f"{base_path}/",
                    method=HTTPMethod.POST,
                    app_name=config.app_name,
                    model_name=model_name,
                    view_name=f"{model_name}CreateView",
                    requires_body=True,
                    requires_auth=config.require_authentication
                ))
            
            # Update endpoint
            if "update" in config.allowed_operations:
                self.register_endpoint(APIEndpoint(
                    path=f"{base_path}/{{id}}/",
                    method=HTTPMethod.PATCH,
                    app_name=config.app_name,
                    model_name=model_name,
                    view_name=f"{model_name}UpdateView",
                    requires_body=True,
                    requires_auth=config.require_authentication
                ))
            
            # Delete endpoint
            if "delete" in config.allowed_operations:
                self.register_endpoint(APIEndpoint(
                    path=f"{base_path}/{{id}}/",
                    method=HTTPMethod.DELETE,
                    app_name=config.app_name,
                    model_name=model_name,
                    view_name=f"{model_name}DeleteView",
                    requires_auth=config.require_authentication
                ))
            
            # Bulk operations if enabled
            if config.enable_bulk_operations:
                self.register_endpoint(APIEndpoint(
                    path=f"{base_path}/bulk/",
                    method=HTTPMethod.POST,
                    app_name=config.app_name,
                    model_name=model_name,
                    view_name=f"{model_name}BulkView",
                    requires_body=True,
                    requires_auth=config.require_authentication
                ))
    
    async def health_check(self) -> HealthCheck:
        """Perform health check on Django backend"""
        checks = {}
        overall_status = "healthy"
        
        try:
            # Test basic connectivity
            start_time = time.time()
            response = await self.get("/health/", auth_token=None)
            response_time = (time.time() - start_time) * 1000
            
            if response.success:
                checks["django_api"] = {
                    "status": "healthy",
                    "response_time_ms": response_time,
                    "details": "API responding normally"
                }
            else:
                checks["django_api"] = {
                    "status": "unhealthy",
                    "response_time_ms": response_time,
                    "details": f"API error: {response.message}"
                }
                overall_status = "unhealthy"
                
        except Exception as e:
            checks["django_api"] = {
                "status": "unhealthy",
                "details": f"Connection failed: {str(e)}"
            }
            overall_status = "unhealthy"
        
        # Add client metrics
        checks["client_metrics"] = {
            "status": "healthy",
            "details": {
                "total_requests": self._request_count,
                "failed_requests": self._failed_request_count,
                "avg_response_time_ms": (
                    self._total_request_time / self._request_count
                    if self._request_count > 0 else 0
                ),
                "success_rate": (
                    (self._request_count - self._failed_request_count) / self._request_count * 100
                    if self._request_count > 0 else 100
                )
            }
        }
        
        return HealthCheck(
            status=overall_status,
            checks=checks
        )
    
    def get_registered_apps(self) -> List[DjangoAppConfig]:
        """Get all registered app configurations"""
        return list(self._app_configs.values())
    
    def get_registered_endpoints(self) -> List[APIEndpoint]:
        """Get all registered endpoints"""
        return list(self._endpoints.values())
    
    async def close(self) -> None:
        """Close HTTP client"""
        await self.http_client.aclose()
        logger.info("Django API client closed")