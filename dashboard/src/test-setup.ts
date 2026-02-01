import 'zone.js';
import 'zone.js/testing';
import { getTestBed } from '@angular/core/testing';
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting
} from '@angular/platform-browser-dynamic/testing';

// Import Vitest globals
import { vi } from 'vitest';

// Make Vitest functions globally available
(globalThis as any).vi = vi;
(globalThis as any).spyOn = vi.spyOn;
(globalThis as any).mock = vi.mock;
(globalThis as any).fn = vi.fn;

// Initialize the Angular testing environment
getTestBed().initTestEnvironment(
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting()
);

// Mock all Lucide Angular icons
vi.mock('lucide-angular', async (importOriginal) => {
  const actual = await importOriginal() as any;
  return {
    ...actual,
    LucideAngularModule: {
      pick: vi.fn(() => ({
        ngModule: vi.fn()
      }))
    },
    // Mock all icons used in the application
    Check: vi.fn(),
    Minus: vi.fn(),
    X: vi.fn(),
    ChevronDown: vi.fn(),
    ChevronUp: vi.fn(),
    ChevronLeft: vi.fn(),
    ChevronRight: vi.fn(),
    RefreshCw: vi.fn(),
    Settings: vi.fn(),
    Maximize2: vi.fn(),
    Loader2: vi.fn(),
    Plus: vi.fn(),
    User: vi.fn(),
    Users: vi.fn(),
    DollarSign: vi.fn(),
    Clock: vi.fn(),
    AlertTriangle: vi.fn(),
    AlertCircle: vi.fn(),
    CheckCircle: vi.fn(),
    XCircle: vi.fn(),
    Info: vi.fn(),
    Home: vi.fn(),
    Edit: vi.fn(),
    Copy: vi.fn(),
    Trash2: vi.fn(),
    PlayCircle: vi.fn(),
    Zap: vi.fn(),
    Cpu: vi.fn(),
    HardDrive: vi.fn(),
    BarChart3: vi.fn(),
    TrendingUp: vi.fn(),
    TrendingDown: vi.fn()
  };
});

// Global test configuration
Object.defineProperty(window, 'CSS', { value: null });
Object.defineProperty(window, 'getComputedStyle', {
  value: () => {
    return {
      display: 'none',
      appearance: ['-webkit-appearance']
    };
  }
});

Object.defineProperty(document, 'doctype', {
  value: '<!DOCTYPE html>'
});

Object.defineProperty(document.body.style, 'transform', {
  value: () => {
    return {
      enumerable: true,
      configurable: true
    };
  }
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock
});

// Mock ResizeObserver
(globalThis as any).ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock IntersectionObserver
(globalThis as any).IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});