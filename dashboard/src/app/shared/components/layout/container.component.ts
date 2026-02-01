import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export type ContainerSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
export type ContainerPadding = 'none' | 'sm' | 'md' | 'lg' | 'xl';

@Component({
  selector: 'app-container',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [class]="containerClasses">
      <ng-content></ng-content>
    </div>
  `
})
export class ContainerComponent {
  @Input() size: ContainerSize = 'xl';
  @Input() padding: ContainerPadding = 'md';
  @Input() centered = true;

  get containerClasses(): string {
    const baseClasses = ['w-full'];

    // Size classes
    const sizeClasses = {
      sm: ['max-w-sm'],
      md: ['max-w-md'],
      lg: ['max-w-lg'],
      xl: ['max-w-7xl'],
      '2xl': ['max-w-screen-2xl'],
      full: ['max-w-full']
    };

    baseClasses.push(...sizeClasses[this.size]);

    // Centering
    if (this.centered) {
      baseClasses.push('mx-auto');
    }

    // Padding classes
    const paddingClasses = {
      none: [],
      sm: ['px-4', 'py-2'],
      md: ['px-6', 'py-4'],
      lg: ['px-8', 'py-6'],
      xl: ['px-12', 'py-8']
    };

    baseClasses.push(...paddingClasses[this.padding]);

    return baseClasses.join(' ');
  }
}

@Component({
  selector: 'app-section',
  standalone: true,
  imports: [CommonModule],
  template: `
    <section [class]="sectionClasses">
      <ng-content></ng-content>
    </section>
  `
})
export class SectionComponent {
  @Input() padding: ContainerPadding = 'lg';
  @Input() background: 'none' | 'white' | 'gray' | 'primary' = 'none';
  @Input() bordered = false;
  @Input() rounded = false;

  get sectionClasses(): string {
    const baseClasses = [];

    // Padding classes
    const paddingClasses = {
      none: [],
      sm: ['py-8'],
      md: ['py-12'],
      lg: ['py-16'],
      xl: ['py-20']
    };

    baseClasses.push(...paddingClasses[this.padding]);

    // Background classes
    const backgroundClasses = {
      none: [],
      white: ['bg-white'],
      gray: ['bg-secondary-50'],
      primary: ['bg-primary-50']
    };

    baseClasses.push(...backgroundClasses[this.background]);

    // Border and rounded
    if (this.bordered) {
      baseClasses.push('border', 'border-secondary-200');
    }

    if (this.rounded) {
      baseClasses.push('rounded-lg');
    }

    return baseClasses.join(' ');
  }
}

@Component({
  selector: 'app-flex',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [class]="flexClasses">
      <ng-content></ng-content>
    </div>
  `
})
export class FlexComponent {
  @Input() direction: 'row' | 'col' | 'row-reverse' | 'col-reverse' = 'row';
  @Input() wrap: 'wrap' | 'nowrap' | 'wrap-reverse' = 'nowrap';
  @Input() justify: 'start' | 'end' | 'center' | 'between' | 'around' | 'evenly' = 'start';
  @Input() align: 'start' | 'end' | 'center' | 'baseline' | 'stretch' = 'start';
  @Input() gap: 'none' | 'sm' | 'md' | 'lg' | 'xl' = 'none';

  get flexClasses(): string {
    const baseClasses = ['flex'];

    // Direction classes
    const directionClasses = {
      row: ['flex-row'],
      col: ['flex-col'],
      'row-reverse': ['flex-row-reverse'],
      'col-reverse': ['flex-col-reverse']
    };

    baseClasses.push(...directionClasses[this.direction]);

    // Wrap classes
    const wrapClasses = {
      wrap: ['flex-wrap'],
      nowrap: ['flex-nowrap'],
      'wrap-reverse': ['flex-wrap-reverse']
    };

    baseClasses.push(...wrapClasses[this.wrap]);

    // Justify classes
    const justifyClasses = {
      start: ['justify-start'],
      end: ['justify-end'],
      center: ['justify-center'],
      between: ['justify-between'],
      around: ['justify-around'],
      evenly: ['justify-evenly']
    };

    baseClasses.push(...justifyClasses[this.justify]);

    // Align classes
    const alignClasses = {
      start: ['items-start'],
      end: ['items-end'],
      center: ['items-center'],
      baseline: ['items-baseline'],
      stretch: ['items-stretch']
    };

    baseClasses.push(...alignClasses[this.align]);

    // Gap classes
    const gapClasses = {
      none: [],
      sm: ['gap-2'],
      md: ['gap-4'],
      lg: ['gap-6'],
      xl: ['gap-8']
    };

    baseClasses.push(...gapClasses[this.gap]);

    return baseClasses.join(' ');
  }
}

@Component({
  selector: 'app-stack',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [class]="stackClasses">
      <ng-content></ng-content>
    </div>
  `
})
export class StackComponent {
  @Input() spacing: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' = 'md';
  @Input() align: 'start' | 'center' | 'end' | 'stretch' = 'stretch';
  @Input() divider = false;

  get stackClasses(): string {
    const baseClasses = ['flex', 'flex-col'];

    // Spacing classes
    const spacingClasses = {
      none: [],
      xs: ['space-y-1'],
      sm: ['space-y-2'],
      md: ['space-y-4'],
      lg: ['space-y-6'],
      xl: ['space-y-8']
    };

    baseClasses.push(...spacingClasses[this.spacing]);

    // Align classes
    const alignClasses = {
      start: ['items-start'],
      center: ['items-center'],
      end: ['items-end'],
      stretch: ['items-stretch']
    };

    baseClasses.push(...alignClasses[this.align]);

    // Divider
    if (this.divider) {
      baseClasses.push('divide-y', 'divide-secondary-200');
    }

    return baseClasses.join(' ');
  }
}