import { Component, Input, Output, EventEmitter, signal, computed, forwardRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { PasswordValidatorService, ValidationResult, PasswordStrength } from '../../../features/auth/services/password-validator.service';

@Component({
  selector: 'app-password-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './password-input.component.html',
  styleUrl: './password-input.component.css',
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => PasswordInputComponent),
      multi: true
    }
  ]
})
export class PasswordInputComponent implements ControlValueAccessor {
  @Input() label = 'Password';
  @Input() placeholder = 'Enter your password';
  @Input() showStrengthIndicator = true;
  @Input() showRequirements = true;
  @Input() disabled = false;
  @Output() validationChange = new EventEmitter<ValidationResult>();

  password = signal('');
  showPassword = signal(false);
  isFocused = signal(false);

  validation = computed(() => {
    const pwd = this.password();
    if (!pwd) {
      return {
        isValid: false,
        errors: [],
        strength: PasswordStrength.LOW,
        score: 0
      };
    }
    return this.passwordValidator.validatePassword(pwd);
  });

  strengthColor = computed(() => 
    this.passwordValidator.getStrengthColor(this.validation().strength)
  );

  strengthBgColor = computed(() => 
    this.passwordValidator.getStrengthBgColor(this.validation().strength)
  );

  strengthWidth = computed(() => `${this.validation().score}%`);

  requirements = computed(() => {
    const reqs = this.passwordValidator.getRequirements();
    const pwd = this.password();
    
    return [
      {
        text: `At least ${reqs.minLength} characters`,
        met: pwd.length >= reqs.minLength
      },
      {
        text: 'One lowercase letter',
        met: /[a-z]/.test(pwd)
      },
      {
        text: 'One uppercase letter',
        met: /[A-Z]/.test(pwd)
      },
      {
        text: 'One number',
        met: /\d/.test(pwd)
      },
      {
        text: 'One special character',
        met: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd)
      }
    ];
  });

  private onChange = (value: string) => {};
  private onTouched = () => {};

  constructor(private passwordValidator: PasswordValidatorService) {}

  onPasswordChange(value: string): void {
    this.password.set(value);
    this.onChange(value);
    this.validationChange.emit(this.validation());
  }

  onFocus(): void {
    this.isFocused.set(true);
  }

  onBlur(): void {
    this.isFocused.set(false);
    this.onTouched();
  }

  togglePasswordVisibility(): void {
    this.showPassword.update(show => !show);
  }

  // ControlValueAccessor implementation
  writeValue(value: string): void {
    this.password.set(value || '');
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