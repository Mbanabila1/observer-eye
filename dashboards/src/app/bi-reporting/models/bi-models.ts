// BI Reporting Data Models

export interface KPIWidget {
  id: string;
  title: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendPercentage: number;
  targetValue?: number;
  thresholdWarning?: number;
  thresholdCritical?: number;
  category: string;
  description?: string;
}

export interface ReportWidgetConfig {
  id: string;
  type: ReportWidgetType;
  title: string;
  dataSource: string;
  aggregations: AggregationConfig[];
  filters: FilterConfig[];
  visualization: VisualizationConfig;
  position: { x: number; y: number; width: number; height: number };
}

export type ReportWidgetType = 
  | 'kpi-card' 
  | 'line-chart' 
  | 'bar-chart' 
  | 'pie-chart' 
  | 'table' 
  | 'heatmap' 
  | 'gauge' 
  | 'trend-analysis';

export interface AggregationConfig {
  field: string;
  function: 'sum' | 'avg' | 'count' | 'min' | 'max' | 'distinct';
  alias?: string;
}

export interface FilterConfig {
  field: string;
  operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'in' | 'between';
  value: any;
  label?: string;
}

export interface VisualizationConfig {
  chartType?: string;
  colors?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  xAxis?: AxisConfig;
  yAxis?: AxisConfig;
}

export interface AxisConfig {
  label: string;
  field: string;
  format?: string;
}

export interface ReportDefinition {
  id: string;
  name: string;
  description: string;
  reportType: 'executive' | 'operational' | 'technical';
  widgets: ReportWidgetConfig[];
  layout: LayoutConfig;
  schedule?: ScheduleConfig;
  distributionList: string[];
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
}

export interface LayoutConfig {
  columns: number;
  rows: number;
  gridSize: number;
  backgroundColor?: string;
  theme?: 'light' | 'dark';
}

export interface ScheduleConfig {
  frequency: 'hourly' | 'daily' | 'weekly' | 'monthly';
  time?: string;
  dayOfWeek?: number;
  dayOfMonth?: number;
  timezone: string;
  enabled: boolean;
}

export interface ExportConfig {
  format: ExportFormat;
  filename?: string;
  includeCharts: boolean;
  includeData: boolean;
  dateRange?: DateRange;
}

export type ExportFormat = 'pdf' | 'excel' | 'csv' | 'json' | 'png';

export interface DateRange {
  start: Date;
  end: Date;
}

export interface AnalyticalDataSource {
  id: string;
  name: string;
  type: 'metrics' | 'events' | 'logs' | 'traces' | 'aggregated';
  fields: DataField[];
  refreshInterval: number;
  lastUpdated: Date;
}

export interface DataField {
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean';
  label: string;
  description?: string;
  aggregatable: boolean;
  filterable: boolean;
}

export interface ExecutiveDashboardConfig {
  kpis: KPIWidget[];
  trends: TrendAnalysisWidget[];
  alerts: AlertSummaryWidget;
  performance: PerformanceMetricsWidget[];
  refreshInterval: number;
  autoRefresh: boolean;
}

export interface TrendAnalysisWidget {
  id: string;
  title: string;
  metric: string;
  timeRange: string;
  data: TimeSeriesData[];
  forecast?: ForecastData[];
}

export interface AlertSummaryWidget {
  id: string;
  title: string;
  criticalCount: number;
  warningCount: number;
  infoCount: number;
  recentAlerts: AlertItem[];
}

export interface PerformanceMetricsWidget {
  id: string;
  title: string;
  metrics: PerformanceMetric[];
  comparison: 'previous_period' | 'target' | 'baseline';
}

export interface TimeSeriesData {
  timestamp: Date;
  value: number;
  label?: string;
}

export interface ForecastData {
  timestamp: Date;
  predicted: number;
  confidence: number;
}

export interface AlertItem {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: Date;
  source: string;
}

export interface PerformanceMetric {
  name: string;
  current: number;
  previous: number;
  target?: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
}

export interface InsightResult {
  type: 'anomaly' | 'trend' | 'correlation' | 'recommendation';
  title: string;
  description: string;
  confidence: number;
  impact: 'high' | 'medium' | 'low';
  actionable: boolean;
  recommendations?: string[];
}

export interface ExportResult {
  success: boolean;
  filename?: string;
  downloadUrl?: string;
  error?: string;
  size?: number;
}