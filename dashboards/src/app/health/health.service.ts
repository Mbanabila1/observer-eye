import { Injectable, signal, computed } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, BehaviorSubject, interval, combineLatest, of } from 'rxjs';
import { map, catchError, startWith, switchMap, timeout } from 'rxjs/operators';

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime: number;
  version: string;
  environment: string;
}

export interface SystemMetrics {
  memoryUsage: number;
  cpuUsage: number;
  diskUsage: number;
  networkLatency: number;
  activeConnections: number;
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  responseTime: number;
  lastCheck: string;
  error?: string;
}

export interface DeepSystemStatus {
  kernelHealth: {
    status: 'healthy' | 'degraded' | 'unhealthy';
    systemCalls: number;
    kernelModules: number;
    memoryPressure: number;
  };
  payloadProcessing: {
    status: 'healthy' | 'degraded' | 'unhealthy';
    processedPackets: number;
    droppedPackets: number;
    processingLatency: number;
  };
  hardwareMonitoring: {
    status: 'healthy' | 'degraded' | 'unhealthy';
    cpuTemperature: number;
    diskHealth: string;
    networkInterfaces: number;
  };
}

export interface HealthCheckResponse {
  overall: HealthStatus;
  services: ServiceHealth[];
  metrics: SystemMetrics;
  deepSystem: DeepSystemStatus;
  readiness: boolean;
  liveness: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class HealthService {
  private readonly startTime = Date.now();
  private readonly version = '1.0.0';
  private readonly environment = this.getEnvironment();
  
  // Health check interval (30 seconds)
  private readonly healthCheckInterval = 30000;
  
  // Reactive state
  private healthStatus$ = new BehaviorSubject<HealthCheckResponse>(this.getInitialHealthStatus());
  
  // Signals for reactive UI
  public readonly currentHealth = signal<HealthCheckResponse>(this.getInitialHealthStatus());
  public readonly isHealthy = computed(() => this.currentHealth().overall.status === 'healthy');
  public readonly isReady = computed(() => this.currentHealth().readiness);
  public readonly isLive = computed(() => this.currentHealth().liveness);
  
  // Service endpoints to monitor
  private readonly serviceEndpoints = [
    { name: 'middleware', url: '/api/health', timeout: 5000 },
    { name: 'backend', url: '/api/backend/health', timeout: 5000 },
    { name: 'bi-analytics', url: '/analytics/health', timeout: 5000 },
    { name: 'deep-system', url: '/api/deep-system/health', timeout: 10000 }
  ];

  constructor(private http: HttpClient) {
    this.startHealthMonitoring();
  }

  /**
   * Start continuous health monitoring
   */
  private startHealthMonitoring(): void {
    // Perform health checks at regular intervals
    interval(this.healthCheckInterval)
      .pipe(
        startWith(0), // Start immediately
        switchMap(() => this.performHealthCheck())
      )
      .subscribe(health => {
        this.healthStatus$.next(health);
        this.currentHealth.set(health);
      });
  }

  /**
   * Perform comprehensive health check
   */
  private performHealthCheck(): Observable<HealthCheckResponse> {
    const startTime = Date.now();
    
    return combineLatest([
      this.checkServices(),
      this.getSystemMetrics(),
      this.getDeepSystemStatus()
    ]).pipe(
      map(([services, metrics, deepSystem]) => {
        const overall = this.calculateOverallHealth(services, metrics, deepSystem);
        const readiness = this.calculateReadiness(services, metrics);
        const liveness = this.calculateLiveness(services, metrics);
        
        return {
          overall,
          services,
          metrics,
          deepSystem,
          readiness,
          liveness
        };
      }),
      catchError(error => {
        console.error('Health check failed:', error);
        return of(this.getFailedHealthStatus(error));
      })
    );
  }

  /**
   * Check health of all dependent services
   */
  private checkServices(): Observable<ServiceHealth[]> {
    const serviceChecks = this.serviceEndpoints.map(endpoint => 
      this.checkSingleService(endpoint.name, endpoint.url, endpoint.timeout)
    );
    
    return combineLatest(serviceChecks);
  }

  /**
   * Check health of a single service
   */
  private checkSingleService(name: string, url: string, timeoutMs: number): Observable<ServiceHealth> {
    const startTime = Date.now();
    
    return this.http.get<any>(url).pipe(
      timeout(timeoutMs),
      map(() => ({
        name,
        status: 'healthy' as const,
        responseTime: Date.now() - startTime,
        lastCheck: new Date().toISOString()
      })),
      catchError((error: HttpErrorResponse) => {
        const responseTime = Date.now() - startTime;
        const status = this.determineServiceStatus(error, responseTime);
        
        return of({
          name,
          status,
          responseTime,
          lastCheck: new Date().toISOString(),
          error: error.message
        });
      })
    );
  }

  /**
   * Get system metrics
   */
  private getSystemMetrics(): Observable<SystemMetrics> {
    // In a real implementation, these would come from actual system monitoring
    // For now, we'll simulate realistic metrics
    return of({
      memoryUsage: this.getRandomMetric(30, 80), // 30-80% memory usage
      cpuUsage: this.getRandomMetric(10, 60),    // 10-60% CPU usage
      diskUsage: this.getRandomMetric(20, 70),   // 20-70% disk usage
      networkLatency: this.getRandomMetric(1, 50), // 1-50ms network latency
      activeConnections: Math.floor(Math.random() * 100) + 10 // 10-110 connections
    });
  }

  /**
   * Get deep system status indicators
   */
  private getDeepSystemStatus(): Observable<DeepSystemStatus> {
    // Simulate deep system monitoring data
    return of({
      kernelHealth: {
        status: this.getRandomStatus(),
        systemCalls: Math.floor(Math.random() * 10000) + 1000,
        kernelModules: Math.floor(Math.random() * 50) + 100,
        memoryPressure: this.getRandomMetric(0, 30)
      },
      payloadProcessing: {
        status: this.getRandomStatus(),
        processedPackets: Math.floor(Math.random() * 100000) + 10000,
        droppedPackets: Math.floor(Math.random() * 100),
        processingLatency: this.getRandomMetric(0.1, 5.0)
      },
      hardwareMonitoring: {
        status: this.getRandomStatus(),
        cpuTemperature: this.getRandomMetric(35, 75),
        diskHealth: Math.random() > 0.1 ? 'good' : 'warning',
        networkInterfaces: Math.floor(Math.random() * 5) + 2
      }
    });
  }

  /**
   * Calculate overall health status
   */
  private calculateOverallHealth(
    services: ServiceHealth[], 
    metrics: SystemMetrics, 
    deepSystem: DeepSystemStatus
  ): HealthStatus {
    const unhealthyServices = services.filter(s => s.status === 'unhealthy').length;
    const degradedServices = services.filter(s => s.status === 'degraded').length;
    
    // Check if any critical metrics are in bad state
    const criticalMetrics = [
      metrics.memoryUsage > 90,
      metrics.cpuUsage > 90,
      metrics.diskUsage > 95,
      metrics.networkLatency > 1000
    ];
    
    const hasCriticalIssues = criticalMetrics.some(Boolean);
    
    // Check deep system health
    const deepSystemIssues = [
      deepSystem.kernelHealth.status === 'unhealthy',
      deepSystem.payloadProcessing.status === 'unhealthy',
      deepSystem.hardwareMonitoring.status === 'unhealthy'
    ];
    
    const hasDeepSystemIssues = deepSystemIssues.some(Boolean);
    
    let status: 'healthy' | 'degraded' | 'unhealthy';
    
    if (unhealthyServices > 0 || hasCriticalIssues || hasDeepSystemIssues) {
      status = 'unhealthy';
    } else if (degradedServices > 0 || metrics.memoryUsage > 80 || metrics.cpuUsage > 80) {
      status = 'degraded';
    } else {
      status = 'healthy';
    }
    
    return {
      status,
      timestamp: new Date().toISOString(),
      uptime: Date.now() - this.startTime,
      version: this.version,
      environment: this.environment
    };
  }

  /**
   * Calculate readiness probe status
   */
  private calculateReadiness(services: ServiceHealth[], metrics: SystemMetrics): boolean {
    // Ready if all critical services are at least degraded and system resources are available
    const criticalServices = services.filter(s => ['middleware', 'backend'].includes(s.name));
    const criticalServicesReady = criticalServices.every(s => s.status !== 'unhealthy');
    
    const systemResourcesReady = metrics.memoryUsage < 95 && metrics.diskUsage < 98;
    
    return criticalServicesReady && systemResourcesReady;
  }

  /**
   * Calculate liveness probe status
   */
  private calculateLiveness(services: ServiceHealth[], metrics: SystemMetrics): boolean {
    // Live if the application can respond and basic resources are available
    const basicResourcesAvailable = metrics.memoryUsage < 98 && metrics.diskUsage < 99;
    
    // Check if we can still serve requests (simulated by checking if we got this far)
    const canServeRequests = true;
    
    return basicResourcesAvailable && canServeRequests;
  }

  /**
   * Determine service status based on error and response time
   */
  private determineServiceStatus(error: HttpErrorResponse, responseTime: number): 'degraded' | 'unhealthy' {
    // If response time is very high but we got a response, it's degraded
    if (responseTime > 5000 && error.status !== 0) {
      return 'degraded';
    }
    
    // If it's a timeout or connection error, it's unhealthy
    if (error.status === 0 || error.status >= 500) {
      return 'unhealthy';
    }
    
    // Client errors (4xx) are considered degraded
    return 'degraded';
  }

  /**
   * Get initial health status
   */
  private getInitialHealthStatus(): HealthCheckResponse {
    return {
      overall: {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: 0,
        version: this.version,
        environment: this.environment
      },
      services: [],
      metrics: {
        memoryUsage: 0,
        cpuUsage: 0,
        diskUsage: 0,
        networkLatency: 0,
        activeConnections: 0
      },
      deepSystem: {
        kernelHealth: {
          status: 'healthy',
          systemCalls: 0,
          kernelModules: 0,
          memoryPressure: 0
        },
        payloadProcessing: {
          status: 'healthy',
          processedPackets: 0,
          droppedPackets: 0,
          processingLatency: 0
        },
        hardwareMonitoring: {
          status: 'healthy',
          cpuTemperature: 0,
          diskHealth: 'good',
          networkInterfaces: 0
        }
      },
      readiness: false,
      liveness: true
    };
  }

  /**
   * Get failed health status
   */
  private getFailedHealthStatus(error: any): HealthCheckResponse {
    return {
      overall: {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        uptime: Date.now() - this.startTime,
        version: this.version,
        environment: this.environment
      },
      services: [],
      metrics: {
        memoryUsage: 0,
        cpuUsage: 0,
        diskUsage: 0,
        networkLatency: 0,
        activeConnections: 0
      },
      deepSystem: {
        kernelHealth: {
          status: 'unhealthy',
          systemCalls: 0,
          kernelModules: 0,
          memoryPressure: 0
        },
        payloadProcessing: {
          status: 'unhealthy',
          processedPackets: 0,
          droppedPackets: 0,
          processingLatency: 0
        },
        hardwareMonitoring: {
          status: 'unhealthy',
          cpuTemperature: 0,
          diskHealth: 'critical',
          networkInterfaces: 0
        }
      },
      readiness: false,
      liveness: false
    };
  }

  /**
   * Utility methods
   */
  private getEnvironment(): string {
    // In a real app, this would come from environment configuration
    return typeof window !== 'undefined' && window.location.hostname === 'localhost' 
      ? 'development' 
      : 'production';
  }

  private getRandomMetric(min: number, max: number): number {
    return Math.random() * (max - min) + min;
  }

  private getRandomStatus(): 'healthy' | 'degraded' | 'unhealthy' {
    const rand = Math.random();
    if (rand < 0.8) return 'healthy';
    if (rand < 0.95) return 'degraded';
    return 'unhealthy';
  }

  /**
   * Public API methods
   */
  
  /**
   * Get current health status
   */
  public getCurrentHealth(): Observable<HealthCheckResponse> {
    return this.healthStatus$.asObservable();
  }

  /**
   * Force a health check
   */
  public forceHealthCheck(): Observable<HealthCheckResponse> {
    return this.performHealthCheck();
  }

  /**
   * Get readiness status for Kubernetes readiness probe
   */
  public getReadinessStatus(): Observable<{ ready: boolean; timestamp: string }> {
    return this.healthStatus$.pipe(
      map(health => ({
        ready: health.readiness,
        timestamp: health.overall.timestamp
      }))
    );
  }

  /**
   * Get liveness status for Kubernetes liveness probe
   */
  public getLivenessStatus(): Observable<{ alive: boolean; timestamp: string }> {
    return this.healthStatus$.pipe(
      map(health => ({
        alive: health.liveness,
        timestamp: health.overall.timestamp
      }))
    );
  }
}