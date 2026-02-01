import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil } from 'rxjs';
import { DashboardWidgetComponent, WidgetConfig } from '../dashboard-widget/dashboard-widget.component';
import { ButtonComponent } from '../button/button.component';
import { DropdownComponent } from '../dropdown/dropdown.component';
import { ModalComponent } from '../modal/modal.component';
import { DashboardService, Dashboard, DashboardTemplate } from '../../../core/services/dashboard.service';
import { WebSocketService } from '../../../core/services/websocket.service';
import { NotificationService } from '../../../core/services/notification.service';
import { IconName } from '../../utils/icons';

export interface DashboardLayout {
  id: string;
  name: string;
  widgets: WidgetConfig[];
  layout: {
    columns: number;
    gap: number;
    autoRows: string;
  };
  settings: {
    refreshInterval: number;
    autoRefresh: boolean;
    theme: 'light' | 'dark';
  };
}

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [
    CommonModule,
    DashboardWidgetComponent,
    ButtonComponent,
    DropdownComponent,
    ModalComponent
  ],
  template: `
    <div class="dashboard-container h-full flex flex-col">
      <!-- Dashboard Header -->
      <div class="dashboard-header flex items-center justify-between p-4 bg-white border-b border-secondary-200">
        <div class="flex items-center space-x-4">
          <h1 class="text-2xl font-bold text-secondary-900">{{ dashboard?.name || 'Dashboard' }}</h1>
          
          <div class="flex items-center space-x-2">
            <app-button
              variant="ghost"
              size="sm"
              [iconOnly]="true"
              leftIcon="refreshCw"
              [loading]="refreshing"
              (clicked)="refreshAll()"
              title="Refresh All Widgets"
            ></app-button>
            
            <app-button
              variant="ghost"
              size="sm"
              [iconOnly]="true"
              leftIcon="play"
              *ngIf="!autoRefreshActive"
              (clicked)="startAutoRefresh()"
              title="Start Auto Refresh"
            ></app-button>
            
            <app-button
              variant="ghost"
              size="sm"
              [iconOnly]="true"
              leftIcon="pause"
              *ngIf="autoRefreshActive"
              (clicked)="stopAutoRefresh()"
              title="Stop Auto Refresh"
            ></app-button>
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <!-- Dashboard Actions -->
          <app-dropdown
            [items]="dashboardActions"
            [showArrow]="false"
            (itemSelected)="onDashboardAction($event)"
          >
            <app-button
              variant="ghost"
              size="sm"
              [iconOnly]="true"
              leftIcon="moreHorizontal"
              title="Dashboard Actions"
            ></app-button>
          </app-dropdown>

          <!-- Add Widget -->
          <app-button
            variant="primary"
            size="sm"
            leftIcon="plus"
            (clicked)="openAddWidgetModal()"
          >
            Add Widget
          </app-button>

          <!-- Dashboard Settings -->
          <app-button
            variant="ghost"
            size="sm"
            [iconOnly]="true"
            leftIcon="settings"
            (clicked)="openSettingsModal()"
            title="Dashboard Settings"
          ></app-button>
        </div>
      </div>

      <!-- Dashboard Grid -->
      <div 
        class="dashboard-grid flex-1 p-4 overflow-auto"
        [style.grid-template-columns]="gridColumns"
        [style.gap]="gridGap"
        [style.grid-auto-rows]="gridAutoRows"
      >
        <app-dashboard-widget
          *ngFor="let widget of widgets; trackBy: trackWidget"
          [config]="widget"
          [loading]="widgetLoading[widget.id]"
          [refreshing]="widgetRefreshing[widget.id]"
          [error]="widgetErrors[widget.id]"
          [lastUpdated]="widgetLastUpdated[widget.id]"
          [metricData]="widgetData[widget.id]?.metrics"
          [chartData]="widgetData[widget.id]?.chart"
          [chartOptions]="widgetData[widget.id]?.chartOptions"
          [chartConfig]="widgetData[widget.id]?.chartConfig"
          [tableColumns]="widgetData[widget.id]?.tableColumns"
          [tableData]="widgetData[widget.id]?.tableData"
          [tableConfig]="widgetData[widget.id]?.tableConfig"
          [statusData]="widgetData[widget.id]?.status"
          [showSettings]="editMode"
          (refreshClicked)="refreshWidget(widget.id)"
          (settingsClicked)="editWidget(widget.id)"
          (fullscreenToggled)="toggleWidgetFullscreen(widget.id)"
          (tableRowClicked)="onWidgetTableRowClick(widget.id, $event)"
        ></app-dashboard-widget>
      </div>

      <!-- Empty State -->
      <div 
        *ngIf="widgets.length === 0" 
        class="flex-1 flex items-center justify-center p-8"
      >
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-4 bg-secondary-100 rounded-full flex items-center justify-center">
            <div class="w-8 h-8 bg-secondary-400 rounded-full"></div>
          </div>
          <h3 class="text-lg font-medium text-secondary-900 mb-2">No widgets added</h3>
          <p class="text-secondary-600 mb-4">Start building your dashboard by adding widgets</p>
          <app-button
            variant="primary"
            leftIcon="plus"
            (clicked)="openAddWidgetModal()"
          >
            Add Your First Widget
          </app-button>
        </div>
      </div>
    </div>

    <!-- Add Widget Modal -->
    <app-modal
      [(isOpen)]="showAddWidgetModal"
      title="Add Widget"
      size="lg"
    >
      <div class="space-y-6">
        <!-- Widget Templates -->
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div
            *ngFor="let template of widgetTemplates"
            class="p-4 border border-secondary-200 rounded-lg cursor-pointer hover:border-primary-300 hover:bg-primary-50 transition-colors"
            [class.border-primary-500]="selectedWidgetTemplate?.id === template.id"
            [class.bg-primary-50]="selectedWidgetTemplate?.id === template.id"
            (click)="selectWidgetTemplate(template)"
          >
            <div class="text-center">
              <div class="w-12 h-12 mx-auto mb-2 bg-secondary-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-secondary-600 rounded"></div>
              </div>
              <h4 class="font-medium text-secondary-900">{{ template.name }}</h4>
              <p class="text-sm text-secondary-600">{{ template.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <div slot="footer" class="flex justify-end space-x-2">
        <app-button
          variant="ghost"
          (clicked)="closeAddWidgetModal()"
        >
          Cancel
        </app-button>
        <app-button
          variant="primary"
          [disabled]="!selectedWidgetTemplate"
          (clicked)="addWidget()"
        >
          Add Widget
        </app-button>
      </div>
    </app-modal>

    <!-- Dashboard Settings Modal -->
    <app-modal
      [(isOpen)]="showSettingsModal"
      title="Dashboard Settings"
      size="md"
    >
      <div class="space-y-4">
        <!-- Dashboard settings form would go here -->
        <p class="text-secondary-600">Dashboard settings configuration...</p>
      </div>

      <div slot="footer" class="flex justify-end space-x-2">
        <app-button
          variant="ghost"
          (clicked)="closeSettingsModal()"
        >
          Cancel
        </app-button>
        <app-button
          variant="primary"
          (clicked)="saveDashboardSettings()"
        >
          Save Settings
        </app-button>
      </div>
    </app-modal>
  `,
  styles: [`
    .dashboard-grid {
      display: grid;
    }
  `]
})
export class DashboardLayoutComponent implements OnInit, OnDestroy {
  @Input() dashboard: Dashboard | null = null;
  @Input() editMode = false;
  @Input() autoRefresh = true;
  @Input() refreshInterval = 30000; // 30 seconds

  @Output() dashboardChanged = new EventEmitter<Dashboard>();
  @Output() widgetAdded = new EventEmitter<WidgetConfig>();
  @Output() widgetRemoved = new EventEmitter<string>();
  @Output() widgetUpdated = new EventEmitter<{ id: string; config: Partial<WidgetConfig> }>();

  widgets: WidgetConfig[] = [];
  widgetData: Record<string, any> = {};
  widgetLoading: Record<string, boolean> = {};
  widgetRefreshing: Record<string, boolean> = {};
  widgetErrors: Record<string, string> = {};
  widgetLastUpdated: Record<string, Date> = {};

  refreshing = false;
  autoRefreshActive = false;
  private autoRefreshTimer?: number;
  private destroy$ = new Subject<void>();

  // Modal states
  showAddWidgetModal = false;
  showSettingsModal = false;
  selectedWidgetTemplate: any = null;

  // Dashboard actions
  dashboardActions = [
    { id: 'save', label: 'Save Dashboard', icon: 'copy' as IconName },
    { id: 'export', label: 'Export Dashboard', icon: 'download' as IconName },
    { id: 'duplicate', label: 'Duplicate Dashboard', icon: 'copy' as IconName },
    { id: 'delete', label: 'Delete Dashboard', icon: 'trash2' as IconName, danger: true }
  ];

  // Widget templates
  widgetTemplates = [
    {
      id: 'metric',
      name: 'Metric Card',
      description: 'Display key metrics',
      icon: 'barChart3',
      type: 'metric',
      size: 'sm'
    },
    {
      id: 'line-chart',
      name: 'Line Chart',
      description: 'Time series data',
      icon: 'barChart3',
      type: 'chart',
      size: 'md'
    },
    {
      id: 'table',
      name: 'Data Table',
      description: 'Tabular data display',
      icon: 'barChart3',
      type: 'table',
      size: 'lg'
    },
    {
      id: 'status',
      name: 'Status List',
      description: 'System status overview',
      icon: 'activity',
      type: 'status',
      size: 'md'
    }
  ];

  constructor(
    private dashboardService: DashboardService,
    private websocketService: WebSocketService,
    private notificationService: NotificationService
  ) {}

  ngOnInit(): void {
    this.loadDashboard();
    this.setupRealTimeUpdates();
    
    if (this.autoRefresh) {
      this.startAutoRefresh();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.stopAutoRefresh();
  }

  private loadDashboard(): void {
    if (this.dashboard) {
      this.widgets = this.dashboard.configuration?.['widgets'] || [];
      this.loadAllWidgetData();
    }
  }

  private setupRealTimeUpdates(): void {
    // Subscribe to real-time updates for dashboard data
    this.websocketService.subscribeToMetrics((data) => {
      this.updateWidgetData(data);
    });
  }

  private updateWidgetData(data: any): void {
    // Update widget data based on real-time updates
    // This would be implemented based on the specific data structure
  }

  get gridColumns(): string {
    return `repeat(${this.dashboard?.configuration?.['layout']?.['columns'] || 4}, 1fr)`;
  }

  get gridGap(): string {
    return `${this.dashboard?.configuration?.['layout']?.['gap'] || 16}px`;
  }

  get gridAutoRows(): string {
    return this.dashboard?.configuration?.['layout']?.['autoRows'] || 'minmax(200px, auto)';
  }

  trackWidget(index: number, widget: WidgetConfig): string {
    return widget.id;
  }

  // Widget Management
  refreshAll(): void {
    this.refreshing = true;
    this.loadAllWidgetData().finally(() => {
      this.refreshing = false;
    });
  }

  refreshWidget(widgetId: string): void {
    this.widgetRefreshing[widgetId] = true;
    this.loadWidgetData(widgetId).finally(() => {
      this.widgetRefreshing[widgetId] = false;
    });
  }

  private async loadAllWidgetData(): Promise<void> {
    const promises = this.widgets.map(widget => this.loadWidgetData(widget.id));
    await Promise.allSettled(promises);
  }

  private async loadWidgetData(widgetId: string): Promise<void> {
    const widget = this.widgets.find(w => w.id === widgetId);
    if (!widget) return;

    this.widgetLoading[widgetId] = true;
    this.widgetErrors[widgetId] = '';

    try {
      // Load data based on widget type and data source
      const data = await this.fetchWidgetData(widget);
      this.widgetData[widgetId] = data;
      this.widgetLastUpdated[widgetId] = new Date();
    } catch (error: any) {
      this.widgetErrors[widgetId] = error.message || 'Failed to load widget data';
      this.notificationService.showError('Widget Error', `Failed to load data for ${widget.title}`);
    } finally {
      this.widgetLoading[widgetId] = false;
    }
  }

  private async fetchWidgetData(widget: WidgetConfig): Promise<any> {
    // This would implement the actual data fetching logic
    // based on the widget's data source and configuration
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          metrics: [],
          chart: { labels: [], datasets: [] },
          tableData: [],
          status: []
        });
      }, 1000);
    });
  }

  // Auto Refresh
  startAutoRefresh(): void {
    if (this.autoRefreshTimer) {
      clearInterval(this.autoRefreshTimer);
    }

    this.autoRefreshActive = true;
    this.autoRefreshTimer = window.setInterval(() => {
      this.refreshAll();
    }, this.refreshInterval);
  }

  stopAutoRefresh(): void {
    if (this.autoRefreshTimer) {
      clearInterval(this.autoRefreshTimer);
      this.autoRefreshTimer = undefined;
    }
    this.autoRefreshActive = false;
  }

  // Modal Management
  openAddWidgetModal(): void {
    this.showAddWidgetModal = true;
    this.selectedWidgetTemplate = null;
  }

  closeAddWidgetModal(): void {
    this.showAddWidgetModal = false;
    this.selectedWidgetTemplate = null;
  }

  selectWidgetTemplate(template: any): void {
    this.selectedWidgetTemplate = template;
  }

  addWidget(): void {
    if (!this.selectedWidgetTemplate) return;

    const newWidget: WidgetConfig = {
      id: `widget_${Date.now()}`,
      title: this.selectedWidgetTemplate.name,
      type: this.selectedWidgetTemplate.type,
      size: this.selectedWidgetTemplate.size,
      refreshInterval: 30000,
      dataSource: 'default'
    };

    this.widgets.push(newWidget);
    this.widgetAdded.emit(newWidget);
    this.closeAddWidgetModal();
    
    // Load data for the new widget
    this.loadWidgetData(newWidget.id);
  }

  editWidget(widgetId: string): void {
    // Open widget configuration modal
    console.log('Edit widget:', widgetId);
  }

  toggleWidgetFullscreen(widgetId: string): void {
    // Implement fullscreen toggle
    console.log('Toggle fullscreen for widget:', widgetId);
  }

  onWidgetTableRowClick(widgetId: string, row: any): void {
    console.log('Table row clicked in widget:', widgetId, row);
  }

  // Dashboard Actions
  onDashboardAction(action: any): void {
    switch (action.id) {
      case 'save':
        this.saveDashboard();
        break;
      case 'export':
        this.exportDashboard();
        break;
      case 'duplicate':
        this.duplicateDashboard();
        break;
      case 'delete':
        this.deleteDashboard();
        break;
    }
  }

  private saveDashboard(): void {
    if (!this.dashboard) return;

    const updatedDashboard = {
      ...this.dashboard,
      configuration: {
        ...this.dashboard.configuration,
        widgets: this.widgets
      }
    };

    this.dashboardService.updateDashboard(this.dashboard.id, updatedDashboard)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (dashboard) => {
          this.dashboard = dashboard;
          this.dashboardChanged.emit(dashboard);
          this.notificationService.showSuccess('Success', 'Dashboard saved successfully');
        },
        error: (error) => {
          this.notificationService.showError('Error', 'Failed to save dashboard');
        }
      });
  }

  private exportDashboard(): void {
    // Implement dashboard export
    console.log('Export dashboard');
  }

  private duplicateDashboard(): void {
    // Implement dashboard duplication
    console.log('Duplicate dashboard');
  }

  private deleteDashboard(): void {
    // Implement dashboard deletion with confirmation
    console.log('Delete dashboard');
  }

  openSettingsModal(): void {
    this.showSettingsModal = true;
  }

  closeSettingsModal(): void {
    this.showSettingsModal = false;
  }

  saveDashboardSettings(): void {
    // Implement dashboard settings save
    this.closeSettingsModal();
  }
}