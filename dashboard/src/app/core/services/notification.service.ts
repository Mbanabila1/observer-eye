import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { ApiService } from './api.service';

export interface NotificationChannel {
  id: string;
  name: string;
  channel_type: 'email' | 'sms' | 'webhook' | 'slack';
  configuration: Record<string, any>;
  is_active: boolean;
}

export interface AlertRule {
  id: string;
  name: string;
  condition: Record<string, any>;
  threshold: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  notification_channels: string[];
  is_active: boolean;
}

export interface Alert {
  id: string;
  rule_id: string;
  triggered_at: string;
  resolved_at?: string;
  status: 'active' | 'resolved' | 'acknowledged';
  message: string;
  metadata: Record<string, any>;
}

export interface UINotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private notificationSubject = new Subject<UINotification>();
  public notifications$ = this.notificationSubject.asObservable();

  constructor(private api: ApiService) {}

  // UI Notifications
  showNotification(notification: Omit<UINotification, 'id'>): void {
    const id = Math.random().toString(36).substr(2, 9);
    this.notificationSubject.next({ ...notification, id });
  }

  showSuccess(title: string, message: string, duration = 5000): void {
    this.showNotification({ type: 'success', title, message, duration });
  }

  showError(title: string, message: string, duration = 0): void {
    this.showNotification({ type: 'error', title, message, duration });
  }

  showWarning(title: string, message: string, duration = 7000): void {
    this.showNotification({ type: 'warning', title, message, duration });
  }

  showInfo(title: string, message: string, duration = 5000): void {
    this.showNotification({ type: 'info', title, message, duration });
  }

  // Backend Notification Management
  getNotificationChannels(): Observable<NotificationChannel[]> {
    return this.api.get<NotificationChannel[]>('/notifications/channels');
  }

  createNotificationChannel(channel: Partial<NotificationChannel>): Observable<NotificationChannel> {
    return this.api.post<NotificationChannel>('/notifications/channels', channel);
  }

  updateNotificationChannel(id: string, channel: Partial<NotificationChannel>): Observable<NotificationChannel> {
    return this.api.put<NotificationChannel>(`/notifications/channels/${id}`, channel);
  }

  deleteNotificationChannel(id: string): Observable<void> {
    return this.api.delete<void>(`/notifications/channels/${id}`);
  }

  // Alert Rules Management
  getAlertRules(): Observable<AlertRule[]> {
    return this.api.get<AlertRule[]>('/notifications/alert-rules');
  }

  createAlertRule(rule: Partial<AlertRule>): Observable<AlertRule> {
    return this.api.post<AlertRule>('/notifications/alert-rules', rule);
  }

  updateAlertRule(id: string, rule: Partial<AlertRule>): Observable<AlertRule> {
    return this.api.put<AlertRule>(`/notifications/alert-rules/${id}`, rule);
  }

  deleteAlertRule(id: string): Observable<void> {
    return this.api.delete<void>(`/notifications/alert-rules/${id}`);
  }

  // Alerts Management
  getAlerts(status?: string): Observable<Alert[]> {
    const params = status ? { status } : undefined;
    return this.api.get<Alert[]>('/notifications/alerts', params as any);
  }

  acknowledgeAlert(id: string): Observable<Alert> {
    return this.api.put<Alert>(`/notifications/alerts/${id}/acknowledge`, {});
  }

  resolveAlert(id: string): Observable<Alert> {
    return this.api.put<Alert>(`/notifications/alerts/${id}/resolve`, {});
  }
}