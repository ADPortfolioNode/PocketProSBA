#!/usr/bin/env node

/**
 * Comprehensive connectivity test script
 * Tests all backend connection scenarios
 */

const axios = require('axios');
const chalk = require('chalk');

// Test configurations
const TEST_CONFIGS = {
  local: {
    name: 'Local Development',
    url: 'http://localhost:5000',
    endpoints: ['/health', '/api/health', '/api/status']
  },
  docker: {
    name: 'Docker Development',
    url: 'http://localhost:5000',
    endpoints: ['/health', '/api/health']
  },
  render: {
    name: 'Render Production',
    url: process.env.RENDER_URL || 'https://your-app.onrender.com',
    endpoints: ['/health', '/api/health', '/api/status']
  }
};

// Test a single endpoint
async function testEndpoint(baseUrl, endpoint) {
  const url = `${baseUrl}${endpoint}`;
  const startTime = Date.now();
  
  try {
    const response = await axios.get(url, {
      timeout: 10000,
      validateStatus: (status) => status < 500
    });
    
    const responseTime = Date.now() - startTime;
    
    return {
      success: true,
      url,
      status: response.status,
      responseTime,
      data: response.data
    };
  } catch (error) {
    return {
      success: false,
      url,
      error: error.message,
      responseTime: Date.now() - startTime
    };
  }
}

// Test all endpoints for a configuration
async function testConfiguration(config) {
  console.log(chalk.blue(`\n🧪 Testing ${config.name}...`));
  console.log(chalk.gray(`Base URL: ${config.url}`));
  
  const results = [];
  
  for (const endpoint of config.endpoints) {
    const result = await testEndpoint(config.url, endpoint);
    results.push(result);
    
    if (result.success) {
      console.log(chalk.green(`  ✅ ${endpoint} - ${result.status} (${result.responseTime}ms)`));
    } else {
      console.log(chalk.red(`  ❌ ${endpoint} - ${result.error}`));
    }
  }
  
  const successCount = results.filter(r => r.success).length;
  const totalCount = results.length;
  
  return {
    config: config.name,
    successRate: (successCount / totalCount) * 100,
    results
  };
}

// Run all tests
async function runAllTests() {
  console.log(chalk.bold('🔍 Frontend-Backend Connectivity Test Suite'));
  console.log(chalk.gray('Testing all connection scenarios...'));
  
  const results = [];
  
  for (const [key, config] of Object.entries(TEST_CONFIGS)) {
    const result = await testConfiguration(config);
    results.push(result);
  }
  
  // Summary
  console.log(chalk.bold('\n📊 Test Summary'));
  console.log('=' * 50);
  
  results.forEach(result => {
    const status = result.successRate === 100 ? chalk.green('✅') : 
                   result.successRate > 0 ? chalk.yellow('⚠️') : chalk.red('❌');
    console.log(`${status} ${result.config}: ${result.successRate.toFixed(1)}% success rate`);
  });
  
  // Recommendations
  console.log(chalk.bold('\n💡 Recommendations'));
  
  const failedConfigs = results.filter(r => r.successRate < 100);
  if (failedConfigs.length > 0) {
    console.log(chalk.yellow('Some configurations failed. Check:'));
    console.log('  1. Backend server is running');
    console.log('  2. Correct port configuration');
    console.log('  3. Network connectivity');
    console.log('  4. CORS settings');
  } else {
    console.log(chalk.green('All configurations working correctly!'));
  }
  
  return results;
}

// Health check endpoint test
async function testHealthEndpoints() {
  console.log(chalk.blue('\n🏥 Testing Health Endpoints'));
  
  const healthEndpoints = [
    '/health',
    '/api/health',
    '/api/status',
    '/ping'
  ];
  
  const baseUrl = 'http://localhost:5000';
  
  for (const endpoint of healthEndpoints) {
    const result = await testEndpoint(baseUrl, endpoint);
    if (result.success) {
      console.log(chalk.green(`  ✅ ${endpoint}: ${JSON.stringify(result.data)}`));
    } else {
      console.log(chalk.red(`  ❌ ${endpoint}: ${result.error}`));
    }
  }
}

// Environment detection test
function testEnvironmentDetection() {
  console.log(chalk.blue('\n🌍 Testing Environment Detection'));
  
  const hostname = 'localhost'; // Mock for testing
  const protocol = 'http:';
  
  let environment = 'development';
  
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    environment = 'development';
  } else if (hostname.includes('onrender.com')) {
    environment = 'render';
  } else if (hostname.includes('herokuapp.com')) {
    environment = 'heroku';
  } else if (protocol === 'https:') {
    environment = 'production';
  }
  
  console.log(chalk.green(`  ✅ Detected environment: ${environment}`));
  
  return environment;
}

// Main execution
async function main() {
  try {
    console.log(chalk.bold('🚀 Frontend-Backend Connectivity Test'));
    console.log(chalk.gray('Testing comprehensive connectivity solutions...'));
    
    // Test environment detection
    testEnvironmentDetection();
    
    // Test health endpoints
    await testHealthEndpoints();
    
    // Run full test suite
    const results = await runAllTests();
    
    // Save results
    const fs = require('fs');
    fs.writeFileSync('connectivity-test-results.json', JSON.stringify(results, null, 2));
    
    console.log(chalk.green('\n✅ Test complete! Results saved to connectivity-test-results.json'));
    
  } catch (error) {
    console.error(chalk.red('❌ Test failed:'), error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  testEndpoint,
  testConfiguration,
  runAllTests,
  testHealthEndpoints,
  testEnvironmentDetection
};
