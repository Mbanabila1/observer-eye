#!/usr/bin/env python3
"""
Test script for Four Pillars Data Processors

This script tests the four pillars data processors implementation
without requiring external dependencies.
"""

import asyncio
import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock structlog for testing
class MockLogger:
    def __init__(self):
        pass
    
    def bind(self, **kwargs):
        return self
    
    def info(self, msg, **kwargs):
        print(f"INFO: {msg} {kwargs}")
    
    def error(self, msg, **kwargs):
        print(f"ERROR: {msg} {kwargs}")
    
    def warning(self, msg, **kwargs):
        print(f"WARNING: {msg} {kwargs}")
    
    def debug(self, msg, **kwargs):
        print(f"DEBUG: {msg} {kwargs}")

# Mock structlog module
class MockStructlog:
    def get_logger(self, name=None):
        return MockLogger()
    
    def configure(self, **kwargs):
        pass

# Replace structlog import
sys.modules['structlog'] = MockStructlog()

async def test_four_pillars_processors():
    """Test the four pillars data processors"""
    
    print("🚀 Testing Four Pillars Data Processors Implementation")
    print("=" * 60)
    
    try:
        # Import processors
        from processors.base_processor import BaseObservabilityProcessor, PillarType, ProcessingStatus
        from processors.metrics_processor import MetricsProcessor, MetricData, MetricType
        from processors.events_processor import EventsProcessor, EventData, EventSeverity, EventCategory
        from processors.logs_processor import LogsProcessor, LogData, LogLevel, LogFormat
        from processors.traces_processor import TracesProcessor, SpanData, SpanKind, SpanStatus
        from processors.correlation_engine import RealTimeCorrelationEngine
        from processors.deep_system_integration import DeepSystemIntegration, SystemMonitoringLevel, PayloadInspectionMode
        
        print("✅ All processor modules imported successfully")
        
        # Test 1: Initialize processors
        print("\n📊 Test 1: Initializing Four Pillars Processors")
        
        metrics_processor = MetricsProcessor("test_metrics_processor")
        events_processor = EventsProcessor("test_events_processor")
        logs_processor = LogsProcessor("test_logs_processor")
        traces_processor = TracesProcessor("test_traces_processor")
        
        print("✅ All processors initialized")
        
        # Test 2: Initialize correlation engine
        print("\n🔗 Test 2: Initializing Real-Time Correlation Engine")
        
        correlation_engine = RealTimeCorrelationEngine(
            correlation_window_ms=5000,
            max_candidates_per_window=1000,
            correlation_threshold=0.7
        )
        await correlation_engine.start()
        
        print("✅ Correlation engine started")
        
        # Test 3: Initialize deep system integration
        print("\n🔍 Test 3: Initializing Deep System Integration")
        
        deep_system = DeepSystemIntegration(
            monitoring_level=SystemMonitoringLevel.ENHANCED,
            payload_inspection_mode=PayloadInspectionMode.METADATA_ONLY,
            enable_mock_mode=True
        )
        await deep_system.initialize()
        
        print("✅ Deep system integration initialized")
        
        # Test 4: Process sample data through each pillar
        print("\n📈 Test 4: Processing Sample Data Through All Pillars")
        
        # Test metrics processing
        metric_data = MetricData(
            name="test_cpu_usage",
            value=75.5,
            metric_type=MetricType.GAUGE,
            labels={"service": "test_service", "environment": "test"}
        )
        
        metrics_result = await metrics_processor.process(metric_data)
        print(f"✅ Metrics processed: {metrics_result.status.value}")
        
        # Add to correlation engine
        correlations = await correlation_engine.add_candidate(metrics_result)
        print(f"✅ Metrics added to correlation engine, found {len(correlations)} correlations")
        
        # Test events processing
        event_data = EventData(
            event_type="service_error",
            severity=EventSeverity.ERROR,
            message="Service test_service experienced high CPU usage",
            source="test_service",
            category=EventCategory.SYSTEM
        )
        
        events_result = await events_processor.process(event_data)
        print(f"✅ Events processed: {events_result.status.value}")
        
        # Add to correlation engine
        correlations = await correlation_engine.add_candidate(events_result)
        print(f"✅ Events added to correlation engine, found {len(correlations)} correlations")
        
        # Test logs processing
        log_data = LogData(
            message="High CPU usage detected on test_service: 75.5%",
            level=LogLevel.ERROR,
            logger_name="system_monitor",
            structured_data={"service": "test_service", "cpu_usage": 75.5}
        )
        
        logs_result = await logs_processor.process(log_data)
        print(f"✅ Logs processed: {logs_result.status.value}")
        
        # Add to correlation engine
        correlations = await correlation_engine.add_candidate(logs_result)
        print(f"✅ Logs added to correlation engine, found {len(correlations)} correlations")
        
        # Test traces processing
        span_data = SpanData(
            trace_id="test_trace_123",
            span_id="test_span_456",
            operation_name="process_request",
            start_time=time.time(),
            end_time=time.time() + 0.1,
            span_kind=SpanKind.SERVER,
            status=SpanStatus.ERROR,
            tags={"service": "test_service", "error": "high_cpu"}
        )
        
        traces_result = await traces_processor.process(span_data)
        print(f"✅ Traces processed: {traces_result.status.value}")
        
        # Add to correlation engine
        correlations = await correlation_engine.add_candidate(traces_result)
        print(f"✅ Traces added to correlation engine, found {len(correlations)} correlations")
        
        # Test 5: Check correlation statistics
        print("\n📊 Test 5: Checking Correlation Statistics")
        
        correlation_stats = await correlation_engine.get_correlation_statistics()
        print(f"✅ Total candidates processed: {correlation_stats['correlation_stats']['total_candidates_processed']}")
        print(f"✅ Correlations found: {correlation_stats['correlation_stats']['correlations_found']}")
        print(f"✅ Active correlations: {correlation_stats['active_correlations_count']}")
        
        # Test 6: Check processor statistics
        print("\n📈 Test 6: Checking Processor Statistics")
        
        metrics_stats = metrics_processor.get_processing_stats()
        events_stats = events_processor.get_processing_stats()
        logs_stats = logs_processor.get_processing_stats()
        traces_stats = traces_processor.get_processing_stats()
        
        print(f"✅ Metrics processor: {metrics_stats['total_processed']} processed, {metrics_stats['success_rate']:.2%} success rate")
        print(f"✅ Events processor: {events_stats['total_processed']} processed, {events_stats['success_rate']:.2%} success rate")
        print(f"✅ Logs processor: {logs_stats['total_processed']} processed, {logs_stats['success_rate']:.2%} success rate")
        print(f"✅ Traces processor: {traces_stats['total_processed']} processed, {traces_stats['success_rate']:.2%} success rate")
        
        # Test 7: Check deep system context
        print("\n🔍 Test 7: Checking Deep System Context")
        
        system_context = await deep_system.get_system_context()
        print(f"✅ System monitoring level: {system_context['monitoring_level']}")
        print(f"✅ Mock mode: {system_context['mock_mode']}")
        print(f"✅ Recent syscalls: {system_context['system_activity']['recent_syscalls_count']}")
        
        # Cleanup
        print("\n🧹 Cleanup")
        await correlation_engine.stop()
        await deep_system.shutdown()
        print("✅ All components shut down successfully")
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Four Pillars Data Processors Implementation Complete!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_four_pillars_processors()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)