import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-alert-rules',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.settings" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Alert Rules</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Create Rule</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total Rules</p>
              <p class="text-2xl font-bold text-secondary-900">24</p>
            </div>
            <lucide-angular [img]="Icons.settings" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Rules</p>
              <p class="text-2xl font-bold text-secondary-900">18</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Triggered Today</p>
              <p class="text-2xl font-bold text-secondary-900">7</p>
            </div>
            <lucide-angular [img]="Icons.bell" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Critical Rules</p>
              <p class="text-2xl font-bold text-secondary-900">5</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Alert Rules</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <div>
                <p class="font-medium text-secondary-900">High CPU Usage</p>
                <p class="text-sm text-secondary-600">Triggers when CPU usage > 80% for 5 minutes</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="px-2 py-1 text-xs font-medium bg-error-100 text-error-800 rounded-full">Critical</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <div>
                <p class="font-medium text-secondary-900">Memory Usage Alert</p>
                <p class="text-sm text-secondary-600">Triggers when memory usage > 90%</p>
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
                <p class="font-medium text-secondary-900">Disk Space Warning</p>
                <p class="text-sm text-secondary-600">Triggers when disk usage > 85%</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="px-2 py-1 text-xs font-medium bg-secondary-100 text-secondary-800 rounded-full">Disabled</span>
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
export class AlertRulesComponent {
  Icons = Icons;
}