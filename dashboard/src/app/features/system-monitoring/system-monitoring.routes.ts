import { Routes } from '@angular/router';
import { AuthGuard } from '../auth/guards/auth.guard';

export const systemMonitoringRoutes: Routes = [
  {
    path: '',
    redirectTo: 'overview',
    pathMatch: 'full'
  },
  {
    path: 'overview',
    loadComponent: () => import('./pages/overview/system-overview.component').then(m => m.SystemOverviewComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'cpu',
    loadComponent: () => import('./pages/cpu/cpu-monitoring.component').then(m => m.CpuMonitoringComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'memory',
    loadComponent: () => import('./pages/memory/memory-monitoring.component').then(m => m.MemoryMonitoringComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'disk',
    loadComponent: () => import('./pages/disk/disk-monitoring.component').then(m => m.DiskMonitoringComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'network',
    loadComponent: () => import('./pages/network/network-monitoring.component').then(m => m.NetworkMonitoringComponent),
    canActivate: [AuthGuard]
  }
];