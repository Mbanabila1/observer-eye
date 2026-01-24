import { Component, Input, OnInit, OnDestroy, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TrendAnalysisWidget, TimeSeriesData } from '../../models/bi-models';

// Import Chart.js
declare var Chart: any;

@Component({
  selector: 'app-trend-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="trend-chart bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-lg font-semibold text-gray-900">{{ trendData.title }}</h3>
          <p class="text-sm text-gray-600">{{ trendData.timeRange }} trend analysis</p>
        </div>
        <div class="flex items-center space-x-2">
          <!-- Time range selector -->
          <select 
            (change)="onTimeRangeChange($event)"
            class="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">1 Hour</option>
            <option value="6h">6 Hours</option>
            <option value="24h" selected>24 Hours</option>
            <option value="7d">7 Days</option>
            <option value="30d">30 Days</option>
          </select>
          
          <!-- Chart type selector -->
          <select 
            (change)="onChartTypeChange($event)"
            class="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="line" selected>Line</option>
            <option value="area">Area</option>
            <option value="bar">Bar</option>
          </select>
        </div>
      </div>

      <!-- Chart Container -->
      <div class="chart-container relative" style="height: 300px;">
        <canvas #chartCanvas></canvas>
        
        <!-- Loading overlay -->
        @if (isLoading) {
          <div class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
            <div class="text-center">
              <svg class="animate-spin h-8 w-8 text-blue-600 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p class="text-sm text-gray-600">Loading chart data...</p>
            </div>
          </div>
        }
      </div>

      <!-- Chart Statistics -->
      <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-100">
        <div class="text-center">
          <div class="text-lg font-semibold text-gray-900">{{ formatValue(currentValue) }}</div>
          <div class="text-xs text-gray-600">Current</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-semibold text-gray-900">{{ formatValue(averageValue) }}</div>
          <div class="text-xs text-gray-600">Average</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-semibold text-gray-900">{{ formatValue(maxValue) }}</div>
          <div class="text-xs text-gray-600">Peak</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-semibold text-gray-900">{{ formatValue(minValue) }}</div>
          <div class="text-xs text-gray-600">Minimum</div>
        </div>
      </div>

      <!-- Trend Insights -->
      @if (trendInsight) {
        <div class="mt-4 p-3 bg-blue-50 rounded-lg">
          <div class="flex items-start space-x-2">
            <svg class="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div>
              <h4 class="text-sm font-medium text-blue-900">Trend Insight</h4>
              <p class="text-sm text-blue-800 mt-1">{{ trendInsight }}</p>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .trend-chart {
      animation: slideInUp 0.4s ease-out;
    }

    @keyframes slideInUp {
      from {
        opacity: 0;
        transform: translateY(15px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .chart-container {
      position: relative;
    }

    canvas {
      max-height: 300px;
    }
  `]
})
export class TrendChartComponent implements OnInit, AfterViewInit, OnDestroy {
  @Input({ required: true }) trendData!: TrendAnalysisWidget;
  @ViewChild('chartCanvas', { static: true }) chartCanvas!: ElementRef<HTMLCanvasElement>;

  chart: any;
  isLoading = false;
  currentTimeRange = '24h';
  currentChartType = 'line';

  // Computed statistics
  get currentValue(): number {
    const data = this.trendData.data;
    return data.length > 0 ? data[data.length - 1].value : 0;
  }

  get averageValue(): number {
    const data = this.trendData.data;
    if (data.length === 0) return 0;
    const sum = data.reduce((acc, point) => acc + point.value, 0);
    return sum / data.length;
  }

  get maxValue(): number {
    const data = this.trendData.data;
    return data.length > 0 ? Math.max(...data.map(point => point.value)) : 0;
  }

  get minValue(): number {
    const data = this.trendData.data;
    return data.length > 0 ? Math.min(...data.map(point => point.value)) : 0;
  }

  get trendInsight(): string | null {
    const data = this.trendData.data;
    if (data.length < 2) return null;

    const recent = data.slice(-5); // Last 5 data points
    const older = data.slice(-10, -5); // Previous 5 data points

    if (recent.length === 0 || older.length === 0) return null;

    const recentAvg = recent.reduce((sum, point) => sum + point.value, 0) / recent.length;
    const olderAvg = older.reduce((sum, point) => sum + point.value, 0) / older.length;

    const change = ((recentAvg - olderAvg) / olderAvg) * 100;

    if (Math.abs(change) < 5) {
      return 'Trend is stable with minimal variation over the selected period.';
    } else if (change > 0) {
      return `Upward trend detected with ${change.toFixed(1)}% increase in recent measurements.`;
    } else {
      return `Downward trend detected with ${Math.abs(change).toFixed(1)}% decrease in recent measurements.`;
    }
  }

  ngOnInit(): void {
    // Component initialization
  }

  ngAfterViewInit(): void {
    this.initializeChart();
  }

  ngOnDestroy(): void {
    if (this.chart) {
      this.chart.destroy();
    }
  }

  private initializeChart(): void {
    const ctx = this.chartCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    // Prepare data for Chart.js
    const labels = this.trendData.data.map(point => 
      new Date(point.timestamp).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    );
    
    const values = this.trendData.data.map(point => point.value);

    const chartConfig = {
      type: this.currentChartType,
      data: {
        labels: labels,
        datasets: [{
          label: this.trendData.metric,
          data: values,
          borderColor: '#3B82F6',
          backgroundColor: this.currentChartType === 'area' ? 'rgba(59, 130, 246, 0.1)' : '#3B82F6',
          borderWidth: 2,
          fill: this.currentChartType === 'area',
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: '#3B82F6',
          pointBorderColor: '#FFFFFF',
          pointBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#FFFFFF',
            bodyColor: '#FFFFFF',
            borderColor: '#3B82F6',
            borderWidth: 1,
            callbacks: {
              label: (context: any) => {
                return `${this.trendData.metric}: ${this.formatValue(context.parsed.y)}`;
              }
            }
          }
        },
        scales: {
          x: {
            display: true,
            grid: {
              display: false
            },
            ticks: {
              maxTicksLimit: 8,
              color: '#6B7280'
            }
          },
          y: {
            display: true,
            grid: {
              color: 'rgba(107, 114, 128, 0.1)'
            },
            ticks: {
              color: '#6B7280',
              callback: (value: any) => this.formatValue(value)
            }
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        },
        animation: {
          duration: 750,
          easing: 'easeInOutQuart'
        }
      }
    };

    // Create chart with error handling
    try {
      this.chart = new Chart(ctx, chartConfig);
    } catch (error) {
      console.error('Error creating chart:', error);
      // Fallback: show a simple message
      ctx.fillStyle = '#6B7280';
      ctx.font = '14px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('Chart unavailable', ctx.canvas.width / 2, ctx.canvas.height / 2);
    }
  }

  onTimeRangeChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.currentTimeRange = target.value;
    // In a real implementation, this would trigger a data refresh
    console.log('Time range changed to:', this.currentTimeRange);
  }

  onChartTypeChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.currentChartType = target.value;
    
    if (this.chart) {
      this.chart.destroy();
      this.initializeChart();
    }
  }

  formatValue(value: number): string {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
      return (value / 1000).toFixed(1) + 'K';
    } else if (value % 1 === 0) {
      return value.toString();
    } else {
      return value.toFixed(2);
    }
  }
}