import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { ButtonComponent } from '../button/button.component';
import { Icons } from '../../utils/icons';

export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  type?: 'text' | 'number' | 'date' | 'boolean' | 'custom';
}

export interface TableRow {
  [key: string]: any;
}

export type SortDirection = 'asc' | 'desc' | null;

export interface SortState {
  column: string;
  direction: SortDirection;
}

@Component({
  selector: 'app-table',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, ButtonComponent],
  template: `
    <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
      <div *ngIf="loading" class="flex items-center justify-center p-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
      
      <div *ngIf="!loading" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-secondary-200">
          <!-- Header -->
          <thead class="bg-secondary-50">
            <tr>
              <th
                *ngFor="let column of columns"
                [class]="getHeaderClasses(column)"
                [style.width]="column.width"
                (click)="handleSort(column)"
              >
                <div class="flex items-center space-x-1">
                  <span>{{ column.label }}</span>
                  
                  <div *ngIf="column.sortable" class="flex flex-col">
                    <lucide-angular
                      [img]="Icons.chevronUp"
                      [size]="12"
                      [class]="getSortIconClasses(column.key, 'asc')"
                    ></lucide-angular>
                    <lucide-angular
                      [img]="Icons.chevronDown"
                      [size]="12"
                      [class]="getSortIconClasses(column.key, 'desc')"
                      class="-mt-1"
                    ></lucide-angular>
                  </div>
                </div>
              </th>
              
              <th *ngIf="hasActions" class="relative px-6 py-3">
                <span class="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          
          <!-- Body -->
          <tbody class="bg-white divide-y divide-secondary-200">
            <tr *ngIf="sortedData.length === 0" class="hover:bg-secondary-50">
              <td [attr.colspan]="columns.length + (hasActions ? 1 : 0)" class="px-6 py-8 text-center text-secondary-500">
                {{ emptyMessage }}
              </td>
            </tr>
            
            <tr
              *ngFor="let row of paginatedData; let i = index"
              [class]="getRowClasses(row, i)"
              (click)="handleRowClick(row)"
            >
              <td
                *ngFor="let column of columns"
                [class]="getCellClasses(column)"
              >
                <ng-container [ngSwitch]="column.type">
                  <!-- Text -->
                  <span *ngSwitchCase="'text'">{{ getCellValue(row, column.key) }}</span>
                  
                  <!-- Number -->
                  <span *ngSwitchCase="'number'" class="font-mono">
                    {{ getCellValue(row, column.key) | number }}
                  </span>
                  
                  <!-- Date -->
                  <span *ngSwitchCase="'date'">
                    {{ getCellValue(row, column.key) | date:'short' }}
                  </span>
                  
                  <!-- Boolean -->
                  <span *ngSwitchCase="'boolean'">
                    <span
                      [class]="getBooleanClasses(getCellValue(row, column.key))"
                    >
                      {{ getCellValue(row, column.key) ? 'Yes' : 'No' }}
                    </span>
                  </span>
                  
                  <!-- Custom -->
                  <ng-container *ngSwitchCase="'custom'">
                    <ng-content [select]="'[slot=cell-' + column.key + ']'"></ng-content>
                  </ng-container>
                  
                  <!-- Default -->
                  <span *ngSwitchDefault>{{ getCellValue(row, column.key) }}</span>
                </ng-container>
              </td>
              
              <!-- Actions -->
              <td *ngIf="hasActions" class="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                <ng-content select="[slot=actions]"></ng-content>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination -->
      <div *ngIf="showPagination && totalPages > 1" class="bg-white px-4 py-3 border-t border-secondary-200 sm:px-6">
        <div class="flex items-center justify-between">
          <div class="flex-1 flex justify-between sm:hidden">
            <app-button
              variant="outline"
              size="sm"
              [disabled]="currentPage === 1"
              (clicked)="goToPage(currentPage - 1)"
            >
              Previous
            </app-button>
            <app-button
              variant="outline"
              size="sm"
              [disabled]="currentPage === totalPages"
              (clicked)="goToPage(currentPage + 1)"
            >
              Next
            </app-button>
          </div>
          
          <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p class="text-sm text-secondary-700">
                Showing
                <span class="font-medium">{{ startIndex + 1 }}</span>
                to
                <span class="font-medium">{{ endIndex > data.length ? data.length : endIndex }}</span>
                of
                <span class="font-medium">{{ data.length }}</span>
                results
              </p>
            </div>
            
            <div class="flex items-center space-x-2">
              <app-button
                variant="outline"
                size="sm"
                leftIcon="chevronLeft"
                [disabled]="currentPage === 1"
                (clicked)="goToPage(currentPage - 1)"
              >
                Previous
              </app-button>
              
              <div class="flex space-x-1">
                <app-button
                  *ngFor="let page of visiblePages"
                  [variant]="page === currentPage ? 'primary' : 'ghost'"
                  size="sm"
                  (clicked)="goToPage(page)"
                >
                  {{ page }}
                </app-button>
              </div>
              
              <app-button
                variant="outline"
                size="sm"
                rightIcon="chevronRight"
                [disabled]="currentPage === totalPages"
                (clicked)="goToPage(currentPage + 1)"
              >
                Next
              </app-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class TableComponent implements OnInit {
  @Input() columns: TableColumn[] = [];
  @Input() data: TableRow[] = [];
  @Input() loading = false;
  @Input() emptyMessage = 'No data available';
  @Input() sortable = true;
  @Input() hoverable = true;
  @Input() striped = false;
  @Input() showPagination = true;
  @Input() pageSize = 10;
  @Input() hasActions = false;

  @Output() rowClicked = new EventEmitter<TableRow>();
  @Output() sortChanged = new EventEmitter<SortState>();
  @Output() pageChanged = new EventEmitter<number>();

  currentPage = 1;
  sortState: SortState = { column: '', direction: null };

  // Make Icons available in template
  Icons = Icons;

  ngOnInit(): void {
    // Initialize component
  }

  get sortedData(): TableRow[] {
    if (!this.sortState.column || !this.sortState.direction) {
      return this.data;
    }

    return [...this.data].sort((a, b) => {
      const aValue = this.getCellValue(a, this.sortState.column);
      const bValue = this.getCellValue(b, this.sortState.column);

      let comparison = 0;
      if (aValue < bValue) comparison = -1;
      if (aValue > bValue) comparison = 1;

      return this.sortState.direction === 'desc' ? -comparison : comparison;
    });
  }

  get paginatedData(): TableRow[] {
    if (!this.showPagination) {
      return this.sortedData;
    }

    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    return this.sortedData.slice(start, end);
  }

  get totalPages(): number {
    return Math.ceil(this.data.length / this.pageSize);
  }

  get startIndex(): number {
    return (this.currentPage - 1) * this.pageSize;
  }

  get endIndex(): number {
    return this.startIndex + this.pageSize;
  }

  get visiblePages(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;
    const half = Math.floor(maxVisible / 2);

    let start = Math.max(1, this.currentPage - half);
    let end = Math.min(this.totalPages, start + maxVisible - 1);

    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }

  getHeaderClasses(column: TableColumn): string {
    const baseClasses = [
      'px-6',
      'py-3',
      'text-xs',
      'font-medium',
      'text-secondary-500',
      'uppercase',
      'tracking-wider'
    ];

    const alignClasses = {
      left: ['text-left'],
      center: ['text-center'],
      right: ['text-right']
    };

    baseClasses.push(...alignClasses[column.align || 'left']);

    if (column.sortable) {
      baseClasses.push('cursor-pointer', 'hover:bg-secondary-100', 'select-none');
    }

    return baseClasses.join(' ');
  }

  getCellClasses(column: TableColumn): string {
    const baseClasses = ['px-6', 'py-4', 'whitespace-nowrap'];

    const alignClasses = {
      left: ['text-left'],
      center: ['text-center'],
      right: ['text-right']
    };

    baseClasses.push(...alignClasses[column.align || 'left']);

    return baseClasses.join(' ');
  }

  getRowClasses(row: TableRow, index: number): string {
    const baseClasses: string[] = [];

    if (this.hoverable) {
      baseClasses.push('hover:bg-secondary-50', 'cursor-pointer');
    }

    if (this.striped && index % 2 === 1) {
      baseClasses.push('bg-secondary-25');
    }

    return baseClasses.join(' ');
  }

  getSortIconClasses(columnKey: string, direction: 'asc' | 'desc'): string {
    const baseClasses = ['text-secondary-400'];

    if (this.sortState.column === columnKey && this.sortState.direction === direction) {
      baseClasses.push('text-primary-600');
    }

    return baseClasses.join(' ');
  }

  getBooleanClasses(value: boolean): string {
    const baseClasses = ['inline-flex', 'px-2', 'py-1', 'text-xs', 'font-medium', 'rounded-full'];

    if (value) {
      baseClasses.push('bg-success-100', 'text-success-800');
    } else {
      baseClasses.push('bg-error-100', 'text-error-800');
    }

    return baseClasses.join(' ');
  }

  getCellValue(row: TableRow, key: string): any {
    return key.split('.').reduce((obj, k) => obj?.[k], row);
  }

  handleSort(column: TableColumn): void {
    if (!column.sortable) return;

    let direction: SortDirection = 'asc';

    if (this.sortState.column === column.key) {
      if (this.sortState.direction === 'asc') {
        direction = 'desc';
      } else if (this.sortState.direction === 'desc') {
        direction = null;
      }
    }

    this.sortState = {
      column: direction ? column.key : '',
      direction
    };

    this.sortChanged.emit(this.sortState);
  }

  handleRowClick(row: TableRow): void {
    this.rowClicked.emit(row);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.pageChanged.emit(page);
    }
  }
}