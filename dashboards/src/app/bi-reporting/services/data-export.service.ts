import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { ExportConfig, ExportResult, ExportFormat } from '../models/bi-models';

@Injectable({
  providedIn: 'root'
})
export class DataExportService {
  private readonly baseUrl = '/api/data-export';

  constructor() {}

  /**
   * Export data in the specified format
   */
  exportData(config: ExportConfig): Observable<ExportResult> {
    switch (config.format) {
      case 'pdf':
        return this.exportToPDF(config);
      case 'excel':
        return this.exportToExcel(config);
      case 'csv':
        return this.exportToCSV(config);
      case 'json':
        return this.exportToJSON(config);
      case 'png':
        return this.exportToPNG(config);
      default:
        return of({
          success: false,
          error: `Unsupported export format: ${config.format}`
        });
    }
  }

  /**
   * Get available export formats
   */
  getAvailableFormats(): ExportFormat[] {
    return ['pdf', 'excel', 'csv', 'json', 'png'];
  }

  /**
   * Validate export configuration
   */
  validateExportConfig(config: ExportConfig): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!config.format) {
      errors.push('Export format is required');
    }

    if (!this.getAvailableFormats().includes(config.format)) {
      errors.push(`Unsupported format: ${config.format}`);
    }

    if (config.dateRange) {
      if (config.dateRange.start >= config.dateRange.end) {
        errors.push('Start date must be before end date');
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Generate filename based on config and current date
   */
  generateFilename(config: ExportConfig, prefix: string = 'export'): string {
    if (config.filename) {
      return config.filename;
    }

    const timestamp = new Date().toISOString().split('T')[0];
    return `${prefix}_${timestamp}.${config.format}`;
  }

  private exportToPDF(config: ExportConfig): Observable<ExportResult> {
    // Mock PDF export - replace with actual implementation
    return of({
      success: true,
      filename: this.generateFilename(config, 'report'),
      downloadUrl: this.generateMockDownloadUrl('pdf'),
      size: this.generateMockFileSize()
    }).pipe(
      catchError(error => of({
        success: false,
        error: `PDF export failed: ${error.message}`
      }))
    );
  }

  private exportToExcel(config: ExportConfig): Observable<ExportResult> {
    // Mock Excel export - replace with actual implementation
    return of({
      success: true,
      filename: this.generateFilename(config, 'data'),
      downloadUrl: this.generateMockDownloadUrl('xlsx'),
      size: this.generateMockFileSize()
    }).pipe(
      catchError(error => of({
        success: false,
        error: `Excel export failed: ${error.message}`
      }))
    );
  }

  private exportToCSV(config: ExportConfig): Observable<ExportResult> {
    // Mock CSV export - replace with actual implementation
    return of({
      success: true,
      filename: this.generateFilename(config, 'data'),
      downloadUrl: this.generateMockDownloadUrl('csv'),
      size: this.generateMockFileSize()
    }).pipe(
      catchError(error => of({
        success: false,
        error: `CSV export failed: ${error.message}`
      }))
    );
  }

  private exportToJSON(config: ExportConfig): Observable<ExportResult> {
    // Mock JSON export - replace with actual implementation
    return of({
      success: true,
      filename: this.generateFilename(config, 'data'),
      downloadUrl: this.generateMockDownloadUrl('json'),
      size: this.generateMockFileSize()
    }).pipe(
      catchError(error => of({
        success: false,
        error: `JSON export failed: ${error.message}`
      }))
    );
  }

  private exportToPNG(config: ExportConfig): Observable<ExportResult> {
    // Mock PNG export - replace with actual implementation
    return of({
      success: true,
      filename: this.generateFilename(config, 'chart'),
      downloadUrl: this.generateMockDownloadUrl('png'),
      size: this.generateMockFileSize()
    }).pipe(
      catchError(error => of({
        success: false,
        error: `PNG export failed: ${error.message}`
      }))
    );
  }

  private generateMockDownloadUrl(extension: string): string {
    const timestamp = Date.now();
    return `/api/downloads/export_${timestamp}.${extension}`;
  }

  private generateMockFileSize(): number {
    // Generate random file size between 50KB and 5MB
    return Math.floor(Math.random() * 5000000) + 50000;
  }

  /**
   * Download file from URL
   */
  downloadFile(url: string, filename: string): void {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}