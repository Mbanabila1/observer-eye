import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-monitoring-overview',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-4">System Monitoring</h1>
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Monitoring Overview</h2>
        <p class="text-gray-600 mb-4">Real-time system performance and health monitoring will be displayed here.</p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-blue-50 p-4 rounded-lg">
            <h3 class="font-medium text-blue-900">System Health</h3>
            <p class="text-2xl font-bold text-blue-600">95%</p>
          </div>
          <div class="bg-green-50 p-4 rounded-lg">
            <h3 class="font-medium text-green-900">CPU Usage</h3>
            <p class="text-2xl font-bold text-green-600">45%</p>
          </div>
          <div class="bg-yellow-50 p-4 rounded-lg">
            <h3 class="font-medium text-yellow-900">Memory Usage</h3>
            <p class="text-2xl font-bold text-yellow-600">68%</p>
          </div>
        </div>
      </div>
    </div>
  `
})
export class MonitoringOverviewComponent {}