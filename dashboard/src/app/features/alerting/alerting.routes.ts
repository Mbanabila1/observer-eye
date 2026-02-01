import { Routes } from '@angular/router';
import { AuthGuard } from '../auth/guards/auth.guard';

export const alertingRoutes: Routes = [
  {
    path: '',
    redirectTo: 'overview',
    pathMatch: 'full'
  },
  {
    path: 'overview',
    loadComponent: () => import('./pages/overview/alerts-overview.component').then(m => m.AlertsOverviewComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'rules',
    loadComponent: () => import('./pages/rules/alert-rules.component').then(m => m.AlertRulesComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'notifications',
    loadComponent: () => import('./pages/notifications/notification-channels.component').then(m => m.NotificationChannelsComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'history',
    loadComponent: () => import('./pages/history/alert-history.component').then(m => m.AlertHistoryComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'escalation',
    loadComponent: () => import('./pages/escalation/escalation-policies.component').then(m => m.EscalationPoliciesComponent),
    canActivate: [AuthGuard]
  }
];