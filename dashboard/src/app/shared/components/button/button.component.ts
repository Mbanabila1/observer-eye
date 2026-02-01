import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons, IconName } from '../../utils/icons';

export type ButtonVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost' | 'outline';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <button
      [type]="type"
      [disabled]="disabled || loading"
      [class]="buttonClasses"
      (click)="handleClick($event)"
    >
      <lucide-angular
        *ngIf="loading"
        [img]="Icons.loader2"
        class="animate-spin"
        [size]="iconSize"
      ></lucide-angular>
      
      <lucide-angular
        *ngIf="!loading && leftIcon"
        [img]="getLeftIcon()"
        [size]="iconSize"
      ></lucide-angular>
      
      <span *ngIf="!iconOnly" [class.sr-only]="loading">
        <ng-content></ng-content>
      </span>
      
      <lucide-angular
        *ngIf="!loading && rightIcon"
        [img]="getRightIcon()"
        [size]="iconSize"
      ></lucide-angular>
    </button>
  `,
  styles: [`
    :host {
      display: inline-block;
    }
  `]
})
export class ButtonComponent {
  @Input() variant: ButtonVariant = 'primary';
  @Input() size: ButtonSize = 'md';
  @Input() type: 'button' | 'submit' | 'reset' = 'button';
  @Input() disabled = false;
  @Input() loading = false;
  @Input() iconOnly = false;
  @Input() leftIcon?: IconName;
  @Input() rightIcon?: IconName;
  @Input() loadingIcon: IconName = 'loader2';
  @Input() fullWidth = false;

  @Output() clicked = new EventEmitter<Event>();

  Icons = Icons;

  getLeftIcon() {
    return this.leftIcon ? Icons[this.leftIcon] : undefined;
  }

  getRightIcon() {
    return this.rightIcon ? Icons[this.rightIcon] : undefined;
  }

  get buttonClasses(): string {
    const baseClasses = [
      'inline-flex',
      'items-center',
      'justify-center',
      'font-medium',
      'transition-all',
      'duration-200',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-offset-2',
      'disabled:opacity-50',
      'disabled:cursor-not-allowed',
      'disabled:pointer-events-none'
    ];

    // Size classes
    const sizeClasses = {
      xs: ['px-2', 'py-1', 'text-xs', 'rounded'],
      sm: ['px-3', 'py-1.5', 'text-sm', 'rounded'],
      md: ['px-4', 'py-2', 'text-sm', 'rounded-md'],
      lg: ['px-6', 'py-3', 'text-base', 'rounded-md'],
      xl: ['px-8', 'py-4', 'text-lg', 'rounded-lg']
    };

    // Variant classes
    const variantClasses = {
      primary: [
        'bg-primary-600',
        'text-white',
        'hover:bg-primary-700',
        'focus:ring-primary-500',
        'shadow-sm'
      ],
      secondary: [
        'bg-secondary-100',
        'text-secondary-900',
        'hover:bg-secondary-200',
        'focus:ring-secondary-500',
        'border',
        'border-secondary-300'
      ],
      success: [
        'bg-success-600',
        'text-white',
        'hover:bg-success-700',
        'focus:ring-success-500',
        'shadow-sm'
      ],
      warning: [
        'bg-warning-600',
        'text-white',
        'hover:bg-warning-700',
        'focus:ring-warning-500',
        'shadow-sm'
      ],
      error: [
        'bg-error-600',
        'text-white',
        'hover:bg-error-700',
        'focus:ring-error-500',
        'shadow-sm'
      ],
      ghost: [
        'text-secondary-700',
        'hover:bg-secondary-100',
        'focus:ring-secondary-500'
      ],
      outline: [
        'border',
        'border-secondary-300',
        'text-secondary-700',
        'bg-white',
        'hover:bg-secondary-50',
        'focus:ring-secondary-500'
      ]
    };

    const classes = [
      ...baseClasses,
      ...sizeClasses[this.size],
      ...variantClasses[this.variant]
    ];

    if (this.fullWidth) {
      classes.push('w-full');
    }

    if (this.iconOnly) {
      // Remove padding for icon-only buttons and make them square
      const iconOnlySizes = {
        xs: ['w-6', 'h-6', 'p-1'],
        sm: ['w-8', 'h-8', 'p-1.5'],
        md: ['w-10', 'h-10', 'p-2'],
        lg: ['w-12', 'h-12', 'p-3'],
        xl: ['w-16', 'h-16', 'p-4']
      };
      
      // Remove padding classes and add icon-only classes
      const filteredClasses = classes.filter(cls => !cls.startsWith('px-') && !cls.startsWith('py-'));
      return [...filteredClasses, ...iconOnlySizes[this.size]].join(' ');
    }

    return classes.join(' ');
  }

  get iconSize(): number {
    const sizes = {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 20
    };
    return sizes[this.size];
  }

  handleClick(event: Event): void {
    if (!this.disabled && !this.loading) {
      this.clicked.emit(event);
    }
  }
}