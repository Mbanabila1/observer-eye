import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-scheduled-reports',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.calendar" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Scheduled Reports</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Schedule Report</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Scheduled Reports</p>
              <p class="text-2xl font-bold text-secondary-900">12</p>
            </div>
            <lucide-angular [img]="Icons.calendar" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Schedules</p>
              <p class="text-2xl font-bold text-secondary-900">9</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Next Execution</p>
              <p class="text-2xl font-bold text-secondary-900">2h</p>
            </div>
            <lucide-angular [img]="Icons.clock" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Failed Executions</p>
              <p class="text-2xl font-bold text-secondary-900">1</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Scheduled Report List</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <div>
                <p class="font-medium text-secondary-900">Weekly Performance Summary</p>
                <p class="text-sm text-secondary-600">Every Monday at 9:00 AM</p>
                <p class="text-xs text-secondary-500">Recipients: management@company.com</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="px-2 py-1 text-xs font-medium bg-success-100 text-success-800 rounded-full">Active</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <div>
                <p class="font-medium text-secondary-900">Monthly Security Report</p>
                <p class="text-sm text-secondary-600">First day of each month at 8:00 AM</p>
                <p class="text-xs text-secondary-500">Recipients: security-team@company.com</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="px-2 py-1 text-xs font-medium bg-success-100 text-success-800 rounded-full">Active</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-3 h-3 bg-warning-500 rounded-full"></div>
              <div>
                <p class="font-medium text-secondary-900">Daily System Health Check</p>
                <p class="text-sm text-secondary-600">Every day at 6:00 AM</p>
                <p class="text-xs text-secondary-500">Recipients: ops-team@company.com</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="px-2 py-1 text-xs font-medium bg-warning-100 text-warning-800 rounded-full">Warning</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-3 h-3 bg-secondary-300 rounded-full"></div>
              <div>
                <p class="font-medium text-secondary-900">Quarterly Business Review</p>
                <p class="text-sm text-secondary-600">Every quarter on the 1st at 10:00 AM</p>
                <p class="text-xs text-secondary-500">Recipients: executives@company.com</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="px-2 py-1 text-xs font-medium bg-secondary-100 text-secondary-800 rounded-full">Paused</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class ScheduledReportsComponent {
  Icons = Icons;
}