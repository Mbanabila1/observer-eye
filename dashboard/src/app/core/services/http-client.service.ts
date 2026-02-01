import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, timeout } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { ErrorHandlerService } from './error-handler.service';
import { StateService } from './state.service';

export interface RequestOptions {
  timeout?: number;
  silent?: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

@Injectable({
  providedIn: 'root'
})
export class HttpClientService {
  private readonly baseUrl = environment.apiUrl;
  private readonly defaultTimeout = 30000;

  constructor(
    private http: HttpClient,
    private errorHandler: ErrorHandlerService,
    private stateService: StateService
  ) {}

  get<T>(endpoint: string, options: RequestOptions = {}): Observable<T> {
    const url = this.buildUrl(endpoint);
    return this.http.get<T>(url).pipe(
      timeout(options.timeout || this.defaultTimeout),
      catchError(error => this.handleError(error, options))
    );
  }

  post<T>(endpoint: string, data: any, options: RequestOptions = {}): Observable<T> {
    const url = this.buildUrl(endpoint);
    return this.http.post<T>(url, data).pipe(
      timeout(options.timeout || this.defaultTimeout),
      catchError(error => this.handleError(error, options))
    );
  }

  put<T>(endpoint: string, data: any, options: RequestOptions = {}): Observable<T> {
    const url = this.buildUrl(endpoint);
    return this.http.put<T>(url, data).pipe(
      timeout(options.timeout || this.defaultTimeout),
      catchError(error => this.handleError(error, options))
    );
  }

  patch<T>(endpoint: string, data: any, options: RequestOptions = {}): Observable<T> {
    const url = this.buildUrl(endpoint);
    return this.http.patch<T>(url, data).pipe(
      timeout(options.timeout || this.defaultTimeout),
      catchError(error => this.handleError(error, options))
    );
  }

  delete<T>(endpoint: string, options: RequestOptions = {}): Observable<T> {
    const url = this.buildUrl(endpoint);
    return this.http.delete<T>(url).pipe(
      timeout(options.timeout || this.defaultTimeout),
      catchError(error => this.handleError(error, options))
    );
  }

  getPaginated<T>(endpoint: string, page: number = 1, pageSize: number = 10, options: RequestOptions = {}): Observable<PaginatedResponse<T>> {
    const url = `${this.buildUrl(endpoint)}?page=${page}&page_size=${pageSize}`;
    return this.get<PaginatedResponse<T>>(url, options);
  }

  healthCheck(): Observable<any> {
    return this.get('/health', { timeout: 5000, silent: true });
  }

  uploadFile<T>(endpoint: string, file: File, additionalData?: Record<string, any>, options: RequestOptions = {}): Observable<T> {
    const url = this.buildUrl(endpoint);
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key]);
      });
    }

    return this.http.post<T>(url, formData).pipe(
      timeout(options.timeout || 60000),
      catchError(error => this.handleError(error, options))
    );
  }

  downloadFile(endpoint: string, filename?: string, options: RequestOptions = {}): Observable<Blob> {
    const url = this.buildUrl(endpoint);
    return this.http.get(url, { responseType: 'blob' }).pipe(
      timeout(options.timeout || 60000),
      catchError(error => this.handleError(error, options))
    );
  }

  private buildUrl(endpoint: string): string {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
    return `${this.baseUrl}/${cleanEndpoint}`;
  }

  private handleError(error: any, options: RequestOptions): Observable<never> {
    if (!options.silent) {
      this.errorHandler.handleError(error);
    }
    return throwError(() => error);
  }
}