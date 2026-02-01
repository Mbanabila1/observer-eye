import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, NavigationEnd } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, filter } from 'rxjs';
import { LucideAngularModule } from 'lucide-angular';
import { ButtonComponent } from '../button/button.component';
import { DropdownComponent } from '../dropdown/dropdown.component';
import { BreadcrumbComponent } from '../breadcrumb/breadcrumb.component';
import { StateService } from '../../../core/services/state.service';
import { AuthService } from '../../../features/auth/services/auth.service';
import { Icons, IconName } from '../../utils/icons';

export interface NavigationItem {
  id: string;
  label: string;
  icon: IconName;
  route: string;
  children?: NavigationItem[];
  badge?: {
    text: string;
    color: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  };
}

@Component({
  selector: 'app-main-navigation',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    LucideAngularModule,
    ButtonComponent,
    DropdownComponent,
    BreadcrumbComponent
  ],
  template: `
    <nav class="main-navigation bg-white border-b border-secondary-200">
      <!-- Top Navigation Bar -->
      <div class="px-6 py-3">
        <div class="flex items-center justify-between">
          <!-- Logo and Brand -->
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div class="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
                <lucide-angular [img]="Icons.eye" [size]="20" class="text-white"></lucide-angular>
              </div>
              <span class="text-xl font-bold text-secondary-900">Observer Eye</span>
            </div>
            
            <!-- Environment Badge -->
            <div 
              *ngIf="environment !== 'production'"
              class="px-2 py-1 text-xs font-medium rounded-full"
              [class]="environmentBadgeClass"
            >
              {{ environment.toUpperCase() }}
            </div>
          </div>

          <!-- Right Side Actions -->
          <div class="flex items-center space-x-4">
            <!-- Global Search -->
            <div class="relative">
              <input
                type="text"
                placeholder="Search..."
                class="w-64 pl-10 pr-4 py-2 border border-secondary-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                [(ngModel)]="searchQuery"
                (keyup.enter)="performSearch()"
              >
              <lucide-angular 
                [img]="Icons.search" 
                [size]="16" 
                class="absolute left-3 top-3 text-secondary-400"
              ></lucide-angular>
            </div>

            <!-- Notifications -->
            <app-dropdown
              [items]="notificationItems"
              [showArrow]="false"
              (itemSelected)="onNotificationAction($event)"
            >
              <div class="relative">
                <app-button
                  variant="ghost"
                  size="sm"
                  [iconOnly]="true"
                  leftIcon="bell"
                  title="Notifications"
                ></app-button>
                <div 
                  *ngIf="unreadNotifications > 0"
                  class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center"
                >
                  {{ unreadNotifications > 9 ? '9+' : unreadNotifications }}
                </div>
              </div>
            </app-dropdown>

            <!-- User Menu -->
            <app-dropdown
              [items]="userMenuItems"
              [showArrow]="false"
              (itemSelected)="onUserMenuAction($event)"
            >
              <div class="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-secondary-100 cursor-pointer">
                <div class="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
                  <span class="text-white text-sm font-medium">{{ userInitials }}</span>
                </div>
                <div class="hidden md:block">
                  <p class="text-sm font-medium text-secondary-900">{{ userName }}</p>
                  <p class="text-xs text-secondary-600">{{ userRole }}</p>
                </div>
              </div>
            </app-dropdown>
          </div>
        </div>
      </div>

      <!-- Main Navigation Menu -->
      <div class="px-6 py-2 border-t border-secondary-100">
        <div class="flex items-center justify-between">
          <!-- Primary Navigation -->
          <div class="flex items-center space-x-1">
            <a
              *ngFor="let item of navigationItems"
              [routerLink]="item.route"
              routerLinkActive="active"
              [routerLinkActiveOptions]="{ exact: item.route === '/' }"
              class="nav-item flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              [class.active]="isActiveRoute(item.route)"
            >
              <lucide-angular [img]="getIcon(item.icon)" [size]="16"></lucide-angular>
              <span>{{ item.label }}</span>
              <div 
                *ngIf="item.badge"
                class="px-2 py-0.5 text-xs font-medium rounded-full"
                [class]="getBadgeClass(item.badge.color)"
              >
                {{ item.badge.text }}
              </div>
            </a>
          </div>

          <!-- Secondary Actions -->
          <div class="flex items-center space-x-2">
            <!-- Quick Actions -->
            <app-dropdown
              [items]="quickActions"
              (itemSelected)="onQuickAction($event)"
            >
              <app-button
                variant="ghost"
                size="sm"
                leftIcon="plus"
              >
                Quick Actions
              </app-button>
            </app-dropdown>

            <!-- Help -->
            <app-button
              variant="ghost"
              size="sm"
              [iconOnly]="true"
              leftIcon="helpCircle"
              (clicked)="openHelp()"
              title="Help & Documentation"
            ></app-button>
          </div>
        </div>
      </div>

      <!-- Breadcrumb Navigation -->
      <div *ngIf="showBreadcrumbs" class="px-6 py-2 border-t border-secondary-100 bg-secondary-50">
        <app-breadcrumb [items]="breadcrumbItems"></app-breadcrumb>
      </div>
    </nav>
  `
})
export class MainNavigationComponent implements OnInit, OnDestroy {
  searchQuery = '';
  unreadNotifications = 3;
  showBreadcrumbs = true;
  environment = 'development'; // This would come from environment config
  
  navigationItems: NavigationItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: 'layoutDashboard',
      route: '/dashboard'
    },
    {
      id: 'monitoring',
      label: 'General Monitoring',
      icon: 'activity',
      route: '/monitoring',
      badge: {
        text: '3',
        color: 'warning'
      }
    },
    {
      id: 'system-monitoring',
      label: 'System Monitoring',
      icon: 'cpu',
      route: '/system-monitoring'
    },
    {
      id: 'application-monitoring',
      label: 'Application Monitoring',
      icon: 'zap',
      route: '/application-monitoring'
    },
    {
      id: 'security-monitoring',
      label: 'Security Monitoring',
      icon: 'shield',
      route: '/security-monitoring'
    },
    {
      id: 'network-monitoring',
      label: 'Network Monitoring',
      icon: 'activity',
      route: '/network-monitoring'
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: 'barChart3',
      route: '/analytics'
    },
    {
      id: 'alerting',
      label: 'Alerting',
      icon: 'bell',
      route: '/alerting'
    },
    {
      id: 'reporting',
      label: 'Reporting',
      icon: 'download',
      route: '/reporting'
    },
    {
      id: 'integrations',
      label: 'Integrations',
      icon: 'share',
      route: '/integrations'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: 'settings',
      route: '/settings'
    }
  ];

  breadcrumbItems: any[] = [];

  notificationItems = [
    {
      id: 'view-all',
      label: 'View All Notifications',
      icon: 'bell' as IconName,
      description: '3 unread notifications'
    },
    { type: 'divider' },
    {
      id: 'alert-1',
      label: 'High CPU Usage Alert',
      description: '2 minutes ago',
      icon: 'alertTriangle' as IconName,
      unread: true
    },
    {
      id: 'alert-2',
      label: 'New Dashboard Shared',
      description: '1 hour ago',
      icon: 'share' as IconName,
      unread: true
    },
    {
      id: 'alert-3',
      label: 'System Update Complete',
      description: '3 hours ago',
      icon: 'checkCircle' as IconName,
      unread: false
    }
  ];

  userMenuItems = [
    { id: 'profile', label: 'Profile', icon: 'user' as IconName },
    { id: 'account', label: 'Account Settings', icon: 'settings' as IconName },
    { id: 'preferences', label: 'Preferences', icon: 'sliders' as IconName },
    { type: 'divider' },
    { id: 'help', label: 'Help & Support', icon: 'helpCircle' as IconName },
    { id: 'feedback', label: 'Send Feedback', icon: 'messageCircle' as IconName },
    { type: 'divider' },
    { id: 'logout', label: 'Sign Out', icon: 'logOut' as IconName, danger: true }
  ];

  quickActions = [
    { id: 'new-dashboard', label: 'New Dashboard', icon: 'layoutDashboard' as IconName },
    { id: 'create-alert', label: 'Create Alert Rule', icon: 'bell' as IconName },
    { id: 'export-data', label: 'Export Data', icon: 'download' as IconName },
    { id: 'import-config', label: 'Import Configuration', icon: 'upload' as IconName }
  ];

  private destroy$ = new Subject<void>();

  // Make Icons available in template
  Icons = Icons;

  constructor(
    private router: Router,
    private stateService: StateService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.setupRouterSubscription();
    this.loadUserData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private setupRouterSubscription(): void {
    this.router.events
      .pipe(
        filter(event => event instanceof NavigationEnd),
        takeUntil(this.destroy$)
      )
      .subscribe((event: NavigationEnd) => {
        this.updateBreadcrumbs(event.url);
      });
  }

  private loadUserData(): void {
    this.stateService.selectUser()
      .pipe(takeUntil(this.destroy$))
      .subscribe(user => {
        // User data is loaded, component will update automatically
      });
  }

  private updateBreadcrumbs(url: string): void {
    const segments = url.split('/').filter(segment => segment);
    this.breadcrumbItems = [];

    // Build breadcrumb items based on route segments
    let currentPath = '';
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      
      const item = {
        label: this.getSegmentLabel(segment),
        route: currentPath,
        active: index === segments.length - 1
      };
      
      this.breadcrumbItems.push(item);
    });

    // Show breadcrumbs only if there are multiple levels
    this.showBreadcrumbs = this.breadcrumbItems.length > 1;
  }

  private getSegmentLabel(segment: string): string {
    const labelMap: Record<string, string> = {
      'dashboard': 'Dashboard',
      'monitoring': 'Monitoring',
      'analytics': 'Analytics',
      'settings': 'Settings',
      'manage': 'Manage',
      'overview': 'Overview',
      'general': 'General'
    };

    return labelMap[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
  }

  isActiveRoute(route: string): boolean {
    return this.router.url.startsWith(route);
  }

  getBadgeClass(color: string): string {
    const colorClasses = {
      primary: 'bg-primary-100 text-primary-800',
      secondary: 'bg-secondary-100 text-secondary-800',
      success: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800'
    };
    return colorClasses[color as keyof typeof colorClasses] || colorClasses.secondary;
  }

  get environmentBadgeClass(): string {
    const classes = {
      development: 'bg-blue-100 text-blue-800',
      staging: 'bg-yellow-100 text-yellow-800',
      production: 'bg-green-100 text-green-800'
    };
    return classes[this.environment as keyof typeof classes] || classes.development;
  }

  get userName(): string {
    const user = this.stateService.getUser();
    return user?.name || user?.email || 'User';
  }

  get userInitials(): string {
    const user = this.stateService.getUser();
    if (user?.name) {
      return user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase();
    }
    if (user?.email) {
      return user.email[0].toUpperCase();
    }
    return 'U';
  }

  get userRole(): string {
    const user = this.stateService.getUser();
    return user?.role || 'Administrator';
  }

  // Event Handlers
  performSearch(): void {
    if (this.searchQuery.trim()) {
      this.router.navigate(['/search'], { 
        queryParams: { q: this.searchQuery.trim() } 
      });
    }
  }

  onNotificationAction(action: any): void {
    switch (action.id) {
      case 'view-all':
        this.router.navigate(['/notifications']);
        break;
      default:
        if (action.id.startsWith('alert-')) {
          // Handle specific notification click
          console.log('Notification clicked:', action);
        }
        break;
    }
  }

  onUserMenuAction(action: any): void {
    switch (action.id) {
      case 'profile':
        this.router.navigate(['/profile']);
        break;
      case 'account':
        this.router.navigate(['/settings/account']);
        break;
      case 'preferences':
        this.router.navigate(['/settings/preferences']);
        break;
      case 'help':
        this.openHelp();
        break;
      case 'feedback':
        this.openFeedback();
        break;
      case 'logout':
        this.logout();
        break;
    }
  }

  onQuickAction(action: any): void {
    switch (action.id) {
      case 'new-dashboard':
        this.router.navigate(['/dashboard/create']);
        break;
      case 'create-alert':
        this.router.navigate(['/monitoring/alerts/create']);
        break;
      case 'export-data':
        // Open export modal
        break;
      case 'import-config':
        // Open import modal
        break;
    }
  }

  openHelp(): void {
    // Open help documentation or modal
    window.open('/help', '_blank');
  }

  openFeedback(): void {
    // Open feedback form or modal
    console.log('Opening feedback form');
  }

  logout(): void {
    this.authService.signOut().subscribe({
      next: () => {
        this.stateService.clearUser();
        this.router.navigate(['/auth/login']);
      },
      error: (error) => {
        console.error('Logout error:', error);
        // Force logout even if API call fails
        this.stateService.clearUser();
        this.router.navigate(['/auth/login']);
      }
    });
  }

  getIcon(iconName: IconName) {
    return Icons[iconName];
  }
}