#!/usr/bin/env node

/**
 * Production Build Validation Script for Angular Frontend
 * 
 * This script validates that the Angular frontend is properly configured for production
 * and contains no mock, seed, or sample data.
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

class FrontendProductionValidator {
    constructor() {
        this.errors = [];
        this.warnings = [];
        this.projectRoot = path.resolve(__dirname, '..');
    }

    /**
     * Run all validation checks
     */
    validateAll() {
        console.log('🔍 Starting production validation for Angular frontend...');
        
        // Configuration validation
        this.validateAngularConfig();
        this.validateEnvironmentConfig();
        
        // Code validation
        this.validateNoMockData();
        this.validateNoSeedData();
        this.validateNoDebugCode();
        
        // Build validation
        this.validateBuildOutput();
        
        // Security validation
        this.validateSecuritySettings();
        
        return {
            status: this.errors.length === 0 ? 'PASS' : 'FAIL',
            errors: this.errors,
            warnings: this.warnings,
            checksPerformed: [
                'Angular configuration check',
                'Environment configuration check',
                'Mock data detection',
                'Seed data detection',
                'Debug code detection',
                'Build output validation',
                'Security settings validation'
            ]
        };
    }

    /**
     * Validate Angular configuration
     */
    validateAngularConfig() {
        console.log('  ✓ Validating Angular configuration...');
        
        const angularJsonPath = path.join(this.projectRoot, 'angular.json');
        if (!fs.existsSync(angularJsonPath)) {
            this.errors.push('angular.json file not found');
            return;
        }

        try {
            const angularConfig = JSON.parse(fs.readFileSync(angularJsonPath, 'utf8'));
            const buildConfig = angularConfig.projects?.dashboard?.architect?.build;
            
            if (!buildConfig) {
                this.errors.push('Build configuration not found in angular.json');
                return;
            }

            // Check production configuration
            const prodConfig = buildConfig.configurations?.production;
            if (!prodConfig) {
                this.errors.push('Production configuration not found in angular.json');
                return;
            }

            // Validate production settings
            if (prodConfig.optimization !== true) {
                this.warnings.push('Optimization is not enabled for production build');
            }

            if (prodConfig.sourceMap !== false) {
                this.warnings.push('Source maps are enabled for production build');
            }

            if (prodConfig.extractLicenses !== true) {
                this.warnings.push('License extraction is not enabled for production build');
            }

        } catch (error) {
            this.errors.push(`Failed to parse angular.json: ${error.message}`);
        }
    }

    /**
     * Validate environment configuration
     */
    validateEnvironmentConfig() {
        console.log('  ✓ Validating environment configuration...');
        
        const envProdPath = path.join(this.projectRoot, 'src/environments/environment.prod.ts');
        const envPath = path.join(this.projectRoot, 'src/environments/environment.ts');
        
        if (!fs.existsSync(envProdPath)) {
            this.warnings.push('Production environment file not found');
        } else {
            try {
                const envContent = fs.readFileSync(envProdPath, 'utf8');
                
                if (envContent.includes('production: false')) {
                    this.errors.push('Production flag is set to false in production environment');
                }
                
                if (envContent.includes('localhost') || envContent.includes('127.0.0.1')) {
                    this.warnings.push('Production environment contains localhost URLs');
                }
                
            } catch (error) {
                this.warnings.push(`Could not read production environment file: ${error.message}`);
            }
        }
        
        // Check development environment for production issues
        if (fs.existsSync(envPath)) {
            try {
                const envContent = fs.readFileSync(envPath, 'utf8');
                
                if (envContent.includes('production: true')) {
                    this.warnings.push('Development environment has production flag set to true');
                }
                
            } catch (error) {
                this.warnings.push(`Could not read development environment file: ${error.message}`);
            }
        }
    }

    /**
     * Check for mock data in the codebase
     */
    validateNoMockData() {
        console.log('  ✓ Checking for mock data...');
        
        const mockPatterns = [
            /mock[_-]?data/gi,
            /MockData/g,
            /MOCK_.*=/g,
            /fake[_-]?data/gi,
            /FakeData/g,
            /test[_-]?data.*=/gi,
            /sample[_-]?data/gi,
            /SampleData/g,
            /dummy[_-]?data/gi,
            /DummyData/g
        ];
        
        this._scanFilesForPatterns(['**/*.ts', '**/*.js'], mockPatterns, 'mock data');
    }

    /**
     * Check for seed data in the codebase
     */
    validateNoSeedData() {
        console.log('  ✓ Checking for seed data...');
        
        const seedPatterns = [
            /seed[_-]?data/gi,
            /SeedData/g,
            /initial[_-]?data/gi,
            /InitialData/g,
            /bootstrap[_-]?data/gi,
            /BootstrapData/g,
            /fixtures/gi
        ];
        
        this._scanFilesForPatterns(['**/*.ts', '**/*.js'], seedPatterns, 'seed data');
        
        // Check for JSON files that might contain seed data
        const dataFiles = glob.sync('**/*.json', { 
            cwd: this.projectRoot,
            ignore: ['node_modules/**', 'dist/**', 'package*.json', 'angular.json', 'tsconfig*.json']
        });
        
        dataFiles.forEach(file => {
            this.warnings.push(`Found data file that might contain seed data: ${file}`);
        });
    }

    /**
     * Check for debug code that shouldn't be in production
     */
    validateNoDebugCode() {
        console.log('  ✓ Checking for debug code...');
        
        const debugPatterns = [
            /console\.log\(/g,
            /console\.debug\(/g,
            /console\.warn\(/g,
            /console\.error\(/g,
            /debugger;/g,
            /TODO:/gi,
            /FIXME:/gi,
            /XXX:/gi,
            /alert\(/g,
            /confirm\(/g
        ];
        
        this._scanFilesForPatterns(['**/*.ts', '**/*.js'], debugPatterns, 'debug code', true);
    }

    /**
     * Validate build output
     */
    validateBuildOutput() {
        console.log('  ✓ Validating build output...');
        
        const distPath = path.join(this.projectRoot, 'dist');
        if (!fs.existsSync(distPath)) {
            this.warnings.push('Build output directory (dist) not found - run ng build first');
            return;
        }

        const dashboardPath = path.join(distPath, 'dashboard');
        if (!fs.existsSync(dashboardPath)) {
            this.warnings.push('Dashboard build output not found in dist directory');
            return;
        }

        // Check for index.html
        const indexPath = path.join(dashboardPath, 'index.html');
        if (!fs.existsSync(indexPath)) {
            this.errors.push('index.html not found in build output');
        }

        // Check for main bundle files
        const files = fs.readdirSync(dashboardPath);
        const hasMainJs = files.some(file => file.startsWith('main.') && file.endsWith('.js'));
        const hasPolyfillsJs = files.some(file => file.startsWith('polyfills.') && file.endsWith('.js'));
        
        if (!hasMainJs) {
            this.errors.push('Main JavaScript bundle not found in build output');
        }
        
        if (!hasPolyfillsJs) {
            this.warnings.push('Polyfills JavaScript bundle not found in build output');
        }

        // Check for source maps in production build
        const sourceMapFiles = files.filter(file => file.endsWith('.map'));
        if (sourceMapFiles.length > 0) {
            this.warnings.push(`Source map files found in production build: ${sourceMapFiles.join(', ')}`);
        }
    }

    /**
     * Validate security settings
     */
    validateSecuritySettings() {
        console.log('  ✓ Validating security settings...');
        
        // Check for security headers in nginx config
        const nginxConfigPath = path.join(this.projectRoot, 'nginx.conf');
        if (fs.existsSync(nginxConfigPath)) {
            try {
                const nginxContent = fs.readFileSync(nginxConfigPath, 'utf8');
                
                const securityHeaders = [
                    'X-Frame-Options',
                    'X-XSS-Protection',
                    'X-Content-Type-Options',
                    'Content-Security-Policy'
                ];
                
                securityHeaders.forEach(header => {
                    if (!nginxContent.includes(header)) {
                        this.warnings.push(`Security header ${header} not found in nginx configuration`);
                    }
                });
                
            } catch (error) {
                this.warnings.push(`Could not read nginx configuration: ${error.message}`);
            }
        } else {
            this.warnings.push('nginx.conf not found - security headers may not be configured');
        }
    }

    /**
     * Scan files for specific patterns
     */
    _scanFilesForPatterns(filePatterns, patterns, description, isWarning = false) {
        const excludePatterns = [
            'node_modules/**',
            'dist/**',
            '.angular/**',
            'coverage/**',
            '**/*.spec.ts',
            '**/*.test.ts',
            '**/test-setup.ts',
            '**/validate_production.js'
        ];

        filePatterns.forEach(filePattern => {
            const files = glob.sync(filePattern, {
                cwd: this.projectRoot,
                ignore: excludePatterns
            });

            files.forEach(file => {
                try {
                    const content = fs.readFileSync(path.join(this.projectRoot, file), 'utf8');
                    
                    patterns.forEach(pattern => {
                        const matches = content.match(pattern);
                        if (matches) {
                            matches.forEach(match => {
                                const lines = content.substring(0, content.indexOf(match)).split('\n');
                                const lineNum = lines.length;
                                const message = `Found ${description} in ${file}:${lineNum} - '${match}'`;
                                
                                if (isWarning) {
                                    this.warnings.push(message);
                                } else {
                                    this.errors.push(message);
                                }
                            });
                        }
                    });
                    
                } catch (error) {
                    this.warnings.push(`Could not scan ${file}: ${error.message}`);
                }
            });
        });
    }
}

/**
 * Main validation function
 */
function main() {
    const validator = new FrontendProductionValidator();
    const results = validator.validateAll();
    
    console.log('\n' + '='.repeat(60));
    console.log('🏁 FRONTEND PRODUCTION VALIDATION RESULTS');
    console.log('='.repeat(60));
    
    console.log(`\n📊 Status: ${results.status}`);
    console.log(`🔍 Checks performed: ${results.checksPerformed.length}`);
    
    if (results.errors.length > 0) {
        console.log(`\n❌ Errors (${results.errors.length}):`);
        results.errors.forEach(error => {
            console.log(`  • ${error}`);
        });
    }
    
    if (results.warnings.length > 0) {
        console.log(`\n⚠️  Warnings (${results.warnings.length}):`);
        results.warnings.forEach(warning => {
            console.log(`  • ${warning}`);
        });
    }
    
    if (results.errors.length === 0 && results.warnings.length === 0) {
        console.log('\n✅ All validation checks passed!');
    }
    
    // Save results to file
    const resultsFile = path.join(__dirname, 'validation_results.json');
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));
    
    console.log(`\n📄 Detailed results saved to: ${resultsFile}`);
    
    // Exit with appropriate code
    process.exit(results.status === 'PASS' ? 0 : 1);
}

if (require.main === module) {
    main();
}