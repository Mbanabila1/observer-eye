import { Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, timer } from 'rxjs';
import { retryWhen, mergeMap, finalize } from 'rxjs/operators';
import { NotificationService } from './notification.service';
import { StateService } from './state.service';

export interface RetryConfig {
  maxRetries: number;
  delay: number;
  backoffMultiplier: number;
}

@Injectable({
  providedIn: 'root'
})
export class ErrorHandlerService {
  private defaultRetryConfig: RetryConfig = {
    maxRetries: 3,
    delay: 1000,
    backoffMultiplier: 2
  };

  constructor(
    private notificationService: NotificationService,
    private stateService: StateService
  ) {}

  handleError(error: any, context?: string): void {
    console.error('Error occurred:', error, 'Context:', context);

    let errorMessage = 'An unexpected error occurred';
    let errorTitle = 'Error';

    if (error instanceof HttpErrorResponse) {
      errorMessage = this.getHttpErrorMessage(error);
      errorTitle = `HTTP ${error.status} Error`;
    } else if (error instanceof Error) {
      errorMessage = error.message;
      errorTitle = 'Application Error';
    } else if (typeof error === 'string') {
      errorMessage = error;
    }

    // Update global error state
    this.stateService.setError(errorMessage);

    // Show user notification
    this.notificationService.showError(errorTitle, errorMessage);

    // Log error for monitoring (in production, this would send to logging service)
    this.logError(error, context);
  }

  private getHttpErrorMessage(error: HttpErrorResponse): string {
    switch (error.status) {
      case 0:
        return 'Unable to connect to the server. Please check your internet connection.';
      case 400:
        return error.error?.message || 'Invalid request. Please check your input.';
      case 401:
        return 'You are not authorized. Please log in again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return 'A conflict occurred. The resource may have been modified by another user.';
      case 422:
        return error.error?.message || 'Validation failed. Please check your input.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'Internal server error. Please try again later.';
      case 502:
        return 'Bad gateway. The server is temporarily unavailable.';
      case 503:
        return 'Service unavailable. Please try again later.';
      case 504:
        return 'Gateway timeout. The request took too long to process.';
      default:
        return error.error?.message || `Server error (${error.status}). Please try again later.`;
    }
  }

  private logError(error: any, context?: string): void {
    const errorLog = {
      timestamp: new Date().toISOString(),
      error: {
        message: error.message || error,
        stack: error.stack,
        name: error.name
      },
      context,
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: this.stateService.getUser()?.id
    };

    // In production, send this to your logging service
    console.error('Error Log:', errorLog);
  }

  // Retry logic for HTTP requests
  retryWithBackoff<T>(retryConfig: Partial<RetryConfig> = {}): (source: Observable<T>) => Observable<T> {
    const config = { ...this.defaultRetryConfig, ...retryConfig };
    
    return (source: Observable<T>) => source.pipe(
      retryWhen(errors => errors.pipe(
        mergeMap((error, index) => {
          const retryAttempt = index + 1;
          
          // Don't retry certain HTTP errors
          if (error instanceof HttpErrorResponse) {
            if ([400, 401, 403, 404, 422].includes(error.status)) {
              return throwError(error);
            }
          }
          
          // Stop retrying after max attempts
          if (retryAttempt > config.maxRetries) {
            return throwError(error);
          }
          
          // Calculate delay with exponential backoff
          const delay = config.delay * Math.pow(config.backoffMultiplier, retryAttempt - 1);
          
          console.log(`Retry attempt ${retryAttempt}/${config.maxRetries} after ${delay}ms`);
          
          return timer(delay);
        })
      )),
      finalize(() => {
        // Clear loading state when request completes (success or failure)
        this.stateService.setLoading(false);
      })
    );
  }

  // Handle specific error types
  handleAuthenticationError(): void {
    this.stateService.clearUser();
    this.notificationService.showError(
      'Authentication Required',
      'Your session has expired. Please log in again.'
    );
    // Redirect to login page
    window.location.href = '/auth/login';
  }

  handleValidationError(errors: Record<string, string[]>): void {
    const errorMessages = Object.entries(errors)
      .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
      .join('\n');
    
    this.notificationService.showError(
      'Validation Error',
      errorMessages
    );
  }

  handleNetworkError(): void {
    this.notificationService.showError(
      'Network Error',
      'Unable to connect to the server. Please check your internet connection and try again.'
    );
  }

  // Clear error state
  clearError(): void {
    this.stateService.clearError();
  }
}