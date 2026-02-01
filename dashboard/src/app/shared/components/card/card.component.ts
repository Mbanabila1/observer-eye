import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, LucideIconData } from 'lucide-angular';

@Component({
  selector: 'app-card',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div [class]="cardClasses">
      <!-- Header -->
      <div *ngIf="showHeader" [class]="headerClasses">
        <div class="flex items-center space-x-3">
          <div *ngIf="icon" class="flex-shrink-0">
            <lucide-angular [img]="icon" [size]="20" class="text-secondary-600"></lucide-angular>
          </div>
          
          <div class="flex-1 min-w-0">
            <h3 *ngIf="title" class="text-lg font-medium text-secondary-900 truncate">
              {{ title }}
            </h3>
            <p *ngIf="subtitle" class="text-sm text-secondary-500 truncate">
              {{ subtitle }}
            </p>
          </div>
        </div>
        
        <div *ngIf="hasHeaderActions" class="flex-shrink-0">
          <ng-content select="[slot=header-actions]"></ng-content>
        </div>
      </div>

      <!-- Body -->
      <div [class]="bodyClasses">
        <ng-content></ng-content>
      </div>

      <!-- Footer -->
      <div *ngIf="hasFooter" [class]="footerClasses">
        <ng-content select="[slot=footer]"></ng-content>
      </div>

      <!-- Loading Overlay -->
      <div *ngIf="loading" class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
        <div class="flex flex-col items-center space-y-2">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p *ngIf="loadingText" class="text-sm text-secondary-600">{{ loadingText }}</p>
        </div>
      </div>
    </div>
  `
})
export class CardComponent {
  @Input() title = '';
  @Input() subtitle = '';
  @Input() icon?: LucideIconData;
  @Input() showHeader = true;
  @Input() showBorder = true;
  @Input() showShadow = true;
  @Input() padding = 'normal'; // 'none' | 'sm' | 'normal' | 'lg'
  @Input() loading = false;
  @Input() loadingText = '';
  @Input() clickable = false;
  @Input() hoverable = false;

  // Content projection flags
  hasHeaderActions = false;
  hasFooter = false;

  ngAfterContentInit(): void {
    // In a real implementation, you would use ContentChildren to detect projected content
    // For now, we'll assume these are set externally or detected through other means
  }

  get cardClasses(): string {
    const baseClasses = [
      'relative',
      'bg-white',
      'rounded-lg',
      'transition-all',
      'duration-200'
    ];

    if (this.showBorder) {
      baseClasses.push('border', 'border-secondary-200');
    }

    if (this.showShadow) {
      baseClasses.push('shadow-sm');
    }

    if (this.clickable) {
      baseClasses.push('cursor-pointer');
    }

    if (this.hoverable || this.clickable) {
      baseClasses.push('hover:shadow-md');
      if (this.showBorder) {
        baseClasses.push('hover:border-secondary-300');
      }
    }

    return baseClasses.join(' ');
  }

  get headerClasses(): string {
    const baseClasses = ['flex', 'items-center', 'justify-between'];
    
    const paddingClasses = {
      none: [],
      sm: ['px-4', 'py-3'],
      normal: ['px-6', 'py-4'],
      lg: ['px-8', 'py-6']
    };

    baseClasses.push(...paddingClasses[this.padding as keyof typeof paddingClasses]);

    if (this.hasFooter || this.bodyHasContent()) {
      baseClasses.push('border-b', 'border-secondary-200');
    }

    return baseClasses.join(' ');
  }

  get bodyClasses(): string {
    const paddingClasses = {
      none: [],
      sm: ['p-4'],
      normal: ['p-6'],
      lg: ['p-8']
    };

    const classes = [...paddingClasses[this.padding as keyof typeof paddingClasses]];

    if (!this.showHeader) {
      const topPaddingClasses = {
        none: [],
        sm: ['pt-4'],
        normal: ['pt-6'],
        lg: ['pt-8']
      };
      classes.push(...topPaddingClasses[this.padding as keyof typeof topPaddingClasses]);
    }

    if (!this.hasFooter) {
      const bottomPaddingClasses = {
        none: [],
        sm: ['pb-4'],
        normal: ['pb-6'],
        lg: ['pb-8']
      };
      classes.push(...bottomPaddingClasses[this.padding as keyof typeof bottomPaddingClasses]);
    }

    return classes.join(' ');
  }

  get footerClasses(): string {
    const baseClasses = ['border-t', 'border-secondary-200', 'bg-secondary-50'];
    
    const paddingClasses = {
      none: [],
      sm: ['px-4', 'py-3'],
      normal: ['px-6', 'py-4'],
      lg: ['px-8', 'py-6']
    };

    baseClasses.push(...paddingClasses[this.padding as keyof typeof paddingClasses]);

    return baseClasses.join(' ');
  }

  private bodyHasContent(): boolean {
    // Simplified check - in a real implementation, you'd check for projected content
    return true;
  }
}