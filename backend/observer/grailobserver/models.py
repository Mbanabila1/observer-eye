"""
Grail Observer models for specialized observability features.
Provides advanced monitoring, analysis, and observability patterns for the Observer Eye Platform.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
import json

from core.models import BaseModel, User


class ObservabilityTarget(BaseModel):
    """
    Represents a target system or service being observed.
    Can be internal services, external dependencies, or infrastructure components.
    """
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    target_type = models.CharField(
        max_length=50,
        choices=[
            ('service', 'Microservice'),
            ('database', 'Database'),
            ('cache', 'Cache System'),
            ('queue', 'Message Queue'),
            ('api', 'External API'),
            ('infrastructure', 'Infrastructure Component'),
            ('custom', 'Custom Target'),
        ]
    )
    endpoint_url = models.URLField(blank=True, help_text="Primary endpoint for health checks")
    health_check_config = models.JSONField(default=dict, help_text="Health check configuration")
    monitoring_config = models.JSONField(default=dict, help_text="Monitoring configuration")
    sla_config = models.JSONField(default=dict, help_text="SLA and performance targets")
    tags = models.JSONField(default=dict, help_text="Classification and metadata tags")
    is_critical = models.BooleanField(default=False, help_text="Critical system component")
    is_monitored = models.BooleanField(default=True)
    last_health_check = models.DateTimeField(null=True, blank=True)
    health_status = models.CharField(
        max_length=20,
        choices=[
            ('healthy', 'Healthy'),
            ('degraded', 'Degraded'),
            ('unhealthy', 'Unhealthy'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    
    class Meta:
        db_table = 'grail_observability_target'
        indexes = [
            models.Index(fields=['target_type', 'is_monitored']),
            models.Index(fields=['is_critical', 'health_status']),
            models.Index(fields=['last_health_check']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_target_type_display()})"


class ObservabilityPattern(BaseModel):
    """
    Defines observability patterns and best practices.
    Templates for monitoring different types of systems and scenarios.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    pattern_type = models.CharField(
        max_length=50,
        choices=[
            ('sli_slo', 'SLI/SLO Pattern'),
            ('circuit_breaker', 'Circuit Breaker Pattern'),
            ('bulkhead', 'Bulkhead Pattern'),
            ('timeout', 'Timeout Pattern'),
            ('retry', 'Retry Pattern'),
            ('rate_limiting', 'Rate Limiting Pattern'),
            ('health_check', 'Health Check Pattern'),
            ('distributed_tracing', 'Distributed Tracing Pattern'),
            ('custom', 'Custom Pattern'),
        ]
    )
    pattern_definition = models.JSONField(help_text="Pattern implementation details")
    metrics_config = models.JSONField(default=dict, help_text="Metrics collection configuration")
    alerting_rules = models.JSONField(default=list, help_text="Associated alerting rules")
    implementation_guide = models.TextField(blank=True)
    applicable_targets = models.ManyToManyField(
        ObservabilityTarget, 
        blank=True, 
        related_name='patterns',
        help_text="Targets where this pattern applies"
    )
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'grail_observability_pattern'
        indexes = [
            models.Index(fields=['pattern_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_pattern_type_display()})"


class ServiceLevelIndicator(BaseModel):
    """
    Service Level Indicators (SLIs) for measuring service performance.
    """
    target = models.ForeignKey(ObservabilityTarget, on_delete=models.CASCADE, related_name='slis')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sli_type = models.CharField(
        max_length=50,
        choices=[
            ('availability', 'Availability'),
            ('latency', 'Latency'),
            ('throughput', 'Throughput'),
            ('error_rate', 'Error Rate'),
            ('saturation', 'Saturation'),
            ('correctness', 'Correctness'),
            ('freshness', 'Data Freshness'),
            ('custom', 'Custom SLI'),
        ]
    )
    measurement_config = models.JSONField(help_text="How to measure this SLI")
    query_definition = models.TextField(help_text="Query or calculation for SLI value")
    unit = models.CharField(max_length=20)
    good_threshold = models.FloatField(help_text="Threshold for 'good' events")
    total_threshold = models.FloatField(help_text="Threshold for total events")
    calculation_window = models.CharField(
        max_length=20,
        choices=[
            ('1m', '1 Minute'),
            ('5m', '5 Minutes'),
            ('15m', '15 Minutes'),
            ('1h', '1 Hour'),
            ('1d', '1 Day'),
        ],
        default='5m'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'grail_service_level_indicator'
        indexes = [
            models.Index(fields=['target', 'sli_type']),
            models.Index(fields=['is_active']),
        ]
        unique_together = [['target', 'name']]
    
    def __str__(self):
        return f"{self.target.name} - {self.name}"


class ServiceLevelObjective(BaseModel):
    """
    Service Level Objectives (SLOs) based on SLIs.
    """
    sli = models.ForeignKey(ServiceLevelIndicator, on_delete=models.CASCADE, related_name='slos')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_percentage = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Target percentage (e.g., 99.9 for 99.9%)"
    )
    time_window = models.CharField(
        max_length=20,
        choices=[
            ('1h', '1 Hour'),
            ('1d', '1 Day'),
            ('7d', '7 Days'),
            ('30d', '30 Days'),
            ('90d', '90 Days'),
        ]
    )
    error_budget_policy = models.JSONField(default=dict, help_text="Error budget consumption policy")
    alerting_config = models.JSONField(default=dict, help_text="SLO alerting configuration")
    is_active = models.BooleanField(default=True)
    current_performance = models.FloatField(null=True, blank=True, help_text="Current SLO performance")
    error_budget_remaining = models.FloatField(null=True, blank=True, help_text="Remaining error budget")
    last_calculated = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'grail_service_level_objective'
        indexes = [
            models.Index(fields=['sli', 'is_active']),
            models.Index(fields=['current_performance']),
        ]
        unique_together = [['sli', 'name']]
    
    def __str__(self):
        return f"{self.sli.target.name} - {self.name} ({self.target_percentage}%)"


class ObservabilityTrace(BaseModel):
    """
    Distributed tracing data for request flow analysis.
    """
    trace_id = models.CharField(max_length=255, unique=True, db_index=True)
    span_id = models.CharField(max_length=255, db_index=True)
    parent_span_id = models.CharField(max_length=255, blank=True, db_index=True)
    operation_name = models.CharField(max_length=255, db_index=True)
    service_name = models.CharField(max_length=255, db_index=True)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    duration_ms = models.PositiveIntegerField(help_text="Duration in milliseconds")
    status = models.CharField(
        max_length=20,
        choices=[
            ('ok', 'OK'),
            ('error', 'Error'),
            ('timeout', 'Timeout'),
            ('cancelled', 'Cancelled'),
        ]
    )
    tags = models.JSONField(default=dict, help_text="Span tags and metadata")
    logs = models.JSONField(default=list, help_text="Span logs and events")
    baggage = models.JSONField(default=dict, help_text="Trace baggage")
    
    class Meta:
        db_table = 'grail_observability_trace'
        indexes = [
            models.Index(fields=['trace_id', 'start_time']),
            models.Index(fields=['service_name', 'operation_name', 'start_time']),
            models.Index(fields=['status', 'start_time']),
            models.Index(fields=['duration_ms']),
        ]
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.service_name}.{self.operation_name} ({self.duration_ms}ms)"


class ObservabilityAnomaly(BaseModel):
    """
    Detected anomalies in observability data.
    Uses machine learning and statistical analysis for anomaly detection.
    """
    target = models.ForeignKey(ObservabilityTarget, on_delete=models.CASCADE, related_name='anomalies')
    anomaly_type = models.CharField(
        max_length=50,
        choices=[
            ('performance', 'Performance Anomaly'),
            ('error_rate', 'Error Rate Anomaly'),
            ('traffic', 'Traffic Anomaly'),
            ('resource', 'Resource Usage Anomaly'),
            ('pattern', 'Pattern Anomaly'),
            ('correlation', 'Correlation Anomaly'),
        ]
    )
    metric_name = models.CharField(max_length=255, db_index=True)
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    time_window_start = models.DateTimeField()
    time_window_end = models.DateTimeField()
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score between 0 and 1"
    )
    anomaly_score = models.FloatField(help_text="Anomaly score indicating deviation")
    baseline_value = models.FloatField(help_text="Expected baseline value")
    observed_value = models.FloatField(help_text="Observed anomalous value")
    deviation_percentage = models.FloatField(help_text="Percentage deviation from baseline")
    detection_method = models.CharField(max_length=100, help_text="Method used for detection")
    context_data = models.JSONField(default=dict, help_text="Additional context and evidence")
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'grail_observability_anomaly'
        indexes = [
            models.Index(fields=['target', 'anomaly_type', 'detected_at']),
            models.Index(fields=['severity', 'is_acknowledged']),
            models.Index(fields=['confidence_score', 'detected_at']),
        ]
        ordering = ['-detected_at', '-severity']
    
    def __str__(self):
        return f"{self.target.name} - {self.anomaly_type} ({self.severity})"


class ObservabilityPlaybook(BaseModel):
    """
    Runbooks and playbooks for incident response and troubleshooting.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    playbook_type = models.CharField(
        max_length=50,
        choices=[
            ('incident_response', 'Incident Response'),
            ('troubleshooting', 'Troubleshooting Guide'),
            ('maintenance', 'Maintenance Procedure'),
            ('escalation', 'Escalation Procedure'),
            ('recovery', 'Recovery Procedure'),
        ]
    )
    trigger_conditions = models.JSONField(default=list, help_text="Conditions that trigger this playbook")
    steps = models.JSONField(default=list, help_text="Ordered list of steps to execute")
    automation_config = models.JSONField(default=dict, help_text="Automation and tooling configuration")
    applicable_targets = models.ManyToManyField(
        ObservabilityTarget, 
        blank=True, 
        related_name='playbooks'
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_playbooks')
    is_active = models.BooleanField(default=True)
    execution_count = models.PositiveIntegerField(default=0)
    success_rate = models.FloatField(null=True, blank=True, help_text="Success rate of executions")
    average_execution_time = models.PositiveIntegerField(null=True, blank=True, help_text="Average execution time in minutes")
    last_executed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'grail_observability_playbook'
        indexes = [
            models.Index(fields=['playbook_type', 'is_active']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_playbook_type_display()})"


class ObservabilityExperiment(BaseModel):
    """
    Chaos engineering and observability experiments.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    experiment_type = models.CharField(
        max_length=50,
        choices=[
            ('chaos', 'Chaos Engineering'),
            ('load_test', 'Load Testing'),
            ('failure_injection', 'Failure Injection'),
            ('latency_injection', 'Latency Injection'),
            ('resource_exhaustion', 'Resource Exhaustion'),
            ('network_partition', 'Network Partition'),
            ('custom', 'Custom Experiment'),
        ]
    )
    target = models.ForeignKey(ObservabilityTarget, on_delete=models.CASCADE, related_name='experiments')
    hypothesis = models.TextField(help_text="Experiment hypothesis")
    experiment_config = models.JSONField(help_text="Experiment configuration and parameters")
    success_criteria = models.JSONField(help_text="Criteria for experiment success")
    safety_checks = models.JSONField(default=list, help_text="Safety checks and abort conditions")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiments')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('aborted', 'Aborted'),
            ('failed', 'Failed'),
        ],
        default='draft'
    )
    results = models.JSONField(default=dict, help_text="Experiment results and findings")
    lessons_learned = models.TextField(blank=True)
    
    class Meta:
        db_table = 'grail_observability_experiment'
        indexes = [
            models.Index(fields=['target', 'status']),
            models.Index(fields=['experiment_type', 'status']),
            models.Index(fields=['scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.target.name}"


class ObservabilityInsight(BaseModel):
    """
    AI-generated insights and recommendations from observability data.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    insight_type = models.CharField(
        max_length=50,
        choices=[
            ('performance_optimization', 'Performance Optimization'),
            ('cost_optimization', 'Cost Optimization'),
            ('reliability_improvement', 'Reliability Improvement'),
            ('security_concern', 'Security Concern'),
            ('capacity_planning', 'Capacity Planning'),
            ('pattern_detection', 'Pattern Detection'),
            ('correlation_analysis', 'Correlation Analysis'),
        ]
    )
    targets = models.ManyToManyField(ObservabilityTarget, related_name='insights')
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    impact_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    evidence_data = models.JSONField(default=dict, help_text="Supporting evidence and data")
    recommendations = models.JSONField(default=list, help_text="Actionable recommendations")
    estimated_impact = models.JSONField(default=dict, help_text="Estimated impact of recommendations")
    generated_by = models.CharField(max_length=100, help_text="AI model or algorithm used")
    is_actionable = models.BooleanField(default=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'grail_observability_insight'
        indexes = [
            models.Index(fields=['insight_type', 'confidence_score']),
            models.Index(fields=['is_actionable', 'is_acknowledged']),
        ]
        ordering = ['-confidence_score', '-impact_score', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_insight_type_display()})"
