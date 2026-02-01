import { Component, Input, Output, EventEmitter, forwardRef, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../utils/icons';

export interface SelectOption {
  value: any;
  label: string;
  disabled?: boolean;
  group?: string;
}

export type SelectSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-select',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  template: `
    <div class="space-y-1">
      <label *ngIf="label" [for]="selectId" class="block text-sm font-medium text-secondary-700">
        {{ label }}
        <span *ngIf="required" class="text-error-500 ml-1">*</span>
      </label>
      
      <div class="relative">
        <select
          [id]="selectId"
          [disabled]="disabled"
          [required]="required"
          [class]="selectClasses"
          [value]="selectedValue()"
          (change)="onSelectionChange($event)"
          (focus)="onFocus()"
          (blur)="onBlur()"
        >
          <option *ngIf="placeholder" value="" disabled>{{ placeholder }}</option>
          
          <ng-container *ngFor="let option of groupedOptions()">
            <optgroup *ngIf="option.isGroup" [label]="option.label">
              <option
                *ngFor="let subOption of option.options"
                [value]="subOption.value"
                [disabled]="subOption.disabled"
              >
                {{ subOption.label }}
              </option>
            </optgroup>
            
            <option
              *ngIf="!option.isGroup"
              [value]="option.value"
              [disabled]="option.disabled"
            >
              {{ option.label }}
            </option>
          </ng-container>
        </select>
        
        <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <lucide-angular
            [img]="Icons.chevronDown"
            [size]="iconSize"
            class="text-secondary-400"
          ></lucide-angular>
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
      useExisting: forwardRef(() => SelectComponent),
      multi: true
    }
  ]
})
export class SelectComponent implements ControlValueAccessor {
  @Input() label = '';
  @Input() placeholder = 'Select an option';
  @Input() options: SelectOption[] = [];
  @Input() size: SelectSize = 'md';
  @Input() disabled = false;
  @Input() required = false;
  @Input() helperText = '';
  @Input() errorMessage = '';
  @Input() selectId = `select-${Math.random().toString(36).substr(2, 9)}`;

  @Output() selectionChange = new EventEmitter<any>();
  @Output() focused = new EventEmitter<void>();
  @Output() blurred = new EventEmitter<void>();

  selectedValue = signal<any>('');
  Icons = Icons;

  private onChange = (value: any) => {};
  private onTouched = () => {};

  groupedOptions = computed(() => {
    const groups: { [key: string]: SelectOption[] } = {};
    const ungrouped: SelectOption[] = [];

    this.options.forEach(option => {
      if (option.group) {
        if (!groups[option.group]) {
          groups[option.group] = [];
        }
        groups[option.group].push(option);
      } else {
        ungrouped.push(option);
      }
    });

    const result: any[] = [];

    // Add ungrouped options first
    result.push(...ungrouped);

    // Add grouped options
    Object.entries(groups).forEach(([groupName, groupOptions]) => {
      result.push({
        isGroup: true,
        label: groupName,
        options: groupOptions
      });
    });

    return result;
  });

  get selectClasses(): string {
    const baseClasses = [
      'block',
      'w-full',
      'border',
      'rounded-md',
      'shadow-sm',
      'bg-white',
      'transition-colors',
      'duration-200',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-offset-0',
      'disabled:bg-secondary-50',
      'disabled:text-secondary-500',
      'disabled:cursor-not-allowed',
      'appearance-none',
      'pr-10'
    ];

    // Size classes
    const sizeClasses = {
      sm: ['px-3', 'py-1.5', 'text-sm'],
      md: ['px-3', 'py-2', 'text-sm'],
      lg: ['px-4', 'py-3', 'text-base']
    };

    // State-based classes
    const stateClasses = [];
    if (this.errorMessage) {
      stateClasses.push(
        'border-error-300',
        'text-error-900',
        'focus:border-error-500',
        'focus:ring-error-500'
      );
    } else {
      stateClasses.push(
        'border-secondary-300',
        'text-secondary-900',
        'focus:border-primary-500',
        'focus:ring-primary-500'
      );
    }

    return [
      ...baseClasses,
      ...sizeClasses[this.size],
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

  onSelectionChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    const value = target.value;
    this.selectedValue.set(value);
    this.onChange(value);
    this.selectionChange.emit(value);
  }

  onFocus(): void {
    this.focused.emit();
  }

  onBlur(): void {
    this.onTouched();
    this.blurred.emit();
  }

  // ControlValueAccessor implementation
  writeValue(value: any): void {
    this.selectedValue.set(value || '');
  }

  registerOnChange(fn: (value: any) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}