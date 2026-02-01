"""
Security Metrics models for the Observer Eye Platform.
Collects and stores security-related metrics and threat intelligence data.
"""

from django.db import models
from django.utils import timezone

from core.models import BaseModel


class SecurityEvent(BaseModel):
    """
    Security events and incidents tracking.
    """
    event_type = models.CharField(
        max_length=100,
        choices=[
            ('authentication_failure', 'Authentication Failure'),
            ('authorization_failure', 'Authorization Failure'),
            ('brute_force_attempt', 'Brute Force Attempt'),
            ('suspicious_activity', 'Suspicious Activity'),
            ('malware_detection', 'Malware Detection'),
            ('intrusion_attempt', 'Intrusion Attempt'),
            ('data_breach', 'Data Breach'),
            ('vulnerability_exploit', 'Vulnerability Exploit'),
            ('ddos_attack', 'DDoS Attack'),
            ('sql_injection', 'SQL Injection'),
            ('xss_attack', 'XSS Attack'),
            ('csrf_attack', 'CSRF Attack'),
        ],
        db_index=True
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    source_ip = models.GenericIPAddressField(db_index=True)
    target_ip = models.GenericIPAddressField(null=True, blank=True)
    source_port = models.PositiveIntegerField(null=True, blank=True)
    target_port = models.PositiveIntegerField(null=True, blank=True)
    protocol = models.CharField(max_length=20, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    payload = models.TextField(blank=True)
    detection_method = models.CharField(
        max_length=50,
        choices=[
            ('signature', 'Signature-based'),
            ('anomaly', 'Anomaly-based'),
            ('behavioral', 'Behavioral Analysis'),
            ('machine_learning', 'Machine Learning'),
            ('rule_based', 'Rule-based'),
        ]
    )
    confidence_score = models.FloatField(
        help_text="Confidence score (0.0 to 1.0)",
        null=True, blank=True
    )
    is_blocked = models.BooleanField(default=False)
    is_false_positive = models.BooleanField(default=False)
    response_action = models.CharField(
        max_length=50,
        choices=[
            ('allow', 'Allow'),
            ('block', 'Block'),
            ('quarantine', 'Quarantine'),
            ('alert', 'Alert Only'),
            ('monitor', 'Monitor'),
        ],
        default='alert'
    )
    event_data = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'security_event'
        indexes = [
            models.Index(fields=['event_type', 'severity', 'timestamp']),
            models.Index(fields=['source_ip', 'timestamp']),
            models.Index(fields=['is_blocked', 'is_false_positive']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.event_type} from {self.source_ip} - {self.get_severity_display()}"


class ThreatIntelligence(BaseModel):
    """
    Threat intelligence data and indicators of compromise (IoCs).
    """
    indicator_type = models.CharField(
        max_length=50,
        choices=[
            ('ip_address', 'IP Address'),
            ('domain', 'Domain'),
            ('url', 'URL'),
            ('file_hash', 'File Hash'),
            ('email', 'Email Address'),
            ('user_agent', 'User Agent'),
            ('certificate', 'Certificate'),
        ]
    )
    indicator_value = models.CharField(max_length=500, db_index=True)
    threat_type = models.CharField(
        max_length=100,
        choices=[
            ('malware', 'Malware'),
            ('botnet', 'Botnet'),
            ('phishing', 'Phishing'),
            ('spam', 'Spam'),
            ('tor_exit_node', 'Tor Exit Node'),
            ('proxy', 'Proxy/VPN'),
            ('scanner', 'Scanner'),
            ('brute_force', 'Brute Force'),
            ('ddos', 'DDoS'),
            ('apt', 'Advanced Persistent Threat'),
        ]
    )
    confidence_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('confirmed', 'Confirmed'),
        ]
    )
    source = models.CharField(max_length=255, help_text="Intelligence source")
    description = models.TextField(blank=True)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    tags = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'threat_intelligence'
        indexes = [
            models.Index(fields=['indicator_type', 'indicator_value']),
            models.Index(fields=['threat_type', 'confidence_level']),
            models.Index(fields=['is_active', 'last_seen']),
        ]
        unique_together = [['indicator_type', 'indicator_value', 'source']]
    
    def __str__(self):
        return f"{self.indicator_value} ({self.threat_type})"


class VulnerabilityAssessment(BaseModel):
    """
    Vulnerability assessment results and security posture metrics.
    """
    target_system = models.CharField(max_length=255, db_index=True)
    target_ip = models.GenericIPAddressField()
    vulnerability_id = models.CharField(max_length=100, help_text="CVE ID or custom identifier")
    vulnerability_name = models.CharField(max_length=255)
    severity_score = models.FloatField(help_text="CVSS score or custom severity score")
    severity_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    category = models.CharField(
        max_length=100,
        choices=[
            ('injection', 'Injection'),
            ('broken_auth', 'Broken Authentication'),
            ('sensitive_data', 'Sensitive Data Exposure'),
            ('xxe', 'XML External Entities'),
            ('broken_access', 'Broken Access Control'),
            ('security_misconfig', 'Security Misconfiguration'),
            ('xss', 'Cross-Site Scripting'),
            ('insecure_deserialization', 'Insecure Deserialization'),
            ('known_vulnerabilities', 'Known Vulnerabilities'),
            ('insufficient_logging', 'Insufficient Logging'),
        ]
    )
    description = models.TextField()
    remediation = models.TextField(blank=True)
    affected_service = models.CharField(max_length=255, blank=True)
    port = models.PositiveIntegerField(null=True, blank=True)
    is_exploitable = models.BooleanField(default=False)
    is_patched = models.BooleanField(default=False)
    patch_available = models.BooleanField(default=False)
    discovery_method = models.CharField(
        max_length=50,
        choices=[
            ('automated_scan', 'Automated Scan'),
            ('manual_test', 'Manual Test'),
            ('penetration_test', 'Penetration Test'),
            ('code_review', 'Code Review'),
            ('threat_intel', 'Threat Intelligence'),
        ]
    )
    scan_date = models.DateTimeField(auto_now_add=True)
    last_verified = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vulnerability_assessment'
        indexes = [
            models.Index(fields=['target_system', 'severity_level']),
            models.Index(fields=['vulnerability_id', 'is_patched']),
            models.Index(fields=['category', 'is_exploitable']),
        ]
        ordering = ['-severity_score', '-scan_date']
    
    def __str__(self):
        return f"{self.vulnerability_name} on {self.target_system}"


class SecurityMetricData(BaseModel):
    """
    Security metrics and KPIs tracking.
    """
    metric_name = models.CharField(max_length=255, db_index=True)
    metric_category = models.CharField(
        max_length=50,
        choices=[
            ('threat_detection', 'Threat Detection'),
            ('incident_response', 'Incident Response'),
            ('vulnerability_management', 'Vulnerability Management'),
            ('access_control', 'Access Control'),
            ('compliance', 'Compliance'),
            ('security_awareness', 'Security Awareness'),
        ]
    )
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    target_value = models.FloatField(null=True, blank=True)
    threshold_warning = models.FloatField(null=True, blank=True)
    threshold_critical = models.FloatField(null=True, blank=True)
    is_kpi = models.BooleanField(default=False, help_text="Key Performance Indicator")
    tags = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'security_metric_data'
        indexes = [
            models.Index(fields=['metric_name', 'metric_category', 'timestamp']),
            models.Index(fields=['is_kpi', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit}"


class ComplianceCheck(BaseModel):
    """
    Compliance and regulatory requirement tracking.
    """
    framework = models.CharField(
        max_length=50,
        choices=[
            ('gdpr', 'GDPR'),
            ('hipaa', 'HIPAA'),
            ('pci_dss', 'PCI DSS'),
            ('sox', 'SOX'),
            ('iso27001', 'ISO 27001'),
            ('nist', 'NIST'),
            ('cis', 'CIS Controls'),
            ('custom', 'Custom Framework'),
        ]
    )
    control_id = models.CharField(max_length=100)
    control_name = models.CharField(max_length=255)
    requirement_description = models.TextField()
    implementation_status = models.CharField(
        max_length=25,
        choices=[
            ('not_implemented', 'Not Implemented'),
            ('partially_implemented', 'Partially Implemented'),
            ('implemented', 'Implemented'),
            ('not_applicable', 'Not Applicable'),
        ]
    )
    compliance_score = models.FloatField(
        help_text="Compliance score (0.0 to 100.0)",
        null=True, blank=True
    )
    evidence = models.TextField(blank=True)
    responsible_party = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(null=True, blank=True)
    last_assessment = models.DateTimeField(auto_now=True)
    next_assessment = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'compliance_check'
        indexes = [
            models.Index(fields=['framework', 'implementation_status']),
            models.Index(fields=['due_date', 'implementation_status']),
        ]
        unique_together = [['framework', 'control_id']]
    
    def __str__(self):
        return f"{self.framework} - {self.control_id}: {self.control_name}"