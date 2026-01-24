import { Component, Input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { KPIWidget } from '../../models/bi-models';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="kpi-card bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-medium text-gray-600 truncate">{{ kpi.title }}</h3>
        <div class="flex items-center space-x-1">
          <!-- Status indicator -->
          <div 
            [class]="statusIndicatorClass()"
            class="w-2 h-2 rounded-full"
          ></div>
          <!-- Trend icon -->
          <svg 
            [class]="trendIconClass()"
            class="w-4 h-4"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            @switch (kpi.trend) {
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
        </div>
      </div>

      <!-- Main Value -->
      <div class="mb-3">
        <div class="flex items-baseline space-x-2">
          <span class="text-3xl font-bold text-gray-900">
            {{ formatValue(kpi.value) }}
          </span>
          <span class="text-lg text-gray-500">{{ kpi.unit }}</span>
        </div>
      </div>

      <!-- Trend Information -->
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center space-x-1">
          <span 
            [class]="trendTextClass()"
            class="text-sm font-medium"
          >
            {{ formatTrendPercentage(kpi.trendPercentage) }}
          </span>
          <span class="text-sm text-gray-500">vs previous period</span>
        </div>
      </div>

      <!-- Target Progress (if target is set) -->
      @if (kpi.targetValue !== undefined) {
        <div class="mb-3">
          <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>Target: {{ formatValue(kpi.targetValue) }}{{ kpi.unit }}</span>
            <span>{{ targetAchievementPercentage() }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div 
              [style.width.%]="Math.min(targetAchievementPercentage(), 100)"
              [class]="progressBarClass()"
              class="h-2 rounded-full transition-all duration-300"
            ></div>
          </div>
        </div>
      }

      <!-- Thresholds (if set) -->
      @if (kpi.thresholdWarning !== undefined || kpi.thresholdCritical !== undefined) {
        <div class="text-xs text-gray-500">
          @if (kpi.thresholdCritical !== undefined) {
            <div class="flex items-center space-x-1">
              <div class="w-2 h-2 bg-red-500 rounded-full"></div>
              <span>Critical: {{ formatValue(kpi.thresholdCritical) }}{{ kpi.unit }}</span>
            </div>
          }
          @if (kpi.thresholdWarning !== undefined) {
            <div class="flex items-center space-x-1 mt-1">
              <div class="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <span>Warning: {{ formatValue(kpi.thresholdWarning) }}{{ kpi.unit }}</span>
            </div>
          }
        </div>
      }

      <!-- Description tooltip -->
      @if (kpi.description) {
        <div class="mt-3 pt-3 border-t border-gray-100">
          <p class="text-xs text-gray-500">{{ kpi.description }}</p>
        </div>
      }
    </div>
  `,
  styles: [`
    .kpi-card {
      animation: slideInUp 0.3s ease-out;
    }

    @keyframes slideInUp {
      from {
        opacity: 0;
        transform: translateY(10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .kpi-card:hover {
      transform: translateY(-1px);
    }
  `]
})
export class KpiCardComponent {
  @Input({ required: true }) kpi!: KPIWidget;

  // Expose Math for template
  Math = Math;

  // Computed values
  targetAchievementPercentage = computed(() => {
    if (this.kpi.targetValue === undefined) return 0;
    return Math.round((this.kpi.value / this.kpi.targetValue) * 100);
  });

  statusIndicatorClass = computed(() => {
    const status = this.getKPIStatus();
    switch (status) {
      case 'critical': return 'bg-red-500';
      case 'warning': return 'bg-yellow-500';
      case 'good': return 'bg-green-500';
      default: return 'bg-gray-400';
    }
  });

  trendIconClass = computed(() => {
    switch (this.kpi.trend) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-400';
    }
  });

  trendTextClass = computed(() => {
    switch (this.kpi.trend) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-600';
    }
  });

  progressBarClass = computed(() => {
    const achievement = this.targetAchievementPercentage();
    if (achievement >= 100) return 'bg-green-500';
    if (achievement >= 80) return 'bg-blue-500';
    if (achievement >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  });

  formatValue(value: number): string {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
      return (value / 1000).toFixed(1) + 'K';
    } else if (value % 1 === 0) {
      return value.toString();
    } else {
      return value.toFixed(2);
    }
  }

  formatTrendPercentage(percentage: number): string {
    const sign = percentage > 0 ? '+' : '';
    return `${sign}${percentage.toFixed(1)}%`;
  }

  private getKPIStatus(): 'critical' | 'warning' | 'good' | 'unknown' {
    const { value, thresholdCritical, thresholdWarning } = this.kpi;

    // For metrics where lower is better (like error rate, response time)
    const isLowerBetter = this.kpi.category === 'quality' || 
                         this.kpi.title.toLowerCase().includes('error') ||
                         this.kpi.title.toLowerCase().includes('response time');

    if (thresholdCritical !== undefined) {
      if (isLowerBetter) {
        if (value >= thresholdCritical) return 'critical';
      } else {
        if (value <= thresholdCritical) return 'critical';
      }
    }

    if (thresholdWarning !== undefined) {
      if (isLowerBetter) {
        if (value >= thresholdWarning) return 'warning';
      } else {
        if (value <= thresholdWarning) return 'warning';
      }
    }

    // If we have thresholds and we're not in warning/critical, we're good
    if (thresholdCritical !== undefined || thresholdWarning !== undefined) {
      return 'good';
    }

    return 'unknown';
  }
}