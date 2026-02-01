import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../utils/icons';

export type FormGroupLayout = 'vertical' | 'horizontal';
export type FormGroupSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-form-group',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div [class]="containerClasses">
      <div *ngIf="label || description" [class]="labelContainerClasses">
        <label *ngIf="label" [for]="fieldId" [class]="labelClasses">
          <div class="flex items-center space-x-2">
            <lucide-angular
              *ngIf="icon"
              [img]="icon"
              [size]="16"
              class="text-secondary-500"
            ></lucide-angular>
            <span>{{ label }}</span>
            <span *ngIf="required" class="text-error-500">*</span>
          </div>
        </label>
        
        <p *ngIf="description" [class]="descriptionClasses">
          {{ description }}
        </p>
      </div>
      
      <div [class]="fieldContainerClasses">
        <ng-content></ng-content>
        
        <div *ngIf="helperText || errorMessage" class="mt-2">
          <p *ngIf="errorMessage" class="text-sm text-error-600 flex items-center space-x-1">
            <lucide-angular
              [img]="Icons.alertCircle"
              [size]="16"
              class="flex-shrink-0"
            ></lucide-angular>
            <span>{{ errorMessage }}</span>
          </p>
          
          <p *ngIf="!errorMessage && helperText" class="text-sm text-secondary-500">
            {{ helperText }}
          </p>
        </div>
      </div>
    </div>
  `
})
export class FormGroupComponent {
  @Input() label = '';
  @Input() description = '';
  @Input() helperText = '';
  @Input() errorMessage = '';
  @Input() required = false;
  @Input() layout: FormGroupLayout = 'vertical';
  @Input() size: FormGroupSize = 'md';
  @Input() icon?: any;
  @Input() fieldId?: string;

  // Make Icons available in template
  Icons = Icons;

  get containerClasses(): string {
    const baseClasses = [];

    const sizeClasses = {
      sm: ['space-y-3'],
      md: ['space-y-4'],
      lg: ['space-y-5']
    };

    if (this.layout === 'horizontal') {
      baseClasses.push('grid', 'grid-cols-3', 'gap-4', 'items-start');
    } else {
      baseClasses.push(...sizeClasses[this.size]);
    }

    return baseClasses.join(' ');
  }

  get labelContainerClasses(): string {
    if (this.layout === 'horizontal') {
      return 'col-span-1';
    }
    return '';
  }

  get fieldContainerClasses(): string {
    if (this.layout === 'horizontal') {
      return 'col-span-2';
    }
    return '';
  }

  get labelClasses(): string {
    const baseClasses = ['block', 'font-medium', 'text-secondary-900'];

    const sizeClasses = {
      sm: ['text-sm'],
      md: ['text-sm'],
      lg: ['text-base']
    };

    baseClasses.push(...sizeClasses[this.size]);

    return baseClasses.join(' ');
  }

  get descriptionClasses(): string {
    const baseClasses = ['text-secondary-600', 'mt-1'];

    const sizeClasses = {
      sm: ['text-xs'],
      md: ['text-sm'],
      lg: ['text-sm']
    };

    baseClasses.push(...sizeClasses[this.size]);

    return baseClasses.join(' ');
  }
}

@Component({
  selector: 'app-form-section',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div [class]="sectionClasses">
      <div *ngIf="title || description" [class]="headerClasses">
        <div class="flex items-center space-x-3">
          <lucide-angular
            *ngIf="icon"
            [img]="icon"
            [size]="20"
            class="text-secondary-600"
          ></lucide-angular>
          
          <div>
            <h3 *ngIf="title" [class]="titleClasses">{{ title }}</h3>
            <p *ngIf="description" [class]="descriptionClasses">{{ description }}</p>
          </div>
        </div>
      </div>
      
      <div [class]="contentClasses">
        <ng-content></ng-content>
      </div>
    </div>
  `
})
export class FormSectionComponent {
  @Input() title = '';
  @Input() description = '';
  @Input() icon?: any;
  @Input() bordered = true;
  @Input() collapsible = false;
  @Input() collapsed = false;

  get sectionClasses(): string {
    const baseClasses = ['space-y-6'];

    if (this.bordered) {
      baseClasses.push('border', 'border-secondary-200', 'rounded-lg', 'p-6');
    }

    return baseClasses.join(' ');
  }

  get headerClasses(): string {
    const baseClasses = [];

    if (this.contentClasses) {
      baseClasses.push('pb-6', 'border-b', 'border-secondary-200');
    }

    return baseClasses.join(' ');
  }

  get titleClasses(): string {
    return 'text-lg font-medium text-secondary-900';
  }

  get descriptionClasses(): string {
    return 'mt-1 text-sm text-secondary-600';
  }

  get contentClasses(): string {
    const baseClasses = ['space-y-6'];

    if (this.collapsed) {
      baseClasses.push('hidden');
    }

    return baseClasses.join(' ');
  }
}

@Component({
  selector: 'app-form-actions',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [class]="containerClasses">
      <ng-content></ng-content>
    </div>
  `
})
export class FormActionsComponent {
  @Input() alignment: 'left' | 'center' | 'right' | 'between' = 'right';
  @Input() sticky = false;
  @Input() bordered = true;

  get containerClasses(): string {
    const baseClasses = ['flex', 'items-center', 'space-x-3'];

    const alignmentClasses = {
      left: ['justify-start'],
      center: ['justify-center'],
      right: ['justify-end'],
      between: ['justify-between']
    };

    baseClasses.push(...alignmentClasses[this.alignment]);

    if (this.sticky) {
      baseClasses.push('sticky', 'bottom-0', 'bg-white', 'py-4', 'z-10');
    }

    if (this.bordered) {
      baseClasses.push('pt-6', 'border-t', 'border-secondary-200');
    }

    return baseClasses.join(' ');
  }
}