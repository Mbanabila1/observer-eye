import { Component, Input, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DataExportService } from '../../services/data-export.service';
import { ExportConfig, ExportFormat, ExportResult } from '../../models/bi-models';

@Component({
  selector: 'app-export-button',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="export-button relative">
      <!-- Export Button -->
      <button
        (click)="toggleDropdown()"
        [disabled]="isExporting()"
        class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
      >
        @if (isExporting()) {
          <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Exporting...</span>
        } @else {
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          <span>Export</span>
        }
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>

      <!-- Export Options Dropdown -->
      @if (showDropdown()) {
        <div class="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div class="p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Export Options</h3>
            
            <!-- Export Format Selection -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Format</label>
              <div class="grid grid-cols-2 gap-2">
                @for (format of availableFormats; track format) {
                  <button
                    (click)="selectFormat(format)"
                    [class]="selectedFormat() === format ? 'bg-blue-100 border-blue-500 text-blue-700' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'"
                    class="px-3 py-2 border rounded-lg text-sm font-medium transition-colors"
                  >
                    {{ getFormatLabel(format) }}
                  </button>
                }
              </div>
            </div>

            <!-- Filename Input -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Filename</label>
              <input
                [(ngModel)]="customFilename"
                type="text"
                [placeholder]="getDefaultFilename()"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
              <p class="text-xs text-gray-500 mt-1">Leave empty to use default filename</p>
            </div>

            <!-- Export Options -->
            <div class="mb-4 space-y-3">
              <label class="block text-sm font-medium text-gray-700">Include</label>
              
              <div class="flex items-center space-x-2">
                <input
                  [(ngModel)]="includeCharts"
                  type="checkbox"
                  id="include-charts"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                >
                <label for="include-charts" class="text-sm text-gray-700">Charts and visualizations</label>
              </div>
              
              <div class="flex items-center space-x-2">
                <input
                  [(ngModel)]="includeData"
                  type="checkbox"
                  id="include-data"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                >
                <label for="include-data" class="text-sm text-gray-700">Raw data tables</label>
              </div>
            </div>

            <!-- Date Range (for data exports) -->
            @if (selectedFormat() === 'csv' || selectedFormat() === 'excel' || selectedFormat() === 'json') {
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
                <div class="grid grid-cols-2 gap-2">
                  <div>
                    <input
                      [(ngModel)]="startDate"
                      type="date"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                  </div>
                  <div>
                    <input
                      [(ngModel)]="endDate"
                      type="date"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                  </div>
                </div>
              </div>
            }

            <!-- Action Buttons -->
            <div class="flex items-center justify-between pt-4 border-t border-gray-100">
              <button
                (click)="closeDropdown()"
                class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                (click)="startExport()"
                [disabled]="isExporting()"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
              >
                {{ isExporting() ? 'Exporting...' : 'Export Now' }}
              </button>
            </div>
          </div>
        </div>
      }

      <!-- Export Progress/Result Toast -->
      @if (exportResult()) {
        <div class="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div class="p-4">
            @if (exportResult()!.success) {
              <!-- Success State -->
              <div class="flex items-start space-x-3">
                <svg class="w-6 h-6 text-green-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <div class="flex-1">
                  <h4 class="text-sm font-medium text-gray-900">Export Successful</h4>
                  <p class="text-sm text-gray-600 mt-1">{{ exportResult()!.filename }}</p>
                  @if (exportResult()!.size) {
                    <p class="text-xs text-gray-500 mt-1">{{ formatFileSize(exportResult()!.size!) }}</p>
                  }
                  <div class="mt-3 flex space-x-2">
                    <button
                      (click)="downloadFile()"
                      class="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                    >
                      Download
                    </button>
                    <button
                      (click)="clearResult()"
                      class="px-3 py-1 bg-gray-100 text-gray-700 rounded text-xs hover:bg-gray-200"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            } @else {
              <!-- Error State -->
              <div class="flex items-start space-x-3">
                <svg class="w-6 h-6 text-red-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <div class="flex-1">
                  <h4 class="text-sm font-medium text-gray-900">Export Failed</h4>
                  <p class="text-sm text-gray-600 mt-1">{{ exportResult()!.error }}</p>
                  <div class="mt-3 flex space-x-2">
                    <button
                      (click)="startExport()"
                      class="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                    >
                      Try Again
                    </button>
                    <button
                      (click)="clearResult()"
                      class="px-3 py-1 bg-gray-100 text-gray-700 rounded text-xs hover:bg-gray-200"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            }
          </div>
        </div>
      }

      <!-- Backdrop -->
      @if (showDropdown() || exportResult()) {
        <div 
          (click)="closeDropdown(); clearResult()"
          class="fixed inset-0 z-40"
        ></div>
      }
    </div>
  `,
  styles: [`
    .export-button {
      position: relative;
    }
  `]
})
export class ExportButtonComponent {
  @Input() data: any = null;
  @Input() filename: string = '';
  @Output() exportComplete = new EventEmitter<ExportResult>();

  // Signals for reactive state
  showDropdown = signal<boolean>(false);
  isExporting = signal<boolean>(false);
  selectedFormat = signal<ExportFormat>('pdf');
  exportResult = signal<ExportResult | null>(null);

  // Form data
  customFilename = '';
  includeCharts = true;
  includeData = true;
  startDate = '';
  endDate = '';

  availableFormats: ExportFormat[] = ['pdf', 'excel', 'csv', 'json', 'png'];

  constructor(private dataExportService: DataExportService) {
    // Set default date range (last 30 days)
    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    
    this.endDate = now.toISOString().split('T')[0];
    this.startDate = thirtyDaysAgo.toISOString().split('T')[0];
  }

  toggleDropdown(): void {
    this.showDropdown.set(!this.showDropdown());
    this.clearResult();
  }

  closeDropdown(): void {
    this.showDropdown.set(false);
  }

  selectFormat(format: ExportFormat): void {
    this.selectedFormat.set(format);
  }

  getFormatLabel(format: ExportFormat): string {
    switch (format) {
      case 'pdf': return 'PDF Report';
      case 'excel': return 'Excel File';
      case 'csv': return 'CSV Data';
      case 'json': return 'JSON Data';
      case 'png': return 'PNG Image';
      default: return (format as string).toUpperCase();
    }
  }

  getDefaultFilename(): string {
    const timestamp = new Date().toISOString().split('T')[0];
    const baseFilename = this.filename || 'export';
    return `${baseFilename}_${timestamp}.${this.selectedFormat()}`;
  }

  startExport(): void {
    this.isExporting.set(true);
    this.clearResult();

    const config: ExportConfig = {
      format: this.selectedFormat(),
      filename: this.customFilename || this.getDefaultFilename(),
      includeCharts: this.includeCharts,
      includeData: this.includeData,
      dateRange: this.startDate && this.endDate ? {
        start: new Date(this.startDate),
        end: new Date(this.endDate)
      } : undefined
    };

    // Validate configuration
    const validation = this.dataExportService.validateExportConfig(config);
    if (!validation.valid) {
      this.exportResult.set({
        success: false,
        error: validation.errors.join(', ')
      });
      this.isExporting.set(false);
      return;
    }

    // Perform export
    this.dataExportService.exportData(config).subscribe({
      next: (result) => {
        this.exportResult.set(result);
        this.isExporting.set(false);
        this.showDropdown.set(false);
        this.exportComplete.emit(result);
      },
      error: (error) => {
        this.exportResult.set({
          success: false,
          error: 'Export failed: ' + error.message
        });
        this.isExporting.set(false);
      }
    });
  }

  downloadFile(): void {
    const result = this.exportResult();
    if (result?.success && result.downloadUrl && result.filename) {
      this.dataExportService.downloadFile(result.downloadUrl, result.filename);
    }
  }

  clearResult(): void {
    this.exportResult.set(null);
  }

  formatFileSize(bytes: number): string {
    return this.dataExportService.formatFileSize(bytes);
  }
}