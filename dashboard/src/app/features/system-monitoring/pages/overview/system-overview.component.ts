import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppLayoutComponent } from '../../../../shared/components/layout/app-layout.component';

@Component({
  selector: 'app-system-overview',
  standalone: true,
  imports: [CommonModule, AppLayoutComponent],
  template: `
    <app-layout>
      <div class="p-6">
        <div class="mb-6">
          <h1 class="text-3xl font-bold text-secondary-900">System Monitoring Overview</h1>
          <p class="text-secondary-600 mt-2">Monitor system resources, performance metrics, and health status</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <!-- CPU Usage -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">CPU Usage</p>
                <p class="text-2xl font-bold text-secondary-900">72%</p>
              </div>
              <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-blue-500 rounded"></div>
              </div>
            </div>
            <div class="mt-4">
              <div class="w-full bg-secondary-200 rounded-full h-2">
                <div class="bg-blue-500 h-2 rounded-full" style="width: 72%"></div>
              </div>
            </div>
          </div>

          <!-- Memory Usage -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Memory Usage</p>
                <p class="text-2xl font-bold text-secondary-900">8.2 GB</p>
              </div>
              <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-green-500 rounded"></div>
              </div>
            </div>
            <div class="mt-4">
              <div class="w-full bg-secondary-200 rounded-full h-2">
                <div class="bg-green-500 h-2 rounded-full" style="width: 65%"></div>
              </div>
            </div>
          </div>

          <!-- Disk Usage -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Disk Usage</p>
                <p class="text-2xl font-bold text-secondary-900">45%</p>
              </div>
              <div class="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-yellow-500 rounded"></div>
              </div>
            </div>
            <div class="mt-4">
              <div class="w-full bg-secondary-200 rounded-full h-2">
                <div class="bg-yellow-500 h-2 rounded-full" style="width: 45%"></div>
              </div>
            </div>
          </div>

          <!-- Network I/O -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Network I/O</p>
                <p class="text-2xl font-bold text-secondary-900">1.2 GB/s</p>
              </div>
              <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-purple-500 rounded"></div>
              </div>
            </div>
            <div class="mt-4">
              <p class="text-sm text-secondary-600">↑ 850 MB/s ↓ 350 MB/s</p>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- System Health Chart -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <h3 class="text-lg font-semibold text-secondary-900 mb-4">System Health Trends</h3>
            <div class="h-64 bg-secondary-50 rounded-lg flex items-center justify-center">
              <p class="text-secondary-500">System health chart will be displayed here</p>
            </div>
          </div>

          <!-- Active Processes -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <h3 class="text-lg font-semibold text-secondary-900 mb-4">Top Processes</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between py-2 border-b border-secondary-100">
                <div>
                  <p class="font-medium text-secondary-900">nginx</p>
                  <p class="text-sm text-secondary-600">PID: 1234</p>
                </div>
                <div class="text-right">
                  <p class="font-medium text-secondary-900">15.2%</p>
                  <p class="text-sm text-secondary-600">CPU</p>
                </div>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-secondary-100">
                <div>
                  <p class="font-medium text-secondary-900">postgres</p>
                  <p class="text-sm text-secondary-600">PID: 5678</p>
                </div>
                <div class="text-right">
                  <p class="font-medium text-secondary-900">12.8%</p>
                  <p class="text-sm text-secondary-600">CPU</p>
                </div>
              </div>
              <div class="flex items-center justify-between py-2">
                <div>
                  <p class="font-medium text-secondary-900">node</p>
                  <p class="text-sm text-secondary-600">PID: 9012</p>
                </div>
                <div class="text-right">
                  <p class="font-medium text-secondary-900">8.5%</p>
                  <p class="text-sm text-secondary-600">CPU</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </app-layout>
  `
})
export class SystemOverviewComponent {}