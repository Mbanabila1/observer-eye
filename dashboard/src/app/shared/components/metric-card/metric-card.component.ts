import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, LucideIconData } from 'lucide-angular';

export type MetricTrend = 'up' | 'down' | 'neutral';
export type MetricStatus = 'success' | 'warning' | 'error' | 'info';

@Component({
  selector: 'app-metric-card',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div [class]="cardClasses">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div *ngIf="icon" [class]="iconContainerClasses">
            <lucide-angular [img]="icon" [size]="20" [class]="iconClasses"></lucide-angular>
          </div>
          <h3 class="text-sm font-medium text-secondary-600">{{ title }}</h3>
        </div>
        
        <div *ngIf="showTrend && trendValue !== undefined" class="flex items-center space-x-1">
          <lucide-angular
            [img]="trendIcon"
            [size]="16"
            [class]="trendIconClasses"
          ></lucide-angular>
          <span [class]="trendTextClasses">{{ trendValue }}%</span>
        </div>
      </div>

      <!-- Main Value -->
      <div class="mt-3">
        <div class="flex items-baseline space-x-2">
          <p class="text-2xl font-semibold text-secondary-900">{{ value }}</p>
          <p *ngIf="unit" class="text-sm text-secondary-500">{{ unit }}</p>
        </div>
        
        <p *ngIf="subtitle" class="mt-1 text-sm text-secondary-600">{{ subtitle }}</p>
      </div>

      <!-- Footer -->
      <div *ngIf="footerText || showLastUpdated" class="mt-4 pt-3 border-t border-secondary-100">
        <p class="text-xs text-secondary-500">
          {{ footerText }}
          <span *ngIf="showLastUpdated && lastUpdated">
            Last updated: {{ lastUpdated | date:'short' }}
          </span>
        </p>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading" class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
      </div>
    </div>
  `
})
export class MetricCardComponent {
  @Input() title = '';
  @Input() value: string | number = '';
  @Input() unit = '';
  @Input() subtitle = '';
  @Input() icon?: LucideIconData;
  @Input() status: MetricStatus = 'info';
  @Input() trend: MetricTrend = 'neutral';
  @Input() trendValue?: number;
  @Input() showTrend = false;
  @Input() footerText = '';
  @Input() lastUpdated?: Date;
  @Input() showLastUpdated = false;
  @Input() loading = false;
  @Input() clickable = false;

  get cardClasses(): string {
    const baseClasses = [
      'relative',
      'bg-white',
      'rounded-lg',
      'border',
      'border-secondary-200',
      'p-6',
      'shadow-sm',
      'transition-all',
      'duration-200'
    ];

    if (this.clickable) {
      baseClasses.push('hover:shadow-md', 'cursor-pointer', 'hover:border-secondary-300');
    }

    return baseClasses.join(' ');
  }

  get iconContainerClasses(): string {
    const statusClasses = {
      success: 'bg-success-100',
      warning: 'bg-warning-100',
      error: 'bg-error-100',
      info: 'bg-primary-100'
    };

    return `p-2 rounded-lg ${statusClasses[this.status]}`;
  }

  get iconClasses(): string {
    const statusClasses = {
      success: 'text-success-600',
      warning: 'text-warning-600',
      error: 'text-error-600',
      info: 'text-primary-600'
    };

    return statusClasses[this.status];
  }

  get trendIcon(): any {
    switch (this.trend) {
      case 'up':
        return 'trending-up';
      case 'down':
        return 'trending-down';
      default:
        return 'minus';
    }
  }

  get trendIconClasses(): string {
    const trendClasses = {
      up: 'text-success-500',
      down: 'text-error-500',
      neutral: 'text-secondary-400'
    };

    return trendClasses[this.trend];
  }

  get trendTextClasses(): string {
    const trendClasses = {
      up: 'text-success-600',
      down: 'text-error-600',
      neutral: 'text-secondary-500'
    };

    return `text-sm font-medium ${trendClasses[this.trend]}`;
  }
}