import { Component, Input, Output, EventEmitter, forwardRef, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Icons, IconName } from '../../utils/icons';

export type InputType = 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';
export type InputSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-input',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  template: `
    <div class="space-y-1">
      <label *ngIf="label" [for]="inputId" class="block text-sm font-medium text-secondary-700">
        {{ label }}
        <span *ngIf="required" class="text-error-500 ml-1">*</span>
      </label>
      
      <div class="relative">
        <div *ngIf="leftIcon" class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <lucide-angular [img]="getLeftIcon()" [size]="iconSize" class="text-secondary-400"></lucide-angular>
        </div>
        
        <input
          [id]="inputId"
          [type]="type"
          [placeholder]="placeholder"
          [disabled]="disabled"
          [readonly]="readonly"
          [required]="required"
          [min]="min"
          [max]="max"
          [step]="step"
          [maxLength]="maxlength"
          [class]="inputClasses"
          [value]="value()"
          (input)="onInput($event)"
          (focus)="onFocus()"
          (blur)="onBlur()"
          (keydown.enter)="onEnterKey($event)"
        />
        
        <div *ngIf="rightIcon || clearable" class="absolute inset-y-0 right-0 flex items-center">
          <button
            *ngIf="clearable && value() && !disabled"
            type="button"
            class="pr-3 text-secondary-400 hover:text-secondary-600 focus:outline-none"
            (click)="clearValue()"
          >
            <lucide-angular [img]="Icons.x" [size]="iconSize"></lucide-angular>
          </button>
          
          <div *ngIf="rightIcon && !(clearable && value())" class="pr-3 pointer-events-none">
            <lucide-angular [img]="getRightIcon()" [size]="iconSize" class="text-secondary-400"></lucide-angular>
          </div>
        </div>
      </div>
      
      <div *ngIf="helperText || errorMessage" class="text-sm">
        <p *ngIf="errorMessage" class="text-error-600">{{ errorMessage }}</p>
        <p *ngIf="!errorMessage && helperText" class="text-secondary-500">{{ helperText }}</p>
      </div>
    </div>
  `,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => InputComponent),
      multi: true
    }
  ]
})
export class InputComponent implements ControlValueAccessor {
  @Input() label = '';
  @Input() placeholder = '';
  @Input() type: InputType = 'text';
  @Input() size: InputSize = 'md';
  @Input() disabled = false;
  @Input() readonly = false;
  @Input() required = false;
  @Input() clearable = false;
  @Input() leftIcon?: IconName;
  @Input() rightIcon?: IconName;
  @Input() helperText = '';
  @Input() errorMessage = '';
  @Input() min?: number;
  @Input() max?: number;
  @Input() step?: number;
  @Input() maxlength?: number;
  @Input() inputId = `input-${Math.random().toString(36).substr(2, 9)}`;

  @Output() valueChange = new EventEmitter<string>();
  @Output() focused = new EventEmitter<void>();
  @Output() blurred = new EventEmitter<void>();
  @Output() enterPressed = new EventEmitter<Event>();

  value = signal('');
  isFocused = signal(false);
  Icons = Icons;

  private onChange = (value: string) => {};
  private onTouched = () => {};

  getLeftIcon() {
    return this.leftIcon ? Icons[this.leftIcon] : undefined;
  }

  getRightIcon() {
    return this.rightIcon ? Icons[this.rightIcon] : undefined;
  }

  get inputClasses(): string {
    const baseClasses = [
      'block',
      'w-full',
      'border',
      'rounded-md',
      'shadow-sm',
      'transition-colors',
      'duration-200',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-offset-0',
      'disabled:bg-secondary-50',
      'disabled:text-secondary-500',
      'disabled:cursor-not-allowed',
      'readonly:bg-secondary-50',
      'readonly:cursor-default'
    ];

    // Size classes
    const sizeClasses = {
      sm: ['px-3', 'py-1.5', 'text-sm'],
      md: ['px-3', 'py-2', 'text-sm'],
      lg: ['px-4', 'py-3', 'text-base']
    };

    // Icon padding adjustments
    const iconPadding = [];
    if (this.leftIcon) {
      iconPadding.push('pl-10');
    }
    if (this.rightIcon || this.clearable) {
      iconPadding.push('pr-10');
    }

    // State-based classes
    const stateClasses = [];
    if (this.errorMessage) {
      stateClasses.push(
        'border-error-300',
        'text-error-900',
        'placeholder-error-400',
        'focus:border-error-500',
        'focus:ring-error-500'
      );
    } else {
      stateClasses.push(
        'border-secondary-300',
        'text-secondary-900',
        'placeholder-secondary-400',
        'focus:border-primary-500',
        'focus:ring-primary-500'
      );
    }

    return [
      ...baseClasses,
      ...sizeClasses[this.size],
      ...iconPadding,
      ...stateClasses
    ].join(' ');
  }

  get iconSize(): number {
    const sizes = {
      sm: 16,
      md: 18,
      lg: 20
    };
    return sizes[this.size];
  }

  onInput(event: Event): void {
    const target = event.target as HTMLInputElement;
    const newValue = target.value;
    this.value.set(newValue);
    this.onChange(newValue);
    this.valueChange.emit(newValue);
  }

  onFocus(): void {
    this.isFocused.set(true);
    this.focused.emit();
  }

  onBlur(): void {
    this.isFocused.set(false);
    this.onTouched();
    this.blurred.emit();
  }

  onEnterKey(event: Event): void {
    this.enterPressed.emit(event);
  }

  clearValue(): void {
    this.value.set('');
    this.onChange('');
    this.valueChange.emit('');
  }

  // ControlValueAccessor implementation
  writeValue(value: string): void {
    this.value.set(value || '');
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}