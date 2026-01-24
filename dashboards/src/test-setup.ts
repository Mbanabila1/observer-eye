// Test setup for vitest
import 'vitest/globals';

// Mock DOM APIs that might not be available in jsdom
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {}, // deprecated
    removeListener: () => {}, // deprecated
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});

// Mock WebGL context for 3D visualization tests
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  writable: true,
  value: (contextType: string) => {
    if (contextType === 'webgl' || contextType === 'webgl2' || contextType === '2d') {
      return {
        canvas: {},
        drawingBufferWidth: 1024,
        drawingBufferHeight: 768,
        getParameter: () => {},
        createShader: () => {},
        shaderSource: () => {},
        compileShader: () => {},
        createProgram: () => {},
        attachShader: () => {},
        linkProgram: () => {},
        useProgram: () => {},
        createBuffer: () => {},
        bindBuffer: () => {},
        bufferData: () => {},
        getAttribLocation: () => {},
        enableVertexAttribArray: () => {},
        vertexAttribPointer: () => {},
        drawArrays: () => {},
        clear: () => {},
        clearColor: () => {},
        viewport: () => {},
        fillRect: () => {},
        clearRect: () => {},
        fillStyle: '',
        font: '',
        textAlign: 'left',
        fillText: () => {},
      };
    }
    return null;
  },
});

// Mock Chart.js
(globalThis as any).Chart = class {
  constructor() {}
  destroy() {}
  update() {}
  resize() {}
};

// Global test utilities
(globalThis as any).testUtils = {
  // Helper for async operations
  waitFor: (ms: number) => new Promise(resolve => setTimeout(resolve, ms)),
  
  // Helper for mocking container operations
  mockContainerOperation: (duration: number, success: boolean = true) => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (success) {
          resolve({ success: true, duration });
        } else {
          reject(new Error('Container operation failed'));
        }
      }, duration);
    });
  },
};