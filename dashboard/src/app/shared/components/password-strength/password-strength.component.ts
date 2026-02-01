import { Component, Input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PasswordStrength, PasswordValidatorService } from '../../../features/auth/services/password-validator.service';

@Component({
  selector: 'app-password-strength',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './password-strength.component.html',
  styleUrl: './password-strength.component.css'
})
export class PasswordStrengthComponent {
  @Input() password = '';
  @Input() showLabel = true;
  @Input() showScore = false;

  validation = computed(() => {
    if (!this.password) {
      return {
        isValid: false,
        errors: [],
        strength: PasswordStrength.LOW,
        score: 0
      };
    }
    return this.passwordValidator.validatePassword(this.password);
  });

  strengthColor = computed(() => 
    this.passwordValidator.getStrengthColor(this.validation().strength)
  );

  strengthBgColor = computed(() => 
    this.passwordValidator.getStrengthBgColor(this.validation().strength)
  );

  strengthWidth = computed(() => `${this.validation().score}%`);

  strengthSegments = computed(() => {
    const score = this.validation().score;
    return [
      { active: score >= 20, color: 'bg-red-500' },
      { active: score >= 40, color: 'bg-orange-500' },
      { active: score >= 60, color: 'bg-yellow-500' },
      { active: score >= 80, color: 'bg-green-500' },
      { active: score >= 100, color: 'bg-green-600' }
    ];
  });

  constructor(private passwordValidator: PasswordValidatorService) {}
}