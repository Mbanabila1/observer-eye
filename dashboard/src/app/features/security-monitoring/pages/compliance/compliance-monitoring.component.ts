import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-compliance-monitoring',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.checkCircle" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Compliance Monitoring</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Compliance Score</p>
              <p class="text-2xl font-bold text-secondary-900">94%</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Policy Violations</p>
              <p class="text-2xl font-bold text-secondary-900">3</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Audit Events</p>
              <p class="text-2xl font-bold text-secondary-900">1,247</p>
            </div>
            <lucide-angular [img]="Icons.fileText" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Frameworks</p>
              <p class="text-2xl font-bold text-secondary-900">5</p>
            </div>
            <lucide-angular [img]="Icons.layers" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <h2 class="text-lg font-semibold text-secondary-900 mb-4">Compliance Frameworks</h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.checkCircle" [size]="16" class="text-success-500"></lucide-angular>
                <span class="font-medium text-secondary-900">SOC 2 Type II</span>
              </div>
              <span class="px-2 py-1 text-xs font-medium bg-success-100 text-success-800 rounded-full">Compliant</span>
            </div>
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.checkCircle" [size]="16" class="text-success-500"></lucide-angular>
                <span class="font-medium text-secondary-900">GDPR</span>
              </div>
              <span class="px-2 py-1 text-xs font-medium bg-success-100 text-success-800 rounded-full">Compliant</span>
            </div>
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.alertTriangle" [size]="16" class="text-warning-500"></lucide-angular>
                <span class="font-medium text-secondary-900">HIPAA</span>
              </div>
              <span class="px-2 py-1 text-xs font-medium bg-warning-100 text-warning-800 rounded-full">Partial</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <h2 class="text-lg font-semibold text-secondary-900 mb-4">Recent Audit Events</h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.fileText" [size]="16" class="text-primary-500"></lucide-angular>
                <div>
                  <p class="font-medium text-secondary-900">Data Access Logged</p>
                  <p class="text-sm text-secondary-600">User accessed customer data</p>
                </div>
              </div>
              <span class="text-sm text-secondary-500">1 min ago</span>
            </div>
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.alertTriangle" [size]="16" class="text-warning-500"></lucide-angular>
                <div>
                  <p class="font-medium text-secondary-900">Policy Violation</p>
                  <p class="text-sm text-secondary-600">Unauthorized access attempt</p>
                </div>
              </div>
              <span class="text-sm text-secondary-500">15 min ago</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class ComplianceMonitoringComponent {
  Icons = Icons;
}