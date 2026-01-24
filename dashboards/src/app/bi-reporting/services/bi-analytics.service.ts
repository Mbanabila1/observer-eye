import { Injectable, signal } from '@angular/core';
import { Observable, BehaviorSubject, of, interval } from 'rxjs';
import { map, switchMap, catchError } from 'rxjs/operators';
import { 
  KPIWidget, 
  ReportDefinition, 
  ExportConfig, 
  ExportResult, 
  AnalyticalDataSource,
  ExecutiveDashboardConfig,
  TrendAnalysisWidget,
  AlertSummaryWidget,
  PerformanceMetricsWidget,
  InsightResult,
  TimeSeriesData
} from '../models/bi-models';

@Injectable({
  providedIn: 'root'
})
export class BiAnalyticsService {
  private readonly baseUrl = '/api/bi-analytics';
  private dashboardConfig = signal<ExecutiveDashboardConfig | null>(null);
  private refreshInterval$ = new BehaviorSubject<number>(30000); // 30 seconds default

  constructor() {
    // Auto-refresh mechanism
    this.refreshInterval$.pipe(
      switchMap(intervalMs => intervalMs > 0 ? interval(intervalMs) : of(null))
    ).subscribe(() => {
      if (this.dashboardConfig()?.autoRefresh) {
        this.refreshDashboardData();
      }
    });
  }

  // Executive Dashboard Methods
  getExecutiveDashboard(): Observable<ExecutiveDashboardConfig> {
    // Mock data for development - replace with actual API call
    return of(this.getMockExecutiveDashboard()).pipe(
      map(config => {
        this.dashboardConfig.set(config);
        return config;
      }),
      catchError(error => {
        console.error('Error fetching executive dashboard:', error);
        return of(this.getMockExecutiveDashboard());
      })
    );
  }

  getKPIWidgets(): Observable<KPIWidget[]> {
    return of(this.getMockKPIWidgets()).pipe(
      catchError(error => {
        console.error('Error fetching KPI widgets:', error);
        return of([]);
      })
    );
  }

  getTrendAnalysis(): Observable<TrendAnalysisWidget[]> {
    return of(this.getMockTrendAnalysis()).pipe(
      catchError(error => {
        console.error('Error fetching trend analysis:', error);
        return of([]);
      })
    );
  }

  getAlertSummary(): Observable<AlertSummaryWidget> {
    return of(this.getMockAlertSummary()).pipe(
      catchError(error => {
        console.error('Error fetching alert summary:', error);
        return of({
          id: 'alerts-error',
          title: 'Alert Summary',
          criticalCount: 0,
          warningCount: 0,
          infoCount: 0,
          recentAlerts: []
        });
      })
    );
  }

  getPerformanceMetrics(): Observable<PerformanceMetricsWidget[]> {
    return of(this.getMockPerformanceMetrics()).pipe(
      catchError(error => {
        console.error('Error fetching performance metrics:', error);
        return of([]);
      })
    );
  }

  // Report Builder Methods
  getAvailableDataSources(): Observable<AnalyticalDataSource[]> {
    return of(this.getMockDataSources()).pipe(
      catchError(error => {
        console.error('Error fetching data sources:', error);
        return of([]);
      })
    );
  }

  saveReport(report: ReportDefinition): Observable<ReportDefinition> {
    // Mock save - replace with actual API call
    return of({ ...report, id: this.generateId(), createdAt: new Date(), updatedAt: new Date() }).pipe(
      catchError(error => {
        console.error('Error saving report:', error);
        throw error;
      })
    );
  }

  getReports(): Observable<ReportDefinition[]> {
    return of(this.getMockReports()).pipe(
      catchError(error => {
        console.error('Error fetching reports:', error);
        return of([]);
      })
    );
  }

  deleteReport(reportId: string): Observable<boolean> {
    // Mock delete - replace with actual API call
    return of(true).pipe(
      catchError(error => {
        console.error('Error deleting report:', error);
        return of(false);
      })
    );
  }

  // Data Export Methods
  exportData(config: ExportConfig): Observable<ExportResult> {
    // Mock export - replace with actual API call
    return of({
      success: true,
      filename: `report_${new Date().toISOString().split('T')[0]}.${config.format}`,
      downloadUrl: `/downloads/report_${Date.now()}.${config.format}`,
      size: Math.floor(Math.random() * 1000000) + 100000 // Random size between 100KB-1MB
    }).pipe(
      catchError(error => {
        console.error('Error exporting data:', error);
        return of({
          success: false,
          error: 'Export failed: ' + error.message
        });
      })
    );
  }

  // Analytics and Insights
  generateInsights(dataSource: string, timeRange: string): Observable<InsightResult[]> {
    return of(this.getMockInsights()).pipe(
      catchError(error => {
        console.error('Error generating insights:', error);
        return of([]);
      })
    );
  }

  // Configuration Methods
  setRefreshInterval(intervalMs: number): void {
    this.refreshInterval$.next(intervalMs);
  }

  private refreshDashboardData(): void {
    // Refresh dashboard data automatically
    this.getExecutiveDashboard().subscribe();
  }

  private generateId(): string {
    return 'id_' + Math.random().toString(36).substr(2, 9);
  }

  // Mock Data Methods (replace with actual API calls)
  private getMockExecutiveDashboard(): ExecutiveDashboardConfig {
    return {
      kpis: this.getMockKPIWidgets(),
      trends: this.getMockTrendAnalysis(),
      alerts: this.getMockAlertSummary(),
      performance: this.getMockPerformanceMetrics(),
      refreshInterval: 30000,
      autoRefresh: true
    };
  }

  private getMockKPIWidgets(): KPIWidget[] {
    return [
      {
        id: 'kpi-1',
        title: 'System Availability',
        value: 99.97,
        unit: '%',
        trend: 'up',
        trendPercentage: 0.03,
        targetValue: 99.95,
        thresholdWarning: 99.90,
        thresholdCritical: 99.85,
        category: 'reliability',
        description: 'Overall system uptime and availability'
      },
      {
        id: 'kpi-2',
        title: 'Response Time',
        value: 145,
        unit: 'ms',
        trend: 'down',
        trendPercentage: -8.2,
        targetValue: 150,
        thresholdWarning: 200,
        thresholdCritical: 300,
        category: 'performance',
        description: 'Average API response time'
      },
      {
        id: 'kpi-3',
        title: 'Error Rate',
        value: 0.12,
        unit: '%',
        trend: 'stable',
        trendPercentage: 0.01,
        targetValue: 0.10,
        thresholdWarning: 0.50,
        thresholdCritical: 1.00,
        category: 'quality',
        description: 'Application error rate'
      },
      {
        id: 'kpi-4',
        title: 'Throughput',
        value: 2847,
        unit: 'req/s',
        trend: 'up',
        trendPercentage: 12.5,
        targetValue: 2500,
        category: 'performance',
        description: 'Requests processed per second'
      }
    ];
  }

  private getMockTrendAnalysis(): TrendAnalysisWidget[] {
    const now = new Date();
    const generateTimeSeriesData = (points: number, baseValue: number, variance: number): TimeSeriesData[] => {
      return Array.from({ length: points }, (_, i) => ({
        timestamp: new Date(now.getTime() - (points - i) * 3600000), // Hourly data
        value: baseValue + (Math.random() - 0.5) * variance
      }));
    };

    return [
      {
        id: 'trend-1',
        title: 'CPU Utilization Trend',
        metric: 'cpu_utilization',
        timeRange: '24h',
        data: generateTimeSeriesData(24, 65, 20)
      },
      {
        id: 'trend-2',
        title: 'Memory Usage Trend',
        metric: 'memory_usage',
        timeRange: '24h',
        data: generateTimeSeriesData(24, 78, 15)
      }
    ];
  }

  private getMockAlertSummary(): AlertSummaryWidget {
    return {
      id: 'alerts-1',
      title: 'Alert Summary',
      criticalCount: 2,
      warningCount: 8,
      infoCount: 15,
      recentAlerts: [
        {
          id: 'alert-1',
          severity: 'critical',
          message: 'Database connection pool exhausted',
          timestamp: new Date(Date.now() - 300000), // 5 minutes ago
          source: 'database-monitor'
        },
        {
          id: 'alert-2',
          severity: 'warning',
          message: 'High memory usage detected',
          timestamp: new Date(Date.now() - 600000), // 10 minutes ago
          source: 'system-monitor'
        },
        {
          id: 'alert-3',
          severity: 'info',
          message: 'Scheduled maintenance completed',
          timestamp: new Date(Date.now() - 1800000), // 30 minutes ago
          source: 'maintenance-system'
        }
      ]
    };
  }

  private getMockPerformanceMetrics(): PerformanceMetricsWidget[] {
    return [
      {
        id: 'perf-1',
        title: 'Application Performance',
        metrics: [
          { name: 'Response Time', current: 145, previous: 158, target: 150, unit: 'ms', trend: 'down' },
          { name: 'Throughput', current: 2847, previous: 2534, unit: 'req/s', trend: 'up' },
          { name: 'Error Rate', current: 0.12, previous: 0.15, target: 0.10, unit: '%', trend: 'down' }
        ],
        comparison: 'previous_period'
      },
      {
        id: 'perf-2',
        title: 'Infrastructure Metrics',
        metrics: [
          { name: 'CPU Usage', current: 68, previous: 72, target: 70, unit: '%', trend: 'down' },
          { name: 'Memory Usage', current: 78, previous: 75, target: 80, unit: '%', trend: 'up' },
          { name: 'Disk I/O', current: 234, previous: 198, unit: 'MB/s', trend: 'up' }
        ],
        comparison: 'target'
      }
    ];
  }

  private getMockDataSources(): AnalyticalDataSource[] {
    return [
      {
        id: 'metrics-source',
        name: 'System Metrics',
        type: 'metrics',
        fields: [
          { name: 'timestamp', type: 'date', label: 'Timestamp', aggregatable: false, filterable: true },
          { name: 'cpu_usage', type: 'number', label: 'CPU Usage (%)', aggregatable: true, filterable: true },
          { name: 'memory_usage', type: 'number', label: 'Memory Usage (%)', aggregatable: true, filterable: true },
          { name: 'service_name', type: 'string', label: 'Service', aggregatable: false, filterable: true }
        ],
        refreshInterval: 60000,
        lastUpdated: new Date()
      },
      {
        id: 'events-source',
        name: 'Application Events',
        type: 'events',
        fields: [
          { name: 'timestamp', type: 'date', label: 'Timestamp', aggregatable: false, filterable: true },
          { name: 'event_type', type: 'string', label: 'Event Type', aggregatable: false, filterable: true },
          { name: 'severity', type: 'string', label: 'Severity', aggregatable: false, filterable: true },
          { name: 'count', type: 'number', label: 'Count', aggregatable: true, filterable: true }
        ],
        refreshInterval: 30000,
        lastUpdated: new Date()
      }
    ];
  }

  private getMockReports(): ReportDefinition[] {
    return [
      {
        id: 'report-1',
        name: 'Daily Performance Report',
        description: 'Comprehensive daily performance metrics and trends',
        reportType: 'operational',
        widgets: [],
        layout: { columns: 12, rows: 8, gridSize: 50 },
        distributionList: ['admin@company.com', 'ops@company.com'],
        createdBy: 'admin',
        createdAt: new Date(Date.now() - 86400000),
        updatedAt: new Date(Date.now() - 3600000),
        isActive: true
      }
    ];
  }

  private getMockInsights(): InsightResult[] {
    return [
      {
        type: 'anomaly',
        title: 'Unusual CPU Spike Detected',
        description: 'CPU usage increased by 45% compared to normal patterns',
        confidence: 0.87,
        impact: 'high',
        actionable: true,
        recommendations: [
          'Check for resource-intensive processes',
          'Consider scaling up infrastructure',
          'Review recent deployments'
        ]
      },
      {
        type: 'trend',
        title: 'Memory Usage Trending Upward',
        description: 'Memory consumption has increased 15% over the past week',
        confidence: 0.92,
        impact: 'medium',
        actionable: true,
        recommendations: [
          'Monitor for memory leaks',
          'Plan for capacity expansion',
          'Optimize memory-intensive operations'
        ]
      }
    ];
  }
}