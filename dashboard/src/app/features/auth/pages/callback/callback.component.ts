import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-callback',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './callback.component.html',
  styleUrl: './callback.component.css'
})
export class CallbackComponent implements OnInit {
  isProcessing = signal(true);
  error = signal<string | null>(null);
  success = signal(false);

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.handleCallback();
  }

  private handleCallback(): void {
    this.route.queryParams.subscribe(params => {
      const code = params['code'];
      const state = params['state'];
      const error = params['error'];

      if (error) {
        this.handleError(`OAuth error: ${error}`);
        return;
      }

      if (!code || !state) {
        this.handleError('Missing required parameters');
        return;
      }

      this.processCallback(code, state);
    });
  }

  private processCallback(code: string, state: string): void {
    this.authService.handleCallback(code, state).subscribe({
      next: (result) => {
        if (result.success) {
          this.success.set(true);
          this.isProcessing.set(false);
          
          // Redirect to dashboard after a brief delay
          setTimeout(() => {
            this.router.navigate(['/dashboard']);
          }, 2000);
        } else {
          this.handleError(result.error || 'Authentication failed');
        }
      },
      error: (error) => {
        console.error('Callback processing error:', error);
        this.handleError('Failed to process authentication callback');
      }
    });
  }

  private handleError(errorMessage: string): void {
    this.error.set(errorMessage);
    this.isProcessing.set(false);
    
    // Redirect to login after a delay
    setTimeout(() => {
      this.router.navigate(['/auth/login']);
    }, 3000);
  }
}