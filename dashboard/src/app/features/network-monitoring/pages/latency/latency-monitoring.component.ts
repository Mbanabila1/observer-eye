import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-latency-monitoring',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.clock" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Latency Monitoring</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Average Latency</p>
              <p class="text-2xl font-bold text-secondary-900">12ms</p>
            </div>
            <lucide-angular [img]="Icons.clock" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Peak Latency</p>
              <p class="text-2xl font-bold text-secondary-900">45ms</p>
            </div>
            <lucide-angular [img]="Icons.trendingUp" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Min Latency</p>
              <p class="text-2xl font-bold text-secondary-900">3ms</p>
            </div>
            <lucide-angular [img]="Icons.trendingDown" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Jitter</p>
              <p class="text-2xl font-bold text-secondary-900">2.1ms</p>
            </div>
            <lucide-angular [img]="Icons.activity" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Latency Distribution</h2>
        <div class="h-64 flex items-center justify-center text-secondary-500">
          <p>Latency distribution chart would be displayed here</p>
        </div>
      </div>
    </div>
  `
})
export class LatencyMonitoringComponent {
  Icons = Icons;
}