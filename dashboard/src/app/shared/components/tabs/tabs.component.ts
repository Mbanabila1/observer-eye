import { Component, Input, Output, EventEmitter, ContentChildren, QueryList, AfterContentInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../utils/icons';

export interface TabItem {
  id: string;
  label: string;
  icon?: any;
  disabled?: boolean;
  badge?: string | number;
  closable?: boolean;
}

export type TabsVariant = 'default' | 'pills' | 'underline';
export type TabsSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-tab',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [hidden]="!active">
      <ng-content></ng-content>
    </div>
  `
})
export class TabComponent {
  @Input() id!: string;
  @Input() label!: string;
  @Input() icon?: any;
  @Input() disabled = false;
  @Input() badge?: string | number;
  @Input() closable = false;
  @Input() active = false;
}

@Component({
  selector: 'app-tabs',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="w-full">
      <!-- Tab Navigation -->
      <div [class]="navClasses">
        <nav class="flex space-x-1" aria-label="Tabs">
          <button
            *ngFor="let tab of tabs; trackBy: trackByTab"
            type="button"
            [disabled]="tab.disabled"
            [class]="getTabClasses(tab)"
            (click)="selectTab(tab.id)"
            [attr.aria-selected]="activeTabId === tab.id"
            role="tab"
          >
            <div class="flex items-center space-x-2">
              <lucide-angular
                *ngIf="tab.icon"
                [img]="tab.icon"
                [size]="iconSize"
                class="flex-shrink-0"
              ></lucide-angular>
              
              <span>{{ tab.label }}</span>
              
              <span
                *ngIf="tab.badge"
                [class]="badgeClasses"
              >
                {{ tab.badge }}
              </span>
              
              <button
                *ngIf="tab.closable"
                type="button"
                class="ml-2 p-0.5 rounded-full hover:bg-secondary-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
                (click)="closeTab($event, tab.id)"
                [attr.aria-label]="'Close ' + tab.label"
              >
                <lucide-angular
                  [img]="Icons.x"
                  [size]="14"
                  class="text-secondary-400 hover:text-secondary-600"
                ></lucide-angular>
              </button>
            </div>
          </button>
        </nav>
        
        <!-- Actions slot -->
        <div *ngIf="hasActions" class="ml-auto">
          <ng-content select="[slot=actions]"></ng-content>
        </div>
      </div>

      <!-- Tab Content -->
      <div [class]="contentClasses">
        <ng-content></ng-content>
        
        <!-- Empty state -->
        <div *ngIf="!tabs.length" class="text-center py-8 text-secondary-500">
          <p>No tabs available</p>
        </div>
      </div>
    </div>
  `
})
export class TabsComponent implements AfterContentInit {
  @Input() variant: TabsVariant = 'default';
  @Input() size: TabsSize = 'md';
  @Input() activeTabId?: string;
  @Input() tabs: TabItem[] = [];
  @Input() hasActions = false;

  @Output() tabChanged = new EventEmitter<string>();
  @Output() tabClosed = new EventEmitter<string>();

  @ContentChildren(TabComponent) tabComponents!: QueryList<TabComponent>;

  // Make Icons available in template
  Icons = Icons;

  ngAfterContentInit(): void {
    // Initialize tabs from content children if not provided via input
    if (!this.tabs.length && this.tabComponents) {
      this.tabs = this.tabComponents.map(tab => ({
        id: tab.id,
        label: tab.label,
        icon: tab.icon,
        disabled: tab.disabled,
        badge: tab.badge,
        closable: tab.closable
      }));
    }

    // Set initial active tab
    if (!this.activeTabId && this.tabs.length > 0) {
      const firstEnabledTab = this.tabs.find(tab => !tab.disabled);
      if (firstEnabledTab) {
        this.selectTab(firstEnabledTab.id);
      }
    }

    this.updateTabComponents();
  }

  get navClasses(): string {
    const baseClasses = ['flex', 'items-center', 'justify-between'];

    const variantClasses = {
      default: ['border-b', 'border-secondary-200'],
      pills: [],
      underline: ['border-b', 'border-secondary-200']
    };

    baseClasses.push(...variantClasses[this.variant]);

    return baseClasses.join(' ');
  }

  get contentClasses(): string {
    const baseClasses = ['mt-4'];
    return baseClasses.join(' ');
  }

  get iconSize(): number {
    const sizes = {
      sm: 14,
      md: 16,
      lg: 18
    };
    return sizes[this.size];
  }

  get badgeClasses(): string {
    return [
      'inline-flex',
      'items-center',
      'px-2',
      'py-0.5',
      'rounded-full',
      'text-xs',
      'font-medium',
      'bg-secondary-100',
      'text-secondary-800'
    ].join(' ');
  }

  getTabClasses(tab: TabItem): string {
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
      'focus:ring-primary-500'
    ];

    // Size classes
    const sizeClasses = {
      sm: ['px-3', 'py-1.5', 'text-sm'],
      md: ['px-4', 'py-2', 'text-sm'],
      lg: ['px-6', 'py-3', 'text-base']
    };

    baseClasses.push(...sizeClasses[this.size]);

    // Variant-specific classes
    const isActive = this.activeTabId === tab.id;

    if (this.variant === 'pills') {
      baseClasses.push('rounded-md');
      if (isActive) {
        baseClasses.push('bg-primary-100', 'text-primary-700');
      } else {
        baseClasses.push('text-secondary-500', 'hover:text-secondary-700', 'hover:bg-secondary-50');
      }
    } else if (this.variant === 'underline') {
      baseClasses.push('border-b-2', 'border-transparent');
      if (isActive) {
        baseClasses.push('border-primary-500', 'text-primary-600');
      } else {
        baseClasses.push('text-secondary-500', 'hover:text-secondary-700', 'hover:border-secondary-300');
      }
    } else {
      // default variant
      baseClasses.push('border-b-2', 'border-transparent', '-mb-px');
      if (isActive) {
        baseClasses.push('border-primary-500', 'text-primary-600');
      } else {
        baseClasses.push('text-secondary-500', 'hover:text-secondary-700', 'hover:border-secondary-300');
      }
    }

    // Disabled state
    if (tab.disabled) {
      baseClasses.push('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
    }

    return baseClasses.join(' ');
  }

  selectTab(tabId: string): void {
    const tab = this.tabs.find(t => t.id === tabId);
    if (!tab || tab.disabled) return;

    this.activeTabId = tabId;
    this.updateTabComponents();
    this.tabChanged.emit(tabId);
  }

  closeTab(event: Event, tabId: string): void {
    event.stopPropagation();
    
    const tabIndex = this.tabs.findIndex(t => t.id === tabId);
    if (tabIndex === -1) return;

    // Remove tab
    this.tabs.splice(tabIndex, 1);

    // If closed tab was active, select another tab
    if (this.activeTabId === tabId) {
      if (this.tabs.length > 0) {
        // Select the tab at the same index, or the last tab if index is out of bounds
        const newIndex = Math.min(tabIndex, this.tabs.length - 1);
        const newActiveTab = this.tabs[newIndex];
        if (newActiveTab && !newActiveTab.disabled) {
          this.selectTab(newActiveTab.id);
        }
      } else {
        this.activeTabId = undefined;
      }
    }

    this.tabClosed.emit(tabId);
  }

  addTab(tab: TabItem): void {
    this.tabs.push(tab);
    if (!this.activeTabId) {
      this.selectTab(tab.id);
    }
  }

  removeTab(tabId: string): void {
    this.closeTab(new Event('click'), tabId);
  }

  private updateTabComponents(): void {
    if (this.tabComponents) {
      this.tabComponents.forEach(tab => {
        tab.active = tab.id === this.activeTabId;
      });
    }
  }

  trackByTab(index: number, tab: TabItem): string {
    return tab.id;
  }
}