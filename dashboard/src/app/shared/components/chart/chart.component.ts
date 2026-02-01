import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Chart, ChartConfiguration, ChartType, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
  tension?: number;
}

export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  plugins?: {
    legend?: {
      display?: boolean;
      position?: 'top' | 'bottom' | 'left' | 'right';
    };
    title?: {
      display?: boolean;
      text?: string;
    };
  };
  scales?: {
    x?: {
      display?: boolean;
      title?: {
        display?: boolean;
        text?: string;
      };
    };
    y?: {
      display?: boolean;
      beginAtZero?: boolean;
      title?: {
        display?: boolean;
        text?: string;
      };
    };
  };
}

@Component({
  selector: 'app-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="relative">
      <canvas
        #chartCanvas
        [style.height]="height"
        [style.width]="width"
      ></canvas>
      
      <div *ngIf="loading" class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
      
      <div *ngIf="error" class="absolute inset-0 flex items-center justify-center bg-error-50 text-error-600 text-sm">
        {{ error }}
      </div>
    </div>
  `
})
export class ChartComponent implements OnInit, OnDestroy, AfterViewInit {
  @Input() type: ChartType = 'line';
  @Input() data: ChartData = { labels: [], datasets: [] };
  @Input() options: ChartOptions = {};
  @Input() height = '400px';
  @Input() width = '100%';
  @Input() loading = false;
  @Input() error = '';

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

  private createChart(): void {
    if (!this.chartCanvas?.nativeElement) {
      return;
    }

    const ctx = this.chartCanvas.nativeElement.getContext('2d');
    if (!ctx) {
      return;
    }

    const config: ChartConfiguration = {
      type: this.type,
      data: this.data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        ...this.options
      }
    };

    this.chart = new Chart(ctx, config);
  }

  private updateChart(): void {
    if (!this.chart) {
      return;
    }

    this.chart.data = this.data;
    this.chart.options = {
      responsive: true,
      maintainAspectRatio: false,
      ...this.options
    };
    this.chart.update();
  }

  public refresh(): void {
    if (this.chart) {
      this.chart.update();
    }
  }
}