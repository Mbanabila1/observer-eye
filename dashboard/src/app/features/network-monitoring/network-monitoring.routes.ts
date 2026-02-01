import { Routes } from '@angular/router';
import { AuthGuard } from '../auth/guards/auth.guard';

export const networkMonitoringRoutes: Routes = [
  {
    path: '',
    redirectTo: 'overview',
    pathMatch: 'full'
  },
  {
    path: 'overview',
    loadComponent: () => import('./pages/overview/network-overview.component').then(m => m.NetworkOverviewComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'traffic',
    loadComponent: () => import('./pages/traffic/traffic-analysis.component').then(m => m.TrafficAnalysisComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'bandwidth',
    loadComponent: () => import('./pages/bandwidth/bandwidth-monitoring.component').then(m => m.BandwidthMonitoringComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'latency',
    loadComponent: () => import('./pages/latency/latency-monitoring.component').then(m => m.LatencyMonitoringComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'topology',
    loadComponent: () => import('./pages/topology/network-topology.component').then(m => m.NetworkTopologyComponent),
    canActivate: [AuthGuard]
  }
];