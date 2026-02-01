import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-escalation-policies',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.trendingUp" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Escalation Policies</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Create Policy</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total Policies</p>
              <p class="text-2xl font-bold text-secondary-900">6</p>
            </div>
            <lucide-angular [img]="Icons.layers" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Policies</p>
              <p class="text-2xl font-bold text-secondary-900">5</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Escalations Today</p>
              <p class="text-2xl font-bold text-secondary-900">3</p>
            </div>
            <lucide-angular [img]="Icons.trendingUp" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Avg Response Time</p>
              <p class="text-2xl font-bold text-secondary-900">8m</p>
            </div>
            <lucide-angular [img]="Icons.clock" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Escalation Policies</h2>
        <div class="space-y-4">
          <div class="p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-3">
                <div class="w-3 h-3 bg-success-500 rounded-full"></div>
                <h3 class="font-medium text-secondary-900">Critical System Alerts</h3>
              </div>
              <span class="px-2 py-1 text-xs font-medium bg-error-100 text-error-800 rounded-full">Critical</span>
            </div>
            <p class="text-sm text-secondary-600 mb-3">Escalation policy for critical system failures and outages</p>
            <div class="space-y-2">
              <div class="flex items-center space-x-3 text-sm">
                <span class="w-6 h-6 bg-primary-100 text-primary-800 rounded-full flex items-center justify-center text-xs font-medium">1</span>
                <span class="text-secondary-600">Notify on-call engineer immediately</span>
              </div>
              <div class="flex items-center space-x-3 text-sm">
                <span class="w-6 h-6 bg-primary-100 text-primary-800 rounded-full flex items-center justify-center text-xs font-medium">2</span>
                <span class="text-secondary-600">After 5 minutes: Escalate to team lead</span>
              </div>
              <div class="flex items-center space-x-3 text-sm">
                <span class="w-6 h-6 bg-primary-100 text-primary-800 rounded-full flex items-center justify-center text-xs font-medium">3</span>
                <span class="text-secondary-600">After 15 minutes: Notify management</span>
              </div>
            </div>
          </div>

          <div class="p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-3">
                <div class="w-3 h-3 bg-success-500 rounded-full"></div>
                <h3 class="font-medium text-secondary-900">Performance Degradation</h3>
              </div>
              <span class="px-2 py-1 text-xs font-medium bg-warning-100 text-warning-800 rounded-full">Warning</span>
            </div>
            <p class="text-sm text-secondary-600 mb-3">Escalation policy for performance issues and resource constraints</p>
            <div class="space-y-2">
              <div class="flex items-center space-x-3 text-sm">
                <span class="w-6 h-6 bg-primary-100 text-primary-800 rounded-full flex items-center justify-center text-xs font-medium">1</span>
                <span class="text-secondary-600">Notify DevOps team</span>
              </div>
              <div class="flex items-center space-x-3 text-sm">
                <span class="w-6 h-6 bg-primary-100 text-primary-800 rounded-full flex items-center justify-center text-xs font-medium">2</span>
                <span class="text-secondary-600">After 10 minutes: Escalate to senior engineer</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class EscalationPoliciesComponent {
  Icons = Icons;
}