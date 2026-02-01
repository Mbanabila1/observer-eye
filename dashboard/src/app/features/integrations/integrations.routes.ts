import { Routes } from '@angular/router';
import { AuthGuard } from '../auth/guards/auth.guard';

export const integrationsRoutes: Routes = [
  {
    path: '',
    redirectTo: 'overview',
    pathMatch: 'full'
  },
  {
    path: 'overview',
    loadComponent: () => import('./pages/overview/integrations-overview.component').then(m => m.IntegrationsOverviewComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'data-sources',
    loadComponent: () => import('./pages/data-sources/data-sources.component').then(m => m.DataSourcesComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'apis',
    loadComponent: () => import('./pages/apis/api-integrations.component').then(m => m.ApiIntegrationsComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'webhooks',
    loadComponent: () => import('./pages/webhooks/webhook-management.component').then(m => m.WebhookManagementComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'external-tools',
    loadComponent: () => import('./pages/external-tools/external-tools.component').then(m => m.ExternalToolsComponent),
    canActivate: [AuthGuard]
  }
];