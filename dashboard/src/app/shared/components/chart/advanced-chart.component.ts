import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Chart, ChartConfiguration, ChartType, registerables, TooltipItem } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

export interface AdvancedChartDataset {
  label: string;
  data: number[] | { x: number; y: number }[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
  tension?: number;
  pointRadius?: number;
  pointHoverRadius?: number;
  borderDash?: number[];
}

export interface AdvancedChartData {
  labels?: string[];
  datasets: AdvancedChartDataset[];
}

export interface AdvancedChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  interaction?: {
    intersect?: boolean;
    mode?: 'index' | 'dataset' | 'point' | 'nearest' | 'x' | 'y';
  };
  plugins?: {
    legend?: {
      display?: boolean;
      position?: 'top' | 'bottom' | 'left' | 'right';
      labels?: {
        usePointStyle?: boolean;
        padding?: number;
      };
    };
    title?: {
      display?: boolean;
      text?: string;
      font?: {
        size?: number;
        weight?: string;
      };
    };
    tooltip?: {
      enabled?: boolean;
      backgroundColor?: string;
      titleColor?: string;
      bodyColor?: string;
      borderColor?: string;
      borderWidth?: number;
      cornerRadius?: number;
      displayColors?: boolean;
      callbacks?: {
        label?: (context: TooltipItem<any>) => string;
        title?: (context: TooltipItem<any>[]) => string;
      };
    };
  };
  scales?: {
    x?: {
      display?: boolean;
      type?: 'linear' | 'logarithmic' | 'category' | 'time' | 'timeseries';
      title?: {
        display?: boolean;
        text?: string;
      };
      grid?: {
        display?: boolean;
        color?: string;
      };
      ticks?: {
        display?: boolean;
        maxTicksLimit?: number;
        callback?: (value: any, index: number, values: any[]) => string;
      };
    };
    y?: {
      display?: boolean;
      beginAtZero?: boolean;
      type?: 'linear' | 'logarithmic';
      title?: {
        display?: boolean;
        text?: string;
      };
      grid?: {
        display?: boolean;
        color?: string;
      };
      ticks?: {
        display?: boolean;
        maxTicksLimit?: number;
        callback?: (value: any, index: number, values: any[]) => string;
      };
    };
  };
  animation?: {
    duration?: number;
    easing?: string;
  };
}

@Component({
  selector: 'app-advanced-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="relative">
      <canvas
        #chartCanvas
        [style.height]="height"
        [style.width]="width"
      ></canvas>
      
      <div *ngIf="loading" class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 rounded-lg">
        <div class="flex flex-col items-center space-y-2">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p *ngIf="loadingText" class="text-sm text-secondary-600">{{ loadingText }}</p>
        </div>
      </div>
      
      <div *ngIf="error" class="absolute inset-0 flex items-center justify-center bg-error-50 text-error-600 text-sm rounded-lg">
        <div class="text-center">
          <p class="font-medium">{{ error }}</p>
          <button *ngIf="onRetry" (click)="onRetry()" class="mt-2 text-xs underline hover:no-underline">
            Try again
          </button>
        </div>
      </div>
      
      <div *ngIf="!loading && !error && isEmpty" class="absolute inset-0 flex items-center justify-center text-secondary-500 text-sm">
        {{ emptyMessage }}
      </div>
    </div>
  `
})
export class AdvancedChartComponent implements OnInit, OnDestroy, AfterViewInit {
  @Input() type: ChartType = 'line';
  @Input() data: AdvancedChartData = { datasets: [] };
  @Input() options: AdvancedChartOptions = {};
  @Input() height = '400px';
  @Input() width = '100%';
  @Input() loading = false;
  @Input() loadingText = 'Loading chart data...';
  @Input() error = '';
  @Input() emptyMessage = 'No data to display';
  @Input() theme: 'light' | 'dark' = 'light';
  @Input() onRetry?: () => void;

  @ViewChild('chartCanvas', { static: true }) chartCanvas!: ElementRef<HTMLCanvasElement>;

  private chart?: Chart;

  ngOnInit(): void {
    // Component initialization
  }

  ngAfterViewInit(): void {
    this.createChart();
  }

  ngOnDestroy(): void {
    if (this.chart) {
      this.chart.destroy();
    }
  }

  ngOnChanges(): void {
    if (this.chart) {
      this.updateChart();
    }
  }

  get isEmpty(): boolean {
    return !this.data.datasets.length || 
           this.data.datasets.every(dataset => !dataset.data.length);
  }

  private createChart(): void {
    if (!this.chartCanvas?.nativeElement || this.loading || this.error || this.isEmpty) {
      return;
    }

    const ctx = this.chartCanvas.nativeElement.getContext('2d');
    if (!ctx) {
      return;
    }

    const config: ChartConfiguration = {
      type: this.type,
      data: this.data,
      options: this.getChartOptions()
    };

    this.chart = new Chart(ctx, config);
  }

  private updateChart(): void {
    if (!this.chart) {
      return;
    }

    this.chart.data = this.data;
    this.chart.options = this.getChartOptions();
    this.chart.update();
  }

  private getChartOptions(): any {
    const defaultOptions = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index' as const,
      },
      plugins: {
        legend: {
          display: true,
          position: 'top' as const,
          labels: {
            usePointStyle: true,
            padding: 20,
            color: this.theme === 'dark' ? '#e2e8f0' : '#475569',
          },
        },
        tooltip: {
          enabled: true,
          backgroundColor: this.theme === 'dark' ? '#1e293b' : '#ffffff',
          titleColor: this.theme === 'dark' ? '#f1f5f9' : '#0f172a',
          bodyColor: this.theme === 'dark' ? '#cbd5e1' : '#475569',
          borderColor: this.theme === 'dark' ? '#475569' : '#e2e8f0',
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: true,
          callbacks: {
            label: (context: TooltipItem<any>) => {
              const label = context.dataset.label || '';
              const value = context.parsed.y || context.parsed;
              return `${label}: ${this.formatValue(value)}`;
            }
          }
        },
      },
      scales: this.getScalesConfig(),
      animation: {
        duration: 750,
        easing: 'easeInOutQuart',
      },
    };

    return { ...defaultOptions, ...this.options };
  }

  private getScalesConfig(): any {
    const gridColor = this.theme === 'dark' ? '#374151' : '#f1f5f9';
    const tickColor = this.theme === 'dark' ? '#9ca3af' : '#6b7280';

    return {
      x: {
        display: true,
        grid: {
          display: true,
          color: gridColor,
        },
        ticks: {
          color: tickColor,
          maxTicksLimit: 10,
        },
        title: {
          display: false,
          color: tickColor,
        },
      },
      y: {
        display: true,
        beginAtZero: true,
        grid: {
          display: true,
          color: gridColor,
        },
        ticks: {
          color: tickColor,
          maxTicksLimit: 8,
          callback: (value: any) => this.formatValue(value),
        },
        title: {
          display: false,
          color: tickColor,
        },
      },
    };
  }

  private formatValue(value: number): string {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
      return (value / 1000).toFixed(1) + 'K';
    }
    return value.toLocaleString();
  }

  public refresh(): void {
    if (this.chart) {
      this.chart.update();
    }
  }

  public downloadChart(filename: string = 'chart'): void {
    if (this.chart) {
      const url = this.chart.toBase64Image();
      const link = document.createElement('a');
      link.download = `${filename}.png`;
      link.href = url;
      link.click();
    }
  }
}