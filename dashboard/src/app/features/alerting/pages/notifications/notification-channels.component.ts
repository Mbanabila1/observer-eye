import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Icons } from '../../../../shared/utils/icons';

@Component({
  selector: 'app-notification-channels',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <lucide-angular [img]="Icons.messageSquare" [size]="24" class="text-primary-500"></lucide-angular>
          <h1 class="text-2xl font-bold text-secondary-900">Notification Channels</h1>
        </div>
        <button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2">
          <lucide-angular [img]="Icons.plus" [size]="16"></lucide-angular>
          <span>Add Channel</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Total Channels</p>
              <p class="text-2xl font-bold text-secondary-900">8</p>
            </div>
            <lucide-angular [img]="Icons.messageSquare" [size]="20" class="text-primary-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Active Channels</p>
              <p class="text-2xl font-bold text-secondary-900">6</p>
            </div>
            <lucide-angular [img]="Icons.checkCircle" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Messages Sent</p>
              <p class="text-2xl font-bold text-secondary-900">247</p>
            </div>
            <lucide-angular [img]="Icons.send" [size]="20" class="text-success-500"></lucide-angular>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-secondary-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-secondary-600">Failed Deliveries</p>
              <p class="text-2xl font-bold text-secondary-900">3</p>
            </div>
            <lucide-angular [img]="Icons.alertTriangle" [size]="20" class="text-error-500"></lucide-angular>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-secondary-200 p-6">
        <h2 class="text-lg font-semibold text-secondary-900 mb-4">Notification Channels</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div class="p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.mail" [size]="20" class="text-primary-500"></lucide-angular>
                <span class="font-medium text-secondary-900">Email</span>
              </div>
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
            </div>
            <p class="text-sm text-secondary-600 mb-2">alerts@company.com</p>
            <p class="text-xs text-secondary-500">Last used: 2 hours ago</p>
          </div>

          <div class="p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.messageCircle" [size]="20" class="text-primary-500"></lucide-angular>
                <span class="font-medium text-secondary-900">Slack</span>
              </div>
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
            </div>
            <p class="text-sm text-secondary-600 mb-2">#alerts-channel</p>
            <p class="text-xs text-secondary-500">Last used: 15 minutes ago</p>
          </div>

          <div class="p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.smartphone" [size]="20" class="text-primary-500"></lucide-angular>
                <span class="font-medium text-secondary-900">SMS</span>
              </div>
              <div class="w-3 h-3 bg-success-500 rounded-full"></div>
            </div>
            <p class="text-sm text-secondary-600 mb-2">+1 (555) 123-4567</p>
            <p class="text-xs text-secondary-500">Last used: 1 day ago</p>
          </div>

          <div class="p-4 border border-secondary-200 rounded-lg">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-3">
                <lucide-angular [img]="Icons.globe" [size]="20" class="text-primary-500"></lucide-angular>
                <span class="font-medium text-secondary-900">Webhook</span>
              </div>
              <div class="w-3 h-3 bg-secondary-300 rounded-full"></div>
            </div>
            <p class="text-sm text-secondary-600 mb-2">https://api.example.com/webhook</p>
            <p class="text-xs text-secondary-500">Disabled</p>
          </div>
        </div>
      </div>
    </div>
  `
})
export class NotificationChannelsComponent {
  Icons = Icons;
}