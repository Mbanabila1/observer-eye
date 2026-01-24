import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'health',
    loadComponent: () => import('./health/health-check.component').then(m => m.HealthCheckComponent)
  },
  {
    path: 'bi-reporting',
    loadChildren: () => import('./bi-reporting/bi-reporting.routes').then(m => m.BI_REPORTING_ROUTES)
  },
  {
    path: '',
    redirectTo: '/bi-reporting',
    pathMatch: 'full'
  }
];
