import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { LucideAngularModule } from 'lucide-angular';
import { MainNavigationComponent } from '../navigation/main-navigation.component';
import { NotificationService, UINotification } from '../../../core/services/notification.service';
import { WebSocketService } from '../../../core/services/websocket.service';
import { StateService } from '../../../core/services/state.service';
import { Icons } from '../../utils/icons';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    LucideAngularModule,
    MainNavigationComponent
  ],
  template: `
    <div class="app-layout min-h-screen bg-secondary-50">
      <!-- Main Navigation -->
      <app-main-navigation></app-main-navigation>

      <!-- Main Content Area -->
      <main class="main-content">
        <router-outlet></router-outlet>
      </main>

      <!-- Global Notifications -->
      <div class="notification-container fixed top-4 right-4 z-50 space-y-2">
        <div
          *ngFor="let notification of notifications; trackBy: trackNotification"
          class="notification-item max-w-sm bg-white rounded-lg shadow-lg border-l-4 p-4 transform transition-all duration-300 ease-in-out"
          [class]="getNotificationClasses(notification)"
          [@slideIn]
        >
          <div class="flex items-start space-x-3">
            <!-- Icon -->
            <div class="flex-shrink-0">
              <lucide-angular
                [img]="getNotificationIcon(notification.type)"
                [size]="20"
                [class]="getNotificationIconClasses(notification.type)"
              ></lucide-angular>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-medium text-secondary-900">{{ notification.title }}</h4>
              <p class="text-sm text-secondary-600 mt-1">{{ notification.message }}</p>
            </div>

            <!-- Close Button -->
            <button
              type="button"
              class="flex-shrink-0 text-secondary-400 hover:text-secondary-600 transition-colors"
              (click)="dismissNotification(notification.id)"
            >
              <lucide-angular [img]="Icons.x" [size]="16"></lucide-angular>
            </button>
          </div>

          <!-- Progress Bar (for timed notifications) -->
          <div
            *ngIf="notification.duration && notification.duration > 0"
            class="mt-3 w-full bg-secondary-200 rounded-full h-1"
          >
            <div
              class="h-1 rounded-full transition-all duration-100 ease-linear"
              [class]="getProgressBarClasses(notification.type)"
              [style.width.%]="getNotificationProgress(notification)"
            ></div>
          </div>
        </div>
      </div>

      <!-- Connection Status Indicator -->
      <div
        *ngIf="!isConnected"
        class="connection-status fixed bottom-4 left-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2"
      >
        <lucide-angular [img]="Icons.wifiOff" [size]="16"></lucide-angular>
        <span class="text-sm font-medium">Connection Lost</span>
        <div class="animate-pulse w-2 h-2 bg-white rounded-full"></div>
      </div>

      <!-- Loading Overlay -->
      <div
        *ngIf="globalLoading"
        class="loading-overlay fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      >
        <div class="bg-white rounded-lg p-6 flex items-center space-x-4">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
          <span class="text-secondary-900 font-medium">{{ loadingMessage }}</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .main-content {
      min-height: calc(100vh - 120px); /* Adjust based on navigation height */
    }

    .notification-item {
      animation: slideIn 0.3s ease-out;
    }

    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    .notification-item.removing {
      animation: slideOut 0.3s ease-in forwards;
    }

    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }
  `]
})
export class AppLayoutComponent implements OnInit, OnDestroy {
  notifications: (UINotification & { startTime?: number; progress?: number })[] = [];
  isConnected = true;
  globalLoading = false;
  loadingMessage = 'Loading...';

  private destroy$ = new Subject<void>();
  private notificationTimers = new Map<string, number>();

  // Make Icons available in template
  Icons = Icons;

  constructor(
    private notificationService: NotificationService,
    private websocketService: WebSocketService,
    private stateService: StateService
  ) {}

  ngOnInit(): void {
    this.setupNotificationSubscription();
    this.setupConnectionMonitoring();
    this.setupGlobalLoadingState();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.clearAllTimers();
  }

  private setupNotificationSubscription(): void {
    this.notificationService.notifications$
      .pipe(takeUntil(this.destroy$))
      .subscribe(notification => {
        this.addNotification(notification);
      });
  }

  private setupConnectionMonitoring(): void {
    this.websocketService.connected$
      .pipe(takeUntil(this.destroy$))
      .subscribe(connected => {
        this.isConnected = connected;
        
        if (!connected) {
          this.notificationService.showError(
            'Connection Lost',
            'Real-time updates are unavailable. Attempting to reconnect...'
          );
        } else if (this.isConnected !== connected) {
          // Only show reconnected message if we were previously disconnected
          this.notificationService.showSuccess(
            'Connected',
            'Real-time updates are now available'
          );
        }
      });
  }

  private setupGlobalLoadingState(): void {
    this.stateService.selectLoading()
      .pipe(takeUntil(this.destroy$))
      .subscribe(loading => {
        this.globalLoading = loading;
      });
  }

  private addNotification(notification: UINotification): void {
    const notificationWithMeta = {
      ...notification,
      startTime: Date.now(),
      progress: 0
    };

    this.notifications.unshift(notificationWithMeta);

    // Auto-dismiss after duration
    if (notification.duration && notification.duration > 0) {
      this.startNotificationTimer(notificationWithMeta);
    }

    // Limit number of visible notifications
    if (this.notifications.length > 5) {
      const removed = this.notifications.splice(5);
      removed.forEach(n => this.clearTimer(n.id));
    }
  }

  private startNotificationTimer(notification: UINotification & { startTime?: number }): void {
    if (!notification.duration || notification.duration <= 0) return;

    const updateInterval = 100; // Update progress every 100ms
    const totalDuration = notification.duration;
    
    const timer = window.setInterval(() => {
      const elapsed = Date.now() - (notification.startTime || 0);
      const progress = Math.min((elapsed / totalDuration) * 100, 100);
      
      const notificationIndex = this.notifications.findIndex(n => n.id === notification.id);
      if (notificationIndex !== -1) {
        this.notifications[notificationIndex].progress = progress;
        
        if (progress >= 100) {
          this.dismissNotification(notification.id);
        }
      } else {
        clearInterval(timer);
      }
    }, updateInterval);

    this.notificationTimers.set(notification.id, timer);
  }

  private clearTimer(notificationId: string): void {
    const timer = this.notificationTimers.get(notificationId);
    if (timer) {
      clearInterval(timer);
      this.notificationTimers.delete(notificationId);
    }
  }

  private clearAllTimers(): void {
    this.notificationTimers.forEach(timer => clearInterval(timer));
    this.notificationTimers.clear();
  }

  dismissNotification(notificationId: string): void {
    const index = this.notifications.findIndex(n => n.id === notificationId);
    if (index !== -1) {
      this.notifications.splice(index, 1);
      this.clearTimer(notificationId);
    }
  }

  trackNotification(index: number, notification: UINotification): string {
    return notification.id;
  }

  getNotificationClasses(notification: UINotification): string {
    const baseClasses = 'border-l-4';
    const typeClasses = {
      success: 'border-green-500 bg-green-50',
      error: 'border-red-500 bg-red-50',
      warning: 'border-yellow-500 bg-yellow-50',
      info: 'border-blue-500 bg-blue-50'
    };
    
    return `${baseClasses} ${typeClasses[notification.type]}`;
  }

  getNotificationIcon(type: string) {
    const iconMap = {
      success: Icons.checkCircle,
      error: Icons.xCircle,
      warning: Icons.alertTriangle,
      info: Icons.info
    };
    
    return iconMap[type as keyof typeof iconMap] || Icons.info;
  }

  getNotificationIconClasses(type: string): string {
    const classes = {
      success: 'text-green-500',
      error: 'text-red-500',
      warning: 'text-yellow-500',
      info: 'text-blue-500'
    };
    
    return classes[type as keyof typeof classes] || 'text-blue-500';
  }

  getProgressBarClasses(type: string): string {
    const classes = {
      success: 'bg-green-500',
      error: 'bg-red-500',
      warning: 'bg-yellow-500',
      info: 'bg-blue-500'
    };
    
    return classes[type as keyof typeof classes] || 'bg-blue-500';
  }

  getNotificationProgress(notification: UINotification & { progress?: number }): number {
    return notification.progress || 0;
  }
}