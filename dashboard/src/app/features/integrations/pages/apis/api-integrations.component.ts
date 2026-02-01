import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-api-integrations',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.globe" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">API Integrations</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Add API Integration</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">API Integrations</p>
              <p class="text-2xl font-bold text-secondary-900">8</p>
            </div>
            <lucide-angular [img]="Icons.globe" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active APIs</p>
              <p class="text-2xl font-bold text-secondary-900">6</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">API Calls Today</p>
              <p class="text-2xl font-bold text-secondary-900">12.4K</p>
            </div>
            <lucide-angular [img]="Icons.activity" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Rate Limit Usage</p>
              <p class="text-2xl font-bold text-secondary-900">67%</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-warning-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">API Integrations</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.globe" [size]="20" class="text-blue-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">REST API v1</p>
                <p class="text-sm text-secondary-600">https://api.company.com/v1</p>
                <p class="text-xs text-secondary-500">Rate limit: 1000/hour | Used: 670</p>
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
                <lucide-angular [img]="Icons.globe" [size]="20" class="text-green-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">GraphQL API</p>
                <p class="text-sm text-secondary-600">https://api.company.com/graphql</p>
                <p class="text-xs text-secondary-500">Rate limit: 500/hour | Used: 234</p>
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
                <lucide-angular [img]="Icons.globe" [size]="20" class="text-purple-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Third-party Analytics API</p>
                <p class="text-sm text-secondary-600">https://analytics.external.com/api</p>
                <p class="text-xs text-secondary-500">Rate limit: 2000/hour | Used: 1456</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-warning-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Rate Limited</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.globe" [size]="20" class="text-red-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Legacy SOAP API</p>
                <p class="text-sm text-secondary-600">https://legacy.company.com/soap</p>
                <p class="text-xs text-secondary-500">Authentication failed</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-error-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Error</span>
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
export class ApiIntegrationsComponent {
  Icons = Icons;
}