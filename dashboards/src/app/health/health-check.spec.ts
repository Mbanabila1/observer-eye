import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { HealthService } from './health.service';
import { HealthApiService } from './health-api.service';
import { HealthEndpointsInterceptor } from './health-endpoints.interceptor';
import { HTTP_INTERCEPTORS, HttpClient } from '@angular/common/http';

describe('Health Check System', () => {
  let healthService: HealthService;
  let healthApiService: HealthApiService;
  let httpClient: HttpClient;
  let httpTestingController: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        HealthService,
        HealthApiService,
        {
          provide: HTTP_INTERCEPTORS,
          useClass: HealthEndpointsInterceptor,
          multi: true
        }
      ]
    });

    healthService = TestBed.inject(HealthService);
    healthApiService = TestBed.inject(HealthApiService);
    httpClient = TestBed.inject(HttpClient);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  describe('HealthService', () => {
    it('should be created', () => {
      expect(healthService).toBeTruthy();
    });

    it('should provide initial health status', () => {
      const currentHealth = healthService.currentHealth();
      expect(currentHealth).toBeDefined();
      expect(currentHealth.overall).toBeDefined();
      expect(currentHealth.overall.status).toBeDefined();
    });

    it('should calculate readiness status', () => {
      const isReady = healthService.isReady();
      expect(typeof isReady).toBe('boolean');
    });

    it('should calculate liveness status', () => {
      const isLive = healthService.isLive();
      expect(typeof isLive).toBe('boolean');
    });

    it('should provide health status observable', (done) => {
      healthService.getCurrentHealth().subscribe(health => {
        expect(health).toBeDefined();
        expect(health.overall).toBeDefined();
        expect(health.services).toBeDefined();
        expect(health.metrics).toBeDefined();
        expect(health.deepSystem).toBeDefined();
        done();
      });
    });
  });

  describe('HealthApiService', () => {
    it('should be created', () => {
      expect(healthApiService).toBeTruthy();
    });

    it('should provide health status', (done) => {
      healthApiService.getHealthStatus().subscribe(status => {
        expect(status).toBeDefined();
        expect(status.status).toMatch(/^(healthy|degraded|unhealthy)$/);
        expect(status.timestamp).toBeDefined();
        expect(status.checks).toBeDefined();
        done();
      });
    });

    it('should provide readiness status', (done) => {
      healthApiService.getReadinessStatus().subscribe(status => {
        expect(status).toBeDefined();
        expect(typeof status.ready).toBe('boolean');
        expect(status.timestamp).toBeDefined();
        expect(status.services).toBeDefined();
        done();
      });
    });

    it('should provide liveness status', (done) => {
      healthApiService.getLivenessStatus().subscribe(status => {
        expect(status).toBeDefined();
        expect(typeof status.alive).toBe('boolean');
        expect(status.timestamp).toBeDefined();
        expect(typeof status.uptime).toBe('number');
        done();
      });
    });

    it('should provide metrics', (done) => {
      healthApiService.getMetrics().subscribe(metrics => {
        expect(metrics).toBeDefined();
        expect(metrics.timestamp).toBeDefined();
        expect(metrics.metrics).toBeDefined();
        expect(typeof metrics.metrics.dashboard_status).toBe('number');
        done();
      });
    });

    it('should provide deep system status', (done) => {
      healthApiService.getDeepSystemStatus().subscribe(status => {
        expect(status).toBeDefined();
        expect(status.timestamp).toBeDefined();
        done();
      });
    });

    it('should generate Prometheus metrics format', (done) => {
      healthApiService.getMetrics().subscribe(response => {
        const prometheusText = healthApiService.generatePrometheusMetrics(response.metrics);
        expect(prometheusText).toContain('# Observer-Eye Dashboard Metrics');
        expect(prometheusText).toContain('dashboard_status');
        done();
      });
    });
  });

  describe('Health Endpoints Integration', () => {
    it('should handle /health endpoint', () => {
      httpClient.get('/health').subscribe(response => {
        expect(response).toBeDefined();
      });

      // The interceptor should handle this request
      httpTestingController.expectNone('/health');
    });

    it('should handle /health/ready endpoint', () => {
      httpClient.get('/health/ready').subscribe(response => {
        expect(response).toBeDefined();
      });

      httpTestingController.expectNone('/health/ready');
    });

    it('should handle /health/live endpoint', () => {
      httpClient.get('/health/live').subscribe(response => {
        expect(response).toBeDefined();
      });

      httpTestingController.expectNone('/health/live');
    });

    it('should handle /metrics endpoint', () => {
      httpClient.get('/metrics').subscribe(response => {
        expect(response).toBeDefined();
      });

      httpTestingController.expectNone('/metrics');
    });

    it('should handle /health/deep-system endpoint', () => {
      httpClient.get('/health/deep-system').subscribe(response => {
        expect(response).toBeDefined();
      });

      httpTestingController.expectNone('/health/deep-system');
    });
  });

  describe('Deep System Status Validation', () => {
    it('should provide kernel health metrics', (done) => {
      healthService.getCurrentHealth().subscribe(health => {
        const kernelHealth = health.deepSystem.kernelHealth;
        expect(kernelHealth).toBeDefined();
        expect(kernelHealth.status).toMatch(/^(healthy|degraded|unhealthy)$/);
        expect(typeof kernelHealth.systemCalls).toBe('number');
        expect(typeof kernelHealth.kernelModules).toBe('number');
        expect(typeof kernelHealth.memoryPressure).toBe('number');
        done();
      });
    });

    it('should provide payload processing metrics', (done) => {
      healthService.getCurrentHealth().subscribe(health => {
        const payloadProcessing = health.deepSystem.payloadProcessing;
        expect(payloadProcessing).toBeDefined();
        expect(payloadProcessing.status).toMatch(/^(healthy|degraded|unhealthy)$/);
        expect(typeof payloadProcessing.processedPackets).toBe('number');
        expect(typeof payloadProcessing.droppedPackets).toBe('number');
        expect(typeof payloadProcessing.processingLatency).toBe('number');
        done();
      });
    });

    it('should provide hardware monitoring metrics', (done) => {
      healthService.getCurrentHealth().subscribe(health => {
        const hardwareMonitoring = health.deepSystem.hardwareMonitoring;
        expect(hardwareMonitoring).toBeDefined();
        expect(hardwareMonitoring.status).toMatch(/^(healthy|degraded|unhealthy)$/);
        expect(typeof hardwareMonitoring.cpuTemperature).toBe('number');
        expect(typeof hardwareMonitoring.diskHealth).toBe('string');
        expect(typeof hardwareMonitoring.networkInterfaces).toBe('number');
        done();
      });
    });
  });

  describe('Kubernetes Probe Compatibility', () => {
    it('should return appropriate HTTP status for readiness probe', () => {
      httpClient.get('/health/ready').subscribe({
        next: (response: any) => {
          // Should be 200 if ready, 503 if not ready
          expect(response).toBeDefined();
        },
        error: (error) => {
          // 503 status is acceptable for not ready state
          expect([200, 503]).toContain(error.status);
        }
      });
    });

    it('should return appropriate HTTP status for liveness probe', () => {
      httpClient.get('/health/live').subscribe({
        next: (response: any) => {
          // Should be 200 if alive, 503 if not alive
          expect(response).toBeDefined();
        },
        error: (error) => {
          // 503 status is acceptable for not alive state
          expect([200, 503]).toContain(error.status);
        }
      });
    });
  });

  describe('System Metrics Validation', () => {
    it('should provide valid system metrics', (done) => {
      healthService.getCurrentHealth().subscribe(health => {
        const metrics = health.metrics;
        expect(metrics).toBeDefined();
        
        // Memory usage should be a percentage (0-100)
        expect(metrics.memoryUsage).toBeGreaterThanOrEqual(0);
        expect(metrics.memoryUsage).toBeLessThanOrEqual(100);
        
        // CPU usage should be a percentage (0-100)
        expect(metrics.cpuUsage).toBeGreaterThanOrEqual(0);
        expect(metrics.cpuUsage).toBeLessThanOrEqual(100);
        
        // Disk usage should be a percentage (0-100)
        expect(metrics.diskUsage).toBeGreaterThanOrEqual(0);
        expect(metrics.diskUsage).toBeLessThanOrEqual(100);
        
        // Network latency should be positive
        expect(metrics.networkLatency).toBeGreaterThanOrEqual(0);
        
        // Active connections should be non-negative
        expect(metrics.activeConnections).toBeGreaterThanOrEqual(0);
        
        done();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle health check failures gracefully', () => {
      // Mock a service failure scenario
      spyOn(console, 'error');
      
      // Force an error in health checking
      const originalMethod = healthApiService.getHealthStatus;
      spyOn(healthApiService, 'getHealthStatus').and.returnValue(
        new Promise((_, reject) => reject(new Error('Service unavailable'))) as any
      );
      
      healthService.forceHealthCheck().subscribe({
        next: (health) => {
          // Should still return a health object, but with unhealthy status
          expect(health).toBeDefined();
          expect(health.overall.status).toBe('unhealthy');
        },
        error: () => {
          // Error handling should prevent this from being called
          fail('Health check should not throw unhandled errors');
        }
      });
    });
  });
});