import { Component, OnInit, OnDestroy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HealthService, HealthCheckResponse, ServiceHealth, DeepSystemStatus } from './health.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-health-status',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-semibold text-gray-900">System Health Status</h2>
        <div class="flex items-center space-x-2">
          <div [class]="overallStatusClass()" class="w-3 h-3 rounded-full"></div>
          <span [class]="overallStatusTextClass()" class="text-sm font-medium">
            {{ healthData().overall.status | titlecase }}
          </span>
        </div>
      </div>

      <!-- Overall Status Card -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-sm text-gray-600">Uptime</div>
          <div class="text-lg font-semibold text-gray-900">{{ formatUptime(healthData().overall.uptime) }}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-sm text-gray-600">Version</div>
          <div class="text-lg font-semibold text-gray-900">{{ healthData().overall.version }}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-sm text-gray-600">Environment</div>
          <div class="text-lg font-semibold text-gray-900">{{ healthData().overall.environment }}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-sm text-gray-600">Last Check</div>
          <div class="text-lg font-semibold text-gray-900">{{ formatTimestamp(healthData().overall.timestamp) }}</div>
        </div>
      </div>

      <!-- Kubernetes Probes Status -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div class="text-sm text-gray-600">Readiness Probe</div>
            <div class="flex items-center space-x-2">
              <div [class]="healthData().readiness ? 'bg-green-500' : 'bg-red-500'" class="w-2 h-2 rounded-full"></div>
              <span [class]="healthData().readiness ? 'text-green-700' : 'text-red-700'" class="text-sm font-medium">
                {{ healthData().readiness ? 'Ready' : 'Not Ready' }}
              </span>
            </div>
          </div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div class="text-sm text-gray-600">Liveness Probe</div>
            <div class="flex items-center space-x-2">
              <div [class]="healthData().liveness ? 'bg-green-500' : 'bg-red-500'" class="w-2 h-2 rounded-full"></div>
              <span [class]="healthData().liveness ? 'text-green-700' : 'text-red-700'" class="text-sm font-medium">
                {{ healthData().liveness ? 'Alive' : 'Dead' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Services Status -->
      <div class="mb-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Service Dependencies</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          @for (service of healthData().services; track service.name) {
            <div class="bg-gray-50 rounded-lg p-4">
              <div class="flex items-center justify-between mb-2">
                <div class="text-sm font-medium text-gray-900">{{ service.name | titlecase }}</div>
                <div [class]="getServiceStatusClass(service.status)" class="w-2 h-2 rounded-full"></div>
              </div>
              <div class="text-xs text-gray-600 mb-1">Response: {{ service.responseTime }}ms</div>
              <div class="text-xs text-gray-600">{{ formatTimestamp(service.lastCheck) }}</div>
              @if (service.error) {
                <div class="text-xs text-red-600 mt-1 truncate" [title]="service.error">{{ service.error }}</div>
              }
            </div>
          }
        </div>
      </div>

      <!-- System Metrics -->
      <div class="mb-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">System Metrics</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-600 mb-2">Memory Usage</div>
            <div class="flex items-center space-x-2">
              <div class="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  [style.width.%]="healthData().metrics.memoryUsage"
                  [class]="getMetricBarClass(healthData().metrics.memoryUsage, 80, 90)"
                  class="h-2 rounded-full transition-all duration-300"
                ></div>
              </div>
              <span class="text-sm font-medium text-gray-900">{{ healthData().metrics.memoryUsage | number:'1.1-1' }}%</span>
            </div>
          </div>
          
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-600 mb-2">CPU Usage</div>
            <div class="flex items-center space-x-2">
              <div class="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  [style.width.%]="healthData().metrics.cpuUsage"
                  [class]="getMetricBarClass(healthData().metrics.cpuUsage, 70, 85)"
                  class="h-2 rounded-full transition-all duration-300"
                ></div>
              </div>
              <span class="text-sm font-medium text-gray-900">{{ healthData().metrics.cpuUsage | number:'1.1-1' }}%</span>
            </div>
          </div>
          
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-600 mb-2">Disk Usage</div>
            <div class="flex items-center space-x-2">
              <div class="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  [style.width.%]="healthData().metrics.diskUsage"
                  [class]="getMetricBarClass(healthData().metrics.diskUsage, 80, 95)"
                  class="h-2 rounded-full transition-all duration-300"
                ></div>
              </div>
              <span class="text-sm font-medium text-gray-900">{{ healthData().metrics.diskUsage | number:'1.1-1' }}%</span>
            </div>
          </div>
          
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-600 mb-2">Network Latency</div>
            <div class="text-lg font-semibold text-gray-900">{{ healthData().metrics.networkLatency | number:'1.1-1' }}ms</div>
          </div>
          
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-600 mb-2">Active Connections</div>
            <div class="text-lg font-semibold text-gray-900">{{ healthData().metrics.activeConnections }}</div>
          </div>
        </div>
      </div>

      <!-- Deep System Status -->
      <div class="mb-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Deep System Monitoring</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Kernel Health -->
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="flex items-center justify-between mb-3">
              <div class="text-sm font-medium text-gray-900">Kernel Health</div>
              <div [class]="getServiceStatusClass(healthData().deepSystem.kernelHealth.status)" class="w-2 h-2 rounded-full"></div>
            </div>
            <div class="space-y-2 text-xs text-gray-600">
              <div>System Calls: {{ healthData().deepSystem.kernelHealth.systemCalls | number }}</div>
              <div>Kernel Modules: {{ healthData().deepSystem.kernelHealth.kernelModules }}</div>
              <div>Memory Pressure: {{ healthData().deepSystem.kernelHealth.memoryPressure | number:'1.1-1' }}%</div>
            </div>
          </div>
          
          <!-- Payload Processing -->
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="flex items-center justify-between mb-3">
              <div class="text-sm font-medium text-gray-900">Payload Processing</div>
              <div [class]="getServiceStatusClass(healthData().deepSystem.payloadProcessing.status)" class="w-2 h-2 rounded-full"></div>
            </div>
            <div class="space-y-2 text-xs text-gray-600">
              <div>Processed: {{ healthData().deepSystem.payloadProcessing.processedPackets | number }}</div>
              <div>Dropped: {{ healthData().deepSystem.payloadProcessing.droppedPackets | number }}</div>
              <div>Latency: {{ healthData().deepSystem.payloadProcessing.processingLatency | number:'1.1-1' }}ms</div>
            </div>
          </div>
          
          <!-- Hardware Monitoring -->
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="flex items-center justify-between mb-3">
              <div class="text-sm font-medium text-gray-900">Hardware Monitoring</div>
              <div [class]="getServiceStatusClass(healthData().deepSystem.hardwareMonitoring.status)" class="w-2 h-2 rounded-full"></div>
            </div>
            <div class="space-y-2 text-xs text-gray-600">
              <div>CPU Temp: {{ healthData().deepSystem.hardwareMonitoring.cpuTemperature | number:'1.0-0' }}°C</div>
              <div>Disk Health: {{ healthData().deepSystem.hardwareMonitoring.diskHealth | titlecase }}</div>
              <div>Network Interfaces: {{ healthData().deepSystem.hardwareMonitoring.networkInterfaces }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center justify-between pt-4 border-t border-gray-200">
        <button 
          (click)="refreshHealth()"
          [disabled]="isRefreshing()"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ isRefreshing() ? 'Refreshing...' : 'Refresh Status' }}
        </button>
        
        <div class="text-sm text-gray-500">
          Auto-refresh every 30 seconds
        </div>
      </div>
    </div>
  `,
  styles: [`
    .health-status-container {
      max-height: 80vh;
      overflow-y: auto;
    }
  `]
})
export class HealthStatusComponent implements OnInit, OnDestroy {
  private subscription?: Subscription;
  
  // Reactive state
  public readonly healthData = signal<HealthCheckResponse>(this.getInitialHealthData());
  public readonly isRefreshing = signal(false);
  
  // Computed properties
  public readonly overallStatusClass = computed(() => {
    const status = this.healthData().overall.status;
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'degraded': return 'bg-yellow-500';
      case 'unhealthy': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  });
  
  public readonly overallStatusTextClass = computed(() => {
    const status = this.healthData().overall.status;
    switch (status) {
      case 'healthy': return 'text-green-700';
      case 'degraded': return 'text-yellow-700';
      case 'unhealthy': return 'text-red-700';
      default: return 'text-gray-700';
    }
  });

  constructor(private healthService: HealthService) {}

  ngOnInit(): void {
    // Subscribe to health updates
    this.subscription = this.healthService.getCurrentHealth().subscribe(health => {
      this.healthData.set(health);
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  /**
   * Force refresh health status
   */
  refreshHealth(): void {
    this.isRefreshing.set(true);
    
    this.healthService.forceHealthCheck().subscribe({
      next: (health) => {
        this.healthData.set(health);
        this.isRefreshing.set(false);
      },
      error: (error) => {
        console.error('Failed to refresh health status:', error);
        this.isRefreshing.set(false);
      }
    });
  }

  /**
   * Get service status indicator class
   */
  getServiceStatusClass(status: string): string {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'degraded': return 'bg-yellow-500';
      case 'unhealthy': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  }

  /**
   * Get metric bar color class based on thresholds
   */
  getMetricBarClass(value: number, warningThreshold: number, criticalThreshold: number): string {
    if (value >= criticalThreshold) {
      return 'bg-red-500';
    } else if (value >= warningThreshold) {
      return 'bg-yellow-500';
    } else {
      return 'bg-green-500';
    }
  }

  /**
   * Format uptime duration
   */
  formatUptime(uptimeMs: number): string {
    const seconds = Math.floor(uptimeMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days}d ${hours % 24}h`;
    } else if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  }

  /**
   * Get initial health data
   */
  private getInitialHealthData(): HealthCheckResponse {
    return {
      overall: {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: 0,
        version: '1.0.0',
        environment: 'development'
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
}