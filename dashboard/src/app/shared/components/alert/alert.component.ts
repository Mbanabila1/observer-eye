import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, LucideIconData } from 'lucide-angular';
import { ButtonComponent } from '../button/button.component';

export type AlertType = 'success' | 'warning' | 'error' | 'info';

@Component({
  selector: 'app-alert',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, ButtonComponent],
  template: `
    <div *ngIf="visible" [class]="alertClasses" role="alert">
      <div class="flex">
        <div class="flex-shrink-0">
          <lucide-angular
            [img]="alertIcon"
            [size]="20"
            [class]="iconClasses"
          ></lucide-angular>
        </div>
        
        <div class="ml-3 flex-1">
          <h3 *ngIf="title" [class]="titleClasses">
            {{ title }}
          </h3>
          
          <div [class]="contentClasses">
            <p *ngIf="message">{{ message }}</p>
            <ng-content></ng-content>
          </div>
          
          <div *ngIf="hasActions" class="mt-4">
            <div class="flex space-x-3">
              <ng-content select="[slot=actions]"></ng-content>
            </div>
          </div>
        </div>
        
        <div *ngIf="dismissible" class="ml-auto pl-3">
          <div class="-mx-1.5 -my-1.5">
            <app-button
              variant="ghost"
              size="sm"
              [iconOnly]="true"
              leftIcon="x"
              (clicked)="dismiss()"
              [class]="dismissButtonClasses"
            ></app-button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class AlertComponent {
  @Input() type: AlertType = 'info';
  @Input() title = '';
  @Input() message = '';
  @Input() dismissible = false;
  @Input() visible = true;
  @Input() hasActions = false;

  @Output() dismissed = new EventEmitter<void>();

  get alertClasses(): string {
    const baseClasses = [
      'rounded-md',
      'p-4',
      'border',
      'transition-all',
      'duration-200'
    ];

    const typeClasses = {
      success: ['bg-success-50', 'border-success-200'],
      warning: ['bg-warning-50', 'border-warning-200'],
      error: ['bg-error-50', 'border-error-200'],
      info: ['bg-primary-50', 'border-primary-200']
    };

    baseClasses.push(...typeClasses[this.type]);

    return baseClasses.join(' ');
  }

  get iconClasses(): string {
    const typeClasses = {
      success: ['text-success-400'],
      warning: ['text-warning-400'],
      error: ['text-error-400'],
      info: ['text-primary-400']
    };

    return typeClasses[this.type].join(' ');
  }

  get titleClasses(): string {
    const baseClasses = ['text-sm', 'font-medium'];

    const typeClasses = {
      success: ['text-success-800'],
      warning: ['text-warning-800'],
      error: ['text-error-800'],
      info: ['text-primary-800']
    };

    baseClasses.push(...typeClasses[this.type]);

    return baseClasses.join(' ');
  }

  get contentClasses(): string {
    const baseClasses = ['text-sm'];

    if (this.title) {
      baseClasses.push('mt-2');
    }

    const typeClasses = {
      success: ['text-success-700'],
      warning: ['text-warning-700'],
      error: ['text-error-700'],
      info: ['text-primary-700']
    };

    baseClasses.push(...typeClasses[this.type]);

    return baseClasses.join(' ');
  }

  get dismissButtonClasses(): string {
    const typeClasses = {
      success: ['text-success-500', 'hover:bg-success-100', 'focus:ring-success-600'],
      warning: ['text-warning-500', 'hover:bg-warning-100', 'focus:ring-warning-600'],
      error: ['text-error-500', 'hover:bg-error-100', 'focus:ring-error-600'],
      info: ['text-primary-500', 'hover:bg-primary-100', 'focus:ring-primary-600']
    };

    return typeClasses[this.type].join(' ');
  }

  get alertIcon(): any {
    const icons = {
      success: 'check-circle',
      warning: 'alert-triangle',
      error: 'x-circle',
      info: 'info'
    };

    return icons[this.type];
  }

  dismiss(): void {
    this.visible = false;
    this.dismissed.emit();
  }
}