import { Component, Input, Output, EventEmitter, ElementRef, ViewChild, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';

export type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';
export type TooltipTrigger = 'hover' | 'click' | 'focus';

@Component({
  selector: 'app-tooltip',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div 
      class="relative inline-block"
      #triggerElement
      (mouseenter)="onMouseEnter()"
      (mouseleave)="onMouseLeave()"
      (click)="onClick()"
      (focus)="onFocus()"
      (blur)="onBlur()"
    >
      <ng-content></ng-content>
      
      <!-- Tooltip -->
      <div
        *ngIf="isVisible"
        [class]="tooltipClasses"
        [style]="tooltipStyles"
        role="tooltip"
        #tooltipElement
      >
        <div [class]="contentClasses">
          {{ content }}
          <ng-content select="[slot=tooltip-content]"></ng-content>
        </div>
        
        <!-- Arrow -->
        <div [class]="arrowClasses"></div>
      </div>
    </div>
  `
})
export class TooltipComponent implements OnDestroy {
  @Input() content = '';
  @Input() position: TooltipPosition = 'top';
  @Input() trigger: TooltipTrigger = 'hover';
  @Input() disabled = false;
  @Input() delay = 200;
  @Input() maxWidth = '200px';
  @Input() dark = true;

  @Output() shown = new EventEmitter<void>();
  @Output() hidden = new EventEmitter<void>();

  @ViewChild('triggerElement') triggerElement!: ElementRef;
  @ViewChild('tooltipElement') tooltipElement!: ElementRef;

  isVisible = false;
  private showTimeout?: number;
  private hideTimeout?: number;

  ngOnDestroy(): void {
    this.clearTimeouts();
  }

  get tooltipClasses(): string {
    const baseClasses = [
      'absolute',
      'z-50',
      'pointer-events-none',
      'transition-opacity',
      'duration-200'
    ];

    const positionClasses = {
      top: ['bottom-full', 'left-1/2', 'transform', '-translate-x-1/2', 'mb-2'],
      bottom: ['top-full', 'left-1/2', 'transform', '-translate-x-1/2', 'mt-2'],
      left: ['right-full', 'top-1/2', 'transform', '-translate-y-1/2', 'mr-2'],
      right: ['left-full', 'top-1/2', 'transform', '-translate-y-1/2', 'ml-2']
    };

    baseClasses.push(...positionClasses[this.position]);

    if (this.isVisible) {
      baseClasses.push('opacity-100');
    } else {
      baseClasses.push('opacity-0');
    }

    return baseClasses.join(' ');
  }

  get tooltipStyles(): { [key: string]: string } {
    return {
      'max-width': this.maxWidth
    };
  }

  get contentClasses(): string {
    const baseClasses = [
      'px-3',
      'py-2',
      'text-sm',
      'rounded-md',
      'shadow-lg',
      'whitespace-nowrap'
    ];

    if (this.dark) {
      baseClasses.push('bg-secondary-900', 'text-white');
    } else {
      baseClasses.push('bg-white', 'text-secondary-900', 'border', 'border-secondary-200');
    }

    return baseClasses.join(' ');
  }

  get arrowClasses(): string {
    const baseClasses = ['absolute', 'w-2', 'h-2', 'transform', 'rotate-45'];

    const positionClasses = {
      top: ['top-full', 'left-1/2', '-translate-x-1/2', '-mt-1'],
      bottom: ['bottom-full', 'left-1/2', '-translate-x-1/2', '-mb-1'],
      left: ['left-full', 'top-1/2', '-translate-y-1/2', '-ml-1'],
      right: ['right-full', 'top-1/2', '-translate-y-1/2', '-mr-1']
    };

    baseClasses.push(...positionClasses[this.position]);

    if (this.dark) {
      baseClasses.push('bg-secondary-900');
    } else {
      baseClasses.push('bg-white', 'border', 'border-secondary-200');
    }

    return baseClasses.join(' ');
  }

  onMouseEnter(): void {
    if (this.trigger === 'hover' && !this.disabled) {
      this.show();
    }
  }

  onMouseLeave(): void {
    if (this.trigger === 'hover' && !this.disabled) {
      this.hide();
    }
  }

  onClick(): void {
    if (this.trigger === 'click' && !this.disabled) {
      this.toggle();
    }
  }

  onFocus(): void {
    if (this.trigger === 'focus' && !this.disabled) {
      this.show();
    }
  }

  onBlur(): void {
    if (this.trigger === 'focus' && !this.disabled) {
      this.hide();
    }
  }

  show(): void {
    this.clearTimeouts();
    
    this.showTimeout = window.setTimeout(() => {
      this.isVisible = true;
      this.shown.emit();
    }, this.delay);
  }

  hide(): void {
    this.clearTimeouts();
    
    this.hideTimeout = window.setTimeout(() => {
      this.isVisible = false;
      this.hidden.emit();
    }, this.delay);
  }

  toggle(): void {
    if (this.isVisible) {
      this.hide();
    } else {
      this.show();
    }
  }

  private clearTimeouts(): void {
    if (this.showTimeout) {
      clearTimeout(this.showTimeout);
      this.showTimeout = undefined;
    }
    if (this.hideTimeout) {
      clearTimeout(this.hideTimeout);
      this.hideTimeout = undefined;
    }
  }
}