"""
Data Warehouse Manager

Manages data warehouse operations for the BI analytics engine including
data extraction, transformation, and loading (ETL) processes.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import structlog

logger = structlog.get_logger(__name__)

class DataWarehouseManager:
    """
    Data Warehouse Manager for BI Analytics
    
    Handles data extraction from various sources, transformation for analytics,
    and provides optimized query interfaces for the BI analytics engine.
    """
    
    def __init__(self, 
                 warehouse_url: Optional[str] = None,
                 operational_db_url: Optional[str] = None,
                 cache_enabled: bool = True):
        
        # Database connections
        self.warehouse_url = warehouse_url or "sqlite:///warehouse.db"  # Default to SQLite for development
        self.operational_db_url = operational_db_url or "sqlite:///observability.db"
        
        self.warehouse_engine = None
        self.operational_engine = None
        
        # Caching
        self.cache_enabled = cache_enabled
        self._query_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Performance tracking
        self._warehouse_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'average_query_time_ms': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_rows_processed': 0
        }
        
        logger.info("Data Warehouse Manager initialized",
                   warehouse_url=self.warehouse_url,
                   cache_enabled=cache_enabled)
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Initialize warehouse connection
            self.warehouse_engine = create_engine(self.warehouse_url, echo=False)
            
            # Initialize operational database connection
            self.operational_engine = create_engine(self.operational_db_url, echo=False)
            
            # Create warehouse schema if needed
            await self._create_warehouse_schema()
            
            logger.info("Data warehouse connections initialized")
            
        except Exception as e:
            logger.error("Failed to initialize data warehouse", error=str(e))
            raise
    
    async def query_observability_data(self, 
                                     data_sources: List[str],
                                     start_time: datetime,
                                     end_time: datetime,
                                     filters: Optional[Dict[str, Any]] = None,
                                     limit: Optional[int] = None) -> pd.DataFrame:
        """
        Query observability data from the warehouse
        
        Args:
            data_sources: List of data source types (metrics, events, logs, traces)
            start_time: Start time for data query
            end_time: End time for data query
            filters: Additional filters to apply
            limit: Maximum number of rows to return
            
        Returns:
            DataFrame with queried data
        """
        start_query_time = time.time()
        self._warehouse_stats['total_queries'] += 1
        
        try:
            # Generate cache key
            cache_key = self._generate_query_cache_key(data_sources, start_time, end_time, filters, limit)
            
            # Check cache first
            if self.cache_enabled and cache_key in self._query_cache:
                cached_result = self._query_cache[cache_key]
                if time.time() - cached_result['timestamp'] < self._cache_ttl:
                    self._warehouse_stats['cache_hits'] += 1
                    logger.debug("Returning cached query result", cache_key=cache_key)
                    return cached_result['data']
            
            self._warehouse_stats['cache_misses'] += 1
            
            # Build and execute query
            query_results = []
            
            for data_source in data_sources:
                source_data = await self._query_data_source(
                    data_source, start_time, end_time, filters, limit
                )
                if not source_data.empty:
                    source_data['data_source'] = data_source
                    query_results.append(source_data)
            
            # Combine results
            if query_results:
                combined_data = pd.concat(query_results, ignore_index=True, sort=False)
            else:
                combined_data = pd.DataFrame()
            
            # Apply global limit if specified
            if limit and len(combined_data) > limit:
                combined_data = combined_data.head(limit)
            
            # Cache result
            if self.cache_enabled:
                self._query_cache[cache_key] = {
                    'data': combined_data,
                    'timestamp': time.time()
                }
            
            # Update statistics
            query_time_ms = (time.time() - start_query_time) * 1000
            self._warehouse_stats['successful_queries'] += 1
            self._warehouse_stats['total_rows_processed'] += len(combined_data)
            self._update_average_query_time(query_time_ms)
            
            logger.info("Data warehouse query completed",
                       data_sources=data_sources,
                       rows_returned=len(combined_data),
                       query_time_ms=query_time_ms)
            
            return combined_data
            
        except Exception as e:
            self._warehouse_stats['failed_queries'] += 1
            logger.error("Data warehouse query failed",
                        data_sources=data_sources,
                        error=str(e))
            return pd.DataFrame()
    
    async def _query_data_source(self, 
                                data_source: str,
                                start_time: datetime,
                                end_time: datetime,
                                filters: Optional[Dict[str, Any]] = None,
                                limit: Optional[int] = None) -> pd.DataFrame:
        """Query a specific data source"""
        
        try:
            # Map data source to table/query
            table_mapping = {
                'metrics': 'observability_metrics',
                'events': 'observability_events', 
                'logs': 'observability_logs',
                'traces': 'observability_traces'
            }
            
            table_name = table_mapping.get(data_source)
            if not table_name:
                logger.warning("Unknown data source", data_source=data_source)
                return pd.DataFrame()
            
            # Build base query
            query_parts = [f"SELECT * FROM {table_name}"]
            query_params = {}
            
            # Add time range filter
            query_parts.append("WHERE timestamp >= :start_time AND timestamp <= :end_time")
            query_params['start_time'] = start_time
            query_params['end_time'] = end_time
            
            # Add additional filters
            if filters:
                for field, value in filters.items():
                    if isinstance(value, list):
                        placeholders = ','.join([f':filter_{field}_{i}' for i in range(len(value))])
                        query_parts.append(f"AND {field} IN ({placeholders})")
                        for i, v in enumerate(value):
                            query_params[f'filter_{field}_{i}'] = v
                    else:
                        query_parts.append(f"AND {field} = :filter_{field}")
                        query_params[f'filter_{field}'] = value
            
            # Add ordering
            query_parts.append("ORDER BY timestamp DESC")
            
            # Add limit
            if limit:
                query_parts.append(f"LIMIT {limit}")
            
            query = ' '.join(query_parts)
            
            # Execute query
            if self.warehouse_engine:
                with self.warehouse_engine.connect() as conn:
                    result = pd.read_sql(text(query), conn, params=query_params)
            else:
                # Fallback to mock data for development
                result = self._generate_mock_data(data_source, start_time, end_time, limit or 100)
            
            return result
            
        except Exception as e:
            logger.error("Error querying data source",
                        data_source=data_source,
                        error=str(e))
            
            # Return mock data as fallback
            return self._generate_mock_data(data_source, start_time, end_time, limit or 100)
    
    def _generate_mock_data(self, data_source: str, start_time: datetime, 
                           end_time: datetime, num_rows: int) -> pd.DataFrame:
        """Generate mock data for development and testing"""
        
        try:
            # Generate time series
            time_range = pd.date_range(start=start_time, end=end_time, periods=num_rows)
            
            base_data = {
                'id': [f"{data_source}_{i}" for i in range(num_rows)],
                'timestamp': time_range,
                'correlation_id': [f"corr_{np.random.randint(1000, 9999)}" for _ in range(num_rows)],
                'source_service': np.random.choice(['web-api', 'user-service', 'payment-service', 'notification-service'], num_rows),
                'environment': np.random.choice(['production', 'staging', 'development'], num_rows)
            }
            
            # Add data source specific fields
            if data_source == 'metrics':
                base_data.update({
                    'metric_name': np.random.choice(['cpu_usage', 'memory_usage', 'response_time', 'error_rate'], num_rows),
                    'metric_value': np.random.normal(50, 20, num_rows),
                    'metric_type': np.random.choice(['gauge', 'counter', 'histogram'], num_rows),
                    'unit': np.random.choice(['percent', 'milliseconds', 'count'], num_rows)
                })
            
            elif data_source == 'events':
                base_data.update({
                    'event_type': np.random.choice(['user_login', 'payment_processed', 'error_occurred', 'system_alert'], num_rows),
                    'severity': np.random.choice(['info', 'warning', 'error', 'critical'], num_rows),
                    'category': np.random.choice(['system', 'application', 'security', 'business'], num_rows),
                    'message': [f"Event message {i}" for i in range(num_rows)]
                })
            
            elif data_source == 'logs':
                base_data.update({
                    'log_level': np.random.choice(['debug', 'info', 'warn', 'error', 'fatal'], num_rows),
                    'logger_name': np.random.choice(['app.controller', 'app.service', 'app.database', 'app.security'], num_rows),
                    'message': [f"Log message {i}" for i in range(num_rows)],
                    'thread_id': np.random.randint(1000, 9999, num_rows)
                })
            
            elif data_source == 'traces':
                base_data.update({
                    'trace_id': [f"trace_{np.random.randint(100000, 999999)}" for _ in range(num_rows)],
                    'span_id': [f"span_{np.random.randint(1000, 9999)}" for _ in range(num_rows)],
                    'operation_name': np.random.choice(['http_request', 'database_query', 'cache_lookup', 'external_api'], num_rows),
                    'duration_microseconds': np.random.exponential(1000, num_rows),
                    'status': np.random.choice(['ok', 'error', 'timeout'], num_rows)
                })
            
            return pd.DataFrame(base_data)
            
        except Exception as e:
            logger.error("Error generating mock data", data_source=data_source, error=str(e))
            return pd.DataFrame()
    
    async def _create_warehouse_schema(self):
        """Create warehouse schema and tables if they don't exist"""
        
        if not self.warehouse_engine:
            return
        
        try:
            schema_sql = """
            -- Metrics fact table
            CREATE TABLE IF NOT EXISTS observability_metrics (
                id TEXT PRIMARY KEY,
                timestamp DATETIME,
                correlation_id TEXT,
                source_service TEXT,
                environment TEXT,
                metric_name TEXT,
                metric_value REAL,
                metric_type TEXT,
                unit TEXT,
                labels TEXT
            );
            
            -- Events fact table
            CREATE TABLE IF NOT EXISTS observability_events (
                id TEXT PRIMARY KEY,
                timestamp DATETIME,
                correlation_id TEXT,
                source_service TEXT,
                environment TEXT,
                event_type TEXT,
                severity TEXT,
                category TEXT,
                message TEXT,
                attributes TEXT
            );
            
            -- Logs fact table
            CREATE TABLE IF NOT EXISTS observability_logs (
                id TEXT PRIMARY KEY,
                timestamp DATETIME,
                correlation_id TEXT,
                source_service TEXT,
                environment TEXT,
                log_level TEXT,
                logger_name TEXT,
                message TEXT,
                thread_id TEXT,
                structured_data TEXT
            );
            
            -- Traces fact table
            CREATE TABLE IF NOT EXISTS observability_traces (
                id TEXT PRIMARY KEY,
                timestamp DATETIME,
                correlation_id TEXT,
                source_service TEXT,
                environment TEXT,
                trace_id TEXT,
                span_id TEXT,
                operation_name TEXT,
                duration_microseconds INTEGER,
                status TEXT,
                tags TEXT
            );
            
            -- Aggregated metrics table for BI
            CREATE TABLE IF NOT EXISTS bi_aggregated_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_key INTEGER,
                hour_key INTEGER,
                service_name TEXT,
                environment TEXT,
                metric_name TEXT,
                avg_value REAL,
                min_value REAL,
                max_value REAL,
                sum_value REAL,
                count_value INTEGER,
                aggregation_level TEXT
            );
            
            -- KPI definitions table
            CREATE TABLE IF NOT EXISTS bi_kpi_definitions (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                calculation_formula TEXT,
                target_value REAL,
                warning_threshold REAL,
                critical_threshold REAL,
                unit_of_measure TEXT,
                category TEXT,
                is_active BOOLEAN
            );
            
            -- Report definitions table
            CREATE TABLE IF NOT EXISTS bi_report_definitions (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                report_type TEXT,
                query_definition TEXT,
                visualization_config TEXT,
                schedule_config TEXT,
                created_by TEXT,
                is_active BOOLEAN,
                created_at DATETIME
            );
            """
            
            with self.warehouse_engine.connect() as conn:
                for statement in schema_sql.split(';'):
                    if statement.strip():
                        conn.execute(text(statement))
                conn.commit()
            
            logger.info("Warehouse schema created successfully")
            
        except Exception as e:
            logger.error("Error creating warehouse schema", error=str(e))
    
    async def store_aggregated_data(self, aggregated_data: pd.DataFrame, table_name: str):
        """Store aggregated data in the warehouse"""
        
        try:
            if self.warehouse_engine and not aggregated_data.empty:
                aggregated_data.to_sql(table_name, self.warehouse_engine, 
                                     if_exists='append', index=False)
                
                logger.info("Aggregated data stored",
                           table_name=table_name,
                           rows_stored=len(aggregated_data))
        
        except Exception as e:
            logger.error("Error storing aggregated data",
                        table_name=table_name,
                        error=str(e))
    
    async def execute_custom_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute a custom SQL query"""
        
        try:
            if not self.warehouse_engine:
                logger.warning("Warehouse engine not initialized")
                return pd.DataFrame()
            
            with self.warehouse_engine.connect() as conn:
                result = pd.read_sql(text(query), conn, params=params or {})
            
            logger.info("Custom query executed",
                       rows_returned=len(result))
            
            return result
            
        except Exception as e:
            logger.error("Error executing custom query",
                        query=query[:100],  # Log first 100 chars
                        error=str(e))
            return pd.DataFrame()
    
    def _generate_query_cache_key(self, data_sources: List[str], start_time: datetime,
                                 end_time: datetime, filters: Optional[Dict[str, Any]], 
                                 limit: Optional[int]) -> str:
        """Generate cache key for query"""
        key_components = [
            '_'.join(sorted(data_sources)),
            start_time.isoformat(),
            end_time.isoformat(),
            str(hash(str(sorted(filters.items())) if filters else '')),
            str(limit or 'no_limit')
        ]
        return hash('_'.join(key_components))
    
    def _update_average_query_time(self, query_time_ms: float):
        """Update average query time statistics"""
        current_avg = self._warehouse_stats['average_query_time_ms']
        successful_queries = self._warehouse_stats['successful_queries']
        
        if successful_queries > 1:
            new_avg = ((current_avg * (successful_queries - 1)) + query_time_ms) / successful_queries
            self._warehouse_stats['average_query_time_ms'] = new_avg
        else:
            self._warehouse_stats['average_query_time_ms'] = query_time_ms
    
    async def get_warehouse_statistics(self) -> Dict[str, Any]:
        """Get warehouse statistics"""
        return {
            'warehouse_stats': self._warehouse_stats.copy(),
            'cache_stats': {
                'cache_size': len(self._query_cache),
                'cache_hit_rate': (
                    self._warehouse_stats['cache_hits'] / 
                    (self._warehouse_stats['cache_hits'] + self._warehouse_stats['cache_misses'])
                    if (self._warehouse_stats['cache_hits'] + self._warehouse_stats['cache_misses']) > 0 else 0.0
                )
            },
            'configuration': {
                'warehouse_url': self.warehouse_url,
                'cache_enabled': self.cache_enabled,
                'cache_ttl_seconds': self._cache_ttl
            }
        }
    
    async def clear_cache(self):
        """Clear the query cache"""
        self._query_cache.clear()
        logger.info("Warehouse query cache cleared")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for the data warehouse"""
        try:
            # Test database connectivity
            if self.warehouse_engine:
                with self.warehouse_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                warehouse_status = "healthy"
            else:
                warehouse_status = "not_initialized"
            
            return {
                'status': warehouse_status,
                'statistics': await self.get_warehouse_statistics(),
                'last_check': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    async def shutdown(self):
        """Shutdown warehouse connections"""
        try:
            if self.warehouse_engine:
                self.warehouse_engine.dispose()
            if self.operational_engine:
                self.operational_engine.dispose()
            
            logger.info("Data warehouse connections closed")
        
        except Exception as e:
            logger.error("Error shutting down warehouse", error=str(e))