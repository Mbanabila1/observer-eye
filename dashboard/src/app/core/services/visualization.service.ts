import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject, combineLatest } from 'rxjs';
import { map, distinctUntilChanged } from 'rxjs/operators';
import { WebSocketService } from './websocket.service';
import { PerformanceService } from './performance.service';
import { AnalyticsService } from './analytics.service';
import { TelemetryService } from './telemetry.service';

export interface ChartDataPoint {
  timestamp: string;
  value: number;
  label?: string;
  metadata?: Record<string, any>;
}

export interface MetricVisualization {
  id: string;
  title: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendValue: number;
  status: 'success' | 'warning' | 'error' | 'info';
  history: ChartDataPoint[];
}

export interface ChartVisualization {
  id: string;
  title: string;
  type: 'line' | 'bar' | 'area' | 'pie' | 'gauge';
  data: ChartDataPoint[];
  options: any;
}

export interface TableVisualization {
  id: string;
  title: string;
  columns: Array<{
    key: string;
    label: string;
    type: 'text' | 'number' | 'date' | 'status' | 'action';
    sortable?: boolean;
    filterable?: boolean;
  }>;
  data: Record<string, any>[];
}

@Injectable({
  providedIn: 'root'
})
export class VisualizationService {
  private realTimeData$ = new BehaviorSubject<Record<string, any>>({});
  private subscriptions = new Map<string, string>();

  constructor(
    private websocketService: WebSocketService,
    private performanceService: PerformanceService,
    private analyticsService: AnalyticsService,
    private telemetryService: TelemetryService
  ) {
    this.setupRealTimeUpdates();
  }

  private setupRealTimeUpdates(): void {
    // Subscribe to real-time performance metrics
    this.websocketService.subscribeToPerformance((data) => {
      this.updateRealTimeData('performance', data);
    });

    // Subscribe to real-time telemetry
    this.websocketService.subscribeToTelemetry((data) => {
      this.updateRealTimeData('telemetry', data);
    });

    // Subscribe to real-time metrics
    this.websocketService.subscribeToMetrics((data) => {
      this.updateRealTimeData('metrics', data);
    });
  }

  private updateRealTimeData(category: string, data: any): void {
    const currentData = this.realTimeData$.value;
    const updatedData = {
      ...currentData,
      [category]: {
        ...currentData[category],
        ...data,
        timestamp: new Date().toISOString()
      }
    };
    this.realTimeData$.next(updatedData);
  }

  // Metric Visualizations
  createMetricVisualization(config: {
    id: string;
    title: string;
    dataSource: string;
    metricKey: string;
    unit: string;
    thresholds?: { warning: number; error: number };
  }): Observable<MetricVisualization> {
    return combineLatest([
      this.getMetricData(config.dataSource, config.metricKey),
      this.realTimeData$
    ]).pipe(
      map(([historicalData, realTimeData]) => {
        const currentValue = this.extractCurrentValue(realTimeData, config.dataSource, config.metricKey);
        const trend = this.calculateTrend(historicalData);
        const status = this.determineStatus(currentValue, config.thresholds);

        return {
          id: config.id,
          title: config.title,
          value: currentValue,
          unit: config.unit,
          trend: trend.direction,
          trendValue: trend.percentage,
          status,
          history: historicalData
        };
      }),
      distinctUntilChanged((a, b) => JSON.stringify(a) === JSON.stringify(b))
    );
  }

  // Chart Visualizations
  createChartVisualization(config: {
    id: string;
    title: string;
    type: 'line' | 'bar' | 'area' | 'pie' | 'gauge';
    dataSource: string;
    metrics: string[];
    timeRange?: string;
    aggregation?: 'avg' | 'sum' | 'min' | 'max' | 'count';
  }): Observable<ChartVisualization> {
    return combineLatest([
      this.getChartData(config.dataSource, config.metrics, config.timeRange, config.aggregation),
      this.realTimeData$
    ]).pipe(
      map(([historicalData, realTimeData]) => {
        const chartData = this.formatChartData(historicalData, realTimeData, config);
        const chartOptions = this.generateChartOptions(config);

        return {
          id: config.id,
          title: config.title,
          type: config.type,
          data: chartData,
          options: chartOptions
        };
      })
    );
  }

  // Table Visualizations
  createTableVisualization(config: {
    id: string;
    title: string;
    dataSource: string;
    columns: Array<{
      key: string;
      label: string;
      type: 'text' | 'number' | 'date' | 'status' | 'action';
      sortable?: boolean;
      filterable?: boolean;
    }>;
    filters?: Record<string, any>;
    limit?: number;
  }): Observable<TableVisualization> {
    return this.getTableData(config.dataSource, config.filters, config.limit).pipe(
      map(data => ({
        id: config.id,
        title: config.title,
        columns: config.columns,
        data
      }))
    );
  }

  // Real-time Dashboard Data
  getDashboardData(widgetConfigs: any[]): Observable<Record<string, any>> {
    const observables = widgetConfigs.map(config => {
      switch (config.type) {
        case 'metric':
          return this.createMetricVisualization(config);
        case 'chart':
          return this.createChartVisualization(config);
        case 'table':
          return this.createTableVisualization(config);
        default:
          return new Observable(observer => observer.next(null));
      }
    });

    return combineLatest(observables).pipe(
      map(results => {
        const dashboardData: Record<string, any> = {};
        results.forEach((result, index) => {
          if (result) {
            dashboardData[widgetConfigs[index].id] = result;
          }
        });
        return dashboardData;
      })
    );
  }

  // Data Fetching Methods
  private getMetricData(dataSource: string, metricKey: string): Observable<ChartDataPoint[]> {
    switch (dataSource) {
      case 'performance':
        return this.performanceService.getSystemMetrics().pipe(
          map(metrics => this.convertToChartData(metrics, metricKey))
        );
      case 'analytics':
        return this.analyticsService.getAnalyticsData({ metric_name: metricKey }).pipe(
          map(data => this.convertToChartData(data, 'metric_value'))
        );
      case 'telemetry':
        return this.telemetryService.getTelemetryData({ type: 'metric' }).pipe(
          map(data => this.convertToChartData(data, metricKey))
        );
      default:
        return new Observable(observer => observer.next([]));
    }
  }

  private getChartData(
    dataSource: string, 
    metrics: string[], 
    timeRange?: string, 
    aggregation?: string
  ): Observable<ChartDataPoint[]> {
    // Implementation would depend on the specific data source
    return new Observable(observer => {
      // Mock data for now
      const mockData: ChartDataPoint[] = [];
      const now = new Date();
      
      for (let i = 23; i >= 0; i--) {
        const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);
        mockData.push({
          timestamp: timestamp.toISOString(),
          value: Math.random() * 100,
          label: timestamp.toLocaleTimeString()
        });
      }
      
      observer.next(mockData);
    });
  }

  private getTableData(
    dataSource: string, 
    filters?: Record<string, any>, 
    limit?: number
  ): Observable<Record<string, any>[]> {
    // Implementation would depend on the specific data source
    return new Observable(observer => {
      // Mock data for now
      const mockData = Array.from({ length: limit || 10 }, (_, i) => ({
        id: i + 1,
        name: `Item ${i + 1}`,
        status: ['active', 'inactive', 'pending'][Math.floor(Math.random() * 3)],
        value: Math.floor(Math.random() * 1000),
        timestamp: new Date().toISOString()
      }));
      
      observer.next(mockData);
    });
  }

  // Utility Methods
  private convertToChartData(data: any[], valueKey: string): ChartDataPoint[] {
    return data.map(item => ({
      timestamp: item.timestamp || new Date().toISOString(),
      value: item[valueKey] || 0,
      label: item.label,
      metadata: item
    }));
  }

  private extractCurrentValue(realTimeData: any, dataSource: string, metricKey: string): number {
    const sourceData = realTimeData[dataSource];
    if (!sourceData) return 0;
    
    return sourceData[metricKey] || 0;
  }

  private calculateTrend(data: ChartDataPoint[]): { direction: 'up' | 'down' | 'stable'; percentage: number } {
    if (data.length < 2) return { direction: 'stable', percentage: 0 };
    
    const recent = data.slice(-5); // Last 5 data points
    const older = data.slice(-10, -5); // Previous 5 data points
    
    const recentAvg = recent.reduce((sum, point) => sum + point.value, 0) / recent.length;
    const olderAvg = older.reduce((sum, point) => sum + point.value, 0) / older.length;
    
    if (olderAvg === 0) return { direction: 'stable', percentage: 0 };
    
    const percentage = ((recentAvg - olderAvg) / olderAvg) * 100;
    
    if (Math.abs(percentage) < 1) return { direction: 'stable', percentage: 0 };
    
    return {
      direction: percentage > 0 ? 'up' : 'down',
      percentage: Math.abs(percentage)
    };
  }

  private determineStatus(
    value: number, 
    thresholds?: { warning: number; error: number }
  ): 'success' | 'warning' | 'error' | 'info' {
    if (!thresholds) return 'info';
    
    if (value >= thresholds.error) return 'error';
    if (value >= thresholds.warning) return 'warning';
    return 'success';
  }

  private formatChartData(
    historicalData: ChartDataPoint[], 
    realTimeData: any, 
    config: any
  ): ChartDataPoint[] {
    // Combine historical and real-time data
    const combined = [...historicalData];
    
    // Add real-time point if available
    const currentValue = this.extractCurrentValue(realTimeData, config.dataSource, config.metrics[0]);
    if (currentValue !== undefined) {
      combined.push({
        timestamp: new Date().toISOString(),
        value: currentValue,
        label: 'Now'
      });
    }
    
    return combined;
  }

  private generateChartOptions(config: any): any {
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Time'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Value'
          }
        }
      }
    };

    // Customize based on chart type
    switch (config.type) {
      case 'line':
        return {
          ...baseOptions,
          elements: {
            line: {
              tension: 0.4
            }
          }
        };
      case 'bar':
        return {
          ...baseOptions,
          plugins: {
            ...baseOptions.plugins,
            legend: {
              display: false
            }
          }
        };
      case 'pie':
        return {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'right'
            }
          }
        };
      default:
        return baseOptions;
    }
  }

  // Subscription Management
  subscribeToWidget(widgetId: string, config: any): string {
    const subscriptionId = this.websocketService.subscribe(
      { type: config.dataSource, ...config.filters },
      (data) => this.updateRealTimeData(`widget_${widgetId}`, data)
    );
    
    this.subscriptions.set(widgetId, subscriptionId);
    return subscriptionId;
  }

  unsubscribeFromWidget(widgetId: string): void {
    const subscriptionId = this.subscriptions.get(widgetId);
    if (subscriptionId) {
      this.websocketService.unsubscribe(subscriptionId);
      this.subscriptions.delete(widgetId);
    }
  }
}