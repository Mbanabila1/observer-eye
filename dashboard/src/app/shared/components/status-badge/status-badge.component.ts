import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, LucideIconData } from 'lucide-angular';

export type StatusType = 'success' | 'warning' | 'error' | 'info' | 'neutral';
export type StatusSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <span [class]="badgeClasses">
      <lucide-angular
        *ngIf="icon"
        [img]="icon"
        [size]="iconSize"
        class="mr-1"
      ></lucide-angular>
      
      <div *ngIf="showDot && !icon" [class]="dotClasses"></div>
      
      <span>{{ label }}</span>
    </span>
  `
})
export class StatusBadgeComponent {
  @Input() label = '';
  @Input() status: StatusType = 'neutral';
  @Input() size: StatusSize = 'md';
  @Input() icon?: LucideIconData;
  @Input() showDot = true;
  @Input() outlined = false;

  get badgeClasses(): string {
    const baseClasses = [
      'inline-flex',
      'items-center',
      'font-medium',
      'rounded-full'
    ];

    // Size classes
    const sizeClasses = {
      sm: ['px-2', 'py-0.5', 'text-xs'],
      md: ['px-2.5', 'py-1', 'text-sm'],
      lg: ['px-3', 'py-1.5', 'text-base']
    };

    baseClasses.push(...sizeClasses[this.size]);

    // Status classes
    if (this.outlined) {
      const outlinedClasses = {
        success: ['text-success-700', 'bg-success-50', 'border', 'border-success-200'],
        warning: ['text-warning-700', 'bg-warning-50', 'border', 'border-warning-200'],
        error: ['text-error-700', 'bg-error-50', 'border', 'border-error-200'],
        info: ['text-primary-700', 'bg-primary-50', 'border', 'border-primary-200'],
        neutral: ['text-secondary-700', 'bg-secondary-50', 'border', 'border-secondary-200']
      };
      baseClasses.push(...outlinedClasses[this.status]);
    } else {
      const solidClasses = {
        success: ['text-success-800', 'bg-success-100'],
        warning: ['text-warning-800', 'bg-warning-100'],
        error: ['text-error-800', 'bg-error-100'],
        info: ['text-primary-800', 'bg-primary-100'],
        neutral: ['text-secondary-800', 'bg-secondary-100']
      };
      baseClasses.push(...solidClasses[this.status]);
    }

    return baseClasses.join(' ');
  }

  get dotClasses(): string {
    const baseClasses = ['w-2', 'h-2', 'rounded-full', 'mr-2'];

    const dotColors = {
      success: ['bg-success-500'],
      warning: ['bg-warning-500'],
      error: ['bg-error-500'],
      info: ['bg-primary-500'],
      neutral: ['bg-secondary-500']
    };

    baseClasses.push(...dotColors[this.status]);

    return baseClasses.join(' ');
  }

  get iconSize(): number {
    const sizes = {
      sm: 12,
      md: 14,
      lg: 16
    };
    return sizes[this.size];
  }
}