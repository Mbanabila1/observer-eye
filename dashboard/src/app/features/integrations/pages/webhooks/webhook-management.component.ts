import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-webhook-management',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.webhook" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Webhook Management</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Create Webhook</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total Webhooks</p>
              <p class="text-2xl font-bold text-secondary-900">6</p>
            </div>
            <lucide-angular [img]="Icons.webhook" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Webhooks</p>
              <p class="text-2xl font-bold text-secondary-900">4</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Deliveries Today</p>
              <p class="text-2xl font-bold text-secondary-900">247</p>
            </div>
            <lucide-angular [img]="Icons.send" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Failed Deliveries</p>
              <p class="text-2xl font-bold text-secondary-900">3</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Webhook Endpoints</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.messageCircle" [size]="20" class="text-blue-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Slack Notifications</p>
                <p class="text-sm text-secondary-600">https://hooks.slack.com/services/...</p>
                <div class="flex items-center space-x-2 mt-1">
                  <span class="px-2 py-1 text-xs bg-primary-100 text-primary-800 rounded">alerts</span>
                  <span class="px-2 py-1 text-xs bg-warning-100 text-warning-800 rounded">incidents</span>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Active</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.webhook" [size]="20" class="text-green-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Custom Alert Handler</p>
                <p class="text-sm text-secondary-600">https://api.company.com/webhooks/alerts</p>
                <div class="flex items-center space-x-2 mt-1">
                  <span class="px-2 py-1 text-xs bg-error-100 text-error-800 rounded">critical</span>
                  <span class="px-2 py-1 text-xs bg-warning-100 text-warning-800 rounded">warnings</span>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Active</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.gitBranch" [size]="20" class="text-purple-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">GitHub Integration</p>
                <p class="text-sm text-secondary-600">https://api.github.com/repos/company/...</p>
                <div class="flex items-center space-x-2 mt-1">
                  <span class="px-2 py-1 text-xs bg-success-100 text-success-800 rounded">deployments</span>
                  <span class="px-2 py-1 text-xs bg-primary-100 text-primary-800 rounded">releases</span>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Active</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.webhook" [size]="20" class="text-red-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Legacy System Webhook</p>
                <p class="text-sm text-secondary-600">https://legacy.company.com/webhook</p>
                <p class="text-xs text-secondary-500">Connection timeout</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-error-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Failed</span>
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
export class WebhookManagementComponent {
  Icons = Icons;
}