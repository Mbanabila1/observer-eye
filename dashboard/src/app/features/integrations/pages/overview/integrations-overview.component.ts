import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-integrations-overview',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.share" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Integrations Overview</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Add Integration</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total Integrations</p>
              <p class="text-2xl font-bold text-secondary-900">24</p>
            </div>
            <lucide-angular [img]="Icons.share" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Integrations</p>
              <p class="text-2xl font-bold text-secondary-900">18</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Data Sources</p>
              <p class="text-2xl font-bold text-secondary-900">12</p>
            </div>
            <lucide-angular [img]="Icons.database" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Failed Connections</p>
              <p class="text-2xl font-bold text-secondary-900">2</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <h2 class="text-lg font-semibold text-secondary-900 mb-4">Integration Categories</h2>
          <div class="grid grid-cols-2 gap-4">
            <div class="p-4 border border-secondary-200 rounded-lg text-center">
              <lucide-angular [img]="Icons.database" [size]="24" class="text-primary-500 mx-auto mb-2"></lucide-angular>
              <p class="font-medium text-secondary-900">Data Sources</p>
              <p class="text-sm text-secondary-600">12 integrations</p>
            </div>
            <div class="p-4 border border-secondary-200 rounded-lg text-center">
              <lucide-angular [img]="Icons.globe" [size]="24" class="text-success-500 mx-auto mb-2"></lucide-angular>
              <p class="font-medium text-secondary-900">APIs</p>
              <p class="text-sm text-secondary-600">8 integrations</p>
            </div>
            <div class="p-4 border border-secondary-200 rounded-lg text-center">
              <lucide-angular [img]="Icons.webhook" [size]="24" class="text-warning-500 mx-auto mb-2"></lucide-angular>
              <p class="font-medium text-secondary-900">Webhooks</p>
              <p class="text-sm text-secondary-600">6 integrations</p>
            </div>
            <div class="p-4 border border-secondary-200 rounded-lg text-center">
              <lucide-angular [img]="Icons.externalLink" [size]="24" class="text-error-500 mx-auto mb-2"></lucide-angular>
              <p class="font-medium text-secondary-900">External Tools</p>
              <p class="text-sm text-secondary-600">4 integrations</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <h2 class="text-lg font-semibold text-secondary-900 mb-4">Recent Activity</h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.checkCircle" [size]="16" class="text-success-500"></lucide-angular>
                <div>
                  <p class="font-medium text-secondary-900">Prometheus Connected</p>
                  <p class="text-sm text-secondary-600">Data source integration successful</p>
                </div>
              </div>
              <span class="text-sm text-secondary-500">2 hours ago</span>
            </div>
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.alertTriangle" [size]="16" class="text-error-500"></lucide-angular>
                <div>
                  <p class="font-medium text-secondary-900">Grafana Connection Failed</p>
                  <p class="text-sm text-secondary-600">Authentication error</p>
                </div>
              </div>
              <span class="text-sm text-secondary-500">4 hours ago</span>
            </div>
            <div class="flex items-center justify-between p-3 border border-secondary-200 rounded-lg">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.webhook" [size]="16" class="text-primary-500"></lucide-angular>
                <div>
                  <p class="font-medium text-secondary-900">Slack Webhook Updated</p>
                  <p class="text-sm text-secondary-600">Notification channel configured</p>
                </div>
              </div>
              <span class="text-sm text-secondary-500">1 day ago</span>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Popular Integrations</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div class="p-4 border border-secondary-200 rounded-lg hover:border-primary-300 cursor-pointer">
            <div class="flex items-center space-x-3 mb-3">
              <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.database" [size]="20" class="text-orange-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Prometheus</p>
                <p class="text-sm text-secondary-600">Metrics collection</p>
              </div>
            </div>
            <button class="w-full px-3 py-2 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
              Connect
            </button>
          </div>

          <div class="p-4 border border-secondary-200 rounded-lg hover:border-primary-300 cursor-pointer">
            <div class="flex items-center space-x-3 mb-3">
              <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.messageCircle" [size]="20" class="text-blue-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Slack</p>
                <p class="text-sm text-secondary-600">Team notifications</p>
              </div>
            </div>
            <button class="w-full px-3 py-2 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
              Connect
            </button>
          </div>

          <div class="p-4 border border-secondary-200 rounded-lg hover:border-primary-300 cursor-pointer">
            <div class="flex items-center space-x-3 mb-3">
              <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.gitBranch" [size]="20" class="text-purple-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">GitHub</p>
                <p class="text-sm text-secondary-600">Code repository</p>
              </div>
            </div>
            <button class="w-full px-3 py-2 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
              Connect
            </button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class IntegrationsOverviewComponent {
  Icons = Icons;
}