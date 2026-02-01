import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-network-overview',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.activity" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Network Overview</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Network Health</p>
              <p class="text-2xl font-bold text-secondary-900">98.5%</p>
            </div>
            <lucide-angular [img]="Icons.activity" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total Bandwidth</p>
              <p class="text-2xl font-bold text-secondary-900">1.2 Gbps</p>
            </div>
            <lucide-angular [img]="Icons.wifi" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Connections</p>
              <p class="text-2xl font-bold text-secondary-900">2,847</p>
            </div>
            <lucide-angular [img]="Icons.users" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Avg Latency</p>
              <p class="text-2xl font-bold text-secondary-900">12ms</p>
            </div>
            <lucide-angular [img]="Icons.clock" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <h2 class="text-lg font-semibold text-secondary-900 mb-4">Network Traffic</h2>
          <div class="h-48 flex items-center justify-center text-secondary-500">
            <p>Network traffic chart would be displayed here</p>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <h2 class="text-lg font-semibold text-secondary-900 mb-4">Top Protocols</h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-secondary-700">HTTP/HTTPS</span>
              <div class="flex items-center space-x-2">
                <div class="w-24 bg-secondary-200 rounded-full h-2">
                  <div class="bg-primary-500 h-2 rounded-full" style="width: 65%"></div>
                </div>
                <span class="text-sm text-secondary-600">65%</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-secondary-700">TCP</span>
              <div class="flex items-center space-x-2">
                <div class="w-24 bg-secondary-200 rounded-full h-2">
                  <div class="bg-success-500 h-2 rounded-full" style="width: 25%"></div>
                </div>
                <span class="text-sm text-secondary-600">25%</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-secondary-700">UDP</span>
              <div class="flex items-center space-x-2">
                <div class="w-24 bg-secondary-200 rounded-full h-2">
                  <div class="bg-warning-500 h-2 rounded-full" style="width: 10%"></div>
                </div>
                <span class="text-sm text-secondary-600">10%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Network Devices</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div class="p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center space-x-2">
                <lucide-angular [img]="Icons.router" [size]="16" class="text-primary-500"></lucide-angular>
                <span class="font-medium text-secondary-900">Router-01</span>
              </div>
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
            </div>
            <p class="text-sm text-secondary-600">192.168.1.1</p>
            <p class="text-xs text-secondary-500">Uptime: 99.9%</p>
          </div>
          <div class="p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center space-x-2">
                <lucide-angular [img]="Icons.server" [size]="16" class="text-primary-500"></lucide-angular>
                <span class="font-medium text-secondary-900">Switch-01</span>
              </div>
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
            </div>
            <p class="text-sm text-secondary-600">192.168.1.10</p>
            <p class="text-xs text-secondary-500">Uptime: 99.8%</p>
          </div>
          <div class="p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center space-x-2">
                <lucide-angular [img]="Icons.wifi" [size]="16" class="text-primary-500"></lucide-angular>
                <span class="font-medium text-secondary-900">AP-01</span>
              </div>
              <div class="w-3 h-3 bg-warning-500 rounded-full"></div>
            </div>
            <p class="text-sm text-secondary-600">192.168.1.20</p>
            <p class="text-xs text-secondary-500">Uptime: 95.2%</p>
          </div>
        </div>
      </div>
    </div>
  `
})
export class NetworkOverviewComponent {
  Icons = Icons;
}