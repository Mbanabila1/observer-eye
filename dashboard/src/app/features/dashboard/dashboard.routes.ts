import { Routes } from '@angular/router';

export const dashboardRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/main/main-dashboard.component').then(m => m.MainDashboardComponent)
  },
  {
    path: 'manage',
    loadComponent: () => import('./pages/manage/manage-dashboards.component').then(m => m.ManageDashboardsComponent)
  }
];