import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-external-tools',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.externalLink" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">External Tools</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Add Tool Integration</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Connected Tools</p>
              <p class="text-2xl font-bold text-secondary-900">4</p>
            </div>
            <lucide-angular [img]="Icons.externalLink" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Connections</p>
              <p class="text-2xl font-bold text-secondary-900">3</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Data Synced Today</p>
              <p class="text-2xl font-bold text-secondary-900">8.7K</p>
            </div>
            <lucide-angular [img]="Icons.refresh" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Sync Errors</p>
              <p class="text-2xl font-bold text-secondary-900">1</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Connected External Tools</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.barChart3" [size]="20" class="text-orange-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Grafana</p>
                <p class="text-sm text-secondary-600">Visualization and dashboards</p>
                <p class="text-xs text-secondary-500">Last sync: 5 minutes ago</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Connected</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.externalLink" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-red-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">PagerDuty</p>
                <p class="text-sm text-secondary-600">Incident management and alerting</p>
                <p class="text-xs text-secondary-500">Last sync: 2 minutes ago</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Connected</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.externalLink" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.messageCircle" [size]="20" class="text-blue-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Jira</p>
                <p class="text-sm text-secondary-600">Issue tracking and project management</p>
                <p class="text-xs text-secondary-500">Last sync: 15 minutes ago</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Connected</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.externalLink" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.server" [size]="20" class="text-gray-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Datadog</p>
                <p class="text-sm text-secondary-600">Infrastructure monitoring</p>
                <p class="text-xs text-secondary-500">Connection failed: API key expired</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-error-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Error</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.settings" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6 mt-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Available Integrations</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div class="p-4 border border-secondary-200 rounded-lg hover:border-primary-300 cursor-pointer">
            <div class="flex items-center space-x-3 mb-3">
              <div class="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.zap" [size]="20" class="text-yellow-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">New Relic</p>
                <p class="text-sm text-secondary-600">APM and monitoring</p>
              </div>
            </div>
            <button class="w-full px-3 py-2 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
              Connect
            </button>
          </div>

          <div class="p-4 border border-secondary-200 rounded-lg hover:border-primary-300 cursor-pointer">
            <div class="flex items-center space-x-3 mb-3">
              <div class="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.shield" [size]="20" class="text-indigo-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Splunk</p>
                <p class="text-sm text-secondary-600">Security and analytics</p>
              </div>
            </div>
            <button class="w-full px-3 py-2 bg-primary-100 text-primary-800 rounded text-sm hover:bg-primary-200">
              Connect
            </button>
          </div>

          <div class="p-4 border border-secondary-200 rounded-lg hover:border-primary-300 cursor-pointer">
            <div class="flex items-center space-x-3 mb-3">
              <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.activity" [size]="20" class="text-green-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Elastic Stack</p>
                <p class="text-sm text-secondary-600">Search and analytics</p>
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
export class ExternalToolsComponent {
  Icons = Icons;
}