import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface DashboardTemplate {
  id: string;
  name: string;
  description: string;
  layout_config: Record<string, any>;
  widget_configs: Record<string, any>;
  version: string;
  is_public: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Dashboard {
  id: string;
  name: string;
  template_id?: string;
  owner: string;
  configuration: Record<string, any>;
  is_shared: boolean;
  created_at: string;
  updated_at: string;
}

export interface DashboardWidget {
  id: string;
  dashboard_id: string;
  widget_type: string;
  configuration: Record<string, any>;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  constructor(private api: ApiService) {}

  // Dashboard Templates
  getDashboardTemplates(): Observable<DashboardTemplate[]> {
    return this.api.get<DashboardTemplate[]>('/dashboards/templates');
  }

  getDashboardTemplate(id: string): Observable<DashboardTemplate> {
    return this.api.get<DashboardTemplate>(`/dashboards/templates/${id}`);
  }

  createDashboardTemplate(template: Partial<DashboardTemplate>): Observable<DashboardTemplate> {
    return this.api.post<DashboardTemplate>('/dashboards/templates', template);
  }

  updateDashboardTemplate(id: string, template: Partial<DashboardTemplate>): Observable<DashboardTemplate> {
    return this.api.put<DashboardTemplate>(`/dashboards/templates/${id}`, template);
  }

  deleteDashboardTemplate(id: string): Observable<void> {
    return this.api.delete<void>(`/dashboards/templates/${id}`);
  }

  // Dashboards
  getDashboards(): Observable<Dashboard[]> {
    return this.api.get<Dashboard[]>('/dashboards');
  }

  getDashboard(id: string): Observable<Dashboard> {
    return this.api.get<Dashboard>(`/dashboards/${id}`);
  }

  createDashboard(dashboard: Partial<Dashboard>): Observable<Dashboard> {
    return this.api.post<Dashboard>('/dashboards', dashboard);
  }

  updateDashboard(id: string, dashboard: Partial<Dashboard>): Observable<Dashboard> {
    return this.api.put<Dashboard>(`/dashboards/${id}`, dashboard);
  }

  deleteDashboard(id: string): Observable<void> {
    return this.api.delete<void>(`/dashboards/${id}`);
  }

  createDashboardFromTemplate(templateId: string, name: string): Observable<Dashboard> {
    return this.api.post<Dashboard>('/dashboards/from-template', {
      template_id: templateId,
      name: name
    });
  }

  // Dashboard Widgets
  getDashboardWidgets(dashboardId: string): Observable<DashboardWidget[]> {
    return this.api.get<DashboardWidget[]>(`/dashboards/${dashboardId}/widgets`);
  }

  createDashboardWidget(dashboardId: string, widget: Partial<DashboardWidget>): Observable<DashboardWidget> {
    return this.api.post<DashboardWidget>(`/dashboards/${dashboardId}/widgets`, widget);
  }

  updateDashboardWidget(dashboardId: string, widgetId: string, widget: Partial<DashboardWidget>): Observable<DashboardWidget> {
    return this.api.put<DashboardWidget>(`/dashboards/${dashboardId}/widgets/${widgetId}`, widget);
  }

  deleteDashboardWidget(dashboardId: string, widgetId: string): Observable<void> {
    return this.api.delete<void>(`/dashboards/${dashboardId}/widgets/${widgetId}`);
  }
}