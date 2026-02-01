import { Routes } from '@angular/router';
import { AuthGuard } from '../auth/guards/auth.guard';

export const analyticsRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/overview/analytics-overview.component').then(m => m.AnalyticsOverviewComponent),
    canActivate: [AuthGuard]
  }
];