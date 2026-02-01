import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-performance-monitoring',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.zap" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Performance Monitoring</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Response Time</p>
              <p class="text-2xl font-bold text-secondary-900">245ms</p>
            </div>
            <lucide-angular [img]="Icons.clock" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Throughput</p>
              <p class="text-2xl font-bold text-secondary-900">1.2K req/s</p>
            </div>
            <lucide-angular [img]="Icons.activity" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Error Rate</p>
              <p class="text-2xl font-bold text-secondary-900">0.3%</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Apdex Score</p>
              <p class="text-2xl font-bold text-secondary-900">0.94</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Application Performance Metrics</h2>
        <div class="h-64 flex items-center justify-center text-secondary-500">
          <p>Performance metrics chart would be displayed here</p>
        </div>
      </div>
    </div>
  `
})
export class PerformanceMonitoringComponent {
  Icons = Icons;
}