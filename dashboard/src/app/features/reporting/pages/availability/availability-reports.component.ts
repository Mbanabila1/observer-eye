import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-availability-reports',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.checkCircle" [size]="24" class="text-success-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Availability Reports</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Generate Report</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">System Uptime</p>
              <p class="text-2xl font-bold text-secondary-900">99.9%</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Service Availability</p>
              <p class="text-2xl font-bold text-secondary-900">99.8%</p>
            </div>
            <lucide-angular [img]="Icons.server" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Downtime Events</p>
              <p class="text-2xl font-bold text-secondary-900">3</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">MTTR</p>
              <p class="text-2xl font-bold text-secondary-900">12m</p>
            </div>
            <lucide-angular [img]="Icons.clock" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Available Availability Reports</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.fileText" [size]="16" class="text-success-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Monthly Uptime Report</p>
                <p class="text-sm text-secondary-600">System availability, downtime analysis, and SLA compliance</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-secondary-500">Last generated: 1 day ago</span>
              <button class="px-3 py-1 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
                Generate
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.fileText" [size]="16" class="text-primary-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Service Level Agreement Report</p>
                <p class="text-sm text-secondary-600">SLA compliance metrics and breach analysis</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-secondary-500">Last generated: 2 days ago</span>
              <button class="px-3 py-1 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
                Generate
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <lucide-angular [img]="Icons.fileText" [size]="16" class="text-warning-500"></lucide-angular>
              <div>
                <p class="font-medium text-secondary-900">Incident Analysis Report</p>
                <p class="text-sm text-secondary-600">Root cause analysis and recovery time metrics</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-secondary-500">Last generated: 1 week ago</span>
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
export class AvailabilityReportsComponent {
  Icons = Icons;
}