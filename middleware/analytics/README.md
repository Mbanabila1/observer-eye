# BI Analytics Engine

Advanced Business Intelligence and Analytics Engine for the Observer-Eye observability platform.

## Overview

The BI Analytics Engine provides comprehensive analytics capabilities including statistical analysis, automated report generation, machine learning pipelines, and predictive analytics for observability data.

## Components

### Core Components

1. **BIAnalyticsEngine** - Main analytics processing engine
2. **DataWarehouseManager** - Data extraction and warehouse operations
3. **ReportGenerator** - Automated report generation with multiple formats
4. **KPICalculator** - Key Performance Indicator calculation and monitoring
5. **TrendAnalyzer** - Advanced trend analysis and forecasting
6. **MachineLearningPipeline** - ML models for predictive analytics

### Key Features

- **Statistical Analysis**: Comprehensive statistical analysis of observability data
- **Real-time Analytics**: Process analytics requests with millisecond precision
- **Automated Reporting**: Generate reports in PDF, Excel, HTML, CSV, and JSON formats
- **KPI Monitoring**: Calculate and monitor key performance indicators
- **Trend Analysis**: Linear, seasonal, and anomaly detection analysis
- **Machine Learning**: Anomaly detection and performance prediction models
- **Data Quality Assessment**: Automated data quality scoring and validation
- **Predictive Analytics**: Forecasting and capacity planning capabilities

## Usage

### Basic Analytics Request

```python
from analytics import BIAnalyticsEngine, AnalyticsRequest, TimeRange, AnalyticsMetric
from datetime import datetime

# Create analytics engine
engine = BIAnalyticsEngine()

# Create analytics request
request = AnalyticsRequest(
    time_range=TimeRange(
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 1, 2)
    ),
    data_sources=['metrics', 'events'],
    metrics=[AnalyticsMetric.MEAN, AnalyticsMetric.COUNT, AnalyticsMetric.MAX]
)

# Process request
result = await engine.process_analytics_request(request)
```

### Report Generation

```python
from analytics import ReportGenerator, ReportRequest, ReportType, ReportFormat

# Create report generator
generator = ReportGenerator(analytics_engine)

# Create report request
report_request = ReportRequest(
    report_type=ReportType.EXECUTIVE,
    report_format=ReportFormat.PDF,
    title="Monthly Performance Report",
    analytics_request=analytics_request,
    include_charts=True,
    include_executive_summary=True
)

# Generate report
report_result = await generator.generate_report(report_request)
```

### KPI Calculation

```python
from analytics import KPICalculator, KPIRequest, KPIType

# Create KPI calculator
calculator = KPICalculator(data_warehouse)

# Calculate availability KPI
kpi_request = KPIRequest(
    kpi_type=KPIType.AVAILABILITY,
    kpi_name="Service Availability",
    time_range=time_range,
    target_value=99.9,
    warning_threshold=99.0,
    critical_threshold=95.0
)

kpi_result = await calculator.calculate_kpi(kpi_request)
```

### Trend Analysis

```python
from analytics import TrendAnalyzer, TrendAnalysisRequest, TrendType

# Create trend analyzer
analyzer = TrendAnalyzer(data_warehouse)

# Analyze linear trend
trend_request = TrendAnalysisRequest(
    trend_type=TrendType.LINEAR,
    time_range=time_range,
    metric_field='response_time',
    data_sources=['metrics'],
    forecast_periods=24
)

trend_result = await analyzer.analyze_trend(trend_request)
```

### Machine Learning

```python
from analytics import MachineLearningPipeline

# Create ML pipeline
ml_pipeline = MachineLearningPipeline()

# Train anomaly detection model
training_result = await ml_pipeline.train_anomaly_detection_model(
    training_data=historical_data,
    model_name="response_time_anomaly_detector"
)

# Predict anomalies
prediction_result = await ml_pipeline.predict_anomalies(
    data=new_data,
    model_name="response_time_anomaly_detector"
)
```

## API Endpoints

### Analytics Processing

- `POST /analytics/analyze` - Process analytics request
- `GET /analytics/statistics` - Get analytics statistics
- `GET /analytics/health` - Health check

### Report Generation

- `POST /analytics/reports/generate` - Generate report
- `GET /analytics/reports/{report_id}` - Get report status

### KPI Management

- `POST /analytics/kpi/calculate` - Calculate KPI
- `GET /analytics/kpi/definitions` - List KPI definitions

### Trend Analysis

- `POST /analytics/trends/analyze` - Perform trend analysis
- `GET /analytics/trends/types` - List supported trend types

### Machine Learning

- `POST /analytics/ml/train/anomaly` - Train anomaly detection model
- `POST /analytics/ml/predict/anomaly` - Predict anomalies
- `POST /analytics/ml/train/performance` - Train performance prediction model
- `POST /analytics/ml/predict/performance` - Predict performance
- `GET /analytics/ml/models` - List available models

## Configuration

### Environment Variables

```bash
# Analytics Configuration
ANALYTICS_URL=http://localhost:8002
WAREHOUSE_URL=clickhouse://localhost:8123/warehouse
REDIS_URL=redis://localhost:6379

# ML Configuration
ML_MODELS_DIRECTORY=ml_models
ML_ENABLE_PROPHET=true
ML_MAX_FEATURES=50
ML_MIN_SAMPLES=100

# Report Configuration
REPORTS_DIRECTORY=reports
TEMPLATES_DIRECTORY=templates
REPORT_CACHE_TTL=300
```

### Data Sources

The analytics engine supports multiple data sources:

- **metrics** - Performance and system metrics
- **events** - System and application events
- **logs** - Application and system logs
- **traces** - Distributed tracing data

### Supported Metrics

- **MEAN** - Average value
- **MEDIAN** - Median value
- **MODE** - Most frequent value
- **STANDARD_DEVIATION** - Standard deviation
- **VARIANCE** - Variance
- **MIN/MAX** - Minimum and maximum values
- **COUNT** - Count of values
- **SUM** - Sum of values
- **PERCENTILE_95/99** - 95th and 99th percentiles
- **CORRELATION** - Correlation analysis
- **REGRESSION** - Regression analysis

### KPI Types

- **AVAILABILITY** - Service availability percentage
- **ERROR_RATE** - Error rate percentage
- **LATENCY** - Average response time
- **THROUGHPUT** - Requests per time period
- **RESOURCE_UTILIZATION** - Resource usage percentage
- **PERFORMANCE** - Composite performance score
- **SECURITY_SCORE** - Security assessment score
- **COMPLIANCE_SCORE** - Compliance assessment score
- **CUSTOM** - Custom KPI with formula

### Trend Analysis Types

- **LINEAR** - Linear trend detection
- **SEASONAL** - Seasonal pattern analysis
- **ANOMALY_DETECTION** - Anomaly detection
- **FORECAST** - Predictive forecasting

### Report Formats

- **PDF** - Portable Document Format
- **EXCEL** - Microsoft Excel format
- **HTML** - Web-based interactive reports
- **CSV** - Comma-separated values
- **JSON** - JavaScript Object Notation

## Dependencies

### Core Dependencies

- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing
- **scipy** - Scientific computing
- **scikit-learn** - Machine learning library
- **matplotlib** - Plotting library
- **plotly** - Interactive plotting
- **jinja2** - Template engine
- **reportlab** - PDF generation

### Optional Dependencies

- **prophet** - Time series forecasting (Facebook Prophet)
- **openpyxl** - Excel file handling
- **xlsxwriter** - Excel file writing
- **seaborn** - Statistical data visualization

## Performance Considerations

### Optimization Features

- **Result Caching** - Cache analytics results for improved performance
- **Data Sampling** - Automatic sampling for large datasets
- **Parallel Processing** - Multi-threaded processing where applicable
- **Memory Management** - Efficient memory usage for large datasets
- **Query Optimization** - Optimized database queries

### Scalability

- **Horizontal Scaling** - Support for multiple analytics engine instances
- **Load Balancing** - Distribute analytics requests across instances
- **Resource Limits** - Configurable limits for memory and processing time
- **Background Processing** - Asynchronous processing for long-running tasks

## Monitoring and Observability

### Health Checks

The analytics engine provides comprehensive health checks:

- Component status monitoring
- Performance metrics tracking
- Error rate monitoring
- Resource utilization tracking

### Statistics

Detailed statistics are available for:

- Request processing times
- Success/failure rates
- Cache hit rates
- Model accuracy metrics
- Data quality scores

### Logging

Structured logging with:

- Request tracing
- Performance metrics
- Error details
- Debug information

## Security

### Data Protection

- Input validation and sanitization
- SQL injection prevention
- Access control integration
- Audit logging

### Model Security

- Model validation and verification
- Secure model storage
- Access control for ML models
- Model versioning and rollback

## Testing

### Test Coverage

- Unit tests for all components
- Integration tests for API endpoints
- Performance tests for scalability
- Property-based tests for correctness

### Running Tests

```bash
# Run all tests
pytest test_bi_analytics.py -v

# Run specific test categories
pytest test_bi_analytics.py::TestBIAnalyticsIntegration -v
pytest test_bi_analytics.py::TestBIAnalyticsModels -v

# Run with coverage
pytest test_bi_analytics.py --cov=analytics --cov-report=html
```

## Troubleshooting

### Common Issues

1. **Memory Issues**: Reduce data sample size or increase memory limits
2. **Performance Issues**: Enable caching and optimize queries
3. **Model Training Failures**: Ensure sufficient training data
4. **Report Generation Errors**: Check template configurations

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('analytics').setLevel(logging.DEBUG)
```

### Health Check Endpoints

Use health check endpoints to diagnose issues:

- `/analytics/health` - Overall health status
- `/analytics/statistics` - Performance statistics
- `/analytics/ml/models` - ML model status

## Contributing

### Development Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `pytest test_bi_analytics.py`
3. Check code style: `black analytics/`
4. Run type checking: `mypy analytics/`

### Adding New Features

1. Create feature branch
2. Implement feature with tests
3. Update documentation
4. Submit pull request

## License

This BI Analytics Engine is part of the Observer-Eye observability platform.