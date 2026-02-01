import { Injectable } from '@angular/core';
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface StreamSubscription {
  id: string;
  filters: Record<string, any>;
  callback: (data: any) => void;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket: WebSocket | null = null;
  private messageSubject = new Subject<WebSocketMessage>();
  private connectionSubject = new BehaviorSubject<boolean>(false);
  private subscriptions = new Map<string, StreamSubscription>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 5000;

  public messages$ = this.messageSubject.asObservable();
  public connected$ = this.connectionSubject.asObservable();

  constructor() {
    this.connect();
  }

  private connect(): void {
    try {
      const wsUrl = environment.wsUrl || 'ws://localhost:8400/ws';
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.connectionSubject.next(true);
        this.reconnectAttempts = 0;
        
        // Resubscribe to all active subscriptions
        this.subscriptions.forEach(sub => {
          this.sendMessage('subscribe', sub.filters);
        });
      };

      this.socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.messageSubject.next(message);
          this.handleMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
        this.connectionSubject.next(false);
        this.attemptReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    // Route messages to appropriate subscriptions
    this.subscriptions.forEach(sub => {
      if (this.messageMatchesFilters(message, sub.filters)) {
        sub.callback(message.data);
      }
    });
  }

  private messageMatchesFilters(message: WebSocketMessage, filters: Record<string, any>): boolean {
    // Simple filter matching - can be enhanced based on requirements
    if (filters['type'] && message.type !== filters['type']) {
      return false;
    }
    
    if (filters['source'] && message.data?.source !== filters['source']) {
      return false;
    }

    return true;
  }

  private sendMessage(type: string, data: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const message = {
        type,
        data,
        timestamp: new Date().toISOString()
      };
      this.socket.send(JSON.stringify(message));
    }
  }

  // Public API
  subscribe(filters: Record<string, any>, callback: (data: any) => void): string {
    const id = Math.random().toString(36).substr(2, 9);
    const subscription: StreamSubscription = { id, filters, callback };
    
    this.subscriptions.set(id, subscription);
    
    if (this.connectionSubject.value) {
      this.sendMessage('subscribe', filters);
    }
    
    return id;
  }

  unsubscribe(subscriptionId: string): void {
    const subscription = this.subscriptions.get(subscriptionId);
    if (subscription) {
      this.subscriptions.delete(subscriptionId);
      this.sendMessage('unsubscribe', { subscription_id: subscriptionId });
    }
  }

  // Specific subscription methods for different data types
  subscribeToTelemetry(callback: (data: any) => void): string {
    return this.subscribe({ type: 'telemetry' }, callback);
  }

  subscribeToMetrics(callback: (data: any) => void): string {
    return this.subscribe({ type: 'metrics' }, callback);
  }

  subscribeToAlerts(callback: (data: any) => void): string {
    return this.subscribe({ type: 'alerts' }, callback);
  }

  subscribeToPerformance(callback: (data: any) => void): string {
    return this.subscribe({ type: 'performance' }, callback);
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.subscriptions.clear();
    this.connectionSubject.next(false);
  }
}