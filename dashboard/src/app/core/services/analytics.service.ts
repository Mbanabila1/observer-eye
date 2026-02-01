import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface AnalyticsData {
  id: string;
  metric_name: string;
  metric_value: any;
  timestamp: string;
  source: string;
  tags: Record<string, any>;
}

export interface AnalyticsQuery {
  metric_name?: string;
  source?: string;
  start_date?: string;
  end_date?: string;
  tags?: Record<string, any>;
}

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private readonly endpoint = '/analytics';

  constructor(private api: ApiService) {}

  getAnalyticsData(query?: AnalyticsQuery): Observable<AnalyticsData[]> {
    return this.api.get<AnalyticsData[]>(`${this.endpoint}/data`, query as any);
  }

  createAnalyticsData(data: Partial<AnalyticsData>): Observable<AnalyticsData> {
    return this.api.post<AnalyticsData>(`${this.endpoint}/data`, data);
  }

  getAnalyticsSummary(query?: AnalyticsQuery): Observable<any> {
    return this.api.get<any>(`${this.endpoint}/summary`, query as any);
  }

  getAnalyticsTrends(query?: AnalyticsQuery): Observable<any> {
    return this.api.get<any>(`${this.endpoint}/trends`, query as any);
  }
}