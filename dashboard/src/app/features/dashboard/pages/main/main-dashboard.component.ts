import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-main-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-4">Observer Eye Dashboard</h1>
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Welcome to Observer Eye</h2>
        <p class="text-gray-600 mb-4">Your comprehensive observability platform is ready.</p>
        <button 
          class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          (click)="handleClick()"
        >
          Get Started
        </button>
      </div>
    </div>
  `
})
export class MainDashboardComponent {
  handleClick() {
    console.log('Button clicked!');
  }
}