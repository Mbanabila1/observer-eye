import { Component, Input, Output, EventEmitter, forwardRef, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../utils/icons';

export type CheckboxSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-checkbox',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  template: `
    <div class="flex items-start space-x-3">
      <div class="relative flex items-center">
        <input
          [id]="checkboxId"
          type="checkbox"
          [checked]="checked()"
          [disabled]="disabled"
          [required]="required"
          [class]="checkboxClasses"
          (change)="onCheckboxChange($event)"
          (focus)="onFocus()"
          (blur)="onBlur()"
        />
        
        <!-- Custom checkbox indicator -->
        <div [class]="indicatorClasses">
          <lucide-angular
            *ngIf="checked() && !indeterminate"
            [img]="Icons.check"
            [size]="iconSize"
            class="text-white"
          ></lucide-angular>
          
          <lucide-angular
            *ngIf="indeterminate"
            [img]="Icons.minus"
            [size]="iconSize"
            class="text-white"
          ></lucide-angular>
        </div>
      </div>
      
      <div class="flex-1 min-w-0">
        <label
          *ngIf="label"
          [for]="checkboxId"
          [class]="labelClasses"
        >
          {{ label }}
          <span *ngIf="required" class="text-error-500 ml-1">*</span>
        </label>
        
        <p *ngIf="description" [class]="descriptionClasses">
          {{ description }}
        </p>
        
        <div *ngIf="helperText || errorMessage" class="mt-1 text-sm">
          <p *ngIf="errorMessage" class="text-error-600">{{ errorMessage }}</p>
          <p *ngIf="!errorMessage && helperText" class="text-secondary-500">{{ helperText }}</p>
        </div>
      </div>
    </div>
  `,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => CheckboxComponent),
      multi: true
    }
  ]
})
export class CheckboxComponent implements ControlValueAccessor {
  @Input() label = '';
  @Input() description = '';
  @Input() size: CheckboxSize = 'md';
  @Input() disabled = false;
  @Input() required = false;
  @Input() indeterminate = false;
  @Input() helperText = '';
  @Input() errorMessage = '';
  @Input() checkboxId = `checkbox-${Math.random().toString(36).substr(2, 9)}`;

  @Output() checkedChange = new EventEmitter<boolean>();
  @Output() focused = new EventEmitter<void>();
  @Output() blurred = new EventEmitter<void>();

  checked = signal(false);
  Icons = Icons;

  private onChange = (value: boolean) => {};
  private onTouched = () => {};

  get checkboxClasses(): string {
    const baseClasses = [
      'absolute',
      'opacity-0',
      'cursor-pointer',
      'peer'
    ];

    if (this.disabled) {
      baseClasses.push('cursor-not-allowed');
    }

    return baseClasses.join(' ');
  }

  get indicatorClasses(): string {
    const baseClasses = [
      'flex',
      'items-center',
      'justify-center',
      'border-2',
      'rounded',
      'transition-all',
      'duration-200',
      'peer-focus:ring-2',
      'peer-focus:ring-offset-2',
      'cursor-pointer'
    ];

    // Size classes
    const sizeClasses = {
      sm: ['w-4', 'h-4'],
      md: ['w-5', 'h-5'],
      lg: ['w-6', 'h-6']
    };

    baseClasses.push(...sizeClasses[this.size]);

    // State classes
    if (this.disabled) {
      baseClasses.push(
        'bg-secondary-100',
        'border-secondary-300',
        'cursor-not-allowed'
      );
    } else if (this.checked() || this.indeterminate) {
      if (this.errorMessage) {
        baseClasses.push(
          'bg-error-600',
          'border-error-600',
          'peer-focus:ring-error-500'
        );
      } else {
        baseClasses.push(
          'bg-primary-600',
          'border-primary-600',
          'peer-focus:ring-primary-500'
        );
      }
    } else {
      if (this.errorMessage) {
        baseClasses.push(
          'bg-white',
          'border-error-300',
          'peer-focus:ring-error-500'
        );
      } else {
        baseClasses.push(
          'bg-white',
          'border-secondary-300',
          'peer-focus:ring-primary-500',
          'hover:border-secondary-400'
        );
      }
    }

    return baseClasses.join(' ');
  }

  get labelClasses(): string {
    const baseClasses = [
      'block',
      'font-medium',
      'cursor-pointer'
    ];

    const sizeClasses = {
      sm: ['text-sm'],
      md: ['text-sm'],
      lg: ['text-base']
    };

    baseClasses.push(...sizeClasses[this.size]);

    if (this.disabled) {
      baseClasses.push('text-secondary-400', 'cursor-not-allowed');
    } else {
      baseClasses.push('text-secondary-900');
    }

    return baseClasses.join(' ');
  }

  get descriptionClasses(): string {
    const baseClasses = ['mt-1'];

    const sizeClasses = {
      sm: ['text-xs'],
      md: ['text-sm'],
      lg: ['text-sm']
    };

    baseClasses.push(...sizeClasses[this.size]);

    if (this.disabled) {
      baseClasses.push('text-secondary-400');
    } else {
      baseClasses.push('text-secondary-600');
    }

    return baseClasses.join(' ');
  }

  get iconSize(): number {
    const sizes = {
      sm: 12,
      md: 14,
      lg: 16
    };
    return sizes[this.size];
  }

  onCheckboxChange(event: Event): void {
    const target = event.target as HTMLInputElement;
    const isChecked = target.checked;
    this.checked.set(isChecked);
    this.onChange(isChecked);
    this.checkedChange.emit(isChecked);
  }

  onFocus(): void {
    this.focused.emit();
  }

  onBlur(): void {
    this.onTouched();
    this.blurred.emit();
  }

  // ControlValueAccessor implementation
  writeValue(value: boolean): void {
    this.checked.set(!!value);
  }

  registerOnChange(fn: (value: boolean) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}