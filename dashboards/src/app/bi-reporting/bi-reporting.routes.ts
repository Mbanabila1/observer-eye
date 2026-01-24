import { Routes } from '@angular/router';

export const BI_REPORTING_ROUTES: Routes = [
  {
    path: 'executive-dashboard',
    loadComponent: () => import('./executive-dashboard/executive-dashboard.component').then(m => m.ExecutiveDashboardComponent)
  },
  {
    path: 'report-builder',
    loadComponent: () => import('./report-builder/report-builder.component').then(m => m.ReportBuilderComponent)
  },
  {
    path: 'reports',
    loadComponent: () => import('./reports-list/reports-list.component').then(m => m.ReportsListComponent)
  },
  {
    path: '',
    redirectTo: 'executive-dashboard',
    pathMatch: 'full'
  }
];