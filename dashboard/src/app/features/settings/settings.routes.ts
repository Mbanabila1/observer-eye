import { Routes } from '@angular/router';
import { AuthGuard } from '../auth/guards/auth.guard';

export const settingsRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/general/general-settings.component').then(m => m.GeneralSettingsComponent),
    canActivate: [AuthGuard]
  }
];