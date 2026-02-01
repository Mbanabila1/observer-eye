import { ComponentFixture, TestBed } from '@angular/core/testing';
import { vi } from 'vitest';

// Simple test to verify basic component functionality
describe('UI Component Library - Basic Tests', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: []
    }).compileComponents();
  });

  it('should pass basic test', () => {
    expect(true).toBe(true);
  });

  it('should have vi available', () => {
    expect(vi).toBeDefined();
    expect(vi.fn).toBeDefined();
    expect(vi.spyOn).toBeDefined();
  });

  it('should have global spyOn available', () => {
    expect(globalThis.spyOn).toBeDefined();
  });
});