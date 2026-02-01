import { Component, Input, Output, EventEmitter, ElementRef, ViewChild, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { ButtonComponent } from '../button/button.component';
import { Icons, IconName } from '../../utils/icons';

export interface DropdownItem {
  id?: string;
  label?: string;
  icon?: IconName;
  disabled?: boolean;
  divider?: boolean;
  danger?: boolean;
  type?: string;
  description?: string;
  unread?: boolean;
  action?: () => void;
}

export type DropdownPosition = 'bottom-left' | 'bottom-right' | 'top-left' | 'top-right';

@Component({
  selector: 'app-dropdown',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, ButtonComponent],
  template: `
    <div class="relative inline-block text-left" #dropdownContainer>
      <!-- Trigger -->
      <div (click)="toggle()">
        <ng-content select="[slot=trigger]"></ng-content>
        
        <!-- Default trigger if none provided -->
        <app-button
          *ngIf="!hasCustomTrigger"
          [variant]="triggerVariant"
          [size]="triggerSize"
          [rightIcon]="showArrow ? 'chevronDown' : undefined"
          [disabled]="disabled"
        >
          {{ triggerText }}
        </app-button>
      </div>

      <!-- Dropdown Menu -->
      <div
        *ngIf="isOpen"
        [class]="menuClasses"
        role="menu"
        aria-orientation="vertical"
        #dropdownMenu
      >
        <div class="py-1">
          <ng-container *ngFor="let item of items; trackBy: trackByItem">
            <!-- Divider -->
            <div *ngIf="item.divider || item.type === 'divider'" class="border-t border-secondary-100 my-1"></div>
            
            <!-- Menu Item -->
            <button
              *ngIf="!item.divider && item.type !== 'divider'"
              type="button"
              [disabled]="item.disabled"
              [class]="getItemClasses(item)"
              (click)="selectItem(item)"
              role="menuitem"
            >
              <lucide-angular
                *ngIf="item.icon"
                [img]="getIcon(item.icon)"
                [size]="16"
                class="mr-3 text-secondary-400"
              ></lucide-angular>
              
              <span class="flex-1 text-left">{{ item.label }}</span>
              
              <lucide-angular
                *ngIf="selectedItem?.id === item.id && showSelection"
                [img]="Icons.check"
                [size]="16"
                class="ml-3 text-primary-600"
              ></lucide-angular>
            </button>
          </ng-container>
          
          <!-- Custom content -->
          <ng-content select="[slot=menu-content]"></ng-content>
        </div>
      </div>
    </div>

    <!-- Backdrop -->
    <div
      *ngIf="isOpen"
      class="fixed inset-0 z-10"
      (click)="close()"
    ></div>
  `
})
export class DropdownComponent implements OnDestroy {
  @Input() items: DropdownItem[] = [];
  @Input() position: DropdownPosition = 'bottom-left';
  @Input() disabled = false;
  @Input() triggerText = 'Options';
  @Input() triggerVariant: 'primary' | 'secondary' | 'outline' | 'ghost' = 'outline';
  @Input() triggerSize: 'sm' | 'md' | 'lg' = 'md';
  @Input() showSelection = false;
  @Input() selectedItem?: DropdownItem;
  @Input() maxHeight = '300px';
  @Input() minWidth = '200px';
  @Input() showArrow = true;

  @Output() itemSelected = new EventEmitter<DropdownItem>();
  @Output() opened = new EventEmitter<void>();
  @Output() closed = new EventEmitter<void>();

  @ViewChild('dropdownContainer') dropdownContainer!: ElementRef;
  @ViewChild('dropdownMenu') dropdownMenu!: ElementRef;

  isOpen = false;
  hasCustomTrigger = false;

  // Make Icons available in template
  Icons = Icons;

  getIcon(iconName: IconName) {
    return Icons[iconName];
  }

  ngAfterContentInit(): void {
    // In a real implementation, you would use ContentChildren to detect custom trigger
    this.hasCustomTrigger = false;
  }

  ngOnDestroy(): void {
    // Cleanup if needed
  }

  @HostListener('document:keydown.escape')
  onEscapeKey(): void {
    if (this.isOpen) {
      this.close();
    }
  }

  get menuClasses(): string {
    const baseClasses = [
      'absolute',
      'z-20',
      'mt-2',
      'bg-white',
      'rounded-md',
      'shadow-lg',
      'ring-1',
      'ring-black',
      'ring-opacity-5',
      'focus:outline-none',
      'animate-fade-in'
    ];

    const positionClasses = {
      'bottom-left': ['left-0', 'origin-top-left'],
      'bottom-right': ['right-0', 'origin-top-right'],
      'top-left': ['left-0', 'bottom-full', 'mb-2', 'origin-bottom-left'],
      'top-right': ['right-0', 'bottom-full', 'mb-2', 'origin-bottom-right']
    };

    baseClasses.push(...positionClasses[this.position]);

    return baseClasses.join(' ');
  }

  getItemClasses(item: DropdownItem): string {
    const baseClasses = [
      'flex',
      'items-center',
      'w-full',
      'px-4',
      'py-2',
      'text-sm',
      'text-left',
      'transition-colors',
      'duration-150'
    ];

    if (item.disabled) {
      baseClasses.push(
        'text-secondary-400',
        'cursor-not-allowed'
      );
    } else {
      baseClasses.push(
        'text-secondary-700',
        'hover:bg-secondary-50',
        'hover:text-secondary-900',
        'focus:bg-secondary-50',
        'focus:text-secondary-900',
        'focus:outline-none'
      );
    }

    if (this.selectedItem?.id === item.id) {
      baseClasses.push('bg-primary-50', 'text-primary-700');
    }

    return baseClasses.join(' ');
  }

  toggle(): void {
    if (this.disabled) return;
    
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  open(): void {
    if (this.disabled) return;
    
    this.isOpen = true;
    this.opened.emit();
  }

  close(): void {
    this.isOpen = false;
    this.closed.emit();
  }

  selectItem(item: DropdownItem): void {
    if (item.disabled || !item.id) return;
    
    this.selectedItem = item;
    this.itemSelected.emit(item);
    
    if (item.action) {
      item.action();
    }
    
    this.close();
  }

  trackByItem(index: number, item: DropdownItem): string {
    return item.id || `item-${index}`;
  }
}