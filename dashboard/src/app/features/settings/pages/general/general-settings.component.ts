import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-general-settings',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6">
      <h1 class="text-2xl font-bold text-secondary-900">General Settings</h1>
      <p class="text-secondary-600 mt-2">Settings page is under construction.</p>
    </div>
  `
})
export class GeneralSettingsComponent {
}