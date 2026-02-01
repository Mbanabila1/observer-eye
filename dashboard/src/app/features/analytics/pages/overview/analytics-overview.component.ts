import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-analytics-overview',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6">
      <h1 class="text-2xl font-bold text-secondary-900">Analytics Overview</h1>
      <p class="text-secondary-600 mt-2">Analytics page is under construction.</p>
    </div>
  `
})
export class AnalyticsOverviewComponent {
}