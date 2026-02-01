"""
Data Ingestion Views for Observer Eye Platform

These views handle real data ingestion from external sources.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings

from .data_ingestion import (
    ingest_metrics_data,
    ingest_log_data,
    ingest_telemetry_data,
    DataSourceType,
    DataValidationLevel
)

import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def ingest_metrics(request):
    """
    Endpoint for ingesting real metrics data.
    
    Expected JSON format:
    {
        "source": "application_name",
        "metrics": [
            {
                "metric_name": "cpu_usage",
                "value": 75.5,
                "unit": "percent",
                "timestamp": "2024-01-01T12:00:00Z",
                "tags": {"host": "server1", "env": "production"}
            }
        ]
    }
    """
    try:
        data = json.loads(request.body)
        source = data.get('source', 'unknown')
        metrics = data.get('metrics', [])
        
        if not metrics:
            return JsonResponse({
                'success': False,
                'error': 'No metrics data provided'
            }, status=400)
        
        # Add data_type to each metric
        for metric in metrics:
            metric['data_type'] = 'metrics'
        
        # Run async ingestion
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ingest_metrics_data(metrics, source))
        finally:
            loop.close()
        
        return JsonResponse({
            'success': result.success,
            'records_processed': result.records_processed,
            'records_failed': result.records_failed,
            'processing_time_ms': result.processing_time_ms,
            'errors': result.errors,
            'warnings': result.warnings,
            'timestamp': result.timestamp.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.error(f"Metrics ingestion failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def ingest_logs(request):
    """
    Endpoint for ingesting real log data.
    
    Expected JSON format:
    {
        "source": "application_name",
        "logs": [
            {
                "level": "ERROR",
                "message": "Database connection failed",
                "timestamp": "2024-01-01T12:00:00Z",
                "context": {"user_id": "123", "request_id": "abc"}
            }
        ]
    }
    """
    try:
        data = json.loads(request.body)
        source = data.get('source', 'unknown')
        logs = data.get('logs', [])
        
        if not logs:
            return JsonResponse({
                'success': False,
                'error': 'No log data provided'
            }, status=400)
        
        # Add data_type to each log
        for log in logs:
            log['data_type'] = 'log'
        
        # Run async ingestion
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ingest_log_data(logs, source))
        finally:
            loop.close()
        
        return JsonResponse({
            'success': result.success,
            'records_processed': result.records_processed,
            'records_failed': result.records_failed,
            'processing_time_ms': result.processing_time_ms,
            'errors': result.errors,
            'warnings': result.warnings,
            'timestamp': result.timestamp.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.error(f"Log ingestion failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def ingest_telemetry(request):
    """
    Endpoint for ingesting real telemetry data.
    
    Expected JSON format:
    {
        "source": "service_name",
        "telemetry": [
            {
                "trace_id": "abc123",
                "span_id": "def456",
                "operation": "database_query",
                "duration_ms": 150,
                "timestamp": "2024-01-01T12:00:00Z",
                "attributes": {"query": "SELECT * FROM users"}
            }
        ]
    }
    """
    try:
        data = json.loads(request.body)
        source = data.get('source', 'unknown')
        telemetry = data.get('telemetry', [])
        
        if not telemetry:
            return JsonResponse({
                'success': False,
                'error': 'No telemetry data provided'
            }, status=400)
        
        # Add data_type to each telemetry record
        for record in telemetry:
            record['data_type'] = 'telemetry'
        
        # Run async ingestion
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ingest_telemetry_data(telemetry, source))
        finally:
            loop.close()
        
        return JsonResponse({
            'success': result.success,
            'records_processed': result.records_processed,
            'records_failed': result.records_failed,
            'processing_time_ms': result.processing_time_ms,
            'errors': result.errors,
            'warnings': result.warnings,
            'timestamp': result.timestamp.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.error(f"Telemetry ingestion failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BulkIngestionView(View):
    """
    View for bulk data ingestion supporting multiple data types.
    """
    
    def post(self, request):
        """
        Handle bulk ingestion of mixed data types.
        
        Expected JSON format:
        {
            "source": "application_name",
            "data": [
                {
                    "data_type": "metrics",
                    "metric_name": "cpu_usage",
                    "value": 75.5,
                    ...
                },
                {
                    "data_type": "log",
                    "level": "ERROR",
                    "message": "Error occurred",
                    ...
                }
            ]
        }
        """
        try:
            data = json.loads(request.body)
            source = data.get('source', 'unknown')
            records = data.get('data', [])
            
            if not records:
                return JsonResponse({
                    'success': False,
                    'error': 'No data provided'
                }, status=400)
            
            # Separate records by type
            metrics_records = []
            log_records = []
            telemetry_records = []
            
            for record in records:
                data_type = record.get('data_type', 'unknown')
                if data_type == 'metrics':
                    metrics_records.append(record)
                elif data_type == 'log':
                    log_records.append(record)
                elif data_type == 'telemetry':
                    telemetry_records.append(record)
            
            # Process each type separately
            results = []
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if metrics_records:
                    result = loop.run_until_complete(ingest_metrics_data(metrics_records, source))
                    results.append({
                        'data_type': 'metrics',
                        'result': {
                            'success': result.success,
                            'records_processed': result.records_processed,
                            'records_failed': result.records_failed,
                            'errors': result.errors
                        }
                    })
                
                if log_records:
                    result = loop.run_until_complete(ingest_log_data(log_records, source))
                    results.append({
                        'data_type': 'logs',
                        'result': {
                            'success': result.success,
                            'records_processed': result.records_processed,
                            'records_failed': result.records_failed,
                            'errors': result.errors
                        }
                    })
                
                if telemetry_records:
                    result = loop.run_until_complete(ingest_telemetry_data(telemetry_records, source))
                    results.append({
                        'data_type': 'telemetry',
                        'result': {
                            'success': result.success,
                            'records_processed': result.records_processed,
                            'records_failed': result.records_failed,
                            'errors': result.errors
                        }
                    })
            finally:
                loop.close()
            
            # Calculate overall success
            overall_success = all(r['result']['success'] for r in results)
            total_processed = sum(r['result']['records_processed'] for r in results)
            total_failed = sum(r['result']['records_failed'] for r in results)
            
            return JsonResponse({
                'success': overall_success,
                'total_records_processed': total_processed,
                'total_records_failed': total_failed,
                'results_by_type': results,
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON format'
            }, status=400)
        except Exception as e:
            logger.error(f"Bulk ingestion failed: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


@require_http_methods(["GET"])
def ingestion_status(request):
    """
    Get the status of the data ingestion system.
    """
    try:
        # This would typically check the health of ingestion components
        status = {
            'ingestion_enabled': True,
            'supported_data_types': ['metrics', 'logs', 'telemetry'],
            'endpoints': {
                'metrics': '/api/ingest/metrics/',
                'logs': '/api/ingest/logs/',
                'telemetry': '/api/ingest/telemetry/',
                'bulk': '/api/ingest/bulk/'
            },
            'validation_levels': ['strict', 'moderate', 'lenient'],
            'max_batch_size': 1000,
            'timestamp': datetime.now().isoformat()
        }
        
        return JsonResponse(status)
        
    except Exception as e:
        logger.error(f"Failed to get ingestion status: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get status'
        }, status=500)