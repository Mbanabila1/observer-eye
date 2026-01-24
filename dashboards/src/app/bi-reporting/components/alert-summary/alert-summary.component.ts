import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AlertSummaryWidget, AlertItem } from '../../models/bi-models';

@Component({
  selector: 'app-alert-summary',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="alert-summary bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-gray-900">{{ alertData.title }}</h3>
        <button class="text-sm text-blue-600 hover:text-blue-800 font-medium">
          View All Alerts
        </button>
      </div>

      <!-- Alert Counts Summary -->
      <div class="grid grid-cols-3 gap-4 mb-6">
        <!-- Critical Alerts -->
        <div class="text-center p-4 bg-red-50 rounded-lg border border-red-100">
          <div class="text-2xl font-bold text-red-600">{{ alertData.criticalCount }}</div>
          <div class="text-sm text-red-700 font-medium">Critical</div>
          <div class="text-xs text-red-600 mt-1">Immediate attention</div>
        </div>

        <!-- Warning Alerts -->
        <div class="text-center p-4 bg-yellow-50 rounded-lg border border-yellow-100">
          <div class="text-2xl font-bold text-yellow-600">{{ alertData.warningCount }}</div>
          <div class="text-sm text-yellow-700 font-medium">Warning</div>
          <div class="text-xs text-yellow-600 mt-1">Monitor closely</div>
        </div>

        <!-- Info Alerts -->
        <div class="text-center p-4 bg-blue-50 rounded-lg border border-blue-100">
          <div class="text-2xl font-bold text-blue-600">{{ alertData.infoCount }}</div>
          <div class="text-sm text-blue-700 font-medium">Info</div>
          <div class="text-xs text-blue-600 mt-1">For awareness</div>
        </div>
      </div>

      <!-- Alert Trend Indicator -->
      <div class="mb-6 p-3 bg-gray-50 rounded-lg">
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600">Alert Trend (24h)</span>
          <div class="flex items-center space-x-2">
            <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
            </svg>
            <span class="text-sm font-medium text-green-600">-12% from yesterday</span>
          </div>
        </div>
      </div>

      <!-- Recent Alerts List -->
      <div>
        <h4 class="text-sm font-medium text-gray-900 mb-3">Recent Alerts</h4>
        <div class="space-y-3 max-h-64 overflow-y-auto">
          @for (alert of alertData.recentAlerts; track alert.id) {
            <div class="flex items-start space-x-3 p-3 rounded-lg border" [class]="getAlertBorderClass(alert.severity)">
              <!-- Severity Icon -->
              <div class="flex-shrink-0 mt-0.5">
                <div [class]="getSeverityIconClass(alert.severity)" class="w-2 h-2 rounded-full"></div>
              </div>

              <!-- Alert Content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <p [class]="getSeverityTextClass(alert.severity)" class="text-sm font-medium truncate">
                      {{ alert.message }}
                    </p>
                    <div class="flex items-center space-x-2 mt-1">
                      <span class="text-xs text-gray-500">{{ alert.source }}</span>
                      <span class="text-xs text-gray-400">•</span>
                      <span class="text-xs text-gray-500">{{ getRelativeTime(alert.timestamp) }}</span>
                    </div>
                  </div>
                  
                  <!-- Severity Badge -->
                  <span [class]="getSeverityBadgeClass(alert.severity)" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ml-2">
                    {{ alert.severity | titlecase }}
                  </span>
                </div>
              </div>

              <!-- Action Menu -->
              <div class="flex-shrink-0">
                <button class="text-gray-400 hover:text-gray-600 p-1 rounded">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path>
                  </svg>
                </button>
              </div>
            </div>
          } @empty {
            <div class="text-center py-8 text-gray-500">
              <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <p class="text-sm">No recent alerts</p>
              <p class="text-xs text-gray-400 mt-1">All systems operating normally</p>
            </div>
          }
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="mt-6 pt-4 border-t border-gray-100">
        <div class="flex items-center justify-between">
          <div class="flex space-x-2">
            <button class="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors">
              Acknowledge All
            </button>
            <button class="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors">
              Filter by Source
            </button>
          </div>
          <div class="text-xs text-gray-500">
            Last updated: {{ getRelativeTime(lastUpdated()) }}
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .alert-summary {
      animation: slideInUp 0.4s ease-out;
    }

    @keyframes slideInUp {
      from {
        opacity: 0;
        transform: translateY(15px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .alert-item {
      transition: all 0.2s ease-in-out;
    }

    .alert-item:hover {
      transform: translateX(2px);
    }
  `]
})
export class AlertSummaryComponent {
  @Input({ required: true }) alertData!: AlertSummaryWidget;

  getSeverityIconClass(severity: string): string {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'warning': return 'bg-yellow-500';
      case 'info': return 'bg-blue-500';
      default: return 'bg-gray-400';
    }
  }

  getSeverityTextClass(severity: string): string {
    switch (severity) {
      case 'critical': return 'text-red-800';
      case 'warning': return 'text-yellow-800';
      case 'info': return 'text-blue-800';
      default: return 'text-gray-800';
    }
  }

  getSeverityBadgeClass(severity: string): string {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'info': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }

  getAlertBorderClass(severity: string): string {
    switch (severity) {
      case 'critical': return 'border-red-200 bg-red-50';
      case 'warning': return 'border-yellow-200 bg-yellow-50';
      case 'info': return 'border-blue-200 bg-blue-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  }

  getRelativeTime(timestamp: Date): string {
    const now = new Date();
    const diff = now.getTime() - new Date(timestamp).getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) {
      return 'Just now';
    } else if (minutes < 60) {
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${hours}h ago`;
    } else {
      return `${days}d ago`;
    }
  }

  lastUpdated(): Date {
    return new Date();
  }
}