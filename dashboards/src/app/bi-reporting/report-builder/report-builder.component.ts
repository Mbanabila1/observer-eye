import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BiAnalyticsService } from '../services/bi-analytics.service';
import { 
  ReportDefinition, 
  ReportWidgetConfig, 
  ReportWidgetType, 
  AnalyticalDataSource,
  LayoutConfig,
  AggregationConfig,
  FilterConfig
} from '../models/bi-models';

@Component({
  selector: 'app-report-builder',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="report-builder p-6 bg-gray-50 min-h-screen">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Report Builder</h1>
          <p class="text-gray-600 mt-2">Create custom reports with drag-and-drop interface</p>
        </div>
        <div class="flex items-center space-x-4">
          <button
            (click)="previewReport()"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
            </svg>
            <span>Preview</span>
          </button>
          <button
            (click)="saveReport()"
            [disabled]="!canSaveReport()"
            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12"></path>
            </svg>
            <span>Save Report</span>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-12 gap-6">
        <!-- Left Sidebar - Widget Library -->
        <div class="col-span-3">
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Widget Library</h2>
            
            <!-- Widget Categories -->
            <div class="space-y-4">
              <div>
                <h3 class="text-sm font-medium text-gray-700 mb-2">Charts</h3>
                <div class="space-y-2">
                  @for (widgetType of chartWidgetTypes; track widgetType) {
                    <div
                      (click)="selectWidgetType(widgetType)"
                      [class]="selectedWidgetType() === widgetType ? 'bg-blue-100 border-blue-500' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'"
                      class="p-3 border rounded-lg cursor-pointer transition-colors"
                    >
                      <div class="flex items-center space-x-2">
                        <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                        <span class="text-sm font-medium">{{ getWidgetTypeLabel(widgetType) }}</span>
                      </div>
                    </div>
                  }
                </div>
              </div>

              <div>
                <h3 class="text-sm font-medium text-gray-700 mb-2">Data</h3>
                <div class="space-y-2">
                  @for (widgetType of dataWidgetTypes; track widgetType) {
                    <div
                      (click)="selectWidgetType(widgetType)"
                      [class]="selectedWidgetType() === widgetType ? 'bg-blue-100 border-blue-500' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'"
                      class="p-3 border rounded-lg cursor-pointer transition-colors"
                    >
                      <div class="flex items-center space-x-2">
                        <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                        </svg>
                        <span class="text-sm font-medium">{{ getWidgetTypeLabel(widgetType) }}</span>
                      </div>
                    </div>
                  }
                </div>
              </div>
            </div>

            <!-- Add Widget Button -->
            <button
              (click)="addWidget()"
              [disabled]="!selectedWidgetType()"
              class="w-full mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              <span>Add Widget</span>
            </button>
          </div>

          <!-- Data Sources -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mt-4">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Data Sources</h2>
            <div class="space-y-2">
              @for (dataSource of dataSources(); track dataSource.id) {
                <div class="p-2 bg-gray-50 rounded border">
                  <div class="text-sm font-medium text-gray-900">{{ dataSource.name }}</div>
                  <div class="text-xs text-gray-600">{{ dataSource.type }} • {{ dataSource.fields.length }} fields</div>
                </div>
              }
            </div>
          </div>
        </div>

        <!-- Center - Report Canvas -->
        <div class="col-span-6">
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-gray-900">Report Canvas</h2>
              <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-600">Grid:</span>
                <button
                  (click)="toggleGrid()"
                  [class]="showGrid() ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'"
                  class="px-2 py-1 rounded text-xs"
                >
                  {{ showGrid() ? 'ON' : 'OFF' }}
                </button>
              </div>
            </div>

            <!-- Canvas Area -->
            <div 
              class="report-canvas relative border-2 border-dashed border-gray-300 rounded-lg min-h-96"
              [class.grid-background]="showGrid()"
              (drop)="onDrop($event)"
              (dragover)="onDragOver($event)"
            >
              @if (reportWidgets().length === 0) {
                <div class="absolute inset-0 flex items-center justify-center">
                  <div class="text-center text-gray-500">
                    <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                    <p class="text-lg font-medium">Start Building Your Report</p>
                    <p class="text-sm mt-1">Select a widget from the library and add it to your report</p>
                  </div>
                </div>
              }

              <!-- Report Widgets -->
              @for (widget of reportWidgets(); track widget.id) {
                <div
                  class="absolute border-2 border-blue-500 rounded-lg bg-white shadow-sm"
                  [style.left.px]="widget.position.x"
                  [style.top.px]="widget.position.y"
                  [style.width.px]="widget.position.width"
                  [style.height.px]="widget.position.height"
                  (click)="selectWidget(widget)"
                  [class.ring-2]="selectedWidget()?.id === widget.id"
                  [class.ring-blue-500]="selectedWidget()?.id === widget.id"
                >
                  <!-- Widget Header -->
                  <div class="flex items-center justify-between p-2 border-b border-gray-200 bg-gray-50 rounded-t-lg">
                    <span class="text-sm font-medium text-gray-900">{{ widget.title }}</span>
                    <div class="flex items-center space-x-1">
                      <button
                        (click)="editWidget(widget)"
                        class="p-1 text-gray-400 hover:text-gray-600"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                        </svg>
                      </button>
                      <button
                        (click)="removeWidget(widget.id)"
                        class="p-1 text-gray-400 hover:text-red-600"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                      </button>
                    </div>
                  </div>

                  <!-- Widget Content Preview -->
                  <div class="p-4 h-full">
                    <div class="text-center text-gray-500">
                      <div class="text-xs">{{ getWidgetTypeLabel(widget.type) }}</div>
                      <div class="text-xs mt-1">{{ widget.dataSource || 'No data source' }}</div>
                    </div>
                  </div>

                  <!-- Resize Handles -->
                  <div class="absolute bottom-0 right-0 w-3 h-3 bg-blue-500 cursor-se-resize"></div>
                </div>
              }
            </div>
          </div>
        </div>

        <!-- Right Sidebar - Widget Properties -->
        <div class="col-span-3">
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Properties</h2>

            @if (selectedWidget()) {
              <!-- Widget Configuration -->
              <div class="space-y-4">
                <!-- Basic Properties -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Title</label>
                  <input
                    [(ngModel)]="selectedWidget()!.title"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                </div>

                <!-- Data Source Selection -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Data Source</label>
                  <select
                    [(ngModel)]="selectedWidget()!.dataSource"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select data source</option>
                    @for (dataSource of dataSources(); track dataSource.id) {
                      <option [value]="dataSource.id">{{ dataSource.name }}</option>
                    }
                  </select>
                </div>

                <!-- Aggregations -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Aggregations</label>
                  <div class="space-y-2">
                    @for (agg of selectedWidget()!.aggregations; track $index; let i = $index) {
                      <div class="flex items-center space-x-2">
                        <select
                          [(ngModel)]="agg.field"
                          class="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                        >
                          <option value="">Select field</option>
                          @for (field of getAvailableFields(); track field.name) {
                            <option [value]="field.name">{{ field.label }}</option>
                          }
                        </select>
                        <select
                          [(ngModel)]="agg.function"
                          class="px-2 py-1 border border-gray-300 rounded text-sm"
                        >
                          <option value="sum">Sum</option>
                          <option value="avg">Average</option>
                          <option value="count">Count</option>
                          <option value="min">Min</option>
                          <option value="max">Max</option>
                        </select>
                        <button
                          (click)="removeAggregation(i)"
                          class="p-1 text-red-600 hover:text-red-800"
                        >
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                          </svg>
                        </button>
                      </div>
                    }
                    <button
                      (click)="addAggregation()"
                      class="w-full px-3 py-1 border border-dashed border-gray-300 rounded text-sm text-gray-600 hover:border-gray-400"
                    >
                      + Add Aggregation
                    </button>
                  </div>
                </div>

                <!-- Position and Size -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Position & Size</label>
                  <div class="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <label class="text-xs text-gray-600">X</label>
                      <input
                        [(ngModel)]="selectedWidget()!.position.x"
                        type="number"
                        class="w-full px-2 py-1 border border-gray-300 rounded"
                      >
                    </div>
                    <div>
                      <label class="text-xs text-gray-600">Y</label>
                      <input
                        [(ngModel)]="selectedWidget()!.position.y"
                        type="number"
                        class="w-full px-2 py-1 border border-gray-300 rounded"
                      >
                    </div>
                    <div>
                      <label class="text-xs text-gray-600">Width</label>
                      <input
                        [(ngModel)]="selectedWidget()!.position.width"
                        type="number"
                        class="w-full px-2 py-1 border border-gray-300 rounded"
                      >
                    </div>
                    <div>
                      <label class="text-xs text-gray-600">Height</label>
                      <input
                        [(ngModel)]="selectedWidget()!.position.height"
                        type="number"
                        class="w-full px-2 py-1 border border-gray-300 rounded"
                      >
                    </div>
                  </div>
                </div>
              </div>
            } @else {
              <div class="text-center text-gray-500 py-8">
                <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"></path>
                </svg>
                <p class="text-sm">Select a widget to configure its properties</p>
              </div>
            }
          </div>

          <!-- Report Settings -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mt-4">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Report Settings</h2>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Report Name</label>
                <input
                  [(ngModel)]="reportName"
                  type="text"
                  placeholder="Enter report name"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  [(ngModel)]="reportDescription"
                  rows="3"
                  placeholder="Enter report description"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                ></textarea>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Report Type</label>
                <select
                  [(ngModel)]="reportType"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="executive">Executive</option>
                  <option value="operational">Operational</option>
                  <option value="technical">Technical</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .report-builder {
      animation: fadeIn 0.3s ease-in-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .report-canvas {
      background-size: 20px 20px;
      background-position: 0 0, 10px 10px;
    }

    .grid-background {
      background-image: 
        linear-gradient(45deg, #f3f4f6 25%, transparent 25%), 
        linear-gradient(-45deg, #f3f4f6 25%, transparent 25%), 
        linear-gradient(45deg, transparent 75%, #f3f4f6 75%), 
        linear-gradient(-45deg, transparent 75%, #f3f4f6 75%);
    }

    .report-canvas .absolute {
      cursor: move;
    }

    .report-canvas .absolute:hover {
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
  `]
})
export class ReportBuilderComponent implements OnInit {
  // Signals for reactive state
  dataSources = signal<AnalyticalDataSource[]>([]);
  reportWidgets = signal<ReportWidgetConfig[]>([]);
  selectedWidgetType = signal<ReportWidgetType | null>(null);
  selectedWidget = signal<ReportWidgetConfig | null>(null);
  showGrid = signal<boolean>(true);

  // Form data
  reportName = '';
  reportDescription = '';
  reportType: 'executive' | 'operational' | 'technical' = 'operational';

  // Widget types
  chartWidgetTypes: ReportWidgetType[] = ['line-chart', 'bar-chart', 'pie-chart', 'heatmap', 'gauge'];
  dataWidgetTypes: ReportWidgetType[] = ['kpi-card', 'table', 'trend-analysis'];

  // Computed values
  canSaveReport = computed(() => {
    return this.reportName.trim().length > 0 && this.reportWidgets().length > 0;
  });

  constructor(private biAnalyticsService: BiAnalyticsService) {}

  ngOnInit(): void {
    this.loadDataSources();
  }

  loadDataSources(): void {
    this.biAnalyticsService.getAvailableDataSources().subscribe({
      next: (sources) => {
        this.dataSources.set(sources);
      },
      error: (error) => {
        console.error('Error loading data sources:', error);
      }
    });
  }

  selectWidgetType(type: ReportWidgetType): void {
    this.selectedWidgetType.set(type);
  }

  addWidget(): void {
    const type = this.selectedWidgetType();
    if (!type) return;

    const newWidget: ReportWidgetConfig = {
      id: this.generateId(),
      type: type,
      title: `New ${this.getWidgetTypeLabel(type)}`,
      dataSource: '',
      aggregations: [],
      filters: [],
      visualization: {},
      position: {
        x: Math.floor(Math.random() * 200) + 50,
        y: Math.floor(Math.random() * 200) + 50,
        width: 300,
        height: 200
      }
    };

    this.reportWidgets.update(widgets => [...widgets, newWidget]);
    this.selectWidget(newWidget);
  }

  selectWidget(widget: ReportWidgetConfig): void {
    this.selectedWidget.set(widget);
  }

  editWidget(widget: ReportWidgetConfig): void {
    this.selectWidget(widget);
  }

  removeWidget(widgetId: string): void {
    this.reportWidgets.update(widgets => widgets.filter(w => w.id !== widgetId));
    if (this.selectedWidget()?.id === widgetId) {
      this.selectedWidget.set(null);
    }
  }

  addAggregation(): void {
    const widget = this.selectedWidget();
    if (!widget) return;

    const newAggregation: AggregationConfig = {
      field: '',
      function: 'sum'
    };

    widget.aggregations.push(newAggregation);
  }

  removeAggregation(index: number): void {
    const widget = this.selectedWidget();
    if (!widget) return;

    widget.aggregations.splice(index, 1);
  }

  getAvailableFields() {
    const widget = this.selectedWidget();
    if (!widget || !widget.dataSource) return [];

    const dataSource = this.dataSources().find(ds => ds.id === widget.dataSource);
    return dataSource?.fields || [];
  }

  toggleGrid(): void {
    this.showGrid.update(show => !show);
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    // Handle widget drop from library
    // This would be implemented with proper drag and drop functionality
  }

  previewReport(): void {
    // Open preview modal or navigate to preview page
    console.log('Preview report:', {
      name: this.reportName,
      widgets: this.reportWidgets()
    });
  }

  saveReport(): void {
    if (!this.canSaveReport()) return;

    const reportDefinition: ReportDefinition = {
      id: '',
      name: this.reportName,
      description: this.reportDescription,
      reportType: this.reportType,
      widgets: this.reportWidgets(),
      layout: {
        columns: 12,
        rows: 8,
        gridSize: 20
      },
      distributionList: [],
      createdBy: 'current-user',
      createdAt: new Date(),
      updatedAt: new Date(),
      isActive: true
    };

    this.biAnalyticsService.saveReport(reportDefinition).subscribe({
      next: (savedReport) => {
        console.log('Report saved successfully:', savedReport);
        // Show success message or navigate to reports list
      },
      error: (error) => {
        console.error('Error saving report:', error);
        // Show error message
      }
    });
  }

  getWidgetTypeLabel(type: ReportWidgetType): string {
    switch (type) {
      case 'kpi-card': return 'KPI Card';
      case 'line-chart': return 'Line Chart';
      case 'bar-chart': return 'Bar Chart';
      case 'pie-chart': return 'Pie Chart';
      case 'table': return 'Data Table';
      case 'heatmap': return 'Heat Map';
      case 'gauge': return 'Gauge';
      case 'trend-analysis': return 'Trend Analysis';
      default: return type;
    }
  }

  private generateId(): string {
    return 'widget_' + Math.random().toString(36).substr(2, 9);
  }
}