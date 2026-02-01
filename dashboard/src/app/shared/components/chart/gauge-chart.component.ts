import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Chart, ChartConfiguration, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

export interface GaugeConfig {
  min: number;
  max: number;
  value: number;
  unit?: string;
  thresholds?: {
    low: number;
    medium: number;
    high: number;
  };
  colors?: {
    low: string;
    medium: string;
    high: string;
    background: string;
  };
}

@Component({
  selector: 'app-gauge-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="relative">
      <canvas
        #chartCanvas
        [style.height]="height"
        [style.width]="width"
      ></canvas>
      
      <!-- Center Value Display -->
      <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div class="text-center">
          <div class="text-3xl font-bold text-secondary-900">
            {{ displayValue }}
          </div>
          <div *ngIf="config.unit" class="text-sm text-secondary-500 mt-1">
            {{ config.unit }}
          </div>
          <div *ngIf="label" class="text-xs text-secondary-400 mt-1">
            {{ label }}
          </div>
        </div>
      </div>
      
      <div *ngIf="loading" class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 rounded-full">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
      
      <div *ngIf="error" class="absolute inset-0 flex items-center justify-center bg-error-50 text-error-600 text-sm rounded-full">
        <div class="text-center">
          <p class="font-medium">Error</p>
          <p class="text-xs">{{ error }}</p>
        </div>
      </div>
    </div>
  `
})
export class GaugeChartComponent implements OnInit, OnDestroy, AfterViewInit {
  @Input() config: GaugeConfig = {
    min: 0,
    max: 100,
    value: 0
  };
  @Input() label = '';
  @Input() height = '200px';
  @Input() width = '200px';
  @Input() loading = false;
  @Input() error = '';
  @Input() animated = true;

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

  get displayValue(): string {
    return this.config.value.toLocaleString();
  }

  get percentage(): number {
    const range = this.config.max - this.config.min;
    return ((this.config.value - this.config.min) / range) * 100;
  }

  get currentColor(): string {
    const colors = this.config.colors || {
      low: '#22c55e',    // success-500
      medium: '#f59e0b', // warning-500
      high: '#ef4444',   // error-500
      background: '#e5e7eb' // secondary-300
    };

    if (!this.config.thresholds) {
      return colors.low;
    }

    const { low, medium, high } = this.config.thresholds;
    const value = this.config.value;

    if (value <= low) {
      return colors.low;
    } else if (value <= medium) {
      return colors.medium;
    } else {
      return colors.high;
    }
  }

  private createChart(): void {
    if (!this.chartCanvas?.nativeElement || this.loading || this.error) {
      return;
    }

    const ctx = this.chartCanvas.nativeElement.getContext('2d');
    if (!ctx) {
      return;
    }

    const data = this.getChartData();
    const options = this.getChartOptions();

    const config: ChartConfiguration = {
      type: 'doughnut',
      data,
      options
    };

    this.chart = new Chart(ctx, config);
  }

  private updateChart(): void {
    if (!this.chart) {
      return;
    }

    this.chart.data = this.getChartData();
    this.chart.options = this.getChartOptions();
    this.chart.update(this.animated ? 'active' : 'none');
  }

  private getChartData(): any {
    const percentage = this.percentage;
    const remaining = 100 - percentage;

    const colors = this.config.colors || {
      low: '#22c55e',
      medium: '#f59e0b',
      high: '#ef4444',
      background: '#e5e7eb'
    };

    return {
      datasets: [{
        data: [percentage, remaining],
        backgroundColor: [
          this.currentColor,
          colors.background
        ],
        borderWidth: 0,
        cutout: '75%',
        circumference: 180,
        rotation: 270,
      }]
    };
  }

  private getChartOptions(): any {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          enabled: false
        }
      },
      animation: this.animated ? {
        duration: 1000,
        easing: 'easeInOutQuart'
      } : false,
      elements: {
        arc: {
          borderWidth: 0
        }
      }
    };
  }

  public refresh(): void {
    if (this.chart) {
      this.chart.update();
    }
  }
}