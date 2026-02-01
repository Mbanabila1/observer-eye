import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-performance-reports',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.zap" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Performance Reports</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Generate Report</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Performance Reports</p>
              <p class="text-2xl font-bold text-secondary-900">15</p>
            </div>
            <lucide-angular [img]="Icons.zap" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Avg Response Time</p>
              <p class="text-2xl font-bold text-secondary-900">245ms</p>
            </div>
            <lucide-angular [img]="Icons.clock" [size]="20" class="text-success-500"></lucide-angular>
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
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Available Performance Reports</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.fileText" [size]="16" class="text-primary-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Application Performance Summary</p>
                <p class="text-sm text-secondary-600">Response times, throughput, and error rates</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-secondary-500">Last generated: 2 hours ago</span>
              <button class="px-3 py-1 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
                Generate
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.fileText" [size]="16" class="text-success-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Database Performance Report</p>
                <p class="text-sm text-secondary-600">Query performance, connection pools, and optimization recommendations</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-secondary-500">Last generated: 1 day ago</span>
              <button class="px-3 py-1 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
                Generate
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.fileText" [size]="16" class="text-warning-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Infrastructure Performance Report</p>
                <p class="text-sm text-secondary-600">CPU, memory, disk, and network performance metrics</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-secondary-500">Last generated: 3 days ago</span>
              <button class="px-3 py-1 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
                Generate
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class PerformanceReportsComponent {
  Icons = Icons;
}