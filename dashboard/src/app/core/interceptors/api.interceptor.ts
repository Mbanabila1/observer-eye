import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, finalize, retry } from 'rxjs/operators';
import { StateService } from '../services/state.service';
import { ErrorHandlerService } from '../services/error-handler.service';
import { NotificationService } from '../services/notification.service';

@Injectable()
export class ApiInterceptor implements HttpInterceptor {
  private activeRequests = 0;

  constructor(
    private stateService: StateService,
    private errorHandler: ErrorHandlerService,
    private notificationService: NotificationService
  ) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Increment active requests counter
    this.activeRequests++;
    this.updateLoadingState();

    // Clone request and add common headers
    const apiRequest = this.addHeaders(request);

    return next.handle(apiRequest).pipe(
      // Retry failed requests (except for certain status codes)
      retry({
        count: this.shouldRetry(request) ? 2 : 0,
        delay: (error: HttpErrorResponse) => {
          if (this.isRetryableError(error)) {
            return new Observable(observer => {
              setTimeout(() => observer.next(undefined), 1000);
            });
          }
          return throwError(() => error);
        }
      }),
      
      // Handle errors
      catchError((error: HttpErrorResponse) => {
        this.handleError(error, request);
        return throwError(() => error);
      }),
      
      // Always decrement counter when request completes
      finalize(() => {
        this.activeRequests--;
        this.updateLoadingState();
      })
    );
  }

  private addHeaders(request: HttpRequest<any>): HttpRequest<any> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };

    // Add authentication token if available
    const user = this.stateService.getUser();
    if (user?.token) {
      headers['Authorization'] = `Bearer ${user.token}`;
    }

    // Add request ID for tracing
    headers['X-Request-ID'] = this.generateRequestId();

    // Add client information
    headers['X-Client-Version'] = '1.0.0';
    headers['X-Client-Platform'] = 'web';

    return request.clone({
      setHeaders: headers
    });
  }

  private shouldRetry(request: HttpRequest<any>): boolean {
    // Only retry GET requests and safe operations
    return request.method === 'GET' || request.url.includes('/health');
  }

  private isRetryableError(error: HttpErrorResponse): boolean {
    // Retry on network errors and 5xx server errors
    return error.status === 0 || (error.status >= 500 && error.status < 600);
  }

  private handleError(error: HttpErrorResponse, request: HttpRequest<any>): void {
    const context = `${request.method} ${request.url}`;
    
    // Handle specific error cases
    switch (error.status) {
      case 0:
        // Network error
        this.notificationService.showError(
          'Network Error',
          'Unable to connect to the server. Please check your internet connection.'
        );
        break;
        
      case 401:
        // Unauthorized - redirect to login
        this.handleUnauthorized();
        break;
        
      case 403:
        // Forbidden
        this.notificationService.showError(
          'Access Denied',
          'You do not have permission to perform this action.'
        );
        break;
        
      case 404:
        // Not found - only show notification for non-silent requests
        if (!request.headers.has('X-Silent-Error')) {
          this.notificationService.showError(
            'Not Found',
            'The requested resource was not found.'
          );
        }
        break;
        
      case 422:
        // Validation error
        this.handleValidationError(error);
        break;
        
      case 429:
        // Rate limited
        this.notificationService.showWarning(
          'Rate Limited',
          'Too many requests. Please wait a moment and try again.'
        );
        break;
        
      case 500:
      case 502:
      case 503:
      case 504:
        // Server errors
        this.notificationService.showError(
          'Server Error',
          'The server is experiencing issues. Please try again later.'
        );
        break;
        
      default:
        // Generic error handling
        this.errorHandler.handleError(error, context);
        break;
    }
  }

  private handleUnauthorized(): void {
    // Clear user state and redirect to login
    this.stateService.clearUser();
    this.notificationService.showError(
      'Session Expired',
      'Your session has expired. Please log in again.'
    );
    
    // Redirect to login page
    window.location.href = '/auth/login';
  }

  private handleValidationError(error: HttpErrorResponse): void {
    if (error.error?.errors) {
      // Handle structured validation errors
      this.errorHandler.handleValidationError(error.error.errors);
    } else {
      // Handle generic validation error
      this.notificationService.showError(
        'Validation Error',
        error.error?.message || 'Please check your input and try again.'
      );
    }
  }

  private updateLoadingState(): void {
    const isLoading = this.activeRequests > 0;
    this.stateService.setLoading(isLoading);
  }

  private generateRequestId(): string {
    return Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
  }
}