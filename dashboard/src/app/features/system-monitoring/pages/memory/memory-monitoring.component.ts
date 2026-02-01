import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-memory-monitoring',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.hardDrive" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Memory Monitoring</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Memory Usage</p>
              <p class="text-2xl font-bold text-secondary-900">68.4%</p>
            </div>
            <lucide-angular [img]="Icons.hardDrive" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total RAM</p>
              <p class="text-2xl font-bold text-secondary-900">16 GB</p>
            </div>
            <lucide-angular [img]="Icons.database" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Available</p>
              <p class="text-2xl font-bold text-secondary-900">5.1 GB</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Swap Usage</p>
              <p class="text-2xl font-bold text-secondary-900">12.3%</p>
            </div>
            <lucide-angular [img]="Icons.shuffle" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Memory Usage Breakdown</h2>
        <div class="h-64 flex items-center justify-center text-secondary-500">
          <p>Memory usage chart would be displayed here</p>
        </div>
      </div>
    </div>
  `
})
export class MemoryMonitoringComponent {
  Icons = Icons;
}