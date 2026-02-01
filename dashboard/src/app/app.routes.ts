import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes').then(m => m.authRoutes)
  },
  {
    path: 'dashboard',
    loadChildren: () => import('./features/dashboard/dashboard.routes').then(m => m.dashboardRoutes)
  },
  {
    path: 'monitoring',
    loadChildren: () => import('./features/monitoring/monitoring.routes').then(m => m.monitoringRoutes)
  },
  {
    path: 'system-monitoring',
    loadChildren: () => import('./features/system-monitoring/system-monitoring.routes').then(m => m.systemMonitoringRoutes)
  },
  {
    path: 'application-monitoring',
    loadChildren: () => import('./features/application-monitoring/application-monitoring.routes').then(m => m.applicationMonitoringRoutes)
  },
  {
    path: 'security-monitoring',
    loadChildren: () => import('./features/security-monitoring/security-monitoring.routes').then(m => m.securityMonitoringRoutes)
  },
  {
    path: 'network-monitoring',
    loadChildren: () => import('./features/network-monitoring/network-monitoring.routes').then(m => m.networkMonitoringRoutes)
  },
  {
    path: 'analytics',
    loadChildren: () => import('./features/analytics/analytics.routes').then(m => m.analyticsRoutes)
  },
  {
    path: 'alerting',
    loadChildren: () => import('./features/alerting/alerting.routes').then(m => m.alertingRoutes)
  },
  {
    path: 'reporting',
    loadChildren: () => import('./features/reporting/reporting.routes').then(m => m.reportingRoutes)
  },
  {
    path: 'integrations',
    loadChildren: () => import('./features/integrations/integrations.routes').then(m => m.integrationsRoutes)
  },
  {
    path: 'settings',
    loadChildren: () => import('./features/settings/settings.routes').then(m => m.settingsRoutes)
  },
  {
    path: '**',
    redirectTo: '/dashboard'
  }
];
