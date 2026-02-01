import { Routes } from '@angular/router';
import { AuthGuard } from '../auth/guards/auth.guard';

export const monitoringRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/overview/monitoring-overview.component').then(m => m.MonitoringOverviewComponent),
    canActivate: [AuthGuard]
  }
];