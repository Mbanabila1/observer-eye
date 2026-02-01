import { Injectable } from '@angular/core';

export enum PasswordStrength {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

export interface PasswordRequirements {
  minLength: number;
  requiresLowercase: boolean;
  requiresUppercase: boolean;
  requiresNumbers: boolean;
  requiresSpecialChars: boolean;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  strength: PasswordStrength;
  score: number;
}

@Injectable({
  providedIn: 'root'
})
export class PasswordValidatorService {
  private readonly requirements: PasswordRequirements = {
    minLength: 16,
    requiresLowercase: true,
    requiresUppercase: true,
    requiresNumbers: true,
    requiresSpecialChars: true
  };

  validatePassword(password: string): ValidationResult {
    const errors: string[] = [];
    let score = 0;

    // Length validation
    if (password.length < this.requirements.minLength) {
      errors.push(`Password must be at least ${this.requirements.minLength} characters long`);
    } else {
      score += 25;
    }

    // Lowercase validation
    if (this.requirements.requiresLowercase && !/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    } else if (/[a-z]/.test(password)) {
      score += 25;
    }

    // Uppercase validation
    if (this.requirements.requiresUppercase && !/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    } else if (/[A-Z]/.test(password)) {
      score += 25;
    }

    // Numbers validation
    if (this.requirements.requiresNumbers && !/\d/.test(password)) {
      errors.push('Password must contain at least one number');
    } else if (/\d/.test(password)) {
      score += 25;
    }

    // Special characters validation
    if (this.requirements.requiresSpecialChars && !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      errors.push('Password must contain at least one special character');
    } else if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      score += 25;
    }

    // Additional scoring for complexity
    if (password.length >= 20) score += 10;
    if (password.length >= 24) score += 10;
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]{2,}/.test(password)) score += 10;
    if (/\d{2,}/.test(password)) score += 5;

    const strength = this.calculateStrength(score);
    const isValid = errors.length === 0;

    return {
      isValid,
      errors,
      strength,
      score: Math.min(score, 100)
    };
  }

  validateStrength(password: string): PasswordStrength {
    const result = this.validatePassword(password);
    return result.strength;
  }

  validateRequirements(password: string): ValidationResult {
    return this.validatePassword(password);
  }

  private calculateStrength(score: number): PasswordStrength {
    if (score >= 80) return PasswordStrength.HIGH;
    if (score >= 60) return PasswordStrength.MEDIUM;
    return PasswordStrength.LOW;
  }

  getRequirements(): PasswordRequirements {
    return { ...this.requirements };
  }

  getStrengthColor(strength: PasswordStrength): string {
    switch (strength) {
      case PasswordStrength.HIGH:
        return 'text-green-600';
      case PasswordStrength.MEDIUM:
        return 'text-yellow-600';
      case PasswordStrength.LOW:
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  }

  getStrengthBgColor(strength: PasswordStrength): string {
    switch (strength) {
      case PasswordStrength.HIGH:
        return 'bg-green-500';
      case PasswordStrength.MEDIUM:
        return 'bg-yellow-500';
      case PasswordStrength.LOW:
        return 'bg-red-500';
      default:
        return 'bg-gray-300';
    }
  }
}