import { Component, OnInit, OnDestroy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil, interval } from 'rxjs';
import { BiAnalyticsService } from '../services/bi-analytics.service';
import { DataExportService } from '../services/data-export.service';
import { 
  ExecutiveDashboardConfig, 
  KPIWidget, 
  TrendAnalysisWidget, 
  AlertSummaryWidget, 
  PerformanceMetricsWidget,
  ExportConfig 
} from '../models/bi-models';
import { KpiCardComponent } from '../components/kpi-card/kpi-card.component';
import { TrendChartComponent } from '../components/trend-chart/trend-chart.component';
import { AlertSummaryComponent } from '../components/alert-summary/alert-summary.component';
import { PerformanceMetricsComponent } from '../components/performance-metrics/performance-metrics.component';
import { ExportButtonComponent } from '../components/export-button/export-button.component';

@Component({
  selector: 'app-executive-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    KpiCardComponent,
    TrendChartComponent,
    AlertSummaryComponent,
    PerformanceMetricsComponent,
    ExportButtonComponent
  ],
  template: `
    <div class="executive-dashboard p-6 bg-gray-50 min-h-screen">
      <!-- Header -->
      <div class="dashboard-header mb-8">
        <div class="flex justify-between items-center">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">Executive Dashboard</h1>
            <p class="text-gray-600 mt-2">Real-time insights and key performance indicators</p>
          </div>
          <div class="flex items-center space-x-4">
            <!-- Auto-refresh toggle -->
            <div class="flex items-center space-x-2">
              <label class="text-sm text-gray-700">Auto-refresh:</label>
              <button
                (click)="toggleAutoRefresh()"
                [class]="autoRefreshEnabled() ? 'bg-blue-600' : 'bg-gray-300'"
                class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <span
                  [class]="autoRefreshEnabled() ? 'translate-x-6' : 'translate-x-1'"
                  class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                ></span>
              </button>
            </div>
            
            <!-- Refresh button -->
            <button
              (click)="refreshDashboard()"
              [disabled]="isLoading()"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              <span>{{ isLoading() ? 'Refreshing...' : 'Refresh' }}</span>
            </button>

            <!-- Export button -->
            <app-export-button
              [data]="dashboardData()"
              [filename]="'executive_dashboard_' + getCurrentDate()"
              (exportComplete)="onExportComplete($event)"
            ></app-export-button>
          </div>
        </div>

        <!-- Last updated indicator -->
        <div class="mt-4 text-sm text-gray-500">
          Last updated: {{ lastUpdated() | date:'medium' }}
          @if (isLoading()) {
            <span class="ml-2 inline-flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading...
            </span>
          }
        </div>
      </div>

      @if (dashboardConfig()) {
        <!-- KPI Cards Grid -->
        <div class="kpi-section mb-8">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">Key Performance Indicators</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            @for (kpi of dashboardConfig()!.kpis; track kpi.id) {
              <app-kpi-card [kpi]="kpi"></app-kpi-card>
            }
          </div>
        </div>

        <!-- Trend Analysis -->
        <div class="trends-section mb-8">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">Trend Analysis</h2>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            @for (trend of dashboardConfig()!.trends; track trend.id) {
              <app-trend-chart [trendData]="trend"></app-trend-chart>
            }
          </div>
        </div>

        <!-- Alerts and Performance Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <!-- Alert Summary -->
          <div class="alerts-section">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Alert Summary</h2>
            <app-alert-summary [alertData]="dashboardConfig()!.alerts"></app-alert-summary>
          </div>

          <!-- Performance Metrics -->
          <div class="performance-section">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Performance Overview</h2>
            @for (perfWidget of dashboardConfig()!.performance; track perfWidget.id) {
              <app-performance-metrics [performanceData]="perfWidget" class="mb-4"></app-performance-metrics>
            }
          </div>
        </div>
      } @else {
        <!-- Loading State -->
        <div class="flex items-center justify-center h-64">
          <div class="text-center">
            <svg class="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="text-gray-600">Loading dashboard data...</p>
          </div>
        </div>
      }

      <!-- Error State -->
      @if (error()) {
        <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div class="flex">
            <svg class="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">Error Loading Dashboard</h3>
              <p class="mt-1 text-sm text-red-700">{{ error() }}</p>
              <button
                (click)="refreshDashboard()"
                class="mt-2 text-sm text-red-800 underline hover:text-red-900"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .executive-dashboard {
      animation: fadeIn 0.3s ease-in-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .kpi-section, .trends-section, .alerts-section, .performance-section {
      animation: slideInUp 0.4s ease-out;
    }

    @keyframes slideInUp {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class ExecutiveDashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Signals for reactive state management
  dashboardConfig = signal<ExecutiveDashboardConfig | null>(null);
  isLoading = signal<boolean>(false);
  error = signal<string | null>(null);
  lastUpdated = signal<Date>(new Date());
  autoRefreshEnabled = signal<boolean>(true);

  // Computed values
  dashboardData = computed(() => {
    const config = this.dashboardConfig();
    return config ? {
      kpis: config.kpis,
      trends: config.trends,
      alerts: config.alerts,
      performance: config.performance,
      timestamp: this.lastUpdated()
    } : null;
  });

  constructor(
    private biAnalyticsService: BiAnalyticsService,
    private dataExportService: DataExportService
  ) {}

  ngOnInit(): void {
    this.loadDashboardData();
    this.setupAutoRefresh();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadDashboardData(): void {
    this.isLoading.set(true);
    this.error.set(null);

    this.biAnalyticsService.getExecutiveDashboard()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (config) => {
          this.dashboardConfig.set(config);
          this.lastUpdated.set(new Date());
          this.isLoading.set(false);
        },
        error: (err) => {
          this.error.set('Failed to load dashboard data. Please try again.');
          this.isLoading.set(false);
          console.error('Dashboard loading error:', err);
        }
      });
  }

  refreshDashboard(): void {
    this.loadDashboardData();
  }

  toggleAutoRefresh(): void {
    const newValue = !this.autoRefreshEnabled();
    this.autoRefreshEnabled.set(newValue);
    
    if (newValue) {
      this.setupAutoRefresh();
    }
  }

  private setupAutoRefresh(): void {
    const config = this.dashboardConfig();
    if (config && this.autoRefreshEnabled()) {
      interval(config.refreshInterval)
        .pipe(takeUntil(this.destroy$))
        .subscribe(() => {
          if (this.autoRefreshEnabled() && !this.isLoading()) {
            this.loadDashboardData();
          }
        });
    }
  }

  onExportComplete(result: any): void {
    if (result.success) {
      console.log('Dashboard exported successfully:', result.filename);
    } else {
      console.error('Export failed:', result.error);
    }
  }

  getCurrentDate(): string {
    return new Date().toISOString().split('T')[0];
  }
}