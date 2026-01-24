import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpResponse } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { HealthApiService } from './health-api.service';
import { switchMap, map } from 'rxjs/operators';

/**
 * HTTP Interceptor to handle health check endpoints
 * This interceptor catches requests to health endpoints and serves them locally
 * without making external HTTP calls
 */
@Injectable()
export class HealthEndpointsInterceptor implements HttpInterceptor {
  
  constructor(private healthApiService: HealthApiService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Check if this is a health check endpoint request
    if (this.isHealthEndpoint(req.url)) {
      return this.handleHealthEndpoint(req);
    }
    
    // For all other requests, continue with normal processing
    return next.handle(req);
  }

  /**
   * Check if the request URL is a health endpoint
   */
  private isHealthEndpoint(url: string): boolean {
    const healthEndpoints = [
      '/health',
      '/health/status',
      '/health/ready',
      '/health/live',
      '/health/metrics',
      '/health/deep-system',
      '/metrics'
    ];
    
    return healthEndpoints.some(endpoint => url.endsWith(endpoint));
  }

  /**
   * Handle health endpoint requests
   */
  private handleHealthEndpoint(req: HttpRequest<any>): Observable<HttpEvent<any>> {
    const url = req.url;
    
    if (url.endsWith('/health') || url.endsWith('/health/status')) {
      return this.healthApiService.getHealthStatus().pipe(
        map(response => new HttpResponse({
          status: 200,
          statusText: 'OK',
          body: response,
          headers: req.headers.set('Content-Type', 'application/json')
        }))
      );
    }
    
    if (url.endsWith('/health/ready')) {
      return this.healthApiService.getReadinessStatus().pipe(
        map(response => {
          const status = response.ready ? 200 : 503;
          const statusText = response.ready ? 'OK' : 'Service Unavailable';
          
          return new HttpResponse({
            status,
            statusText,
            body: response,
            headers: req.headers.set('Content-Type', 'application/json')
          });
        })
      );
    }
    
    if (url.endsWith('/health/live')) {
      return this.healthApiService.getLivenessStatus().pipe(
        map(response => {
          const status = response.alive ? 200 : 503;
          const statusText = response.alive ? 'OK' : 'Service Unavailable';
          
          return new HttpResponse({
            status,
            statusText,
            body: response,
            headers: req.headers.set('Content-Type', 'application/json')
          });
        })
      );
    }
    
    if (url.endsWith('/health/metrics') || url.endsWith('/metrics')) {
      return this.healthApiService.getMetrics().pipe(
        map(response => {
          // Return Prometheus-style metrics if requested
          const acceptHeader = req.headers.get('Accept') || '';
          
          if (acceptHeader.includes('text/plain') || url.endsWith('/metrics')) {
            const metricsText = this.healthApiService.generatePrometheusMetrics(response.metrics);
            
            return new HttpResponse({
              status: 200,
              statusText: 'OK',
              body: metricsText,
              headers: req.headers.set('Content-Type', 'text/plain; charset=utf-8')
            });
          } else {
            return new HttpResponse({
              status: 200,
              statusText: 'OK',
              body: response,
              headers: req.headers.set('Content-Type', 'application/json')
            });
          }
        })
      );
    }
    
    if (url.endsWith('/health/deep-system')) {
      return this.healthApiService.getDeepSystemStatus().pipe(
        map(response => new HttpResponse({
          status: 200,
          statusText: 'OK',
          body: response,
          headers: req.headers.set('Content-Type', 'application/json')
        }))
      );
    }
    
    // If we get here, it's an unknown health endpoint
    return of(new HttpResponse({
      status: 404,
      statusText: 'Not Found',
      body: { error: 'Health endpoint not found' },
      headers: req.headers.set('Content-Type', 'application/json')
    }));
  }
}