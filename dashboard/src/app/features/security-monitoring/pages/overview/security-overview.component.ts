import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-security-overview',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.shield" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Security Overview</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Security Score</p>
              <p class="text-2xl font-bold text-secondary-900">87/100</p>
            </div>
            <lucide-angular [img]="Icons.shield" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Threats</p>
              <p class="text-2xl font-bold text-secondary-900">3</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Vulnerabilities</p>
              <p class="text-2xl font-bold text-secondary-900">12</p>
            </div>
            <lucide-angular [img]="Icons.bug" [size]="20" class="text-warning-500"></lucide-angular>
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
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <h2 class="text-lg font-semibold text-secondary-900 mb-4">Recent Security Events</h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.alertTriangle" [size]="16" class="text-error-500"></lucide-angular>
                <div>
                  <p class="font-medium text-secondary-900">Suspicious Login Attempt</p>
                  <p class="text-sm text-secondary-600">IP: 192.168.1.100</p>
                </div>
              </div>
              <span class="text-sm text-secondary-500">2 min ago</span>
            </div>
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.shield" [size]="16" class="text-success-500"></lucide-angular>
                <div>
                  <p class="font-medium text-secondary-900">Security Scan Completed</p>
                  <p class="text-sm text-secondary-600">No new vulnerabilities found</p>
                </div>
              </div>
              <span class="text-sm text-secondary-500">1 hour ago</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <h2 class="text-lg font-semibold text-secondary-900 mb-4">Security Metrics</h2>
          <div class="h-48 flex items-center justify-center text-secondary-500">
            <p>Security metrics chart would be displayed here</p>
          </div>
        </div>
      </div>
    </div>
  `
})
export class SecurityOverviewComponent {
  Icons = Icons;
}