import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-log-analysis',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.fileText" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Log Analysis</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Log Entries</p>
              <p class="text-2xl font-bold text-secondary-900">45.2K</p>
            </div>
            <lucide-angular [img]="Icons.fileText" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Error Logs</p>
              <p class="text-2xl font-bold text-secondary-900">127</p>
            </div>
            <lucide-angular [img]="Icons.alertCircle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Warning Logs</p>
              <p class="text-2xl font-bold text-secondary-900">342</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Log Sources</p>
              <p class="text-2xl font-bold text-secondary-900">8</p>
            </div>
            <lucide-angular [img]="Icons.layers" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Recent Log Entries</h2>
        <div class="space-y-2 font-mono text-sm">
          <div class="p-3 bg-secondary-50 rounded border-l-4 border-l-success-500">
            <span class="text-secondary-500">2024-02-01 10:30:15</span>
            <span class="text-success-600 ml-2">[INFO]</span>
            <span class="ml-2">Application started successfully</span>
          </div>
          <div class="p-3 bg-secondary-50 rounded border-l-4 border-l-warning-500">
            <span class="text-secondary-500">2024-02-01 10:30:22</span>
            <span class="text-warning-600 ml-2">[WARN]</span>
            <span class="ml-2">Database connection pool is 80% full</span>
          </div>
          <div class="p-3 bg-secondary-50 rounded border-l-4 border-l-error-500">
            <span class="text-secondary-500">2024-02-01 10:30:45</span>
            <span class="text-error-600 ml-2">[ERROR]</span>
            <span class="ml-2">Failed to process user request: timeout</span>
          </div>
        </div>
      </div>
    </div>
  `
})
export class LogAnalysisComponent {
  Icons = Icons;
}