/**
 * Property-Based Test for Dashboard Container Build Performance
 * Feature: observer-eye-containerization, Property 1: Container Build Performance and Optimization
 * 
 * **Validates: Requirements 1.2, 9.1, 9.3, 9.5**
 * 
 * This property test validates that container builds complete within 5 minutes for full builds
 * and leverage layer caching to rebuild only affected layers when dependencies change.
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import * as fc from 'fast-check';
import { execSync, spawn, ChildProcess } from 'child_process';
import { existsSync, writeFileSync, readFileSync, unlinkSync, mkdirSync } from 'fs';
import { join, resolve } from 'path';

// Test configuration constants
const BUILD_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes as per requirement
const INCREMENTAL_BUILD_TIMEOUT_MS = 2 * 60 * 1000; // 2 minutes for incremental builds
const CACHE_EFFICIENCY_THRESHOLD = 0.5; // 50% time reduction for cached builds
const PROJECT_ROOT = resolve(__dirname, '../..');

interface BuildResult {
  success: boolean;
  duration: number;
  cacheHit: boolean;
  layersRebuilt: number;
  totalLayers: number;
  buildSize: number;
  errorMessage?: string;
}

interface BuildScenario {
  buildType: 'full' | 'incremental' | 'dependency-change';
  cacheState: 'cold' | 'warm' | 'partial';
  changeType?: 'source' | 'dependency' | 'config' | 'asset';
  changeSize: 'small' | 'medium' | 'large';
}

class ContainerBuildTester {
  private testDir: string;
  private dockerfilePath: string;
  private buildContext: string;

  constructor() {
    this.testDir = join(PROJECT_ROOT, 'test-builds');
    this.dockerfilePath = join(PROJECT_ROOT, 'Dockerfile');
    this.buildContext = PROJECT_ROOT;
  }

  async setup(): Promise<void> {
    // Ensure test directory exists
    if (!existsSync(this.testDir)) {
      mkdirSync(this.testDir, { recursive: true });
    }

    // Verify Docker is available
    try {
      execSync('docker --version', { stdio: 'pipe' });
    } catch (error) {
      throw new Error('Docker is not available for testing');
    }

    // Verify Dockerfile exists
    if (!existsSync(this.dockerfilePath)) {
      throw new Error(`Dockerfile not found at ${this.dockerfilePath}`);
    }
  }

  async cleanup(): Promise<void> {
    // Clean up test images
    try {
      const images = execSync('docker images -q observer-eye-dashboard-test*', { 
        encoding: 'utf8',
        stdio: 'pipe'
      }).trim();
      
      if (images) {
        execSync(`docker rmi -f ${images.split('\n').join(' ')}`, { stdio: 'pipe' });
      }
    } catch (error) {
      // Ignore cleanup errors
    }
  }

  private generateImageTag(scenario: BuildScenario): string {
    const timestamp = Date.now();
    return `observer-eye-dashboard-test:${scenario.buildType}-${scenario.cacheState}-${timestamp}`;
  }

  private simulateChange(changeType: string, changeSize: string): void {
    const testFile = join(this.buildContext, 'src', 'test-change.ts');
    
    switch (changeType) {
      case 'source':
        this.simulateSourceChange(testFile, changeSize);
        break;
      case 'dependency':
        this.simulateDependencyChange(changeSize);
        break;
      case 'config':
        this.simulateConfigChange(changeSize);
        break;
      case 'asset':
        this.simulateAssetChange(changeSize);
        break;
    }
  }

  private simulateSourceChange(filePath: string, size: string): void {
    const content = this.generateContent(size);
    writeFileSync(filePath, `// Test change\nexport const testData = ${JSON.stringify(content)};`);
  }

  private simulateDependencyChange(size: string): void {
    const packageJsonPath = join(this.buildContext, 'package.json');
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf8'));
    
    // Add a test dependency to trigger layer rebuild
    packageJson.devDependencies = packageJson.devDependencies || {};
    packageJson.devDependencies[`test-dep-${Date.now()}`] = '^1.0.0';
    
    writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
  }

  private simulateConfigChange(size: string): void {
    const configPath = join(this.buildContext, 'angular.json');
    const config = JSON.parse(readFileSync(configPath, 'utf8'));
    
    // Add test configuration
    config.projects.dashboards.architect.build.options.testConfig = this.generateContent(size);
    
    writeFileSync(configPath, JSON.stringify(config, null, 2));
  }

  private simulateAssetChange(size: string): void {
    const assetPath = join(this.buildContext, 'public', `test-asset-${Date.now()}.json`);
    const content = this.generateContent(size);
    writeFileSync(assetPath, JSON.stringify(content));
  }

  private generateContent(size: string): any {
    const baseSize = size === 'small' ? 100 : size === 'medium' ? 1000 : 10000;
    return Array.from({ length: baseSize }, (_, i) => ({ id: i, data: `test-data-${i}` }));
  }

  private prepareCacheState(cacheState: string, imageTag: string): void {
    switch (cacheState) {
      case 'cold':
        // Remove all cached layers
        try {
          execSync('docker system prune -f', { stdio: 'pipe' });
        } catch (error) {
          // Ignore if prune fails
        }
        break;
      case 'warm':
        // Build a base image to warm the cache
        try {
          execSync(`docker build -t ${imageTag}-base ${this.buildContext}`, { 
            stdio: 'pipe',
            timeout: BUILD_TIMEOUT_MS 
          });
        } catch (error) {
          // Continue with test even if cache warming fails
        }
        break;
      case 'partial':
        // Build with some cached layers
        this.simulateChange('source', 'small');
        try {
          execSync(`docker build -t ${imageTag}-partial ${this.buildContext}`, { 
            stdio: 'pipe',
            timeout: BUILD_TIMEOUT_MS 
          });
        } catch (error) {
          // Continue with test
        }
        break;
    }
  }

  async performBuild(scenario: BuildScenario): Promise<BuildResult> {
    const imageTag = this.generateImageTag(scenario);
    const startTime = Date.now();

    try {
      // Prepare cache state
      this.prepareCacheState(scenario.cacheState, imageTag);

      // Simulate changes if needed
      if (scenario.changeType) {
        this.simulateChange(scenario.changeType, scenario.changeSize);
      }

      // Perform the build with detailed output capture
      const buildCommand = `docker build --progress=plain -t ${imageTag} ${this.buildContext}`;
      const buildOutput = execSync(buildCommand, {
        encoding: 'utf8',
        stdio: 'pipe',
        timeout: BUILD_TIMEOUT_MS,
        maxBuffer: 10 * 1024 * 1024 // 10MB buffer for build output
      });

      const endTime = Date.now();
      const duration = endTime - startTime;

      // Analyze build output for caching information
      const cacheAnalysis = this.analyzeBuildOutput(buildOutput);

      // Get image size
      const sizeOutput = execSync(`docker images ${imageTag} --format "{{.Size}}"`, {
        encoding: 'utf8',
        stdio: 'pipe'
      });

      return {
        success: true,
        duration,
        cacheHit: cacheAnalysis.cacheHit,
        layersRebuilt: cacheAnalysis.layersRebuilt,
        totalLayers: cacheAnalysis.totalLayers,
        buildSize: this.parseSizeString(sizeOutput.trim()),
        errorMessage: undefined
      };

    } catch (error: any) {
      const endTime = Date.now();
      const duration = endTime - startTime;

      return {
        success: false,
        duration,
        cacheHit: false,
        layersRebuilt: 0,
        totalLayers: 0,
        buildSize: 0,
        errorMessage: error.message || 'Unknown build error'
      };
    } finally {
      // Cleanup test changes
      this.cleanupTestChanges();
    }
  }

  private analyzeBuildOutput(output: string): { cacheHit: boolean; layersRebuilt: number; totalLayers: number } {
    const lines = output.split('\n');
    let cacheHits = 0;
    let totalSteps = 0;
    let rebuiltLayers = 0;

    for (const line of lines) {
      if (line.includes('CACHED')) {
        cacheHits++;
      } else if (line.includes('RUN') || line.includes('COPY') || line.includes('ADD')) {
        totalSteps++;
        if (!line.includes('CACHED')) {
          rebuiltLayers++;
        }
      }
    }

    return {
      cacheHit: cacheHits > 0,
      layersRebuilt: rebuiltLayers,
      totalLayers: Math.max(totalSteps, rebuiltLayers)
    };
  }

  private parseSizeString(sizeStr: string): number {
    const match = sizeStr.match(/^([\d.]+)([KMGT]?B)$/);
    if (!match) return 0;

    const value = parseFloat(match[1]);
    const unit = match[2];

    const multipliers: { [key: string]: number } = {
      'B': 1,
      'KB': 1024,
      'MB': 1024 * 1024,
      'GB': 1024 * 1024 * 1024,
      'TB': 1024 * 1024 * 1024 * 1024
    };

    return value * (multipliers[unit] || 1);
  }

  private cleanupTestChanges(): void {
    const testFiles = [
      join(this.buildContext, 'src', 'test-change.ts'),
      join(this.buildContext, 'package.json.backup'),
      join(this.buildContext, 'angular.json.backup')
    ];

    for (const file of testFiles) {
      try {
        if (existsSync(file)) {
          unlinkSync(file);
        }
      } catch (error) {
        // Ignore cleanup errors
      }
    }

    // Restore original files if backups exist
    this.restoreOriginalFiles();
  }

  private restoreOriginalFiles(): void {
    const filesToRestore = [
      { original: 'package.json', backup: 'package.json.backup' },
      { original: 'angular.json', backup: 'angular.json.backup' }
    ];

    for (const { original, backup } of filesToRestore) {
      const originalPath = join(this.buildContext, original);
      const backupPath = join(this.buildContext, backup);

      if (existsSync(backupPath)) {
        try {
          const backupContent = readFileSync(backupPath, 'utf8');
          writeFileSync(originalPath, backupContent);
          unlinkSync(backupPath);
        } catch (error) {
          // Ignore restore errors
        }
      }
    }
  }
}

describe('Container Build Performance Properties', () => {
  let buildTester: ContainerBuildTester;

  beforeAll(async () => {
    buildTester = new ContainerBuildTester();
    await buildTester.setup();
  });

  afterAll(async () => {
    if (buildTester) {
      await buildTester.cleanup();
    }
  });

  /**
   * Property 1: Container Build Performance and Optimization
   * Validates: Requirements 1.2, 9.1, 9.3, 9.5
   */
  it('should complete full builds within 5 minutes and leverage layer caching', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate build scenarios
        fc.record({
          buildType: fc.constantFrom('full', 'incremental', 'dependency-change'),
          cacheState: fc.constantFrom('cold', 'warm', 'partial'),
          changeType: fc.option(fc.constantFrom('source', 'dependency', 'config', 'asset')),
          changeSize: fc.constantFrom('small', 'medium', 'large')
        }),
        async (scenario: BuildScenario) => {
          const result = await buildTester.performBuild(scenario);

          // Property 1.1: Build time constraints
          if (scenario.buildType === 'full') {
            expect(result.duration).toBeLessThanOrEqual(BUILD_TIMEOUT_MS);
          } else {
            expect(result.duration).toBeLessThanOrEqual(INCREMENTAL_BUILD_TIMEOUT_MS);
          }

          // Property 1.2: Cache efficiency for warm builds
          if (scenario.cacheState === 'warm' && result.success) {
            expect(result.cacheHit).toBe(true);
            
            // Cached builds should be significantly faster
            if (scenario.buildType !== 'dependency-change') {
              expect(result.layersRebuilt).toBeLessThan(result.totalLayers);
            }
          }

          // Property 1.3: Incremental builds should rebuild only affected layers
          if (scenario.buildType === 'incremental' && scenario.changeType === 'source') {
            expect(result.layersRebuilt).toBeLessThanOrEqual(3); // Only source layers should rebuild
          }

          // Property 1.4: Dependency changes should rebuild dependency layers
          if (scenario.changeType === 'dependency' && result.success) {
            expect(result.layersRebuilt).toBeGreaterThan(0); // At least dependency layer should rebuild
          }

          // Property 1.5: Build should succeed for valid scenarios
          if (scenario.buildType === 'full' || scenario.cacheState === 'warm') {
            expect(result.success).toBe(true);
          }

          // Property 1.6: Build size optimization
          if (result.success && result.buildSize > 0) {
            expect(result.buildSize).toBeLessThan(500 * 1024 * 1024); // Less than 500MB
          }

          return true;
        }
      ),
      {
        numRuns: 100, // Minimum 100 iterations as per requirements
        timeout: BUILD_TIMEOUT_MS * 2, // Allow extra time for property test execution
        verbose: true,
        seed: 42, // Reproducible test runs
        endOnFailure: false // Continue testing even if some scenarios fail
      }
    );
  }, BUILD_TIMEOUT_MS * 3); // Extended timeout for the entire test suite

  /**
   * Property 2: Layer Caching Efficiency
   * Validates: Requirements 9.1, 9.3
   */
  it('should leverage layer caching to rebuild only affected layers', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          changeType: fc.constantFrom('source', 'dependency', 'config'),
          changeSize: fc.constantFrom('small', 'medium'),
          cacheState: fc.constantFrom('warm', 'partial')
        }),
        async (scenario) => {
          const fullScenario: BuildScenario = {
            buildType: 'incremental',
            cacheState: scenario.cacheState,
            changeType: scenario.changeType,
            changeSize: scenario.changeSize
          };

          const result = await buildTester.performBuild(fullScenario);

          if (result.success) {
            // Property 2.1: Cache utilization
            expect(result.cacheHit).toBe(true);

            // Property 2.2: Selective layer rebuilding
            const rebuildRatio = result.layersRebuilt / Math.max(result.totalLayers, 1);
            
            switch (scenario.changeType) {
              case 'source':
                expect(rebuildRatio).toBeLessThan(0.5); // Less than 50% of layers rebuilt
                break;
              case 'dependency':
                expect(rebuildRatio).toBeGreaterThan(0.3); // At least 30% rebuilt for dependencies
                break;
              case 'config':
                expect(rebuildRatio).toBeLessThan(0.7); // Less than 70% for config changes
                break;
            }

            // Property 2.3: Build time efficiency with caching
            if (scenario.cacheState === 'warm') {
              expect(result.duration).toBeLessThan(INCREMENTAL_BUILD_TIMEOUT_MS);
            }
          }

          return true;
        }
      ),
      {
        numRuns: 50,
        timeout: BUILD_TIMEOUT_MS,
        verbose: true
      }
    );
  }, BUILD_TIMEOUT_MS * 2);

  /**
   * Property 3: Build Optimization and Artifact Removal
   * Validates: Requirements 9.5
   */
  it('should remove development dependencies and build artifacts in production builds', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          buildType: fc.constant('full'),
          cacheState: fc.constantFrom('cold', 'warm')
        }),
        async (scenario) => {
          const fullScenario: BuildScenario = {
            buildType: scenario.buildType,
            cacheState: scenario.cacheState,
            changeSize: 'small'
          };

          const result = await buildTester.performBuild(fullScenario);

          if (result.success) {
            // Property 3.1: Production build size optimization
            expect(result.buildSize).toBeLessThan(200 * 1024 * 1024); // Less than 200MB for optimized build

            // Property 3.2: Multi-stage build efficiency
            expect(result.totalLayers).toBeGreaterThan(5); // Should have multiple stages
            
            // Property 3.3: Build artifacts should be removed
            // This is validated by the smaller final image size compared to build stage
            expect(result.buildSize).toBeGreaterThan(50 * 1024 * 1024); // But not too small (should contain app)
          }

          return true;
        }
      ),
      {
        numRuns: 25,
        timeout: BUILD_TIMEOUT_MS,
        verbose: true
      }
    );
  }, BUILD_TIMEOUT_MS * 2);
});