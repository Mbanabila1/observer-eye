import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppLayoutComponent } from '../../../../shared/components/layout/app-layout.component';

@Component({
  selector: 'app-alerts-overview',
  standalone: true,
  imports: [CommonModule, AppLayoutComponent],
  template: `
    <app-layout>
      <div class="p-6">
        <div class="mb-6">
          <h1 class="text-3xl font-bold text-secondary-900">Alerting & Notifications</h1>
          <p class="text-secondary-600 mt-2">Manage alert rules, notification channels, and escalation policies</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <!-- Active Alerts -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Active Alerts</p>
                <p class="text-2xl font-bold text-secondary-900">7</p>
              </div>
              <div class="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-red-500 rounded"></div>
              </div>
            </div>
            <p class="text-sm text-red-600 mt-2">3 critical, 4 warning</p>
          </div>

          <!-- Alert Rules -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Alert Rules</p>
                <p class="text-2xl font-bold text-secondary-900">24</p>
              </div>
              <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-blue-500 rounded"></div>
              </div>
            </div>
            <p class="text-sm text-secondary-600 mt-2">22 enabled, 2 disabled</p>
          </div>

          <!-- Notification Channels -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Channels</p>
                <p class="text-2xl font-bold text-secondary-900">8</p>
              </div>
              <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-green-500 rounded"></div>
              </div>
            </div>
            <p class="text-sm text-secondary-600 mt-2">Email, Slack, PagerDuty</p>
          </div>

          <!-- Response Time -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Avg Response Time</p>
                <p class="text-2xl font-bold text-secondary-900">3.2m</p>
              </div>
              <div class="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-yellow-500 rounded"></div>
              </div>
            </div>
            <p class="text-sm text-secondary-600 mt-2">Last 24 hours</p>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Recent Alerts -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <h3 class="text-lg font-semibold text-secondary-900 mb-4">Recent Alerts</h3>
            <div class="space-y-4">
              <div class="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                <div class="w-3 h-3 bg-red-500 rounded-full mt-1"></div>
                <div class="flex-1">
                  <p class="font-medium text-secondary-900">High CPU Usage</p>
                  <p class="text-sm text-secondary-600">Server: web-01 - CPU usage above 90%</p>
                  <p class="text-xs text-secondary-500 mt-1">2 minutes ago</p>
                </div>
                <span class="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">Critical</span>
              </div>
              <div class="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                <div class="w-3 h-3 bg-yellow-500 rounded-full mt-1"></div>
                <div class="flex-1">
                  <p class="font-medium text-secondary-900">Disk Space Low</p>
                  <p class="text-sm text-secondary-600">Server: db-01 - Disk usage above 85%</p>
                  <p class="text-xs text-secondary-500 mt-1">5 minutes ago</p>
                </div>
                <span class="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">Warning</span>
              </div>
              <div class="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                <div class="w-3 h-3 bg-blue-500 rounded-full mt-1"></div>
                <div class="flex-1">
                  <p class="font-medium text-secondary-900">Service Restart</p>
                  <p class="text-sm text-secondary-600">Service: nginx - Automatically restarted</p>
                  <p class="text-xs text-secondary-500 mt-1">8 minutes ago</p>
                </div>
                <span class="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">Info</span>
              </div>
            </div>
          </div>

          <!-- Alert Statistics -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <h3 class="text-lg font-semibold text-secondary-900 mb-4">Alert Statistics (24h)</h3>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-4 h-4 bg-red-500 rounded"></div>
                  <span class="text-secondary-900">Critical</span>
                </div>
                <div class="text-right">
                  <span class="font-medium text-secondary-900">12</span>
                  <p class="text-xs text-secondary-600">+3 from yesterday</p>
                </div>
              </div>
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-4 h-4 bg-yellow-500 rounded"></div>
                  <span class="text-secondary-900">Warning</span>
                </div>
                <div class="text-right">
                  <span class="font-medium text-secondary-900">28</span>
                  <p class="text-xs text-secondary-600">-5 from yesterday</p>
                </div>
              </div>
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-4 h-4 bg-blue-500 rounded"></div>
                  <span class="text-secondary-900">Info</span>
                </div>
                <div class="text-right">
                  <span class="font-medium text-secondary-900">45</span>
                  <p class="text-xs text-secondary-600">+12 from yesterday</p>
                </div>
              </div>
              <div class="flex items-center justify-between pt-4 border-t border-secondary-200">
                <span class="text-secondary-900 font-medium">Total Resolved</span>
                <div class="text-right">
                  <span class="font-medium text-green-600">67</span>
                  <p class="text-xs text-secondary-600">94% resolution rate</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </app-layout>
  `
})
export class AlertsOverviewComponent {}