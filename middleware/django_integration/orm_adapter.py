"""
Django ORM Adapter

Provides ORM integration and database operations for Django backend.
Handles model operations, query execution, and data transformation.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime, timezone
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models import QueryResult, DjangoAppConfig
from .error_handler import DjangoErrorHandler

logger = structlog.get_logger()


class DjangoORMAdapter:
    """Django ORM adapter for database operations"""
    
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.error_handler = DjangoErrorHandler()
        self.logger = structlog.get_logger()
        self.async_engine = None
        self.async_session_factory = None
        
        # Initialize async engine
        asyncio.create_task(self._initialize_async_engine())
    
    async def _initialize_async_engine(self):
        """Initialize async SQLAlchemy engine"""
        try:
            # Get database URL from connection manager
            db_url = self.connection_manager.get_database_url()
            
            # Convert to async URL if needed
            if db_url.startswith('postgresql://'):
                async_db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
            elif db_url.startswith('sqlite://'):
                async_db_url = db_url.replace('sqlite://', 'sqlite+aiosqlite://')
            elif db_url.startswith('mysql://'):
                async_db_url = db_url.replace('mysql://', 'mysql+aiomysql://')
            else:
                async_db_url = db_url
            
            self.async_engine = create_async_engine(
                async_db_url,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            self.async_session_factory = sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self.logger.info("Django ORM adapter initialized", db_url=async_db_url)
            
        except Exception as e:
            self.logger.error("Failed to initialize Django ORM adapter", error=str(e))
            raise
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        Execute raw SQL query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            QueryResult with data and metadata
        """
        try:
            if not self.async_session_factory:
                await self._initialize_async_engine()
            
            async with self.async_session_factory() as session:
                result = await session.execute(text(query), params or {})
                
                # Handle different result types
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = list(result.keys())
                    data = [dict(zip(columns, row)) for row in rows]
                else:
                    data = []
                    columns = []
                
                await session.commit()
                
                return QueryResult(
                    success=True,
                    data=data,
                    columns=columns,
                    row_count=len(data),
                    query=query,
                    execution_time=0.0  # TODO: Add timing
                )
                
        except Exception as e:
            error_info = self.error_handler.handle_database_error(e)
            return QueryResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                query=query,
                error=error_info['message'],
                execution_time=0.0
            )
    
    async def get_model_data(self, app_name: str, model_name: str, 
                           filters: Optional[Dict[str, Any]] = None,
                           limit: Optional[int] = None,
                           offset: Optional[int] = None) -> QueryResult:
        """
        Get data from Django model
        
        Args:
            app_name: Django app name
            model_name: Model name
            filters: Filter conditions
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            QueryResult with model data
        """
        try:
            # Build query
            table_name = f"{app_name}_{model_name.lower()}"
            query_parts = [f"SELECT * FROM {table_name}"]
            params = {}
            
            # Add filters
            if filters:
                where_conditions = []
                for key, value in filters.items():
                    where_conditions.append(f"{key} = :{key}")
                    params[key] = value
                
                if where_conditions:
                    query_parts.append("WHERE " + " AND ".join(where_conditions))
            
            # Add pagination
            if limit:
                query_parts.append(f"LIMIT {limit}")
            if offset:
                query_parts.append(f"OFFSET {offset}")
            
            query = " ".join(query_parts)
            
            return await self.execute_query(query, params)
            
        except Exception as e:
            error_info = self.error_handler.handle_database_error(e)
            return QueryResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                query="",
                error=error_info['message'],
                execution_time=0.0
            )
    
    async def create_record(self, app_name: str, model_name: str, 
                          data: Dict[str, Any]) -> QueryResult:
        """
        Create new record in Django model
        
        Args:
            app_name: Django app name
            model_name: Model name
            data: Record data
            
        Returns:
            QueryResult with created record
        """
        try:
            table_name = f"{app_name}_{model_name.lower()}"
            
            # Build INSERT query
            columns = list(data.keys())
            placeholders = [f":{col}" for col in columns]
            
            query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
            """
            
            return await self.execute_query(query, data)
            
        except Exception as e:
            error_info = self.error_handler.handle_database_error(e)
            return QueryResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                query="",
                error=error_info['message'],
                execution_time=0.0
            )
    
    async def update_record(self, app_name: str, model_name: str,
                          record_id: Union[str, int], data: Dict[str, Any]) -> QueryResult:
        """
        Update record in Django model
        
        Args:
            app_name: Django app name
            model_name: Model name
            record_id: Record ID
            data: Updated data
            
        Returns:
            QueryResult with updated record
        """
        try:
            table_name = f"{app_name}_{model_name.lower()}"
            
            # Build UPDATE query
            set_clauses = [f"{col} = :{col}" for col in data.keys()]
            data['record_id'] = record_id
            
            query = f"""
                UPDATE {table_name}
                SET {', '.join(set_clauses)}
                WHERE id = :record_id
                RETURNING *
            """
            
            return await self.execute_query(query, data)
            
        except Exception as e:
            error_info = self.error_handler.handle_database_error(e)
            return QueryResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                query="",
                error=error_info['message'],
                execution_time=0.0
            )
    
    async def delete_record(self, app_name: str, model_name: str,
                          record_id: Union[str, int]) -> QueryResult:
        """
        Delete record from Django model
        
        Args:
            app_name: Django app name
            model_name: Model name
            record_id: Record ID
            
        Returns:
            QueryResult with deletion result
        """
        try:
            table_name = f"{app_name}_{model_name.lower()}"
            
            query = f"""
                DELETE FROM {table_name}
                WHERE id = :record_id
                RETURNING id
            """
            
            return await self.execute_query(query, {'record_id': record_id})
            
        except Exception as e:
            error_info = self.error_handler.handle_database_error(e)
            return QueryResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                query="",
                error=error_info['message'],
                execution_time=0.0
            )
    
    async def get_table_schema(self, app_name: str, model_name: str) -> Dict[str, Any]:
        """
        Get table schema information
        
        Args:
            app_name: Django app name
            model_name: Model name
            
        Returns:
            Schema information
        """
        try:
            table_name = f"{app_name}_{model_name.lower()}"
            
            # Query for table schema (PostgreSQL specific)
            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """
            
            result = await self.execute_query(query, {'table_name': table_name})
            
            if result.success:
                schema = {
                    'table_name': table_name,
                    'columns': result.data
                }
                return schema
            else:
                return {'error': result.error}
                
        except Exception as e:
            error_info = self.error_handler.handle_database_error(e)
            return {'error': error_info['message']}
    
    async def get_app_models(self, app_name: str) -> List[str]:
        """
        Get list of models for Django app
        
        Args:
            app_name: Django app name
            
        Returns:
            List of model names
        """
        try:
            # Query for tables with app prefix
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name LIKE :pattern
                AND table_schema = 'public'
            """
            
            pattern = f"{app_name}_%"
            result = await self.execute_query(query, {'pattern': pattern})
            
            if result.success:
                models = []
                for row in result.data:
                    table_name = row['table_name']
                    # Extract model name from table name
                    model_name = table_name.replace(f"{app_name}_", "")
                    models.append(model_name)
                return models
            else:
                return []
                
        except Exception as e:
            self.logger.error("Failed to get app models", app_name=app_name, error=str(e))
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check
        
        Returns:
            Health check results
        """
        try:
            if not self.async_session_factory:
                await self._initialize_async_engine()
            
            async with self.async_session_factory() as session:
                result = await session.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                
                return {
                    'status': 'healthy',
                    'database_connected': True,
                    'test_query_result': row[0] if row else None
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'database_connected': False,
                'error': str(e)
            }
    
    async def close(self):
        """Close database connections"""
        try:
            if self.async_engine:
                await self.async_engine.dispose()
                self.logger.info("Django ORM adapter closed")
        except Exception as e:
            self.logger.error("Failed to close Django ORM adapter", error=str(e))