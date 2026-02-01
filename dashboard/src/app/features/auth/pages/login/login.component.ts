import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { IdentityProviderType } from '../../../../core/models/user.model';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  isLoading = signal(false);
  error = signal<string | null>(null);

  readonly identityProviders = [
    {
      type: IdentityProviderType.GITHUB,
      name: 'GitHub',
      icon: 'github',
      color: 'bg-gray-800 hover:bg-gray-700'
    },
    {
      type: IdentityProviderType.GITLAB,
      name: 'GitLab',
      icon: 'gitlab',
      color: 'bg-orange-600 hover:bg-orange-500'
    },
    {
      type: IdentityProviderType.GOOGLE,
      name: 'Google',
      icon: 'google',
      color: 'bg-blue-600 hover:bg-blue-500'
    },
    {
      type: IdentityProviderType.MICROSOFT,
      name: 'Microsoft',
      icon: 'microsoft',
      color: 'bg-blue-700 hover:bg-blue-600'
    }
  ];

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  async signInWithProvider(provider: IdentityProviderType): Promise<void> {
    this.isLoading.set(true);
    this.error.set(null);

    try {
      const result = await this.authService.signIn(provider);
      if (!result.success) {
        this.error.set(result.error || 'Authentication failed');
      }
      // Note: If successful, user will be redirected to OAuth provider
    } catch (error) {
      this.error.set('An unexpected error occurred');
      console.error('Sign in error:', error);
    } finally {
      this.isLoading.set(false);
    }
  }
}