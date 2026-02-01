import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-threat-detection',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.alertTriangle" [size]="24" class="text-error-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Threat Detection</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
              <p class="text-sm font-medium text-secondary-600">Blocked Attacks</p>
              <p class="text-2xl font-bold text-secondary-900">127</p>
            </div>
            <lucide-angular [img]="Icons.shield" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Malware Detected</p>
              <p class="text-2xl font-bold text-secondary-900">0</p>
            </div>
            <lucide-angular [img]="Icons.bug" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Suspicious IPs</p>
              <p class="text-2xl font-bold text-secondary-900">15</p>
            </div>
            <lucide-angular [img]="Icons.globe" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Threat Timeline</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-error-200 bg-error-50 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.alertTriangle" [size]="16" class="text-error-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">SQL Injection Attempt</p>
                <p class="text-sm text-secondary-600">Source: 203.0.113.45 | Target: /api/users</p>
              </div>
            </div>
            <span class="text-sm text-secondary-500">Active</span>
          </div>
          <div class="flex items-center justify-between p-4 border border-warning-200 bg-warning-50 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.alertCircle" [size]="16" class="text-warning-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Brute Force Attack</p>
                <p class="text-sm text-secondary-600">Source: 198.51.100.23 | Target: /login</p>
              </div>
            </div>
            <span class="text-sm text-secondary-500">Blocked</span>
          </div>
        </div>
      </div>
    </div>
  `
})
export class ThreatDetectionComponent {
  Icons = Icons;
}