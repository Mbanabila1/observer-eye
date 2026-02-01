import { Routes } from '@angular/router';
import { GuestGuard } from './guards/auth.guard';

export const authRoutes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
    canActivate: [GuestGuard]
  },
  {
    path: 'callback',
    loadComponent: () => import('./pages/callback/callback.component').then(m => m.CallbackComponent)
  }
];