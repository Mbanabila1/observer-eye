import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface TelemetryData {
  id: string;
  source: string;
  type: 'log' | 'metric' | 'trace';
  data: Record<string, any>;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface TelemetryQuery {
  source?: string;
  type?: 'log' | 'metric' | 'trace';
  start_time?: string;
  end_time?: string;
  filters?: Record<string, any>;
  limit?: number;
  offset?: number;
}

export interface TelemetryStream {
  id: string;
  filters: Record<string, any>;
  active: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class TelemetryService {
  constructor(private api: ApiService) {}

  // Telemetry Data Retrieval
  getTelemetryData(query?: TelemetryQuery): Observable<TelemetryData[]> {
    return this.api.get<TelemetryData[]>('/telemetry/data', query as any);
  }

  getTelemetryById(id: string): Observable<TelemetryData> {
    return this.api.get<TelemetryData>(`/telemetry/data/${id}`);
  }

  // Telemetry Ingestion
  ingestTelemetryData(data: Partial<TelemetryData>): Observable<TelemetryData> {
    return this.api.post<TelemetryData>('/telemetry/ingest', data);
  }

  ingestBulkTelemetryData(data: Partial<TelemetryData>[]): Observable<{ success: number; failed: number }> {
    return this.api.post<{ success: number; failed: number }>('/telemetry/ingest/bulk', data);
  }

  // Telemetry Analysis
  getTelemetryAggregation(query: TelemetryQuery & { aggregation: string }): Observable<any> {
    return this.api.get<any>('/telemetry/aggregate', query as any);
  }

  getTelemetryCorrelation(traceId: string): Observable<TelemetryData[]> {
    return this.api.get<TelemetryData[]>(`/telemetry/correlation/${traceId}`);
  }

  // Real-time Streaming
  createTelemetryStream(filters: Record<string, any>): Observable<TelemetryStream> {
    return this.api.post<TelemetryStream>('/telemetry/streams', { filters });
  }

  getTelemetryStreams(): Observable<TelemetryStream[]> {
    return this.api.get<TelemetryStream[]>('/telemetry/streams');
  }

  deleteTelemetryStream(id: string): Observable<void> {
    return this.api.delete<void>(`/telemetry/streams/${id}`);
  }

  // Telemetry Sources
  getTelemetrySources(): Observable<string[]> {
    return this.api.get<string[]>('/telemetry/sources');
  }

  // Telemetry Statistics
  getTelemetryStats(): Observable<{
    total_records: number;
    sources: Record<string, number>;
    types: Record<string, number>;
    last_updated: string;
  }> {
    return this.api.get('/telemetry/stats');
  }
}