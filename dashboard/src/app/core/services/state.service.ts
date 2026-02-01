import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface AppState {
  user: any | null;
  loading: boolean;
  error: string | null;
  notifications: any[];
  dashboards: any[];
  selectedDashboard: any | null;
  realTimeData: Record<string, any>;
}

const initialState: AppState = {
  user: null,
  loading: false,
  error: null,
  notifications: [],
  dashboards: [],
  selectedDashboard: null,
  realTimeData: {}
};

@Injectable({
  providedIn: 'root'
})
export class StateService {
  private stateSubject = new BehaviorSubject<AppState>(initialState);
  public state$ = this.stateSubject.asObservable();

  constructor() {}

  private updateState(updates: Partial<AppState>): void {
    const currentState = this.stateSubject.value;
    const newState = { ...currentState, ...updates };
    this.stateSubject.next(newState);
  }

  // User state management
  setUser(user: any): void {
    this.updateState({ user });
  }

  clearUser(): void {
    this.updateState({ user: null });
  }

  getUser(): any | null {
    return this.stateSubject.value.user;
  }

  // Loading state management
  setLoading(loading: boolean): void {
    this.updateState({ loading });
  }

  isLoading(): boolean {
    return this.stateSubject.value.loading;
  }

  // Error state management
  setError(error: string | null): void {
    this.updateState({ error });
  }

  clearError(): void {
    this.updateState({ error: null });
  }

  getError(): string | null {
    return this.stateSubject.value.error;
  }

  // Notifications management
  addNotification(notification: any): void {
    const notifications = [...this.stateSubject.value.notifications, notification];
    this.updateState({ notifications });
  }

  removeNotification(id: string): void {
    const notifications = this.stateSubject.value.notifications.filter(n => n.id !== id);
    this.updateState({ notifications });
  }

  clearNotifications(): void {
    this.updateState({ notifications: [] });
  }

  // Dashboard state management
  setDashboards(dashboards: any[]): void {
    this.updateState({ dashboards });
  }

  addDashboard(dashboard: any): void {
    const dashboards = [...this.stateSubject.value.dashboards, dashboard];
    this.updateState({ dashboards });
  }

  updateDashboard(id: string, updates: Partial<any>): void {
    const dashboards = this.stateSubject.value.dashboards.map(d => 
      d.id === id ? { ...d, ...updates } : d
    );
    this.updateState({ dashboards });
  }

  removeDashboard(id: string): void {
    const dashboards = this.stateSubject.value.dashboards.filter(d => d.id !== id);
    this.updateState({ dashboards });
  }

  setSelectedDashboard(dashboard: any | null): void {
    this.updateState({ selectedDashboard: dashboard });
  }

  getSelectedDashboard(): any | null {
    return this.stateSubject.value.selectedDashboard;
  }

  // Real-time data management
  updateRealTimeData(key: string, data: any): void {
    const realTimeData = {
      ...this.stateSubject.value.realTimeData,
      [key]: data
    };
    this.updateState({ realTimeData });
  }

  getRealTimeData(key: string): any {
    return this.stateSubject.value.realTimeData[key];
  }

  clearRealTimeData(): void {
    this.updateState({ realTimeData: {} });
  }

  // Utility methods
  getCurrentState(): AppState {
    return this.stateSubject.value;
  }

  resetState(): void {
    this.stateSubject.next(initialState);
  }

  // Selectors
  selectUser(): Observable<any | null> {
    return new Observable(observer => {
      this.state$.subscribe(state => observer.next(state.user));
    });
  }

  selectLoading(): Observable<boolean> {
    return new Observable(observer => {
      this.state$.subscribe(state => observer.next(state.loading));
    });
  }

  selectError(): Observable<string | null> {
    return new Observable(observer => {
      this.state$.subscribe(state => observer.next(state.error));
    });
  }

  selectDashboards(): Observable<any[]> {
    return new Observable(observer => {
      this.state$.subscribe(state => observer.next(state.dashboards));
    });
  }

  selectSelectedDashboard(): Observable<any | null> {
    return new Observable(observer => {
      this.state$.subscribe(state => observer.next(state.selectedDashboard));
    });
  }
}