import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-alert-history',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.history" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Alert History</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total Alerts</p>
              <p class="text-2xl font-bold text-secondary-900">1,247</p>
            </div>
            <lucide-angular [img]="Icons.bell" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Critical Alerts</p>
              <p class="text-2xl font-bold text-secondary-900">23</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Resolved</p>
              <p class="text-2xl font-bold text-secondary-900">1,198</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Avg Resolution Time</p>
              <p class="text-2xl font-bold text-secondary-900">12m</p>
            </div>
            <lucide-angular [img]="Icons.clock" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Recent Alerts</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-error-200 bg-error-50 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.alertTriangle" [size]="16" class="text-error-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">High CPU Usage</p>
                <p class="text-sm text-secondary-600">CPU usage exceeded 85% threshold</p>
                <p class="text-xs text-secondary-500">Server: web-01 | Duration: 15 minutes</p>
              </div>
            </div>
            <div class="text-right">
              <span class="px-2 py-1 text-xs font-medium bg-error-100 text-error-800 rounded-full">Critical</span>
              <p class="text-sm text-secondary-500 mt-1">2 hours ago</p>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-success-200 bg-success-50 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.checkCircle" [size]="16" class="text-success-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Memory Usage Alert</p>
                <p class="text-sm text-secondary-600">Memory usage returned to normal levels</p>
                <p class="text-xs text-secondary-500">Server: db-01 | Resolved in: 8 minutes</p>
              </div>
            </div>
            <div class="text-right">
              <span class="px-2 py-1 text-xs font-medium bg-success-100 text-success-800 rounded-full">Resolved</span>
              <p class="text-sm text-secondary-500 mt-1">4 hours ago</p>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-warning-200 bg-warning-50 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.alertCircle" [size]="16" class="text-warning-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Disk Space Warning</p>
                <p class="text-sm text-secondary-600">Disk usage approaching 80% threshold</p>
                <p class="text-xs text-secondary-500">Server: storage-01 | Duration: 2 hours</p>
              </div>
            </div>
            <div class="text-right">
              <span class="px-2 py-1 text-xs font-medium bg-warning-100 text-warning-800 rounded-full">Warning</span>
              <p class="text-sm text-secondary-500 mt-1">6 hours ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class AlertHistoryComponent {
  Icons = Icons;
}