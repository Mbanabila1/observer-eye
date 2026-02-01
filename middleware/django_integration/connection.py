"""
Django database connection manager.
Handles database connections, connection pooling, and health monitoring.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import os

import structlog
import asyncpg
import aiosqlite
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text

from .models import DatabaseConfig, ConnectionInfo, ConnectionStatus, DatabaseEngine
from crud.exceptions import DatabaseConnectionError, DatabaseOperationError

logger = structlog.get_logger(__name__)


class DjangoConnectionManager:
    """
    Database connection manager for Django backend integration.
    Provides connection pooling, health monitoring, and async database operations.
    """
    
    def __init__(
        self,
        config: DatabaseConfig,
        enable_health_monitoring: bool = True,
        health_check_interval_seconds: int = 30
    ):
        self.config = config
        self.enable_health_monitoring = enable_health_monitoring
        self.health_check_interval_seconds = health_check_interval_seconds
        
        # Connection state
        self._engine = None
        self._session_factory = None
        self._connection_info = ConnectionInfo(
            status=ConnectionStatus.DISCONNECTED,
            database_name=config.name,
            host=config.host,
            port=config.port
        )
        
        # Health monitoring
        self._health_monitor_task = None
        self._shutdown_event = asyncio.Event()
        
        # Metrics
        self._query_count = 0
        self._failed_query_count = 0
        self._total_query_time = 0.0
        
        logger.info(
            "Django connection manager initialized",
            database=config.name,
            host=config.host,
            port=config.port,
            engine=config.engine.value
        )
    
    async def connect(self) -> None:
        """Establish database connection"""
        try:
            self._connection_info.status = ConnectionStatus.CONNECTING
            
            # Build connection URL
            connection_url = self._build_connection_url()
            
            # Create async engine
            self._engine = create_async_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=False,  # Set to True for SQL debugging
                **self.config.options
            )
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            await self._test_connection()
            
            # Update connection info
            self._connection_info.status = ConnectionStatus.CONNECTED
            self._connection_info.connected_at = datetime.now(timezone.utc)
            self._connection_info.last_activity = datetime.now(timezone.utc)
            
            # Start health monitoring
            if self.enable_health_monitoring:
                self._health_monitor_task = asyncio.create_task(self._health_monitor())
            
            logger.info(
                "Database connection established",
                database=self.config.name,
                host=self.config.host,
                engine=self.config.engine.value
            )
            
        except Exception as e:
            self._connection_info.status = ConnectionStatus.ERROR
            logger.error(
                "Failed to establish database connection",
                database=self.config.name,
                host=self.config.host,
                error=str(e)
            )
            raise DatabaseConnectionError(f"Connection failed: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close database connection"""
        try:
            # Stop health monitoring
            if self._health_monitor_task:
                self._shutdown_event.set()
                await self._health_monitor_task
                self._health_monitor_task = None
            
            # Close engine
            if self._engine:
                await self._engine.dispose()
                self._engine = None
                self._session_factory = None
            
            self._connection_info.status = ConnectionStatus.DISCONNECTED
            
            logger.info(
                "Database connection closed",
                database=self.config.name
            )
            
        except Exception as e:
            logger.error(
                "Error closing database connection",
                database=self.config.name,
                error=str(e)
            )
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self._session_factory:
            raise DatabaseConnectionError("Database not connected")
        
        return self._session_factory()
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute raw SQL query"""
        if not self._engine:
            raise DatabaseConnectionError("Database not connected")
        
        start_time = time.time()
        
        try:
            async with self._engine.begin() as conn:
                result = await conn.execute(text(query), parameters or {})
                
                # Update metrics
                execution_time = (time.time() - start_time) * 1000
                self._query_count += 1
                self._total_query_time += execution_time
                self._connection_info.last_activity = datetime.now(timezone.utc)
                
                logger.debug(
                    "Query executed successfully",
                    query=query[:100] + "..." if len(query) > 100 else query,
                    execution_time_ms=execution_time
                )
                
                return result
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._failed_query_count += 1
            
            logger.error(
                "Query execution failed",
                query=query[:100] + "..." if len(query) > 100 else query,
                error=str(e),
                execution_time_ms=execution_time
            )
            
            raise DatabaseOperationError(
                message=f"Query execution failed: {str(e)}",
                operation="execute_query",
                sql_error=str(e)
            )
    
    async def execute_transaction(
        self,
        queries: List[Dict[str, Any]]
    ) -> List[Any]:
        """Execute multiple queries in a transaction"""
        if not self._engine:
            raise DatabaseConnectionError("Database not connected")
        
        start_time = time.time()
        results = []
        
        try:
            async with self._engine.begin() as conn:
                for query_info in queries:
                    query = query_info.get("query")
                    parameters = query_info.get("parameters", {})
                    
                    result = await conn.execute(text(query), parameters)
                    results.append(result)
                
                # Update metrics
                execution_time = (time.time() - start_time) * 1000
                self._query_count += len(queries)
                self._total_query_time += execution_time
                self._connection_info.last_activity = datetime.now(timezone.utc)
                
                logger.debug(
                    "Transaction executed successfully",
                    query_count=len(queries),
                    execution_time_ms=execution_time
                )
                
                return results
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._failed_query_count += len(queries)
            
            logger.error(
                "Transaction execution failed",
                query_count=len(queries),
                error=str(e),
                execution_time_ms=execution_time
            )
            
            raise DatabaseOperationError(
                message=f"Transaction failed: {str(e)}",
                operation="execute_transaction",
                sql_error=str(e)
            )
    
    def _build_connection_url(self) -> str:
        """Build database connection URL"""
        if self.config.engine == DatabaseEngine.POSTGRESQL:
            url = f"postgresql+asyncpg://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.name}"
        elif self.config.engine == DatabaseEngine.SQLITE:
            url = f"sqlite+aiosqlite:///{self.config.name}"
        elif self.config.engine == DatabaseEngine.MYSQL:
            url = f"mysql+aiomysql://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.name}"
        else:
            raise ValueError(f"Unsupported database engine: {self.config.engine}")
        
        # Add SSL parameters if configured
        if self.config.use_ssl and self.config.engine != DatabaseEngine.SQLITE:
            ssl_params = []
            if self.config.ssl_cert_path:
                ssl_params.append(f"sslcert={self.config.ssl_cert_path}")
            if self.config.ssl_key_path:
                ssl_params.append(f"sslkey={self.config.ssl_key_path}")
            if self.config.ssl_ca_path:
                ssl_params.append(f"sslrootcert={self.config.ssl_ca_path}")
            
            if ssl_params:
                url += "?" + "&".join(ssl_params)
        
        return url
    
    async def _test_connection(self) -> None:
        """Test database connection"""
        try:
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            logger.debug("Database connection test successful")
            
        except Exception as e:
            logger.error("Database connection test failed", error=str(e))
            raise
    
    async def _health_monitor(self) -> None:
        """Background health monitoring"""
        while not self._shutdown_event.is_set():
            try:
                # Wait for interval or shutdown
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.health_check_interval_seconds
                )
                break  # Shutdown event was set
                
            except asyncio.TimeoutError:
                # Timeout reached, perform health check
                await self._perform_health_check()
    
    async def _perform_health_check(self) -> None:
        """Perform database health check"""
        try:
            start_time = time.time()
            
            # Simple health check query
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            health_check_time = (time.time() - start_time) * 1000
            
            # Update connection info
            self._connection_info.status = ConnectionStatus.CONNECTED
            self._connection_info.last_activity = datetime.now(timezone.utc)
            
            # Update metrics
            if self._query_count > 0:
                self._connection_info.avg_query_time_ms = self._total_query_time / self._query_count
            self._connection_info.total_queries = self._query_count
            self._connection_info.failed_queries = self._failed_query_count
            
            logger.debug(
                "Health check successful",
                response_time_ms=health_check_time,
                total_queries=self._query_count,
                failed_queries=self._failed_query_count
            )
            
        except Exception as e:
            self._connection_info.status = ConnectionStatus.ERROR
            
            logger.error(
                "Health check failed",
                error=str(e)
            )
    
    def get_connection_info(self) -> ConnectionInfo:
        """Get current connection information"""
        # Update pool statistics if available
        if self._engine and hasattr(self._engine.pool, 'size'):
            pool = self._engine.pool
            self._connection_info.total_connections = pool.size()
            self._connection_info.active_connections = pool.checkedout()
            self._connection_info.idle_connections = pool.checkedin()
        
        return self._connection_info
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_info = {
            "status": "unknown",
            "connection_status": self._connection_info.status.value,
            "response_time_ms": None,
            "details": {}
        }
        
        try:
            start_time = time.time()
            
            # Test connection
            await self._test_connection()
            
            response_time = (time.time() - start_time) * 1000
            
            health_info.update({
                "status": "healthy",
                "response_time_ms": response_time,
                "details": {
                    "database": self.config.name,
                    "host": self.config.host,
                    "port": self.config.port,
                    "engine": self.config.engine.value,
                    "total_queries": self._query_count,
                    "failed_queries": self._failed_query_count,
                    "avg_query_time_ms": self._connection_info.avg_query_time_ms,
                    "connected_at": self._connection_info.connected_at.isoformat() if self._connection_info.connected_at else None,
                    "last_activity": self._connection_info.last_activity.isoformat() if self._connection_info.last_activity else None
                }
            })
            
        except Exception as e:
            health_info.update({
                "status": "unhealthy",
                "details": {
                    "error": str(e),
                    "connection_status": self._connection_info.status.value
                }
            })
        
        return health_info
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()