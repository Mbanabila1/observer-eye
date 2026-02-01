import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';

// Import all components
import { ButtonComponent } from './components/button/button.component';
import { InputComponent } from './components/input/input.component';
import { SelectComponent } from './components/select/select.component';
import { CheckboxComponent } from './components/checkbox/checkbox.component';
import { ModalComponent } from './components/modal/modal.component';
import { ProgressComponent } from './components/progress/progress.component';
import { AlertComponent } from './components/alert/alert.component';
import { StatusBadgeComponent } from './components/status-badge/status-badge.component';
import { TooltipComponent } from './components/tooltip/tooltip.component';
import { DropdownComponent } from './components/dropdown/dropdown.component';

// Layout Components
import { CardComponent } from './components/card/card.component';
import { GridComponent, GridItemComponent } from './components/grid/grid.component';
import { ContainerComponent, SectionComponent, FlexComponent, StackComponent } from './components/layout/container.component';
import { BreadcrumbComponent } from './components/breadcrumb/breadcrumb.component';

// Navigation Components
import { TabsComponent, TabComponent } from './components/tabs/tabs.component';
import { AccordionComponent, AccordionItemComponent } from './components/accordion/accordion.component';

// Form Components
import { FormGroupComponent, FormSectionComponent, FormActionsComponent } from './components/form/form-group.component';

// Data Visualization Components
import { ChartComponent } from './components/chart/chart.component';
import { AdvancedChartComponent } from './components/chart/advanced-chart.component';
import { GaugeChartComponent } from './components/chart/gauge-chart.component';
import { SparklineComponent } from './components/chart/sparkline.component';
import { MetricCardComponent } from './components/metric-card/metric-card.component';
import { TableComponent } from './components/table/table.component';
import { DashboardWidgetComponent } from './components/dashboard-widget/dashboard-widget.component';

// Password Components
import { PasswordInputComponent } from './components/password-input/password-input.component';
import { PasswordStrengthComponent } from './components/password-strength/password-strength.component';

const COMPONENTS = [
  // Basic UI Components
  ButtonComponent,
  InputComponent,
  SelectComponent,
  CheckboxComponent,
  ModalComponent,
  ProgressComponent,
  AlertComponent,
  StatusBadgeComponent,
  TooltipComponent,
  DropdownComponent,
  
  // Layout Components
  CardComponent,
  GridComponent,
  GridItemComponent,
  ContainerComponent,
  SectionComponent,
  FlexComponent,
  StackComponent,
  BreadcrumbComponent,
  
  // Navigation Components
  TabsComponent,
  TabComponent,
  AccordionComponent,
  AccordionItemComponent,
  
  // Form Components
  FormGroupComponent,
  FormSectionComponent,
  FormActionsComponent,
  
  // Data Visualization Components
  ChartComponent,
  AdvancedChartComponent,
  GaugeChartComponent,
  SparklineComponent,
  MetricCardComponent,
  TableComponent,
  DashboardWidgetComponent,
  
  // Password Components
  PasswordInputComponent,
  PasswordStrengthComponent
];

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule,
    LucideAngularModule,
    ...COMPONENTS
  ],
  exports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule,
    LucideAngularModule,
    ...COMPONENTS
  ]
})
export class SharedModule { }