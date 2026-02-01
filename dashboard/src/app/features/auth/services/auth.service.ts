import { Injectable, signal } from '@angular/core';
import { Observable, BehaviorSubject, of, throwError } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { ApiService } from '../../../core/services/api.service';
import { User, IdentityProviderType } from '../../../core/models/user.model';
import { environment } from '../../../../environments/environment';

export interface AuthResult {
  success: boolean;
  user?: User;
  token?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(false);
  
  public currentUser$ = this.currentUserSubject.asObservable();
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();
  
  // Signals for reactive UI
  public currentUser = signal<User | null>(null);
  public isAuthenticated = signal<boolean>(false);

  constructor(private apiService: ApiService) {
    this.initializeAuth();
  }

  private initializeAuth(): void {
    const token = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
      try {
        const user = JSON.parse(userData);
        this.setAuthenticatedUser(user, token);
      } catch (error) {
        this.clearAuthData();
      }
    }
  }

  signIn(provider: IdentityProviderType): Promise<AuthResult> {
    return new Promise((resolve) => {
      try {
        const providerConfig = environment.identityProviders[provider];
        if (!providerConfig) {
          resolve({ success: false, error: 'Provider not configured' });
          return;
        }

        // Store the provider for callback handling
        sessionStorage.setItem('auth_provider', provider);
        
        // Construct OAuth URL
        const authUrl = this.buildOAuthUrl(provider, providerConfig);
        
        // Redirect to OAuth provider
        window.location.href = authUrl;
        
        // This won't be reached due to redirect, but needed for Promise
        resolve({ success: true });
      } catch (error) {
        resolve({ success: false, error: 'Failed to initiate OAuth flow' });
      }
    });
  }

  private buildOAuthUrl(provider: IdentityProviderType, config: any): string {
    const params = new URLSearchParams({
      client_id: config.clientId,
      redirect_uri: config.redirectUri,
      response_type: 'code',
      scope: this.getProviderScope(provider),
      state: this.generateState()
    });

    const baseUrls = {
      [IdentityProviderType.GITHUB]: 'https://github.com/login/oauth/authorize',
      [IdentityProviderType.GITLAB]: 'https://gitlab.com/oauth/authorize',
      [IdentityProviderType.GOOGLE]: 'https://accounts.google.com/oauth2/v2/auth',
      [IdentityProviderType.MICROSOFT]: 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
    };

    return `${baseUrls[provider]}?${params.toString()}`;
  }

  private getProviderScope(provider: IdentityProviderType): string {
    const scopes = {
      [IdentityProviderType.GITHUB]: 'user:email',
      [IdentityProviderType.GITLAB]: 'read_user',
      [IdentityProviderType.GOOGLE]: 'openid email profile',
      [IdentityProviderType.MICROSOFT]: 'openid email profile'
    };
    return scopes[provider];
  }

  private generateState(): string {
    const state = Math.random().toString(36).substring(2, 15) + 
                  Math.random().toString(36).substring(2, 15);
    sessionStorage.setItem('oauth_state', state);
    return state;
  }

  handleCallback(code: string, state: string): Observable<AuthResult> {
    const storedState = sessionStorage.getItem('oauth_state');
    const provider = sessionStorage.getItem('auth_provider') as IdentityProviderType;
    
    if (!storedState || storedState !== state) {
      return of({ success: false, error: 'Invalid state parameter' });
    }
    
    if (!provider) {
      return of({ success: false, error: 'No provider found in session' });
    }

    // Clean up session storage
    sessionStorage.removeItem('oauth_state');
    sessionStorage.removeItem('auth_provider');

    return this.apiService.post<AuthResult>('/auth/callback', {
      code,
      provider,
      redirectUri: environment.identityProviders[provider].redirectUri
    }).pipe(
      tap(result => {
        if (result.success && result.user && result.token) {
          this.setAuthenticatedUser(result.user, result.token);
        }
      }),
      catchError(error => {
        console.error('Authentication callback error:', error);
        return of({ success: false, error: 'Authentication failed' });
      })
    );
  }

  signOut(): Observable<void> {
    return new Observable(observer => {
      this.clearAuthData();
      
      // Call backend to invalidate session
      this.apiService.post('/auth/logout', {}).subscribe({
        next: () => {
          observer.next();
          observer.complete();
        },
        error: () => {
          // Even if logout API fails, we still clear local data
          observer.next();
          observer.complete();
        }
      });
    });
  }

  getCurrentUser(): Observable<User | null> {
    return this.currentUser$;
  }

  refreshToken(): Promise<string> {
    return new Promise((resolve, reject) => {
      const currentToken = localStorage.getItem('auth_token');
      if (!currentToken) {
        reject('No token available');
        return;
      }

      this.apiService.post<{ token: string }>('/auth/refresh', {}).subscribe({
        next: (response) => {
          localStorage.setItem('auth_token', response.token);
          resolve(response.token);
        },
        error: (error) => {
          this.clearAuthData();
          reject(error);
        }
      });
    });
  }

  private setAuthenticatedUser(user: User, token: string): void {
    localStorage.setItem('auth_token', token);
    localStorage.setItem('user_data', JSON.stringify(user));
    
    this.currentUserSubject.next(user);
    this.isAuthenticatedSubject.next(true);
    
    // Update signals
    this.currentUser.set(user);
    this.isAuthenticated.set(true);
  }

  private clearAuthData(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    
    this.currentUserSubject.next(null);
    this.isAuthenticatedSubject.next(false);
    
    // Update signals
    this.currentUser.set(null);
    this.isAuthenticated.set(false);
  }
}