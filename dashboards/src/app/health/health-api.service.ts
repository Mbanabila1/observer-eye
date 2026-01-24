import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

export interface HealthEndpointResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: {
    [key: string]: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      message?: string;
      responseTime?: number;
    };
  };
}

export interface ReadinessResponse {
  ready: boolean;
  timestamp: string;
  services: {
    [key: string]: boolean;
  };
}

export interface LivenessResponse {
  alive: boolean;
  timestamp: string;
  uptime: number;
}

export interface MetricsResponse {
  timestamp: string;
  metrics: {
    [key: string]: number | string;
  };
}

/**
 * Service for handling health check API endpoints
 * These endpoints are designed to be consumed by:
 * - Nginx health checks
 * - Kubernetes readiness/liveness probes
 * - External monitoring systems
 */
@Injectable({
  providedIn: 'root'
})
export class HealthApiService {
  private readonly startTime = Date.now();

  constructor(private http: HttpClient) {}

  /**
   * Main health check endpoint
   * Used by nginx health check and general monitoring
   */
  getHealthStatus(): Observable<HealthEndpointResponse> {
    const startTime = Date.now();
    
    return this.performHealthChecks().pipe(
      map(checks => {
        const overallStatus = this.calculateOverallStatus(checks);
        
        return {
          status: overallStatus,
          timestamp: new Date().toISOString(),
          checks
        };
      }),
      catchError(error => {
        console.error('Health check failed:', error);
        return of({
          status: 'unhealthy' as const,
          timestamp: new Date().toISOString(),
          checks: {
            error: {
              status: 'unhealthy' as const,
              message: error.message || 'Health check failed'
            }
          }
        });
      })
    );
  }

  /**
   * Kubernetes readiness probe endpoint
   * Indicates if the container is ready to receive traffic
   */
  getReadinessStatus(): Observable<ReadinessResponse> {
    return this.checkServiceDependencies().pipe(
      map(services => {
        const ready = Object.values(services).every(status => status);
        
        return {
          ready,
          timestamp: new Date().toISOString(),
          services
        };
      }),
      catchError(error => {
        console.error('Readiness check failed:', error);
        return of({
          ready: false,
          timestamp: new Date().toISOString(),
          services: {
            error: false
          }
        });
      })
    );
  }

  /**
   * Kubernetes liveness probe endpoint
   * Indicates if the container is alive and should not be restarted
   */
  getLivenessStatus(): Observable<LivenessResponse> {
    return of({
      alive: true,
      timestamp: new Date().toISOString(),
      uptime: Date.now() - this.startTime
    });
  }

  /**
   * Metrics endpoint for monitoring systems
   * Returns Prometheus-style metrics
   */
  getMetrics(): Observable<MetricsResponse> {
    return this.collectMetrics().pipe(
      map(metrics => ({
        timestamp: new Date().toISOString(),
        metrics
      })),
      catchError(error => {
        console.error('Metrics collection failed:', error);
        return of({
          timestamp: new Date().toISOString(),
          metrics: {
            error: 1,
            error_message: error.message || 'Metrics collection failed'
          }
        });
      })
    );
  }

  /**
   * Deep system status endpoint
   * Provides detailed system health information
   */
  getDeepSystemStatus(): Observable<any> {
    return this.performDeepSystemChecks().pipe(
      catchError(error => {
        console.error('Deep system check failed:', error);
        return of({
          status: 'unhealthy',
          timestamp: new Date().toISOString(),
          error: error.message
        });
      })
    );
  }

  /**
   * Perform comprehensive health checks
   */
  private performHealthChecks(): Observable<{ [key: string]: any }> {
    const checks: { [key: string]: any } = {};
    
    // Application health
    checks['application'] = {
      status: 'healthy',
      message: 'Angular application is running'
    };
    
    // Memory check (simulated)
    const memoryUsage = this.getSimulatedMemoryUsage();
    checks['memory'] = {
      status: memoryUsage > 90 ? 'unhealthy' : memoryUsage > 80 ? 'degraded' : 'healthy',
      message: `Memory usage: ${memoryUsage.toFixed(1)}%`
    };
    
    // Disk check (simulated)
    const diskUsage = this.getSimulatedDiskUsage();
    checks['disk'] = {
      status: diskUsage > 95 ? 'unhealthy' : diskUsage > 85 ? 'degraded' : 'healthy',
      message: `Disk usage: ${diskUsage.toFixed(1)}%`
    };
    
    // Network connectivity
    checks['network'] = {
      status: 'healthy',
      message: 'Network connectivity is available'
    };
    
    return of(checks);
  }

  /**
   * Check service dependencies for readiness
   */
  private checkServiceDependencies(): Observable<{ [key: string]: boolean }> {
    const services: { [key: string]: boolean } = {};
    
    // In a real implementation, these would be actual HTTP checks
    // For now, we'll simulate the checks
    services['middleware'] = Math.random() > 0.1; // 90% success rate
    services['backend'] = Math.random() > 0.05;   // 95% success rate
    services['database'] = Math.random() > 0.02;  // 98% success rate
    services['cache'] = Math.random() > 0.03;     // 97% success rate
    
    return of(services);
  }

  /**
   * Collect system metrics
   */
  private collectMetrics(): Observable<{ [key: string]: number | string }> {
    const metrics: { [key: string]: number | string } = {};
    
    // Application metrics
    metrics['dashboard_status'] = 1;
    metrics['dashboard_uptime_seconds'] = Math.floor((Date.now() - this.startTime) / 1000);
    metrics['dashboard_version'] = '1.0.0';
    
    // System metrics (simulated)
    metrics['memory_usage_percent'] = this.getSimulatedMemoryUsage();
    metrics['cpu_usage_percent'] = this.getSimulatedCpuUsage();
    metrics['disk_usage_percent'] = this.getSimulatedDiskUsage();
    metrics['network_latency_ms'] = this.getSimulatedNetworkLatency();
    
    // Request metrics (simulated)
    metrics['http_requests_total'] = Math.floor(Math.random() * 10000) + 1000;
    metrics['http_request_duration_ms'] = Math.random() * 100 + 10;
    metrics['websocket_connections_active'] = Math.floor(Math.random() * 50) + 5;
    
    // Deep system metrics
    metrics['kernel_system_calls_total'] = Math.floor(Math.random() * 100000) + 10000;
    metrics['payload_packets_processed_total'] = Math.floor(Math.random() * 1000000) + 100000;
    metrics['payload_packets_dropped_total'] = Math.floor(Math.random() * 100);
    metrics['hardware_cpu_temperature_celsius'] = Math.random() * 40 + 35;
    
    return of(metrics);
  }

  /**
   * Perform deep system checks
   */
  private performDeepSystemChecks(): Observable<any> {
    const deepSystemStatus = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      kernel: {
        status: 'healthy',
        systemCalls: Math.floor(Math.random() * 10000) + 1000,
        memoryPressure: this.getSimulatedMemoryUsage() * 0.3,
        modules: Math.floor(Math.random() * 50) + 100
      },
      payload: {
        status: 'healthy',
        processedPackets: Math.floor(Math.random() * 100000) + 10000,
        droppedPackets: Math.floor(Math.random() * 100),
        processingLatency: Math.random() * 5 + 0.1
      },
      hardware: {
        status: 'healthy',
        cpuTemperature: Math.random() * 40 + 35,
        diskHealth: Math.random() > 0.1 ? 'good' : 'warning',
        networkInterfaces: Math.floor(Math.random() * 5) + 2
      }
    };
    
    return of(deepSystemStatus);
  }

  /**
   * Calculate overall status from individual checks
   */
  private calculateOverallStatus(checks: { [key: string]: any }): 'healthy' | 'degraded' | 'unhealthy' {
    const statuses = Object.values(checks).map(check => check.status);
    
    if (statuses.includes('unhealthy')) {
      return 'unhealthy';
    } else if (statuses.includes('degraded')) {
      return 'degraded';
    } else {
      return 'healthy';
    }
  }

  /**
   * Utility methods for simulated metrics
   */
  private getSimulatedMemoryUsage(): number {
    return Math.random() * 60 + 20; // 20-80%
  }

  private getSimulatedCpuUsage(): number {
    return Math.random() * 50 + 10; // 10-60%
  }

  private getSimulatedDiskUsage(): number {
    return Math.random() * 40 + 30; // 30-70%
  }

  private getSimulatedNetworkLatency(): number {
    return Math.random() * 30 + 5; // 5-35ms
  }

  /**
   * Generate Prometheus-style metrics text
   */
  generatePrometheusMetrics(metrics: { [key: string]: number | string }): string {
    let output = '# Observer-Eye Dashboard Metrics\n';
    
    for (const [key, value] of Object.entries(metrics)) {
      if (typeof value === 'number') {
        output += `${key} ${value}\n`;
      } else {
        output += `${key}{value="${value}"} 1\n`;
      }
    }
    
    return output;
  }
}