import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { ButtonComponent } from '../button/button.component';

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

@Component({
  selector: 'app-modal',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, ButtonComponent],
  template: `
    <!-- Backdrop -->
    <div
      *ngIf="isOpen"
      class="fixed inset-0 z-50 overflow-y-auto"
      [class.animate-fade-in]="isOpen"
    >
      <!-- Background overlay -->
      <div
        class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        (click)="handleBackdropClick()"
      ></div>

      <!-- Modal container -->
      <div class="flex min-h-full items-center justify-center p-4">
        <div
          #modalContent
          [class]="modalClasses"
          class="relative transform overflow-hidden rounded-lg bg-white shadow-xl transition-all animate-slide-up"
          role="dialog"
          aria-modal="true"
          [attr.aria-labelledby]="title ? 'modal-title' : null"
        >
          <!-- Header -->
          <div *ngIf="showHeader" class="flex items-center justify-between p-6 border-b border-secondary-200">
            <h3 *ngIf="title" id="modal-title" class="text-lg font-semibold text-secondary-900">
              {{ title }}
            </h3>
            <ng-content select="[slot=header]"></ng-content>
            
            <app-button
              *ngIf="showCloseButton"
              variant="ghost"
              size="sm"
              [iconOnly]="true"
              leftIcon="x"
              (clicked)="close()"
              class="ml-auto"
            ></app-button>
          </div>

          <!-- Body -->
          <div [class]="bodyClasses">
            <ng-content></ng-content>
          </div>

          <!-- Footer -->
          <div *ngIf="showFooter" class="flex items-center justify-end gap-3 p-6 border-t border-secondary-200 bg-secondary-50">
            <ng-content select="[slot=footer]"></ng-content>
            
            <!-- Default footer buttons if no custom footer provided -->
            <div *ngIf="!hasCustomFooter" class="flex gap-3">
              <app-button
                *ngIf="showCancelButton"
                variant="outline"
                (clicked)="cancel()"
              >
                {{ cancelText }}
              </app-button>
              
              <app-button
                *ngIf="showConfirmButton"
                [variant]="confirmVariant"
                [loading]="confirmLoading"
                (clicked)="confirm()"
              >
                {{ confirmText }}
              </app-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class ModalComponent implements OnInit, OnDestroy {
  @Input() isOpen = false;
  @Input() title = '';
  @Input() size: ModalSize = 'md';
  @Input() showHeader = true;
  @Input() showFooter = false;
  @Input() showCloseButton = true;
  @Input() showCancelButton = true;
  @Input() showConfirmButton = true;
  @Input() cancelText = 'Cancel';
  @Input() confirmText = 'Confirm';
  @Input() confirmVariant: 'primary' | 'success' | 'warning' | 'error' = 'primary';
  @Input() confirmLoading = false;
  @Input() closeOnBackdropClick = true;
  @Input() closeOnEscape = true;

  @Output() isOpenChange = new EventEmitter<boolean>();
  @Output() opened = new EventEmitter<void>();
  @Output() closed = new EventEmitter<void>();
  @Output() cancelled = new EventEmitter<void>();
  @Output() confirmed = new EventEmitter<void>();

  @ViewChild('modalContent') modalContent!: ElementRef;

  hasCustomFooter = false;

  ngOnInit(): void {
    if (this.isOpen) {
      this.handleOpen();
    }
    
    // Check if custom footer content is provided
    this.hasCustomFooter = this.hasFooterContent();
  }

  ngOnDestroy(): void {
    this.handleClose();
  }

  ngOnChanges(): void {
    if (this.isOpen) {
      this.handleOpen();
    } else {
      this.handleClose();
    }
  }

  get modalClasses(): string {
    const sizeClasses = {
      sm: 'max-w-sm',
      md: 'max-w-md',
      lg: 'max-w-lg',
      xl: 'max-w-xl',
      full: 'max-w-full mx-4'
    };

    return `w-full ${sizeClasses[this.size]}`;
  }

  get bodyClasses(): string {
    const baseClasses = ['p-6'];
    
    if (!this.showHeader) {
      baseClasses.push('pt-6');
    }
    
    if (!this.showFooter) {
      baseClasses.push('pb-6');
    }

    return baseClasses.join(' ');
  }

  handleOpen(): void {
    document.body.style.overflow = 'hidden';
    this.opened.emit();
    
    if (this.closeOnEscape) {
      document.addEventListener('keydown', this.handleEscapeKey);
    }
  }

  handleClose(): void {
    document.body.style.overflow = '';
    document.removeEventListener('keydown', this.handleEscapeKey);
  }

  handleBackdropClick(): void {
    if (this.closeOnBackdropClick) {
      this.close();
    }
  }

  handleEscapeKey = (event: KeyboardEvent): void => {
    if (event.key === 'Escape') {
      this.close();
    }
  };

  close(): void {
    this.isOpen = false;
    this.isOpenChange.emit(false);
    this.handleClose();
    this.closed.emit();
  }

  cancel(): void {
    this.cancelled.emit();
    this.close();
  }

  confirm(): void {
    this.confirmed.emit();
  }

  private hasFooterContent(): boolean {
    // This is a simplified check - in a real implementation,
    // you might want to use ContentChildren to detect projected content
    return false;
  }
}