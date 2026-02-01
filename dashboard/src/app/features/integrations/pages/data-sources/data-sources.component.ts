import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-data-sources',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.database" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Data Sources</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Add Data Source</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Connected Sources</p>
              <p class="text-2xl font-bold text-secondary-900">12</p>
            </div>
            <lucide-angular [img]="Icons.database" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Connections</p>
              <p class="text-2xl font-bold text-secondary-900">10</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Data Points/Hour</p>
              <p class="text-2xl font-bold text-secondary-900">45.2K</p>
            </div>
            <lucide-angular [img]="Icons.activity" [size]="20" class="text-success-500"></lucide-angular>
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

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Connected Data Sources</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.database" [size]="20" class="text-orange-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Prometheus</p>
                <p class="text-sm text-secondary-600">http://prometheus.local:9090</p>
                <p class="text-xs text-secondary-500">Last sync: 2 minutes ago</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Connected</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.database" [size]="20" class="text-blue-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">InfluxDB</p>
                <p class="text-sm text-secondary-600">influxdb.company.com:8086</p>
                <p class="text-xs text-secondary-500">Last sync: 5 minutes ago</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Connected</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.database" [size]="20" class="text-green-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">Elasticsearch</p>
                <p class="text-sm text-secondary-600">elasticsearch.company.com:9200</p>
                <p class="text-xs text-secondary-500">Last sync: 1 hour ago</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-error-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Connection Failed</span>
              <button class="p-2 text-secondary-400 hover:text-secondary-600">
                <lucide-angular [img]="Icons.moreHorizontal" [size]="16"></lucide-angular>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.database" [size]="20" class="text-purple-600"></lucide-angular>
              </div>
              <div>
                <p class="font-medium text-secondary-900">PostgreSQL</p>
                <p class="text-sm text-secondary-600">postgres.company.com:5432</p>
                <p class="text-xs text-secondary-500">Last sync: 10 minutes ago</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
              <span class="text-sm text-secondary-600">Connected</span>
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
export class DataSourcesComponent {
  Icons = Icons;
}