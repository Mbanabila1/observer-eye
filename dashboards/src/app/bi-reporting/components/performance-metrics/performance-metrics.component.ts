import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PerformanceMetricsWidget, PerformanceMetric } from '../../models/bi-models';

@Component({
  selector: 'app-performance-metrics',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="performance-metrics bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h3 class="text-lg font-semibold text-gray-900">{{ performanceData.title }}</h3>
          <p class="text-sm text-gray-600">
            Compared to {{ getComparisonLabel(performanceData.comparison) }}
          </p>
        </div>
        <div class="flex items-center space-x-2">
          <button class="text-sm text-blue-600 hover:text-blue-800 font-medium">
            View Details
          </button>
        </div>
      </div>

      <!-- Metrics Grid -->
      <div class="space-y-4">
        @for (metric of performanceData.metrics; track metric.name) {
          <div class="metric-item p-4 border border-gray-100 rounded-lg hover:border-gray-200 transition-colors">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-3">
                <h4 class="text-sm font-medium text-gray-900">{{ metric.name }}</h4>
                <span class="text-xs text-gray-500">{{ metric.unit }}</span>
              </div>
              
              <!-- Trend Indicator -->
              <div class="flex items-center space-x-1">
                <svg 
                  [class]="getTrendIconClass(metric.trend)"
                  class="w-4 h-4"
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  @switch (metric.trend) {
                    @case ('up') {
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 17l9.2-9.2M17 17V7H7"></path>
                    }
                    @case ('down') {
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 7l-9.2 9.2M7 7v10h10"></path>
                    }
                    @default {
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path>
                    }
                  }
                </svg>
                <span [class]="getTrendTextClass(metric.trend)" class="text-sm font-medium">
                  {{ calculatePercentageChange(metric) }}
                </span>
              </div>
            </div>

            <!-- Current Value and Comparison -->
            <div class="flex items-end justify-between mb-3">
              <div>
                <div class="text-2xl font-bold text-gray-900">
                  {{ formatValue(metric.current) }}
                </div>
                <div class="text-sm text-gray-600">
                  Current: {{ formatValue(metric.current) }} {{ metric.unit }}
                </div>
              </div>
              
              <div class="text-right">
                <div class="text-sm text-gray-600">
                  Previous: {{ formatValue(metric.previous) }} {{ metric.unit }}
                </div>
                @if (metric.target !== undefined) {
                  <div class="text-sm text-gray-600">
                    Target: {{ formatValue(metric.target) }} {{ metric.unit }}
                  </div>
                }
              </div>
            </div>

            <!-- Progress Bar (if target is set) -->
            @if (metric.target !== undefined) {
              <div class="mb-3">
                <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
                  <span>Progress to Target</span>
                  <span>{{ getTargetProgress(metric) }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    [style.width.%]="Math.min(getTargetProgress(metric), 100)"
                    [class]="getProgressBarClass(metric)"
                    class="h-2 rounded-full transition-all duration-300"
                  ></div>
                </div>
              </div>
            }

            <!-- Comparison Bars -->
            <div class="grid grid-cols-2 gap-2">
              <!-- Current vs Previous -->
              <div class="text-center p-2 bg-gray-50 rounded">
                <div class="text-xs text-gray-600 mb-1">vs Previous</div>
                <div [class]="getComparisonClass(metric.current, metric.previous)" class="text-sm font-medium">
                  {{ formatValue(metric.current - metric.previous, true) }} {{ metric.unit }}
                </div>
              </div>

              <!-- Current vs Target (if available) -->
              @if (metric.target !== undefined) {
                <div class="text-center p-2 bg-gray-50 rounded">
                  <div class="text-xs text-gray-600 mb-1">vs Target</div>
                  <div [class]="getComparisonClass(metric.current, metric.target)" class="text-sm font-medium">
                    {{ formatValue(metric.current - metric.target, true) }} {{ metric.unit }}
                  </div>
                </div>
              }
            </div>

            <!-- Performance Status -->
            <div class="mt-3 flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <div [class]="getStatusIndicatorClass(metric)" class="w-2 h-2 rounded-full"></div>
                <span class="text-xs text-gray-600">{{ getPerformanceStatus(metric) }}</span>
              </div>
              
              <!-- Sparkline placeholder -->
              <div class="flex items-center space-x-1">
                @for (bar of getSparklineData(); track $index) {
                  <div 
                    [style.height.px]="bar"
                    class="w-1 bg-blue-300 rounded-full"
                  ></div>
                }
              </div>
            </div>
          </div>
        }
      </div>

      <!-- Summary Statistics -->
      <div class="mt-6 pt-4 border-t border-gray-100">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div class="text-lg font-semibold text-green-600">{{ getImprovingMetricsCount() }}</div>
            <div class="text-xs text-gray-600">Improving</div>
          </div>
          <div>
            <div class="text-lg font-semibold text-red-600">{{ getDecliningMetricsCount() }}</div>
            <div class="text-xs text-gray-600">Declining</div>
          </div>
          <div>
            <div class="text-lg font-semibold text-gray-600">{{ getStableMetricsCount() }}</div>
            <div class="text-xs text-gray-600">Stable</div>
          </div>
          <div>
            <div class="text-lg font-semibold text-blue-600">{{ getOnTargetMetricsCount() }}</div>
            <div class="text-xs text-gray-600">On Target</div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .performance-metrics {
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

    .metric-item {
      transition: all 0.2s ease-in-out;
    }

    .metric-item:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
  `]
})
export class PerformanceMetricsComponent {
  @Input({ required: true }) performanceData!: PerformanceMetricsWidget;

  // Expose Math for template
  Math = Math;

  getTrendIconClass(trend: string): string {
    switch (trend) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-400';
    }
  }

  getTrendTextClass(trend: string): string {
    switch (trend) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-600';
    }
  }

  calculatePercentageChange(metric: PerformanceMetric): string {
    if (metric.previous === 0) return '0%';
    const change = ((metric.current - metric.previous) / metric.previous) * 100;
    const sign = change > 0 ? '+' : '';
    return `${sign}${change.toFixed(1)}%`;
  }

  getTargetProgress(metric: PerformanceMetric): number {
    if (metric.target === undefined) return 0;
    return Math.round((metric.current / metric.target) * 100);
  }

  getProgressBarClass(metric: PerformanceMetric): string {
    const progress = this.getTargetProgress(metric);
    if (progress >= 100) return 'bg-green-500';
    if (progress >= 80) return 'bg-blue-500';
    if (progress >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  }

  getComparisonClass(current: number, comparison: number): string {
    if (current > comparison) return 'text-green-600';
    if (current < comparison) return 'text-red-600';
    return 'text-gray-600';
  }

  getStatusIndicatorClass(metric: PerformanceMetric): string {
    if (metric.target !== undefined) {
      const progress = this.getTargetProgress(metric);
      if (progress >= 95) return 'bg-green-500';
      if (progress >= 80) return 'bg-blue-500';
      if (progress >= 60) return 'bg-yellow-500';
      return 'bg-red-500';
    }
    
    // If no target, base on trend
    switch (metric.trend) {
      case 'up': return 'bg-green-500';
      case 'down': return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  }

  getPerformanceStatus(metric: PerformanceMetric): string {
    if (metric.target !== undefined) {
      const progress = this.getTargetProgress(metric);
      if (progress >= 95) return 'Excellent';
      if (progress >= 80) return 'Good';
      if (progress >= 60) return 'Fair';
      return 'Needs Attention';
    }
    
    switch (metric.trend) {
      case 'up': return 'Improving';
      case 'down': return 'Declining';
      default: return 'Stable';
    }
  }

  getComparisonLabel(comparison: string): string {
    switch (comparison) {
      case 'previous_period': return 'previous period';
      case 'target': return 'target values';
      case 'baseline': return 'baseline';
      default: return 'comparison';
    }
  }

  formatValue(value: number, showSign: boolean = false): string {
    const sign = showSign && value > 0 ? '+' : '';
    
    if (Math.abs(value) >= 1000000) {
      return sign + (value / 1000000).toFixed(1) + 'M';
    } else if (Math.abs(value) >= 1000) {
      return sign + (value / 1000).toFixed(1) + 'K';
    } else if (value % 1 === 0) {
      return sign + value.toString();
    } else {
      return sign + value.toFixed(2);
    }
  }

  getSparklineData(): number[] {
    // Generate mock sparkline data (8 bars with heights 4-16px)
    return Array.from({ length: 8 }, () => Math.floor(Math.random() * 12) + 4);
  }

  getImprovingMetricsCount(): number {
    return this.performanceData.metrics.filter(m => m.trend === 'up').length;
  }

  getDecliningMetricsCount(): number {
    return this.performanceData.metrics.filter(m => m.trend === 'down').length;
  }

  getStableMetricsCount(): number {
    return this.performanceData.metrics.filter(m => m.trend === 'stable').length;
  }

  getOnTargetMetricsCount(): number {
    return this.performanceData.metrics.filter(m => {
      if (m.target === undefined) return false;
      const progress = this.getTargetProgress(m);
      return progress >= 95 && progress <= 105; // Within 5% of target
    }).length;
  }
}