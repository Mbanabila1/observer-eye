import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppLayoutComponent } from '../../../../shared/components/layout/app-layout.component';

@Component({
  selector: 'app-application-overview',
  standalone: true,
  imports: [CommonModule, AppLayoutComponent],
  template: `
    <app-layout>
      <div class="p-6">
        <div class="mb-6">
          <h1 class="text-3xl font-bold text-secondary-900">Application Performance Monitoring</h1>
          <p class="text-secondary-600 mt-2">Monitor application performance, errors, and user experience</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <!-- Response Time -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Avg Response Time</p>
                <p class="text-2xl font-bold text-secondary-900">245ms</p>
              </div>
              <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-green-500 rounded"></div>
              </div>
            </div>
            <p class="text-sm text-green-600 mt-2">↓ 12% from last hour</p>
          </div>

          <!-- Error Rate -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Error Rate</p>
                <p class="text-2xl font-bold text-secondary-900">0.8%</p>
              </div>
              <div class="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-red-500 rounded"></div>
              </div>
            </div>
            <p class="text-sm text-red-600 mt-2">↑ 0.2% from last hour</p>
          </div>

          <!-- Throughput -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Throughput</p>
                <p class="text-2xl font-bold text-secondary-900">1,247</p>
              </div>
              <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-blue-500 rounded"></div>
              </div>
            </div>
            <p class="text-sm text-secondary-600 mt-2">requests/min</p>
          </div>

          <!-- Apdex Score -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-secondary-600">Apdex Score</p>
                <p class="text-2xl font-bold text-secondary-900">0.94</p>
              </div>
              <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <div class="w-6 h-6 bg-green-500 rounded"></div>
              </div>
            </div>
            <p class="text-sm text-green-600 mt-2">Excellent</p>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Performance Trends -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <h3 class="text-lg font-semibold text-secondary-900 mb-4">Performance Trends</h3>
            <div class="h-64 bg-secondary-50 rounded-lg flex items-center justify-center">
              <p class="text-secondary-500">Performance trends chart will be displayed here</p>
            </div>
          </div>

          <!-- Recent Errors -->
          <div class="bg-white rounded-lg shadow-sm border border-secondary-200 p-6">
            <h3 class="text-lg font-semibold text-secondary-900 mb-4">Recent Errors</h3>
            <div class="space-y-3">
              <div class="flex items-start space-x-3 py-3 border-b border-secondary-100">
                <div class="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                <div class="flex-1">
                  <p class="font-medium text-secondary-900">Database Connection Timeout</p>
                  <p class="text-sm text-secondary-600">api/users endpoint - 2 minutes ago</p>
                </div>
              </div>
              <div class="flex items-start space-x-3 py-3 border-b border-secondary-100">
                <div class="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                <div class="flex-1">
                  <p class="font-medium text-secondary-900">Slow Query Warning</p>
                  <p class="text-sm text-secondary-600">api/reports endpoint - 5 minutes ago</p>
                </div>
              </div>
              <div class="flex items-start space-x-3 py-3">
                <div class="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                <div class="flex-1">
                  <p class="font-medium text-secondary-900">Memory Leak Detected</p>
                  <p class="text-sm text-secondary-600">background worker - 8 minutes ago</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </app-layout>
  `
})
export class ApplicationOverviewComponent {}