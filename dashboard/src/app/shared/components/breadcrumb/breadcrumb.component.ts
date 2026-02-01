import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { LucideAngularModule, LucideIconData } from 'lucide-angular';
import { Icons, IconName } from '../../utils/icons';

export interface BreadcrumbItem {
  label: string;
  url?: string;
  icon?: LucideIconData;
  disabled?: boolean;
  active?: boolean;
}

@Component({
  selector: 'app-breadcrumb',
  standalone: true,
  imports: [CommonModule, RouterModule, LucideAngularModule],
  template: `
    <nav class="flex" aria-label="Breadcrumb">
      <ol [class]="containerClasses">
        <li *ngFor="let item of items; let i = index; trackBy: trackByItem" class="flex items-center">
          <!-- Separator -->
          <lucide-angular
            *ngIf="i > 0"
            [img]="separatorIcon"
            [size]="16"
            class="flex-shrink-0 mx-2 text-secondary-400"
          ></lucide-angular>
          
          <!-- Breadcrumb Item -->
          <div class="flex items-center">
            <!-- Home icon for first item if showHome is true -->
            <div
              *ngIf="i === 0 && showHome && !item.icon"
              class="w-4 h-4 bg-secondary-400 rounded flex-shrink-0 mr-2"
            ></div>
            
            <!-- Custom icon -->
            <div
              *ngIf="item.icon"
              class="w-4 h-4 bg-secondary-400 rounded flex-shrink-0 mr-2"
            ></div>
            
            <!-- Link -->
            <a
              *ngIf="item.url && !item.disabled && !item.active"
              [routerLink]="item.url"
              [class]="linkClasses"
              (click)="onItemClick(item, i)"
            >
              {{ item.label }}
            </a>
            
            <!-- Button (for items without URL) -->
            <button
              *ngIf="!item.url && !item.disabled && !item.active"
              type="button"
              [class]="buttonClasses"
              (click)="onItemClick(item, i)"
            >
              {{ item.label }}
            </button>
            
            <!-- Active/Disabled item -->
            <span
              *ngIf="item.disabled || item.active"
              [class]="item.active ? activeClasses : disabledClasses"
              [attr.aria-current]="item.active ? 'page' : null"
            >
              {{ item.label }}
            </span>
          </div>
        </li>
      </ol>
    </nav>
  `
})
export class BreadcrumbComponent {
  @Input() items: BreadcrumbItem[] = [];
  @Input() separatorIcon: LucideIconData = Icons.chevronRight;
  @Input() showHome = true;
  @Input() maxItems?: number;
  @Input() size: 'sm' | 'md' | 'lg' = 'md';

  @Output() itemClicked = new EventEmitter<{ item: BreadcrumbItem; index: number }>();

  get containerClasses(): string {
    const baseClasses = ['flex', 'flex-wrap', 'items-center'];

    const sizeClasses = {
      sm: ['text-sm'],
      md: ['text-sm'],
      lg: ['text-base']
    };

    baseClasses.push(...sizeClasses[this.size]);

    return baseClasses.join(' ');
  }

  get linkClasses(): string {
    const baseClasses = [
      'text-secondary-600',
      'hover:text-secondary-900',
      'transition-colors',
      'duration-200',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-primary-500',
      'focus:ring-offset-2',
      'rounded'
    ];

    return baseClasses.join(' ');
  }

  get buttonClasses(): string {
    const baseClasses = [
      'text-secondary-600',
      'hover:text-secondary-900',
      'transition-colors',
      'duration-200',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-primary-500',
      'focus:ring-offset-2',
      'rounded',
      'bg-transparent',
      'border-none',
      'p-0',
      'cursor-pointer'
    ];

    return baseClasses.join(' ');
  }

  get activeClasses(): string {
    return 'text-secondary-900 font-medium';
  }

  get disabledClasses(): string {
    return 'text-secondary-400 cursor-not-allowed';
  }

  get visibleItems(): BreadcrumbItem[] {
    if (!this.maxItems || this.items.length <= this.maxItems) {
      return this.items;
    }

    // Show first item, ellipsis, and last few items
    const firstItem = this.items[0];
    const lastItems = this.items.slice(-(this.maxItems - 2));
    
    return [
      firstItem,
      { label: '...', disabled: true },
      ...lastItems
    ];
  }

  onItemClick(item: BreadcrumbItem, index: number): void {
    if (!item.disabled) {
      this.itemClicked.emit({ item, index });
    }
  }

  trackByItem(index: number, item: BreadcrumbItem): string {
    return `${index}-${item.label}`;
  }
}