import { Routes } from '@angular/router';
import { AuthGuard } from '../auth/guards/auth.guard';

export const applicationMonitoringRoutes: Routes = [
  {
    path: '',
    redirectTo: 'overview',
    pathMatch: 'full'
  },
  {
    path: 'overview',
    loadComponent: () => import('./pages/overview/application-overview.component').then(m => m.ApplicationOverviewComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'performance',
    loadComponent: () => import('./pages/performance/performance-monitoring.component').then(m => m.PerformanceMonitoringComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'errors',
    loadComponent: () => import('./pages/errors/error-tracking.component').then(m => m.ErrorTrackingComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'traces',
    loadComponent: () => import('./pages/traces/distributed-tracing.component').then(m => m.DistributedTracingComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'logs',
    loadComponent: () => import('./pages/logs/log-analysis.component').then(m => m.LogAnalysisComponent),
    canActivate: [AuthGuard]
  }
];