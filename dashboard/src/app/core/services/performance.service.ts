import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface PerformanceMetric {
  id: string;
  service_name: string;
  metric_type: string;
  value: number;
  unit: string;
  timestamp: string;
}

export interface ApplicationMetrics {
  id: string;
  application_name: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: any;
  timestamp: string;
}

export interface NetworkMetrics {
  id: string;
  interface_name: string;
  bytes_sent: number;
  bytes_received: number;
  packets_sent: number;
  packets_received: number;
  errors: number;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class PerformanceService {
  constructor(private api: ApiService) {}

  // Application Performance Monitoring
  getApplicationMetrics(applicationName?: string): Observable<ApplicationMetrics[]> {
    const params = applicationName ? { application_name: applicationName } : undefined;
    return this.api.get<ApplicationMetrics[]>('/performance/application', params as any);
  }

  // Network Performance Monitoring
  getNetworkMetrics(interfaceName?: string): Observable<NetworkMetrics[]> {
    const params = interfaceName ? { interface_name: interfaceName } : undefined;
    return this.api.get<NetworkMetrics[]>('/performance/network', params as any);
  }

  // System Performance Monitoring
  getSystemMetrics(): Observable<PerformanceMetric[]> {
    return this.api.get<PerformanceMetric[]>('/performance/system');
  }

  // Security Performance Monitoring
  getSecurityMetrics(): Observable<any[]> {
    return this.api.get<any[]>('/performance/security');
  }

  // Traffic Performance Monitoring
  getTrafficMetrics(): Observable<any[]> {
    return this.api.get<any[]>('/performance/traffic');
  }

  // Identity Performance Monitoring
  getIdentityMetrics(): Observable<any[]> {
    return this.api.get<any[]>('/performance/identity');
  }
}