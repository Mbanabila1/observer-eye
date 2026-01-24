"""
Report Generator

Automated report generation with multiple output formats, scheduling capabilities,
and template-based report creation for the BI analytics engine.
"""

import asyncio
import time
import os
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from jinja2 import Environment, FileSystemLoader, Template
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import structlog

from .models import (
    ReportRequest, ReportResult, ReportFormat, ReportType, 
    AnalyticsResult, ScheduleConfig, ScheduleFrequency
)
from .analytics_engine import BIAnalyticsEngine

logger = structlog.get_logger(__name__)

class ReportGenerator:
    """
    Advanced Report Generator for BI Analytics
    
    Provides comprehensive report generation capabilities including:
    - Multiple output formats (PDF, Excel, HTML, PowerPoint)
    - Template-based report creation
    - Automated scheduling and distribution
    - Interactive charts and visualizations
    - Executive and operational report types
    """
    
    def __init__(self, 
                 analytics_engine: BIAnalyticsEngine,
                 reports_directory: str = "reports",
                 templates_directory: str = "templates"):
        
        self.analytics_engine = analytics_engine
        self.reports_dir = Path(reports_directory)
        self.templates_dir = Path(templates_directory)
        
        # Create directories if they don't exist
        self.reports_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
        
        # Report generation statistics
        self._report_stats = {
            'total_reports_generated': 0,
            'successful_reports': 0,
            'failed_reports': 0,
            'reports_by_format': {},
            'reports_by_type': {},
            'average_generation_time_ms': 0.0
        }
        
        # Scheduled reports
        self._scheduled_reports = {}
        self._scheduler_task = None
        
        # Chart styling
        self.chart_theme = {
            'color_palette': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
            'background_color': 'white',
            'grid_color': '#f0f0f0',
            'text_color': '#333333'
        }
        
        logger.info("Report Generator initialized",
                   reports_directory=str(self.reports_dir),
                   templates_directory=str(self.templates_dir))
    
    async def generate_report(self, request: ReportRequest) -> ReportResult:
        """
        Generate a report based on the request parameters
        
        Args:
            request: Report generation request
            
        Returns:
            ReportResult with generated report information
        """
        start_time = time.time()
        self._report_stats['total_reports_generated'] += 1
        
        try:
            logger.info("Starting report generation",
                       request_id=request.request_id,
                       report_type=request.report_type.value,
                       report_format=request.report_format.value)
            
            # Execute analytics request first
            analytics_result = await self.analytics_engine.process_analytics_request(request.analytics_request)
            
            if analytics_result.status != "success":
                raise Exception(f"Analytics processing failed: {analytics_result.error_message}")
            
            # Generate report based on format
            report_id = f"report_{request.report_type.value}_{int(time.time())}"
            
            if request.report_format == ReportFormat.PDF:
                file_path = await self._generate_pdf_report(request, analytics_result, report_id)
            elif request.report_format == ReportFormat.EXCEL:
                file_path = await self._generate_excel_report(request, analytics_result, report_id)
            elif request.report_format == ReportFormat.HTML:
                file_path = await self._generate_html_report(request, analytics_result, report_id)
            elif request.report_format == ReportFormat.CSV:
                file_path = await self._generate_csv_report(request, analytics_result, report_id)
            elif request.report_format == ReportFormat.JSON:
                file_path = await self._generate_json_report(request, analytics_result, report_id)
            else:
                raise Exception(f"Unsupported report format: {request.report_format.value}")
            
            # Get file size
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            generation_time_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            self._report_stats['successful_reports'] += 1
            self._update_format_stats(request.report_format)
            self._update_type_stats(request.report_type)
            self._update_average_generation_time(generation_time_ms)
            
            result = ReportResult(
                request_id=request.request_id,
                report_id=report_id,
                status="success",
                report_format=request.report_format,
                file_path=str(file_path),
                file_size_bytes=file_size,
                analytics_result=analytics_result,
                generation_time_ms=generation_time_ms
            )
            
            logger.info("Report generated successfully",
                       request_id=request.request_id,
                       report_id=report_id,
                       file_size_bytes=file_size,
                       generation_time_ms=generation_time_ms)
            
            return result
            
        except Exception as e:
            self._report_stats['failed_reports'] += 1
            generation_time_ms = (time.time() - start_time) * 1000
            
            logger.error("Report generation failed",
                        request_id=request.request_id,
                        error=str(e),
                        generation_time_ms=generation_time_ms)
            
            return ReportResult(
                request_id=request.request_id,
                report_id="",
                status="error",
                report_format=request.report_format,
                generation_time_ms=generation_time_ms,
                error_message=str(e)
            )
    
    async def _generate_pdf_report(self, request: ReportRequest, 
                                  analytics_result: AnalyticsResult, report_id: str) -> str:
        """Generate PDF report"""
        
        file_path = self.reports_dir / f"{report_id}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(str(file_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1f77b4')
        )
        story.append(Paragraph(request.title, title_style))
        story.append(Spacer(1, 12))
        
        # Description
        if request.description:
            story.append(Paragraph(request.description, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Executive Summary
        if request.include_executive_summary:
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            summary = await self._generate_executive_summary(analytics_result)
            story.append(Paragraph(summary, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Analytics Results
        story.append(Paragraph("Analytics Results", styles['Heading2']))
        
        # Add data tables
        if request.include_tables and analytics_result.data.get('aggregations'):
            story.append(Paragraph("Key Metrics", styles['Heading3']))
            table_data = self._prepare_table_data(analytics_result.data['aggregations'])
            if table_data:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 12))
        
        # Add charts
        if request.include_charts:
            chart_paths = await self._generate_charts_for_pdf(analytics_result, report_id)
            for chart_path in chart_paths:
                if os.path.exists(chart_path):
                    story.append(Image(chart_path, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 12))
        
        # Metadata
        story.append(Paragraph("Report Metadata", styles['Heading3']))
        metadata_text = f"""
        Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>
        Data Sources: {', '.join(request.analytics_request.data_sources)}<br/>
        Time Range: {request.analytics_request.time_range.start_time.strftime('%Y-%m-%d')} to {request.analytics_request.time_range.end_time.strftime('%Y-%m-%d')}<br/>
        Rows Processed: {analytics_result.row_count:,}<br/>
        Processing Time: {analytics_result.processing_time_ms:.2f}ms
        """
        story.append(Paragraph(metadata_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return str(file_path)
    
    async def _generate_excel_report(self, request: ReportRequest, 
                                   analytics_result: AnalyticsResult, report_id: str) -> str:
        """Generate Excel report"""
        
        file_path = self.reports_dir / f"{report_id}.xlsx"
        
        with pd.ExcelWriter(str(file_path), engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Create formats
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'font_color': '#1f77b4'
            })
            
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#f0f0f0',
                'border': 1
            })
            
            # Summary sheet
            summary_sheet = workbook.add_worksheet('Summary')
            summary_sheet.write('A1', request.title, title_format)
            
            row = 3
            if request.description:
                summary_sheet.write(f'A{row}', 'Description:')
                summary_sheet.write(f'B{row}', request.description)
                row += 2
            
            # Executive summary
            if request.include_executive_summary:
                summary_sheet.write(f'A{row}', 'Executive Summary:')
                row += 1
                summary = await self._generate_executive_summary(analytics_result)
                summary_sheet.write(f'A{row}', summary)
                row += 2
            
            # Metadata
            summary_sheet.write(f'A{row}', 'Report Metadata', header_format)
            row += 1
            metadata_items = [
                ('Generated', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')),
                ('Data Sources', ', '.join(request.analytics_request.data_sources)),
                ('Time Range Start', request.analytics_request.time_range.start_time.strftime('%Y-%m-%d %H:%M:%S')),
                ('Time Range End', request.analytics_request.time_range.end_time.strftime('%Y-%m-%d %H:%M:%S')),
                ('Rows Processed', f"{analytics_result.row_count:,}"),
                ('Processing Time (ms)', f"{analytics_result.processing_time_ms:.2f}")
            ]
            
            for label, value in metadata_items:
                summary_sheet.write(f'A{row}', label)
                summary_sheet.write(f'B{row}', value)
                row += 1
            
            # Raw data sheet
            if analytics_result.data.get('raw_data_sample'):
                raw_data_df = pd.DataFrame(analytics_result.data['raw_data_sample'])
                raw_data_df.to_excel(writer, sheet_name='Raw Data', index=False)
            
            # Aggregations sheet
            if analytics_result.data.get('aggregations'):
                agg_data = []
                for key, value in analytics_result.data['aggregations'].items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            agg_data.append({'Metric': f"{key}.{sub_key}", 'Value': sub_value})
                    else:
                        agg_data.append({'Metric': key, 'Value': value})
                
                if agg_data:
                    agg_df = pd.DataFrame(agg_data)
                    agg_df.to_excel(writer, sheet_name='Aggregations', index=False)
            
            # Metrics sheet
            if analytics_result.data.get('metrics'):
                metrics_data = []
                for metric_type, metric_values in analytics_result.data['metrics'].items():
                    if isinstance(metric_values, dict):
                        for column, value in metric_values.items():
                            metrics_data.append({
                                'Metric Type': metric_type,
                                'Column': column,
                                'Value': value
                            })
                
                if metrics_data:
                    metrics_df = pd.DataFrame(metrics_data)
                    metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
        
        return str(file_path)
    
    async def _generate_html_report(self, request: ReportRequest, 
                                  analytics_result: AnalyticsResult, report_id: str) -> str:
        """Generate HTML report"""
        
        file_path = self.reports_dir / f"{report_id}.html"
        
        # Try to load custom template, fall back to default
        try:
            if request.template_id:
                template = self.jinja_env.get_template(f"{request.template_id}.html")
            else:
                template = self.jinja_env.get_template("default_report.html")
        except:
            # Create default template if none exists
            template = Template(self._get_default_html_template())
        
        # Prepare template context
        context = {
            'title': request.title,
            'description': request.description,
            'report_type': request.report_type.value,
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'analytics_result': analytics_result,
            'include_charts': request.include_charts,
            'include_tables': request.include_tables,
            'include_executive_summary': request.include_executive_summary
        }
        
        # Add executive summary
        if request.include_executive_summary:
            context['executive_summary'] = await self._generate_executive_summary(analytics_result)
        
        # Generate charts for HTML
        if request.include_charts:
            context['charts'] = await self._generate_charts_for_html(analytics_result, report_id)
        
        # Render template
        html_content = template.render(**context)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(file_path)
    
    async def _generate_csv_report(self, request: ReportRequest, 
                                 analytics_result: AnalyticsResult, report_id: str) -> str:
        """Generate CSV report"""
        
        file_path = self.reports_dir / f"{report_id}.csv"
        
        # Combine all available data
        all_data = []
        
        # Add raw data sample
        if analytics_result.data.get('raw_data_sample'):
            raw_df = pd.DataFrame(analytics_result.data['raw_data_sample'])
            raw_df['data_type'] = 'raw_data'
            all_data.append(raw_df)
        
        # Add aggregations as rows
        if analytics_result.data.get('aggregations'):
            agg_rows = []
            for key, value in analytics_result.data['aggregations'].items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        agg_rows.append({
                            'data_type': 'aggregation',
                            'metric_name': f"{key}.{sub_key}",
                            'value': sub_value,
                            'timestamp': datetime.utcnow()
                        })
                else:
                    agg_rows.append({
                        'data_type': 'aggregation',
                        'metric_name': key,
                        'value': value,
                        'timestamp': datetime.utcnow()
                    })
            
            if agg_rows:
                agg_df = pd.DataFrame(agg_rows)
                all_data.append(agg_df)
        
        # Combine and save
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True, sort=False)
            combined_df.to_csv(file_path, index=False)
        else:
            # Create empty CSV with headers
            pd.DataFrame({'message': ['No data available']}).to_csv(file_path, index=False)
        
        return str(file_path)
    
    async def _generate_json_report(self, request: ReportRequest, 
                                  analytics_result: AnalyticsResult, report_id: str) -> str:
        """Generate JSON report"""
        
        file_path = self.reports_dir / f"{report_id}.json"
        
        # Prepare report data
        report_data = {
            'report_metadata': {
                'report_id': report_id,
                'title': request.title,
                'description': request.description,
                'report_type': request.report_type.value,
                'generated_at': datetime.utcnow().isoformat(),
                'data_sources': request.analytics_request.data_sources,
                'time_range': {
                    'start': request.analytics_request.time_range.start_time.isoformat(),
                    'end': request.analytics_request.time_range.end_time.isoformat()
                }
            },
            'analytics_result': {
                'status': analytics_result.status,
                'row_count': analytics_result.row_count,
                'processing_time_ms': analytics_result.processing_time_ms,
                'data': analytics_result.data,
                'metadata': analytics_result.metadata
            }
        }
        
        # Add executive summary
        if request.include_executive_summary:
            report_data['executive_summary'] = await self._generate_executive_summary(analytics_result)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return str(file_path)
    
    async def _generate_executive_summary(self, analytics_result: AnalyticsResult) -> str:
        """Generate executive summary from analytics results"""
        
        summary_parts = []
        
        # Data overview
        summary_parts.append(f"This report analyzes {analytics_result.row_count:,} data points processed in {analytics_result.processing_time_ms:.2f}ms.")
        
        # Key findings from aggregations
        if analytics_result.data.get('aggregations'):
            agg_count = len(analytics_result.data['aggregations'])
            summary_parts.append(f"Analysis includes {agg_count} key metrics and aggregations.")
        
        # Data quality insights
        if analytics_result.data.get('data_quality'):
            quality_score = analytics_result.data['data_quality'].get('overall_score', 0)
            if quality_score > 0.9:
                summary_parts.append("Data quality is excellent with high completeness and accuracy.")
            elif quality_score > 0.7:
                summary_parts.append("Data quality is good with minor completeness or accuracy issues.")
            else:
                summary_parts.append("Data quality requires attention due to completeness or accuracy concerns.")
        
        # Performance insights
        if analytics_result.data.get('insights'):
            insights = analytics_result.data['insights']
            
            performance_insights = insights.get('performance_insights', [])
            if performance_insights:
                summary_parts.append(f"Identified {len(performance_insights)} performance-related issues requiring attention.")
            
            anomaly_insights = insights.get('anomaly_insights', [])
            if anomaly_insights:
                summary_parts.append(f"Detected {len(anomaly_insights)} data anomalies that may indicate system issues.")
        
        # Recommendations
        if analytics_result.data.get('insights', {}).get('recommendations'):
            rec_count = len(analytics_result.data['insights']['recommendations'])
            summary_parts.append(f"Report includes {rec_count} actionable recommendations for improvement.")
        
        return ' '.join(summary_parts)
    
    def _prepare_table_data(self, aggregations: Dict[str, Any]) -> List[List[str]]:
        """Prepare table data for PDF reports"""
        
        table_data = [['Metric', 'Value']]
        
        for key, value in aggregations.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    formatted_value = f"{sub_value:.2f}" if isinstance(sub_value, (int, float)) else str(sub_value)
                    table_data.append([f"{key}.{sub_key}", formatted_value])
            else:
                formatted_value = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
                table_data.append([key, formatted_value])
        
        return table_data
    
    async def _generate_charts_for_pdf(self, analytics_result: AnalyticsResult, report_id: str) -> List[str]:
        """Generate charts for PDF reports"""
        
        chart_paths = []
        
        try:
            # Set matplotlib style
            plt.style.use('default')
            sns.set_palette(self.chart_theme['color_palette'])
            
            # Generate aggregations chart
            if analytics_result.data.get('aggregations'):
                fig, ax = plt.subplots(figsize=(10, 6))
                
                metrics = []
                values = []
                
                for key, value in analytics_result.data['aggregations'].items():
                    if isinstance(value, (int, float)):
                        metrics.append(key)
                        values.append(value)
                
                if metrics and values:
                    bars = ax.bar(metrics, values, color=self.chart_theme['color_palette'][:len(metrics)])
                    ax.set_title('Key Metrics Overview', fontsize=14, fontweight='bold')
                    ax.set_ylabel('Value')
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    
                    chart_path = self.reports_dir / f"{report_id}_aggregations_chart.png"
                    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                    chart_paths.append(str(chart_path))
                    plt.close()
            
            # Generate time series chart if raw data is available
            if analytics_result.data.get('raw_data_sample'):
                raw_data = pd.DataFrame(analytics_result.data['raw_data_sample'])
                
                if 'timestamp' in raw_data.columns:
                    numeric_columns = raw_data.select_dtypes(include=[np.number]).columns
                    
                    if len(numeric_columns) > 0:
                        fig, ax = plt.subplots(figsize=(12, 6))
                        
                        # Convert timestamp to datetime
                        raw_data['timestamp'] = pd.to_datetime(raw_data['timestamp'])
                        
                        # Plot up to 3 numeric columns
                        for i, col in enumerate(numeric_columns[:3]):
                            ax.plot(raw_data['timestamp'], raw_data[col], 
                                   label=col, color=self.chart_theme['color_palette'][i])
                        
                        ax.set_title('Time Series Data', fontsize=14, fontweight='bold')
                        ax.set_xlabel('Time')
                        ax.set_ylabel('Value')
                        ax.legend()
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        
                        chart_path = self.reports_dir / f"{report_id}_timeseries_chart.png"
                        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                        chart_paths.append(str(chart_path))
                        plt.close()
        
        except Exception as e:
            logger.error("Error generating charts for PDF", error=str(e))
        
        return chart_paths
    
    async def _generate_charts_for_html(self, analytics_result: AnalyticsResult, report_id: str) -> List[str]:
        """Generate interactive charts for HTML reports"""
        
        charts = []
        
        try:
            # Generate aggregations chart
            if analytics_result.data.get('aggregations'):
                metrics = []
                values = []
                
                for key, value in analytics_result.data['aggregations'].items():
                    if isinstance(value, (int, float)):
                        metrics.append(key)
                        values.append(value)
                
                if metrics and values:
                    fig = go.Figure(data=[
                        go.Bar(x=metrics, y=values, 
                              marker_color=self.chart_theme['color_palette'][:len(metrics)])
                    ])
                    
                    fig.update_layout(
                        title='Key Metrics Overview',
                        xaxis_title='Metrics',
                        yaxis_title='Value',
                        template='plotly_white'
                    )
                    
                    chart_html = fig.to_html(include_plotlyjs='cdn', div_id=f"chart_aggregations_{report_id}")
                    charts.append(chart_html)
            
            # Generate time series chart
            if analytics_result.data.get('raw_data_sample'):
                raw_data = pd.DataFrame(analytics_result.data['raw_data_sample'])
                
                if 'timestamp' in raw_data.columns:
                    numeric_columns = raw_data.select_dtypes(include=[np.number]).columns
                    
                    if len(numeric_columns) > 0:
                        fig = go.Figure()
                        
                        # Convert timestamp to datetime
                        raw_data['timestamp'] = pd.to_datetime(raw_data['timestamp'])
                        
                        # Add up to 3 numeric columns
                        for i, col in enumerate(numeric_columns[:3]):
                            fig.add_trace(go.Scatter(
                                x=raw_data['timestamp'],
                                y=raw_data[col],
                                mode='lines+markers',
                                name=col,
                                line=dict(color=self.chart_theme['color_palette'][i])
                            ))
                        
                        fig.update_layout(
                            title='Time Series Data',
                            xaxis_title='Time',
                            yaxis_title='Value',
                            template='plotly_white'
                        )
                        
                        chart_html = fig.to_html(include_plotlyjs='cdn', div_id=f"chart_timeseries_{report_id}")
                        charts.append(chart_html)
        
        except Exception as e:
            logger.error("Error generating charts for HTML", error=str(e))
        
        return charts
    
    def _get_default_html_template(self) -> str:
        """Get default HTML template"""
        
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { border-bottom: 2px solid #1f77b4; padding-bottom: 20px; margin-bottom: 30px; }
                .title { color: #1f77b4; font-size: 28px; margin: 0; }
                .description { color: #666; margin-top: 10px; }
                .section { margin: 30px 0; }
                .section-title { color: #333; font-size: 20px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
                .metadata { background: #f9f9f9; padding: 15px; border-radius: 5px; }
                .chart-container { margin: 20px 0; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1 class="title">{{ title }}</h1>
                {% if description %}
                <p class="description">{{ description }}</p>
                {% endif %}
            </div>
            
            {% if include_executive_summary and executive_summary %}
            <div class="section">
                <h2 class="section-title">Executive Summary</h2>
                <p>{{ executive_summary }}</p>
            </div>
            {% endif %}
            
            {% if include_charts and charts %}
            <div class="section">
                <h2 class="section-title">Charts</h2>
                {% for chart in charts %}
                <div class="chart-container">{{ chart|safe }}</div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if include_tables and analytics_result.data.aggregations %}
            <div class="section">
                <h2 class="section-title">Key Metrics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    {% for key, value in analytics_result.data.aggregations.items() %}
                    <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
                    {% endfor %}
                </table>
            </div>
            {% endif %}
            
            <div class="section">
                <h2 class="section-title">Report Metadata</h2>
                <div class="metadata">
                    <p><strong>Generated:</strong> {{ generated_at }}</p>
                    <p><strong>Report Type:</strong> {{ report_type }}</p>
                    <p><strong>Rows Processed:</strong> {{ analytics_result.row_count|default(0) }}</p>
                    <p><strong>Processing Time:</strong> {{ "%.2f"|format(analytics_result.processing_time_ms|default(0)) }}ms</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _update_format_stats(self, report_format: ReportFormat):
        """Update report format statistics"""
        format_key = report_format.value
        self._report_stats['reports_by_format'][format_key] = (
            self._report_stats['reports_by_format'].get(format_key, 0) + 1
        )
    
    def _update_type_stats(self, report_type: ReportType):
        """Update report type statistics"""
        type_key = report_type.value
        self._report_stats['reports_by_type'][type_key] = (
            self._report_stats['reports_by_type'].get(type_key, 0) + 1
        )
    
    def _update_average_generation_time(self, generation_time_ms: float):
        """Update average generation time statistics"""
        current_avg = self._report_stats['average_generation_time_ms']
        successful_reports = self._report_stats['successful_reports']
        
        if successful_reports > 1:
            new_avg = ((current_avg * (successful_reports - 1)) + generation_time_ms) / successful_reports
            self._report_stats['average_generation_time_ms'] = new_avg
        else:
            self._report_stats['average_generation_time_ms'] = generation_time_ms
    
    async def get_report_statistics(self) -> Dict[str, Any]:
        """Get report generation statistics"""
        return {
            'report_stats': self._report_stats.copy(),
            'scheduled_reports_count': len(self._scheduled_reports),
            'reports_directory': str(self.reports_dir),
            'templates_directory': str(self.templates_dir)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for the report generator"""
        try:
            # Check directories
            reports_accessible = self.reports_dir.exists() and os.access(self.reports_dir, os.W_OK)
            templates_accessible = self.templates_dir.exists() and os.access(self.templates_dir, os.R_OK)
            
            status = "healthy" if reports_accessible and templates_accessible else "degraded"
            
            return {
                'status': status,
                'statistics': await self.get_report_statistics(),
                'directories': {
                    'reports_accessible': reports_accessible,
                    'templates_accessible': templates_accessible
                },
                'last_check': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }