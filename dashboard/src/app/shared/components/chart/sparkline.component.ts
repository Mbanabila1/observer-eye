import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Chart, ChartConfiguration, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

export type SparklineType = 'line' | 'bar' | 'area';

@Component({
  selector: 'app-sparkline',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="relative inline-block">
      <canvas
        #chartCanvas
        [style.height]="height"
        [style.width]="width"
      ></canvas>
      
      <div *ngIf="loading" class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75">
        <div class="animate-spin rounded-full h-3 w-3 border border-primary-600 border-t-transparent"></div>
      </div>
    </div>
  `
})
export class SparklineComponent implements OnInit, OnDestroy, AfterViewInit {
  @Input() data: number[] = [];
  @Input() type: SparklineType = 'line';
  @Input() color = '#3b82f6'; // primary-500
  @Input() height = '40px';
  @Input() width = '120px';
  @Input() loading = false;
  @Input() showPoints = false;
  @Input() smooth = true;
  @Input() fillArea = false;

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
    if (!this.chartCanvas?.nativeElement || this.loading || !this.data.length) {
      return;
    }

    const ctx = this.chartCanvas.nativeElement.getContext('2d');
    if (!ctx) {
      return;
    }

    const config: ChartConfiguration = {
      type: this.getChartType(),
      data: this.getChartData(),
      options: this.getChartOptions()
    };

    this.chart = new Chart(ctx, config);
  }

  private updateChart(): void {
    if (!this.chart) {
      return;
    }

    this.chart.data = this.getChartData();
    this.chart.update('none'); // No animation for sparklines
  }

  private getChartType(): 'line' | 'bar' {
    return this.type === 'bar' ? 'bar' : 'line';
  }

  private getChartData(): any {
    const labels = this.data.map((_, index) => index.toString());

    return {
      labels,
      datasets: [{
        data: this.data,
        borderColor: this.color,
        backgroundColor: this.fillArea || this.type === 'area' 
          ? this.hexToRgba(this.color, 0.2) 
          : this.type === 'bar' 
            ? this.color 
            : 'transparent',
        borderWidth: this.type === 'bar' ? 0 : 2,
        fill: this.fillArea || this.type === 'area',
        tension: this.smooth ? 0.4 : 0,
        pointRadius: this.showPoints ? 2 : 0,
        pointHoverRadius: this.showPoints ? 4 : 0,
        pointBackgroundColor: this.color,
        pointBorderColor: this.color,
        pointBorderWidth: 0,
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
      scales: {
        x: {
          display: false,
          grid: {
            display: false
          }
        },
        y: {
          display: false,
          grid: {
            display: false
          }
        }
      },
      elements: {
        point: {
          radius: 0,
          hoverRadius: 0
        }
      },
      animation: false,
      interaction: {
        intersect: false,
        mode: 'index' as const
      }
    };
  }

  private hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  public refresh(): void {
    if (this.chart) {
      this.chart.update('none');
    }
  }
}