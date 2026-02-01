import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-custom-reports',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.settings" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Custom Reports</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Create Custom Report</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Custom Reports</p>
              <p class="text-2xl font-bold text-secondary-900">12</p>
            </div>
            <lucide-angular [img]="Icons.settings" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Templates</p>
              <p class="text-2xl font-bold text-secondary-900">8</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Generated This Month</p>
              <p class="text-2xl font-bold text-secondary-900">47</p>
            </div>
            <lucide-angular [img]="Icons.download" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Shared Reports</p>
              <p class="text-2xl font-bold text-secondary-900">5</p>
            </div>
            <lucide-angular [img]="Icons.share" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Custom Report Templates</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.fileText" [size]="16" class="text-primary-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Executive Dashboard Summary</p>
                <p class="text-sm text-secondary-600">High-level metrics and KPIs for executive reporting</p>
                <div class="flex items-center space-x-2 mt-1">
                  <span class="px-2 py-1 text-xs bg-primary-100 text-primary-800 rounded">Performance</span>
                  <span class="px-2 py-1 text-xs bg-success-100 text-success-800 rounded">Availability</span>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.edit" [size]="16"></lucide-angular>
              </button>
              <button class="px-3 py-1 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
                Generate
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.fileText" [size]="16" class="text-success-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Technical Operations Report</p>
                <p class="text-sm text-secondary-600">Detailed technical metrics for operations teams</p>
                <div class="flex items-center space-x-2 mt-1">
                  <span class="px-2 py-1 text-xs bg-warning-100 text-warning-800 rounded">System</span>
                  <span class="px-2 py-1 text-xs bg-error-100 text-error-800 rounded">Security</span>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.edit" [size]="16"></lucide-angular>
              </button>
              <button class="px-3 py-1 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
                Generate
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.fileText" [size]="16" class="text-warning-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Customer Impact Analysis</p>
                <p class="text-sm text-secondary-600">Customer-facing metrics and service impact analysis</p>
                <div class="flex items-center space-x-2 mt-1">
                  <span class="px-2 py-1 text-xs bg-primary-100 text-primary-800 rounded">Performance</span>
                  <span class="px-2 py-1 text-xs bg-success-100 text-success-800 rounded">Availability</span>
                  <span class="px-2 py-1 text-xs bg-secondary-100 text-secondary-800 rounded">Network</span>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.edit" [size]="16"></lucide-angular>
              </button>
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
export class CustomReportsComponent {
  Icons = Icons;
}