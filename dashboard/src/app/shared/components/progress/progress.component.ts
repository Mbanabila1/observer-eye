import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export type ProgressVariant = 'primary' | 'success' | 'warning' | 'error';
export type ProgressSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-progress',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-2">
      <div *ngIf="showLabel" class="flex justify-between items-center">
        <span class="text-sm font-medium text-secondary-700">{{ label }}</span>
        <span *ngIf="showValue" class="text-sm text-secondary-500">{{ value }}{{ unit }}</span>
      </div>
      
      <div [class]="containerClasses">
        <div
          [class]="barClasses"
          [style.width.%]="percentage"
          [attr.aria-valuenow]="value"
          [attr.aria-valuemin]="min"
          [attr.aria-valuemax]="max"
          role="progressbar"
        >
          <span *ngIf="showValueInBar && percentage > 20" class="text-xs font-medium text-white">
            {{ value }}{{ unit }}
          </span>
        </div>
      </div>
      
      <div *ngIf="helperText" class="text-xs text-secondary-500">
        {{ helperText }}
      </div>
    </div>
  `
})
export class ProgressComponent {
  @Input() value = 0;
  @Input() max = 100;
  @Input() min = 0;
  @Input() label = '';
  @Input() unit = '%';
  @Input() variant: ProgressVariant = 'primary';
  @Input() size: ProgressSize = 'md';
  @Input() showLabel = true;
  @Input() showValue = true;
  @Input() showValueInBar = false;
  @Input() helperText = '';
  @Input() animated = false;
  @Input() striped = false;

  get percentage(): number {
    const range = this.max - this.min;
    const adjustedValue = Math.max(this.min, Math.min(this.max, this.value));
    return ((adjustedValue - this.min) / range) * 100;
  }

  get containerClasses(): string {
    const baseClasses = [
      'w-full',
      'bg-secondary-200',
      'rounded-full',
      'overflow-hidden'
    ];

    const sizeClasses = {
      sm: ['h-2'],
      md: ['h-3'],
      lg: ['h-4']
    };

    return [...baseClasses, ...sizeClasses[this.size]].join(' ');
  }

  get barClasses(): string {
    const baseClasses = [
      'h-full',
      'flex',
      'items-center',
      'justify-center',
      'transition-all',
      'duration-300',
      'ease-in-out'
    ];

    const variantClasses = {
      primary: ['bg-primary-600'],
      success: ['bg-success-600'],
      warning: ['bg-warning-600'],
      error: ['bg-error-600']
    };

    baseClasses.push(...variantClasses[this.variant]);

    if (this.animated) {
      baseClasses.push('animate-pulse');
    }

    if (this.striped) {
      baseClasses.push('bg-gradient-to-r', 'from-transparent', 'via-white', 'via-opacity-20', 'to-transparent');
    }

    return baseClasses.join(' ');
  }
}