import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-access-monitoring',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.userCheck" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Access Monitoring</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Sessions</p>
              <p class="text-2xl font-bold text-secondary-900">247</p>
            </div>
            <lucide-angular [img]="Icons.users" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Failed Logins</p>
              <p class="text-2xl font-bold text-secondary-900">47</p>
            </div>
            <lucide-angular [img]="Icons.userX" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Privileged Access</p>
              <p class="text-2xl font-bold text-secondary-900">12</p>
            </div>
            <lucide-angular [img]="Icons.crown" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Suspicious Activity</p>
              <p class="text-2xl font-bold text-secondary-900">3</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Recent Access Events</h2>
        <div class="space-y-3">
          <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.userCheck" [size]="16" class="text-success-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Successful Login</p>
                <p class="text-sm text-secondary-600">admin@example.com from 192.168.1.100</p>
              </div>
            </div>
            <span class="text-sm text-secondary-500">2 min ago</span>
          </div>
          <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.userX" [size]="16" class="text-error-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Failed Login Attempt</p>
                <p class="text-sm text-secondary-600">unknown@example.com from 203.0.113.45</p>
              </div>
            </div>
            <span class="text-sm text-secondary-500">5 min ago</span>
          </div>
          <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.crown" [size]="16" class="text-warning-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Privileged Access</p>
                <p class="text-sm text-secondary-600">root@example.com accessed system settings</p>
              </div>
            </div>
            <span class="text-sm text-secondary-500">10 min ago</span>
          </div>
        </div>
      </div>
    </div>
  `
})
export class AccessMonitoringComponent {
  Icons = Icons;
}