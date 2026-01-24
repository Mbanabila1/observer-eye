"""
Four Pillars Data Processors Package

This package implements polymorphic processors for the four pillars of observability:
- Metrics: Quantitative measurements and performance indicators
- Events: Discrete occurrences and state changes
- Logs: Textual records and structured logging data
- Traces: Request flows and distributed transaction tracking

Each processor implements a common interface while providing specialized
processing capabilities for their respective data types.
"""

from .base_processor import BaseObservabilityProcessor, ProcessingResult
from .metrics_processor import MetricsProcessor
from .events_processor import EventsProcessor
from .logs_processor import LogsProcessor
from .traces_processor import TracesProcessor
from .correlation_engine import RealTimeCorrelationEngine
from .deep_system_integration import DeepSystemIntegration

__all__ = [
    'BaseObservabilityProcessor',
    'ProcessingResult',
    'MetricsProcessor',
    'EventsProcessor', 
    'LogsProcessor',
    'TracesProcessor',
    'RealTimeCorrelationEngine',
    'DeepSystemIntegration'
]