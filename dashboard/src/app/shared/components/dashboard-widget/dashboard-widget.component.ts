import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { CardComponent } from '../card/card.component';
import { ButtonComponent } from '../button/button.component';
import { ChartComponent, ChartData, ChartOptions } from '../chart/chart.component';
import { MetricCardComponent } from '../metric-card/metric-card.component';
import { TableComponent, TableColumn, TableRow } from '../table/table.component';
import { StatusBadgeComponent } from '../status-badge/status-badge.component';

export type WidgetType = 'metric' | 'chart' | 'table' | 'status' | 'custom';
export type WidgetSize = 'sm' | 'md' | 'lg' | 'xl';

export interface WidgetConfig {
  id: string;
  title: string;
  type: WidgetType;
  size: WidgetSize;
  refreshInterval?: number;
  dataSource?: string;
  options?: any;
}

@Component({
  selector: 'app-dashboard-widget',
  standalone: true,
  imports: [
    CommonModule,
    LucideAngularModule,
    CardComponent,
    ButtonComponent,
    ChartComponent,
    MetricCardComponent,
    TableComponent,
    StatusBadgeComponent
  ],
  template: `
    <app-card
      [title]="config.title"
      [loading]="loading"
      [loadingText]="loadingText"
      [class]="widgetClasses"
    >
      <!-- Header Actions -->
      <div slot="header-actions" class="flex items-center space-x-2">
        <app-button
          *ngIf="showRefresh"
          variant="ghost"
          size="sm"
          [iconOnly]="true"
          leftIcon="refreshCw"
          [loading]="refreshing"
          (clicked)="refresh()"
          title="Refresh"
        ></app-button>
        
        <app-button
          *ngIf="showSettings"
          variant="ghost"
          size="sm"
          [iconOnly]="true"
          leftIcon="settings"
          (clicked)="openSettings()"
          title="Settings"
        ></app-button>
        
        <app-button
          *ngIf="showFullscreen"
          variant="ghost"
          size="sm"
          [iconOnly]="true"
          leftIcon="maximize2"
          (clicked)="toggleFullscreen()"
          title="Fullscreen"
        ></app-button>
      </div>

      <!-- Widget Content -->
      <div [ngSwitch]="config.type" class="h-full">
        <!-- Metric Widget -->
        <div *ngSwitchCase="'metric'" class="space-y-4">
          <app-metric-card
            *ngFor="let metric of metricData"
            [title]="metric.title"
            [value]="metric.value"
            [unit]="metric.unit"
            [subtitle]="metric.subtitle"
            [icon]="metric.icon"
            [status]="metric.status"
            [trend]="metric.trend"
            [trendValue]="metric.trendValue"
            [showTrend]="metric.showTrend"
            [loading]="metric.loading"
          ></app-metric-card>
        </div>

        <!-- Chart Widget -->
        <div *ngSwitchCase="'chart'" class="h-full">
          <app-chart
            [type]="chartConfig?.type || 'line'"
            [data]="chartData"
            [options]="chartOptions"
            [loading]="loading"
            [error]="error"
            height="100%"
          ></app-chart>
        </div>

        <!-- Table Widget -->
        <div *ngSwitchCase="'table'" class="h-full">
          <app-table
            [columns]="tableColumns"
            [data]="tableData"
            [loading]="loading"
            [emptyMessage]="emptyMessage"
            [showPagination]="tableConfig?.showPagination !== false"
            [pageSize]="tableConfig?.pageSize || 10"
            (rowClicked)="onTableRowClick($event)"
          ></app-table>
        </div>

        <!-- Status Widget -->
        <div *ngSwitchCase="'status'" class="space-y-3">
          <div *ngFor="let status of statusData" class="flex items-center justify-between p-3 bg-secondary-50 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular
                *ngIf="status.icon"
                [img]="status.icon"
                [size]="20"
                class="text-secondary-600"
              ></lucide-angular>
              <div>
                <p class="text-sm font-medium text-secondary-900">{{ status.label }}</p>
                <p *ngIf="status.description" class="text-xs text-secondary-600">{{ status.description }}</p>
              </div>
            </div>
            
            <app-status-badge
              [label]="status.status"
              [status]="status.type"
              [size]="'sm'"
            ></app-status-badge>
          </div>
        </div>

        <!-- Custom Widget -->
        <div *ngSwitchCase="'custom'" class="h-full">
          <ng-content></ng-content>
        </div>
      </div>

      <!-- Footer -->
      <div slot="footer" *ngIf="showFooter" class="flex items-center justify-between text-xs text-secondary-500">
        <span *ngIf="lastUpdated">Last updated: {{ lastUpdated | date:'short' }}</span>
        <span *ngIf="dataSource">Source: {{ dataSource }}</span>
      </div>
    </app-card>
  `
})
export class DashboardWidgetComponent {
  @Input() config!: WidgetConfig;
  @Input() loading = false;
  @Input() refreshing = false;
  @Input() loadingText = 'Loading...';
  @Input() error = '';
  @Input() lastUpdated?: Date;
  @Input() dataSource = '';
  @Input() showRefresh = true;
  @Input() showSettings = false;
  @Input() showFullscreen = false;
  @Input() showFooter = true;
  @Input() emptyMessage = 'No data available';

  // Data inputs for different widget types
  @Input() metricData: any[] = [];
  @Input() chartData: ChartData = { labels: [], datasets: [] };
  @Input() chartOptions: ChartOptions = {};
  @Input() chartConfig: any = {};
  @Input() tableColumns: TableColumn[] = [];
  @Input() tableData: TableRow[] = [];
  @Input() tableConfig: any = {};
  @Input() statusData: any[] = [];

  @Output() refreshClicked = new EventEmitter<void>();
  @Output() settingsClicked = new EventEmitter<void>();
  @Output() fullscreenToggled = new EventEmitter<void>();
  @Output() tableRowClicked = new EventEmitter<TableRow>();

  get widgetClasses(): string {
    const sizeClasses = {
      sm: ['col-span-1', 'row-span-1', 'h-64'],
      md: ['col-span-2', 'row-span-1', 'h-80'],
      lg: ['col-span-2', 'row-span-2', 'h-96'],
      xl: ['col-span-3', 'row-span-2', 'h-128']
    };

    return sizeClasses[this.config.size].join(' ');
  }

  refresh(): void {
    this.refreshClicked.emit();
  }

  openSettings(): void {
    this.settingsClicked.emit();
  }

  toggleFullscreen(): void {
    this.fullscreenToggled.emit();
  }

  onTableRowClick(row: TableRow): void {
    this.tableRowClicked.emit(row);
  }
}