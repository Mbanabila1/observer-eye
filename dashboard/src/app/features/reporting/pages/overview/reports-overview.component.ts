import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-reports-overview',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.fileText" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Reports Overview</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Create Report</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total Reports</p>
              <p class="text-2xl font-bold text-secondary-900">47</p>
            </div>
            <lucide-angular [img]="Icons.fileText" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Scheduled Reports</p>
              <p class="text-2xl font-bold text-secondary-900">12</p>
            </div>
            <lucide-angular [img]="Icons.calendar" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Generated Today</p>
              <p class="text-2xl font-bold text-secondary-900">8</p>
            </div>
            <lucide-angular [img]="Icons.download" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Failed Reports</p>
              <p class="text-2xl font-bold text-secondary-900">1</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <h2 class="text-lg font-semibold text-secondary-900 mb-4">Report Categories</h2>
          <div class="grid grid-cols-2 gap-4">
            <div class="p-4 border border-secondary-200 rounded-lg text-center">
              <lucide-angular [img]="Icons.zap" [size]="24" class="text-primary-500 mx-auto mb-2"></lucide-angular>
              <p class="font-medium text-secondary-900">Performance</p>
              <p class="text-sm text-secondary-600">15 reports</p>
            </div>
            <div class="p-4 border border-secondary-200 rounded-lg text-center">
              <lucide-angular [img]="Icons.checkCircle" [size]="24" class="text-success-500 mx-auto mb-2"></lucide-angular>
              <p class="font-medium text-secondary-900">Availability</p>
              <p class="text-sm text-secondary-600">8 reports</p>
            </div>
            <div class="p-4 border border-secondary-200 rounded-lg text-center">
              <lucide-angular [img]="Icons.shield" [size]="24" class="text-error-500 mx-auto mb-2"></lucide-angular>
              <p class="font-medium text-secondary-900">Security</p>
              <p class="text-sm text-secondary-600">12 reports</p>
            </div>
            <div class="p-4 border border-secondary-200 rounded-lg text-center">
              <lucide-angular [img]="Icons.settings" [size]="24" class="text-warning-500 mx-auto mb-2"></lucide-angular>
              <p class="font-medium text-secondary-900">Custom</p>
              <p class="text-sm text-secondary-600">12 reports</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <h2 class="text-lg font-semibold text-secondary-900 mb-4">Recent Reports</h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.fileText" [size]="16" class="text-primary-500"></lucide-angular>
                <div>
                  <p class="font-medium text-secondary-900">Monthly Performance Report</p>
                  <p class="text-sm text-secondary-600">Generated 2 hours ago</p>
                </div>
              </div>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.download" [size]="16"></lucide-angular>
              </button>
            </div>
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.fileText" [size]="16" class="text-success-500"></lucide-angular>
                <div>
                  <p class="font-medium text-secondary-900">System Availability Report</p>
                  <p class="text-sm text-secondary-600">Generated 1 day ago</p>
                </div>
              </div>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.download" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class ReportsOverviewComponent {
  Icons = Icons;
}