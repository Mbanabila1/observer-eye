import { Routes } from '@angular/router';
import { AuthGuard } from '../auth/guards/auth.guard';

export const securityMonitoringRoutes: Routes = [
  {
    path: '',
    redirectTo: 'overview',
    pathMatch: 'full'
  },
  {
    path: 'overview',
    loadComponent: () => import('./pages/overview/security-overview.component').then(m => m.SecurityOverviewComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'threats',
    loadComponent: () => import('./pages/threats/threat-detection.component').then(m => m.ThreatDetectionComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'vulnerabilities',
    loadComponent: () => import('./pages/vulnerabilities/vulnerability-assessment.component').then(m => m.VulnerabilityAssessmentComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'access',
    loadComponent: () => import('./pages/access/access-monitoring.component').then(m => m.AccessMonitoringComponent),
    canActivate: [AuthGuard]
  },
  {
    path: 'compliance',
    loadComponent: () => import('./pages/compliance/compliance-monitoring.component').then(m => m.ComplianceMonitoringComponent),
    canActivate: [AuthGuard]
  }
];