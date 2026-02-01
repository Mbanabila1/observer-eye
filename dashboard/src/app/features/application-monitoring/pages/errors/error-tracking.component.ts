import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-error-tracking',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.alertCircle" [size]="24" class="text-error-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Error Tracking</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total Errors</p>
              <p class="text-2xl font-bold text-secondary-900">127</p>
            </div>
            <lucide-angular [img]="Icons.alertCircle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Critical Errors</p>
              <p class="text-2xl font-bold text-secondary-900">8</p>
            </div>
            <lucide-angular [img]="Icons.xCircle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Error Rate</p>
              <p class="text-2xl font-bold text-secondary-900">2.1%</p>
            </div>
            <lucide-angular [img]="Icons.trendingUp" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Resolved</p>
              <p class="text-2xl font-bold text-secondary-900">94</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Recent Errors</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.alertCircle" [size]="16" class="text-error-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">NullPointerException</p>
                <p class="text-sm text-secondary-600">UserService.getUserById()</p>
              </div>
            </div>
            <span class="text-sm text-secondary-500">2 min ago</span>
          </div>
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.alertTriangle" [size]="16" class="text-warning-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Database Connection Timeout</p>
                <p class="text-sm text-secondary-600">DatabaseService.connect()</p>
              </div>
            </div>
            <span class="text-sm text-secondary-500">5 min ago</span>
          </div>
        </div>
      </div>
    </div>
  `
})
export class ErrorTrackingComponent {
  Icons = Icons;
}