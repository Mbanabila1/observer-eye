import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-network-topology',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.share2" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Network Topology</h1>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total Nodes</p>
              <p class="text-2xl font-bold text-secondary-900">47</p>
            </div>
            <lucide-angular [img]="Icons.server" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Connections</p>
              <p class="text-2xl font-bold text-secondary-900">124</p>
            </div>
            <lucide-angular [img]="Icons.link" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Network Segments</p>
              <p class="text-2xl font-bold text-secondary-900">8</p>
            </div>
            <lucide-angular [img]="Icons.layers" [size]="20" class="text-primary-500"></lucide-angular>
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
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Network Topology Map</h2>
        <div class="h-96 flex items-center justify-center text-secondary-500 border-2 border-dashed border-secondary-200 rounded-lg">
          <div class="text-center">
            <lucide-angular [img]="Icons.share2" [size]="48" class="text-secondary-400 mx-auto mb-2"></lucide-angular>
            <p>Interactive network topology visualization would be displayed here</p>
            <p class="text-sm mt-1">Showing device connections, network paths, and status indicators</p>
          </div>
        </div>
      </div>
    </div>
  `
})
export class NetworkTopologyComponent {
  Icons = Icons;
}