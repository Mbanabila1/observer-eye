import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export type GridCols = 1 | 2 | 3 | 4 | 5 | 6 | 12;
export type GridGap = 'none' | 'sm' | 'md' | 'lg' | 'xl';
export type GridBreakpoint = 'sm' | 'md' | 'lg' | 'xl' | '2xl';

export interface ResponsiveGridCols {
  default?: GridCols;
  sm?: GridCols;
  md?: GridCols;
  lg?: GridCols;
  xl?: GridCols;
  '2xl'?: GridCols;
}

@Component({
  selector: 'app-grid',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [class]="gridClasses">
      <ng-content></ng-content>
    </div>
  `
})
export class GridComponent {
  @Input() cols: GridCols | ResponsiveGridCols = 1;
  @Input() gap: GridGap = 'md';
  @Input() autoRows = false;
  @Input() autoFit = false;
  @Input() minItemWidth = '250px';

  get gridClasses(): string {
    const baseClasses = ['grid'];

    // Handle gap
    const gapClasses = {
      none: 'gap-0',
      sm: 'gap-2',
      md: 'gap-4',
      lg: 'gap-6',
      xl: 'gap-8'
    };
    baseClasses.push(gapClasses[this.gap]);

    // Handle columns
    if (typeof this.cols === 'number') {
      // Simple number of columns
      const colClasses = {
        1: 'grid-cols-1',
        2: 'grid-cols-2',
        3: 'grid-cols-3',
        4: 'grid-cols-4',
        5: 'grid-cols-5',
        6: 'grid-cols-6',
        12: 'grid-cols-12'
      };
      baseClasses.push(colClasses[this.cols]);
    } else {
      // Responsive columns
      const responsiveCols = this.cols as ResponsiveGridCols;
      
      if (responsiveCols.default) {
        const colClasses = {
          1: 'grid-cols-1',
          2: 'grid-cols-2',
          3: 'grid-cols-3',
          4: 'grid-cols-4',
          5: 'grid-cols-5',
          6: 'grid-cols-6',
          12: 'grid-cols-12'
        };
        baseClasses.push(colClasses[responsiveCols.default]);
      }

      // Add responsive classes
      Object.entries(responsiveCols).forEach(([breakpoint, cols]) => {
        if (breakpoint !== 'default' && cols) {
          const prefix = breakpoint === '2xl' ? '2xl:' : `${breakpoint}:`;
          const colClasses = {
            1: `${prefix}grid-cols-1`,
            2: `${prefix}grid-cols-2`,
            3: `${prefix}grid-cols-3`,
            4: `${prefix}grid-cols-4`,
            5: `${prefix}grid-cols-5`,
            6: `${prefix}grid-cols-6`,
            12: `${prefix}grid-cols-12`
          };
          baseClasses.push(colClasses[cols as GridCols]);
        }
      });
    }

    // Handle auto-fit
    if (this.autoFit) {
      baseClasses.push(`grid-cols-[repeat(auto-fit,minmax(${this.minItemWidth},1fr))]`);
    }

    // Handle auto rows
    if (this.autoRows) {
      baseClasses.push('auto-rows-fr');
    }

    return baseClasses.join(' ');
  }
}

@Component({
  selector: 'app-grid-item',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [class]="itemClasses">
      <ng-content></ng-content>
    </div>
  `
})
export class GridItemComponent {
  @Input() colSpan: number = 1;
  @Input() rowSpan: number = 1;
  @Input() colStart?: number;
  @Input() rowStart?: number;

  get itemClasses(): string {
    const classes: string[] = [];

    // Column span
    if (this.colSpan > 1) {
      const spanClasses = {
        2: 'col-span-2',
        3: 'col-span-3',
        4: 'col-span-4',
        5: 'col-span-5',
        6: 'col-span-6',
        7: 'col-span-7',
        8: 'col-span-8',
        9: 'col-span-9',
        10: 'col-span-10',
        11: 'col-span-11',
        12: 'col-span-12'
      };
      classes.push(spanClasses[this.colSpan as keyof typeof spanClasses] || `col-span-${this.colSpan}`);
    }

    // Row span
    if (this.rowSpan > 1) {
      const spanClasses = {
        2: 'row-span-2',
        3: 'row-span-3',
        4: 'row-span-4',
        5: 'row-span-5',
        6: 'row-span-6'
      };
      classes.push(spanClasses[this.rowSpan as keyof typeof spanClasses] || `row-span-${this.rowSpan}`);
    }

    // Column start
    if (this.colStart) {
      classes.push(`col-start-${this.colStart}`);
    }

    // Row start
    if (this.rowStart) {
      classes.push(`row-start-${this.rowStart}`);
    }

    return classes.join(' ');
  }
}