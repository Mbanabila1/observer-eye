import { HTTP_INTERCEPTORS, provideHttpClient } from '@angular/common/http';
import { Provider, EnvironmentProviders } from '@angular/core';
import { ApiInterceptor } from '../interceptors/api.interceptor';

export const httpProviders: (Provider | EnvironmentProviders)[] = [
  provideHttpClient(),
  // Temporarily disable interceptors to fix build issues
  // {
  //   provide: HTTP_INTERCEPTORS,
  //   useClass: ApiInterceptor,
  //   multi: true
  // }
];