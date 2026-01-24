import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { BiAnalyticsService } from '../services/bi-analytics.service';
import { DataExportService } from '../services/data-export.service';
import { ReportDefinition, ExportConfig } from '../models/bi-models';

@Component({
  selector: 'app-reports-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="reports-list p-6 bg-gray-50 min-h-screen">
      <!-- Header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Reports</h1>
          <p class="text-gray-600 mt-2">Manage and view your custom reports</p>
        </div>
        <div class="flex items-center space-x-4">
          <button
            routerLink="/bi-reporting/report-builder"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            <span>New Report</span>
          </button>
        </div>
      </div>

      <!-- Filters and Search -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <!-- Search -->
            <div class="relative">
              <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
              <input
                [(ngModel)]="searchTerm"
                type="text"
                placeholder="Search reports..."
                class="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
              >
            </div>

            <!-- Type Filter -->
            <select
              [(ngModel)]="selectedType"
              class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="executive">Executive</option>
              <option value="operational">Operational</option>
              <option value="technical">Technical</option>
            </select>

            <!-- Status Filter -->
            <select
              [(ngModel)]="selectedStatus"
              class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          <!-- View Toggle -->
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-600">View:</span>
            <button
              (click)="setViewMode('grid')"
              [class]="viewMode() === 'grid' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'"
              class="p-2 rounded"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>
              </svg>
            </button>
            <button
              (click)="setViewMode('list')"
              [class]="viewMode() === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'"
              class="p-2 rounded"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Reports Grid/List -->
      @if (viewMode() === 'grid') {
        <!-- Grid View -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          @for (report of filteredReports(); track report.id) {
            <div class="report-card bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200">
              <!-- Report Preview -->
              <div class="h-32 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-t-lg p-4 flex items-center justify-center">
                <svg class="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>

              <!-- Report Info -->
              <div class="p-4">
                <div class="flex items-start justify-between mb-2">
                  <h3 class="text-lg font-semibold text-gray-900 truncate">{{ report.name }}</h3>
                  <span [class]="getReportTypeBadgeClass(report.reportType)" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium">
                    {{ report.reportType | titlecase }}
                  </span>
                </div>

                <p class="text-sm text-gray-600 mb-3 line-clamp-2">{{ report.description }}</p>

                <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
                  <span>{{ report.widgets.length }} widgets</span>
                  <span>{{ getRelativeTime(report.updatedAt) }}</span>
                </div>

                <!-- Status Indicator -->
                <div class="flex items-center space-x-2 mb-4">
                  <div [class]="report.isActive ? 'bg-green-500' : 'bg-gray-400'" class="w-2 h-2 rounded-full"></div>
                  <span class="text-xs text-gray-600">{{ report.isActive ? 'Active' : 'Inactive' }}</span>
                </div>

                <!-- Actions -->
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-2">
                    <button
                      (click)="viewReport(report)"
                      class="px-3 py-1 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200"
                    >
                      View
                    </button>
                    <button
                      (click)="editReport(report)"
                      class="px-3 py-1 bg-gray-100 text-gray-700 rounded text-xs hover:bg-gray-200"
                    >
                      Edit
                    </button>
                  </div>
                  
                  <div class="relative">
                    <button
                      (click)="toggleReportMenu(report.id)"
                      class="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path>
                      </svg>
                    </button>

                    @if (activeMenuId() === report.id) {
                      <div class="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
                        <div class="py-1">
                          <button
                            (click)="exportReport(report, 'pdf')"
                            class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            Export as PDF
                          </button>
                          <button
                            (click)="exportReport(report, 'excel')"
                            class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            Export as Excel
                          </button>
                          <button
                            (click)="duplicateReport(report)"
                            class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            Duplicate
                          </button>
                          <button
                            (click)="toggleReportStatus(report)"
                            class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            {{ report.isActive ? 'Deactivate' : 'Activate' }}
                          </button>
                          <hr class="my-1">
                          <button
                            (click)="deleteReport(report)"
                            class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    }
                  </div>
                </div>
              </div>
            </div>
          } @empty {
            <div class="col-span-full text-center py-12">
              <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
              <h3 class="text-lg font-medium text-gray-900 mb-2">No reports found</h3>
              <p class="text-gray-600 mb-4">Get started by creating your first report</p>
              <button
                routerLink="/bi-reporting/report-builder"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Report
              </button>
            </div>
          }
        </div>
      } @else {
        <!-- List View -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Report</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Widgets</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Updated</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              @for (report of filteredReports(); track report.id) {
                <tr class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div class="text-sm font-medium text-gray-900">{{ report.name }}</div>
                      <div class="text-sm text-gray-500">{{ report.description }}</div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span [class]="getReportTypeBadgeClass(report.reportType)" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium">
                      {{ report.reportType | titlecase }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ report.widgets.length }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center space-x-2">
                      <div [class]="report.isActive ? 'bg-green-500' : 'bg-gray-400'" class="w-2 h-2 rounded-full"></div>
                      <span class="text-sm text-gray-600">{{ report.isActive ? 'Active' : 'Inactive' }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ getRelativeTime(report.updatedAt) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div class="flex items-center space-x-2">
                      <button
                        (click)="viewReport(report)"
                        class="text-blue-600 hover:text-blue-900"
                      >
                        View
                      </button>
                      <button
                        (click)="editReport(report)"
                        class="text-gray-600 hover:text-gray-900"
                      >
                        Edit
                      </button>
                      <button
                        (click)="exportReport(report, 'pdf')"
                        class="text-green-600 hover:text-green-900"
                      >
                        Export
                      </button>
                    </div>
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="6" class="px-6 py-12 text-center">
                    <div class="text-gray-500">
                      <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                      </svg>
                      <p class="text-lg font-medium text-gray-900 mb-2">No reports found</p>
                      <p class="text-gray-600">Create your first report to get started</p>
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }

      <!-- Backdrop for menus -->
      @if (activeMenuId()) {
        <div 
          (click)="closeMenus()"
          class="fixed inset-0 z-5"
        ></div>
      }
    </div>
  `,
  styles: [`
    .reports-list {
      animation: fadeIn 0.3s ease-in-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .report-card {
      transition: all 0.2s ease-in-out;
    }

    .report-card:hover {
      transform: translateY(-2px);
    }

    .line-clamp-2 {
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  `]
})
export class ReportsListComponent implements OnInit {
  // Signals for reactive state
  reports = signal<ReportDefinition[]>([]);
  viewMode = signal<'grid' | 'list'>('grid');
  activeMenuId = signal<string | null>(null);

  // Filter state
  searchTerm = '';
  selectedType = '';
  selectedStatus = '';

  // Computed filtered reports
  filteredReports = computed(() => {
    let filtered = this.reports();

    // Search filter
    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase();
      filtered = filtered.filter(report => 
        report.name.toLowerCase().includes(term) ||
        report.description.toLowerCase().includes(term)
      );
    }

    // Type filter
    if (this.selectedType) {
      filtered = filtered.filter(report => report.reportType === this.selectedType);
    }

    // Status filter
    if (this.selectedStatus) {
      const isActive = this.selectedStatus === 'active';
      filtered = filtered.filter(report => report.isActive === isActive);
    }

    return filtered;
  });

  constructor(
    private biAnalyticsService: BiAnalyticsService,
    private dataExportService: DataExportService
  ) {}

  ngOnInit(): void {
    this.loadReports();
  }

  loadReports(): void {
    this.biAnalyticsService.getReports().subscribe({
      next: (reports) => {
        this.reports.set(reports);
      },
      error: (error) => {
        console.error('Error loading reports:', error);
      }
    });
  }

  setViewMode(mode: 'grid' | 'list'): void {
    this.viewMode.set(mode);
  }

  toggleReportMenu(reportId: string): void {
    this.activeMenuId.set(this.activeMenuId() === reportId ? null : reportId);
  }

  closeMenus(): void {
    this.activeMenuId.set(null);
  }

  viewReport(report: ReportDefinition): void {
    // Navigate to report view or open in modal
    console.log('View report:', report.name);
  }

  editReport(report: ReportDefinition): void {
    // Navigate to report builder with report data
    console.log('Edit report:', report.name);
  }

  exportReport(report: ReportDefinition, format: 'pdf' | 'excel'): void {
    this.closeMenus();
    
    const config: ExportConfig = {
      format: format,
      filename: `${report.name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.${format}`,
      includeCharts: true,
      includeData: true
    };

    this.dataExportService.exportData(config).subscribe({
      next: (result) => {
        if (result.success && result.downloadUrl && result.filename) {
          this.dataExportService.downloadFile(result.downloadUrl, result.filename);
        }
      },
      error: (error) => {
        console.error('Export failed:', error);
      }
    });
  }

  duplicateReport(report: ReportDefinition): void {
    this.closeMenus();
    
    const duplicatedReport: ReportDefinition = {
      ...report,
      id: '',
      name: `${report.name} (Copy)`,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.biAnalyticsService.saveReport(duplicatedReport).subscribe({
      next: (savedReport) => {
        this.reports.update(reports => [...reports, savedReport]);
        console.log('Report duplicated successfully');
      },
      error: (error) => {
        console.error('Error duplicating report:', error);
      }
    });
  }

  toggleReportStatus(report: ReportDefinition): void {
    this.closeMenus();
    
    const updatedReport = { ...report, isActive: !report.isActive, updatedAt: new Date() };
    
    this.biAnalyticsService.saveReport(updatedReport).subscribe({
      next: (savedReport) => {
        this.reports.update(reports => 
          reports.map(r => r.id === savedReport.id ? savedReport : r)
        );
        console.log(`Report ${savedReport.isActive ? 'activated' : 'deactivated'}`);
      },
      error: (error) => {
        console.error('Error updating report status:', error);
      }
    });
  }

  deleteReport(report: ReportDefinition): void {
    this.closeMenus();
    
    if (confirm(`Are you sure you want to delete "${report.name}"? This action cannot be undone.`)) {
      this.biAnalyticsService.deleteReport(report.id).subscribe({
        next: (success) => {
          if (success) {
            this.reports.update(reports => reports.filter(r => r.id !== report.id));
            console.log('Report deleted successfully');
          }
        },
        error: (error) => {
          console.error('Error deleting report:', error);
        }
      });
    }
  }

  getReportTypeBadgeClass(type: string): string {
    switch (type) {
      case 'executive': return 'bg-purple-100 text-purple-800';
      case 'operational': return 'bg-blue-100 text-blue-800';
      case 'technical': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }

  getRelativeTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - new Date(date).getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) {
      return 'Just now';
    } else if (minutes < 60) {
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${hours}h ago`;
    } else if (days < 7) {
      return `${days}d ago`;
    } else {
      return new Date(date).toLocaleDateString();
    }
  }
}