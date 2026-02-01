import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpParams } from '@angular/common/http';
import { HttpClientService, RequestOptions, PaginatedResponse } from './http-client.service';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  constructor(private httpClient: HttpClientService) {}

  get<T>(endpoint: string, params?: HttpParams | Record<string, any>, options?: RequestOptions): Observable<T> {
    // For now, ignore params since our simplified HTTP client doesn't support them
    return this.httpClient.get<T>(endpoint, options);
  }

  post<T>(endpoint: string, data: any, options?: RequestOptions): Observable<T> {
    return this.httpClient.post<T>(endpoint, data, options);
  }

  put<T>(endpoint: string, data: any, options?: RequestOptions): Observable<T> {
    return this.httpClient.put<T>(endpoint, data, options);
  }

  patch<T>(endpoint: string, data: any, options?: RequestOptions): Observable<T> {
    return this.httpClient.patch<T>(endpoint, data, options);
  }

  delete<T>(endpoint: string, options?: RequestOptions): Observable<T> {
    return this.httpClient.delete<T>(endpoint, options);
  }

  // Paginated requests
  getPaginated<T>(
    endpoint: string, 
    page: number = 1, 
    pageSize: number = 10, 
    params?: Record<string, any>,
    options?: RequestOptions
  ): Observable<PaginatedResponse<T>> {
    return this.httpClient.getPaginated<T>(endpoint, page, pageSize, options);
  }

  // File operations
  uploadFile<T>(
    endpoint: string, 
    file: File, 
    additionalData?: Record<string, any>,
    options?: RequestOptions
  ): Observable<T> {
    return this.httpClient.uploadFile<T>(endpoint, file, additionalData, options);
  }

  downloadFile(
    endpoint: string, 
    filename?: string,
    options?: RequestOptions
  ): Observable<Blob> {
    return this.httpClient.downloadFile(endpoint, filename, options);
  }

  // Health check
  healthCheck(): Observable<any> {
    return this.httpClient.healthCheck();
  }

  // Common API endpoints
  
  // Authentication
  login(credentials: { email: string; password: string }): Observable<any> {
    return this.post('/auth/login', credentials);
  }

  logout(): Observable<any> {
    return this.post('/auth/logout', {});
  }

  refreshToken(): Observable<any> {
    return this.post('/auth/refresh', {});
  }

  // User management
  getCurrentUser(): Observable<any> {
    return this.get('/auth/me');
  }

  updateProfile(data: any): Observable<any> {
    return this.put('/auth/profile', data);
  }

  // Dashboard operations
  getDashboards(): Observable<any[]> {
    return this.get('/dashboards');
  }

  getDashboard(id: string): Observable<any> {
    return this.get(`/dashboards/${id}`);
  }

  createDashboard(data: any): Observable<any> {
    return this.post('/dashboards', data);
  }

  updateDashboard(id: string, data: any): Observable<any> {
    return this.put(`/dashboards/${id}`, data);
  }

  deleteDashboard(id: string): Observable<any> {
    return this.delete(`/dashboards/${id}`);
  }

  // Metrics and monitoring
  getMetrics(type?: string): Observable<any> {
    const endpoint = type ? `/metrics?type=${type}` : '/metrics';
    return this.get(endpoint);
  }

  getSystemHealth(): Observable<any> {
    return this.get('/system/health');
  }

  getPerformanceData(timeRange?: string): Observable<any> {
    const endpoint = timeRange ? `/performance?range=${timeRange}` : '/performance';
    return this.get(endpoint);
  }

  // Notifications
  getNotifications(): Observable<any[]> {
    return this.get('/notifications');
  }

  markNotificationRead(id: string): Observable<any> {
    return this.patch(`/notifications/${id}`, { read: true });
  }

  // Settings
  getSettings(): Observable<any> {
    return this.get('/settings');
  }

  updateSettings(data: any): Observable<any> {
    return this.put('/settings', data);
  }
}