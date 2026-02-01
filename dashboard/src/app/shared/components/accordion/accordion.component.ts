import { Component, Input, Output, EventEmitter, ContentChildren, QueryList, AfterContentInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, LucideIconData } from 'lucide-angular';

export interface AccordionItem {
  id: string;
  title: string;
  icon?: LucideIconData;
  disabled?: boolean;
  expanded?: boolean;
}

@Component({
  selector: 'app-accordion-item',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div [class]="itemClasses">
      <!-- Header -->
      <button
        type="button"
        [disabled]="disabled"
        [class]="headerClasses"
        (click)="toggle()"
        [attr.aria-expanded]="expanded"
        [attr.aria-controls]="contentId"
      >
        <div class="flex items-center space-x-3">
          <lucide-angular
            *ngIf="icon"
            [img]="icon"
            [size]="20"
            class="text-secondary-500"
          ></lucide-angular>
          
          <span class="text-left font-medium">{{ title }}</span>
        </div>
        
        <div class="w-5 h-5 bg-secondary-400 rounded transform transition-transform" [class.rotate-180]="expanded"></div>
      </button>

      <!-- Content -->
      <div
        [id]="contentId"
        [class]="contentWrapperClasses"
        [attr.aria-hidden]="!expanded"
      >
        <div [class]="contentClasses">
          <ng-content></ng-content>
        </div>
      </div>
    </div>
  `
})
export class AccordionItemComponent {
  @Input() id!: string;
  @Input() title!: string;
  @Input() icon?: LucideIconData;
  @Input() disabled = false;
  @Input() expanded = false;

  @Output() expandedChange = new EventEmitter<boolean>();
  @Output() toggled = new EventEmitter<{ id: string; expanded: boolean }>();

  get contentId(): string {
    return `accordion-content-${this.id}`;
  }

  get itemClasses(): string {
    return 'border-b border-secondary-200 last:border-b-0';
  }

  get headerClasses(): string {
    const baseClasses = [
      'flex',
      'items-center',
      'justify-between',
      'w-full',
      'px-6',
      'py-4',
      'text-left',
      'transition-colors',
      'duration-200',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-inset',
      'focus:ring-primary-500'
    ];

    if (this.disabled) {
      baseClasses.push('opacity-50', 'cursor-not-allowed');
    } else {
      baseClasses.push('hover:bg-secondary-50', 'text-secondary-900');
    }

    return baseClasses.join(' ');
  }

  get contentWrapperClasses(): string {
    const baseClasses = [
      'overflow-hidden',
      'transition-all',
      'duration-300',
      'ease-in-out'
    ];

    if (this.expanded) {
      baseClasses.push('max-h-screen', 'opacity-100');
    } else {
      baseClasses.push('max-h-0', 'opacity-0');
    }

    return baseClasses.join(' ');
  }

  get contentClasses(): string {
    return 'px-6 pb-4 text-secondary-700';
  }

  get chevronClasses(): string {
    const baseClasses = [
      'text-secondary-400',
      'transition-transform',
      'duration-200'
    ];

    if (this.expanded) {
      baseClasses.push('transform', 'rotate-180');
    }

    return baseClasses.join(' ');
  }

  toggle(): void {
    if (this.disabled) return;
    
    this.expanded = !this.expanded;
    this.expandedChange.emit(this.expanded);
    this.toggled.emit({ id: this.id, expanded: this.expanded });
  }
}

@Component({
  selector: 'app-accordion',
  standalone: true,
  imports: [CommonModule, AccordionItemComponent],
  template: `
    <div [class]="accordionClasses">
      <ng-content></ng-content>
      
      <!-- Programmatic items -->
      <app-accordion-item
        *ngFor="let item of items; trackBy: trackByItem"
        [id]="item.id"
        [title]="item.title"
        [icon]="item.icon"
        [disabled]="item.disabled || false"
        [expanded]="item.expanded || false"
        (toggled)="onItemToggled($event)"
      >
        <ng-container [ngSwitch]="item.id">
          <ng-content [select]="'[slot=content-' + item.id + ']'"></ng-content>
        </ng-container>
      </app-accordion-item>
    </div>
  `
})
export class AccordionComponent implements AfterContentInit {
  @Input() items: AccordionItem[] = [];
  @Input() allowMultiple = false;
  @Input() bordered = true;
  @Input() rounded = true;

  @Output() itemToggled = new EventEmitter<{ id: string; expanded: boolean }>();

  @ContentChildren(AccordionItemComponent) accordionItems!: QueryList<AccordionItemComponent>;

  ngAfterContentInit(): void {
    // Subscribe to item toggles from content children
    if (this.accordionItems) {
      this.accordionItems.forEach(item => {
        item.toggled.subscribe(event => this.onItemToggled(event));
      });
    }
  }

  get accordionClasses(): string {
    const baseClasses = ['divide-y', 'divide-secondary-200'];

    if (this.bordered) {
      baseClasses.push('border', 'border-secondary-200');
    }

    if (this.rounded) {
      baseClasses.push('rounded-lg', 'overflow-hidden');
    }

    return baseClasses.join(' ');
  }

  onItemToggled(event: { id: string; expanded: boolean }): void {
    // If allowMultiple is false, close other items
    if (!this.allowMultiple && event.expanded) {
      // Close programmatic items
      this.items.forEach(item => {
        if (item.id !== event.id) {
          item.expanded = false;
        }
      });

      // Close content children items
      if (this.accordionItems) {
        this.accordionItems.forEach(item => {
          if (item.id !== event.id && item.expanded) {
            item.expanded = false;
            item.expandedChange.emit(false);
          }
        });
      }
    }

    this.itemToggled.emit(event);
  }

  expandItem(itemId: string): void {
    // Expand programmatic item
    const item = this.items.find(i => i.id === itemId);
    if (item && !item.disabled) {
      item.expanded = true;
      this.onItemToggled({ id: itemId, expanded: true });
    }

    // Expand content child item
    if (this.accordionItems) {
      const childItem = this.accordionItems.find(i => i.id === itemId);
      if (childItem && !childItem.disabled) {
        childItem.expanded = true;
        childItem.expandedChange.emit(true);
        this.onItemToggled({ id: itemId, expanded: true });
      }
    }
  }

  collapseItem(itemId: string): void {
    // Collapse programmatic item
    const item = this.items.find(i => i.id === itemId);
    if (item) {
      item.expanded = false;
    }

    // Collapse content child item
    if (this.accordionItems) {
      const childItem = this.accordionItems.find(i => i.id === itemId);
      if (childItem) {
        childItem.expanded = false;
        childItem.expandedChange.emit(false);
      }
    }

    this.itemToggled.emit({ id: itemId, expanded: false });
  }

  expandAll(): void {
    if (!this.allowMultiple) return;

    this.items.forEach(item => {
      if (!item.disabled) {
        item.expanded = true;
      }
    });

    if (this.accordionItems) {
      this.accordionItems.forEach(item => {
        if (!item.disabled) {
          item.expanded = true;
          item.expandedChange.emit(true);
        }
      });
    }
  }

  collapseAll(): void {
    this.items.forEach(item => {
      item.expanded = false;
    });

    if (this.accordionItems) {
      this.accordionItems.forEach(item => {
        item.expanded = false;
        item.expandedChange.emit(false);
      });
    }
  }

  trackByItem(index: number, item: AccordionItem): string {
    return item.id;
  }
}