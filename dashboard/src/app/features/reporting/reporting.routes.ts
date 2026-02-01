import { Routes } from '@angular/router';
import { AuthGuard } from '../auth/guards/auth.guard';

export const reportingRoutes: Routes = [
  {
    path: '',
    redirectTo: 'overview',
    pathMatch: 'full'
  },
  {
    path: 'overview',
    loadComponent: () => import('./pages/overview/reports-overview.component').then(m => m.ReportsOverviewComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'performance',
    loadComponent: () => import('./pages/performance/performance-reports.component').then(m => m.PerformanceReportsComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'availability',
    loadComponent: () => import('./pages/availability/availability-reports.component').then(m => m.AvailabilityReportsComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'security',
    loadComponent: () => import('./pages/security/security-reports.component').then(m => m.SecurityReportsComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'custom',
    loadComponent: () => import('./pages/custom/custom-reports.component').then(m => m.CustomReportsComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'scheduled',
    loadComponent: () => import('./pages/scheduled/scheduled-reports.component').then(m => m.ScheduledReportsComponent),
    canActivate: [AuthGuard]
  }
];