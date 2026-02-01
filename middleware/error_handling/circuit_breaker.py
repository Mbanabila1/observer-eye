"""
Circuit breaker implementation for resilience patterns
"""

import asyncio
import time
import structlog
from enum import Enum
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass

from .exceptions import CircuitBreakerOpenError

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5      # Number of failures before opening
    timeout: int = 60              # Timeout in seconds before trying half-open
    success_threshold: int = 3      # Successes needed to close from half-open
    monitoring_window: int = 300    # Time window for failure counting (seconds)


class CircuitBreaker:
    """
    Circuit breaker implementation for handling service failures gracefully
    
    Validates Requirements 5.2, 5.4: Graceful degradation and circuit breaker patterns
    """
    
    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.circuits: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    def initialize(self):
        """Initialize the circuit breaker"""
        logger.info("Initializing circuit breaker system")
    
    async def call(self, service_name: str, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection
        
        Args:
            service_name: Name of the service being called
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
        """
        async with self._lock:
            circuit = self._get_or_create_circuit(service_name)
        
        # Check circuit state
        if circuit["state"] == CircuitState.OPEN:
            if time.time() - circuit["last_failure_time"] > self.config.timeout:
                # Transition to half-open
                async with self._lock:
                    circuit["state"] = CircuitState.HALF_OPEN
                    circuit["success_count"] = 0
                logger.info(f"Circuit breaker for {service_name} transitioned to HALF_OPEN")
            else:
                # Circuit is still open
                raise CircuitBreakerOpenError(service_name)
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Record success
            await self._record_success(service_name)
            return result
            
        except Exception as e:
            # Record failure
            await self._record_failure(service_name, e)
            raise
    
    async def get_circuit_status(self, service_name: str) -> Dict[str, Any]:
        """Get the current status of a circuit"""
        async with self._lock:
            circuit = self.circuits.get(service_name)
            if not circuit:
                return {"service": service_name, "state": "not_initialized"}
            
            return {
                "service": service_name,
                "state": circuit["state"].value,
                "failure_count": circuit["failure_count"],
                "success_count": circuit["success_count"],
                "last_failure_time": circuit["last_failure_time"],
                "last_success_time": circuit["last_success_time"]
            }
    
    async def get_all_circuits_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuits"""
        async with self._lock:
            status = {}
            for service_name in self.circuits:
                circuit = self.circuits[service_name]
                status[service_name] = {
                    "state": circuit["state"].value,
                    "failure_count": circuit["failure_count"],
                    "success_count": circuit["success_count"],
                    "last_failure_time": circuit["last_failure_time"],
                    "last_success_time": circuit["last_success_time"]
                }
            return status
    
    async def reset_circuit(self, service_name: str):
        """Manually reset a circuit to closed state"""
        async with self._lock:
            if service_name in self.circuits:
                circuit = self.circuits[service_name]
                circuit["state"] = CircuitState.CLOSED
                circuit["failure_count"] = 0
                circuit["success_count"] = 0
                circuit["last_failure_time"] = None
                logger.info(f"Circuit breaker for {service_name} manually reset to CLOSED")
    
    def _get_or_create_circuit(self, service_name: str) -> Dict[str, Any]:
        """Get or create a circuit for a service"""
        if service_name not in self.circuits:
            self.circuits[service_name] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "last_failure_time": None,
                "last_success_time": None,
                "failures": []  # Track failures with timestamps
            }
        return self.circuits[service_name]
    
    async def _record_success(self, service_name: str):
        """Record a successful call"""
        async with self._lock:
            circuit = self.circuits[service_name]
            circuit["success_count"] += 1
            circuit["last_success_time"] = time.time()
            
            if circuit["state"] == CircuitState.HALF_OPEN:
                if circuit["success_count"] >= self.config.success_threshold:
                    # Close the circuit
                    circuit["state"] = CircuitState.CLOSED
                    circuit["failure_count"] = 0
                    circuit["failures"] = []
                    logger.info(f"Circuit breaker for {service_name} transitioned to CLOSED")
    
    async def _record_failure(self, service_name: str, exception: Exception):
        """Record a failed call"""
        async with self._lock:
            circuit = self.circuits[service_name]
            current_time = time.time()
            
            # Add failure to the list
            circuit["failures"].append({
                "timestamp": current_time,
                "exception": str(exception)
            })
            
            # Remove old failures outside the monitoring window
            circuit["failures"] = [
                f for f in circuit["failures"]
                if current_time - f["timestamp"] <= self.config.monitoring_window
            ]
            
            circuit["failure_count"] = len(circuit["failures"])
            circuit["last_failure_time"] = current_time
            
            # Check if we should open the circuit
            if (circuit["state"] == CircuitState.CLOSED and 
                circuit["failure_count"] >= self.config.failure_threshold):
                
                circuit["state"] = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker for {service_name} opened due to failures",
                    failure_count=circuit["failure_count"],
                    threshold=self.config.failure_threshold
                )
            
            elif circuit["state"] == CircuitState.HALF_OPEN:
                # If we fail in half-open state, go back to open
                circuit["state"] = CircuitState.OPEN
                logger.warning(f"Circuit breaker for {service_name} returned to OPEN state")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get health status of the circuit breaker system"""
        async with self._lock:
            total_circuits = len(self.circuits)
            open_circuits = sum(1 for c in self.circuits.values() if c["state"] == CircuitState.OPEN)
            half_open_circuits = sum(1 for c in self.circuits.values() if c["state"] == CircuitState.HALF_OPEN)
            
            return {
                "total_circuits": total_circuits,
                "open_circuits": open_circuits,
                "half_open_circuits": half_open_circuits,
                "closed_circuits": total_circuits - open_circuits - half_open_circuits,
                "health_status": "degraded" if open_circuits > 0 else "healthy"
            }