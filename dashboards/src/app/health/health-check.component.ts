import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HealthStatusComponent } from './health-status.component';
import { HealthService } from './health.service';

@Component({
  selector: 'app-health-check',
  standalone: true,
  imports: [CommonModule, HealthStatusComponent],
  template: `
    <div class="min-h-screen bg-gray-50 py-8">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="mb-8">
          <h1 class="text-3xl font-bold text-gray-900">System Health Dashboard</h1>
          <p class="mt-2 text-gray-600">
            Monitor the health and performance of the Observer-Eye observability platform
          </p>
        </div>
        
        <app-health-status></app-health-status>
        
        <!-- Additional Health Information -->
        <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Health Check Endpoints -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Health Check Endpoints</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div class="font-medium text-gray-900">/health</div>
                  <div class="text-sm text-gray-600">General health status</div>
                </div>
                <a 
                  href="/health" 
                  target="_blank"
                  class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  Test →
                </a>
              </div>
              
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div class="font-medium text-gray-900">/health/ready</div>
                  <div class="text-sm text-gray-600">Kubernetes readiness probe</div>
                </div>
                <a 
                  href="/health/ready" 
                  target="_blank"
                  class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  Test →
                </a>
              </div>
              
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div class="font-medium text-gray-900">/health/live</div>
                  <div class="text-sm text-gray-600">Kubernetes liveness probe</div>
                </div>
                <a 
                  href="/health/live" 
                  target="_blank"
                  class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  Test →
                </a>
              </div>
              
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div class="font-medium text-gray-900">/metrics</div>
                  <div class="text-sm text-gray-600">Prometheus metrics</div>
                </div>
                <a 
                  href="/metrics" 
                  target="_blank"
                  class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  Test →
                </a>
              </div>
              
              <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div class="font-medium text-gray-900">/health/deep-system</div>
                  <div class="text-sm text-gray-600">Deep system monitoring</div>
                </div>
                <a 
                  href="/health/deep-system" 
                  target="_blank"
                  class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  Test →
                </a>
              </div>
            </div>
          </div>
          
          <!-- Kubernetes Configuration -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Kubernetes Configuration</h3>
            <div class="space-y-4">
              <div>
                <h4 class="font-medium text-gray-900 mb-2">Readiness Probe</h4>
                <pre class="bg-gray-50 p-3 rounded-lg text-sm overflow-x-auto"><code>readinessProbe:
  httpGet:
    path: /health/ready
    port: 80
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3</code></pre>
              </div>
              
              <div>
                <h4 class="font-medium text-gray-900 mb-2">Liveness Probe</h4>
                <pre class="bg-gray-50 p-3 rounded-lg text-sm overflow-x-auto"><code>livenessProbe:
  httpGet:
    path: /health/live
    port: 80
  initialDelaySeconds: 30
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 3</code></pre>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Docker Health Check -->
        <div class="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Docker Health Check Configuration</h3>
          <pre class="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto"><code>HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:80/health || exit 1</code></pre>
          
          <div class="mt-4 p-4 bg-blue-50 rounded-lg">
            <div class="flex items-start">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="ml-3">
                <h4 class="text-sm font-medium text-blue-800">Health Check Features</h4>
                <div class="mt-2 text-sm text-blue-700">
                  <ul class="list-disc list-inside space-y-1">
                    <li>Deep system status indicators including kernel health and payload processing</li>
                    <li>Kubernetes-compatible readiness and liveness probes</li>
                    <li>Prometheus metrics endpoint for monitoring integration</li>
                    <li>Real-time service dependency checking</li>
                    <li>Hardware-level monitoring with eBPF integration</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class HealthCheckComponent implements OnInit {
  
  constructor(private healthService: HealthService) {}
  
  ngOnInit(): void {
    // Component initialization is handled by the health service
  }
}