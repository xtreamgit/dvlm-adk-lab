/**
 * Test Script: Get Started Button Navigation Flow
 * 
 * This script tests where the "Get Started" button sends users and what happens next.
 * 
 * Flow:
 * 1. User clicks "Get Started" on landing page (/landing)
 * 2. Button calls router.push('/') to navigate to root
 * 3. Root page (page.tsx) checks authentication
 * 4. IAP authentication flow executes
 * 5. User is shown chatbot UI or redirected back to landing
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://34.49.46.115.nip.io';

console.log('========================================');
console.log('Get Started Button Navigation Flow Test');
console.log('========================================\n');

console.log('Step 1: Landing Page');
console.log('  Location: /landing');
console.log('  Button: "Get Started"');
console.log('  Action: router.push(\'/\')');
console.log('  → Navigates to: / (root page)\n');

console.log('Step 2: Root Page Authentication Check');
console.log('  Location: /');
console.log('  File: frontend/src/app/page.tsx');
console.log('  Process:\n');

console.log('  2a. Check IAP Status');
console.log('      Endpoint: GET /api/iap/status');
console.log('      Full URL: ' + BACKEND_URL + '/api/iap/status');
console.log('      Expected Response:');
console.log('      {');
console.log('        "iap_enabled": true,');
console.log('        "iap_audience": "...",');
console.log('        "message": "IAP is properly configured"');
console.log('      }\n');

console.log('  2b. If iap_enabled === true:');
console.log('      Endpoint: GET /api/iap/me');
console.log('      Full URL: ' + BACKEND_URL + '/api/iap/me');
console.log('      Headers: X-Goog-IAP-JWT-Assertion (injected by IAP)');
console.log('      Expected Response:');
console.log('      {');
console.log('        "id": 1,');
console.log('        "username": "...",');
console.log('        "email": "user@example.com",');
console.log('        "full_name": "...",');
console.log('        "is_active": true,');
console.log('        ...');
console.log('      }\n');

console.log('  2c. If IAP succeeds:');
console.log('      → User data stored in state');
console.log('      → Load user agents, corpus preferences');
console.log('      → Show chatbot UI\n');

console.log('  2d. If IAP fails:');
console.log('      → Falls back to token-based auth');
console.log('      → If no token: router.push(\'/landing\')');
console.log('      → Redirects back to landing page\n');

console.log('========================================');
console.log('Testing Backend Endpoints');
console.log('========================================\n');

async function testEndpoint(name, url, description) {
  console.log(`Testing: ${name}`);
  console.log(`  URL: ${url}`);
  console.log(`  Description: ${description}`);
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    console.log(`  Status: ${response.status} ${response.statusText}`);
    
    if (response.ok) {
      const data = await response.json();
      console.log(`  Response: ${JSON.stringify(data, null, 2).split('\n').map((line, i) => i === 0 ? line : '  ' + line).join('\n')}`);
      return { success: true, data };
    } else {
      const text = await response.text();
      console.log(`  Error: ${text}`);
      return { success: false, error: text };
    }
  } catch (error) {
    console.log(`  Error: ${error.message}`);
    return { success: false, error: error.message };
  } finally {
    console.log('');
  }
}

async function runTests() {
  // Test 1: IAP Status
  const statusResult = await testEndpoint(
    'IAP Status Check',
    `${BACKEND_URL}/api/iap/status`,
    'Checks if IAP is enabled on the backend'
  );
  
  // Test 2: IAP Me (will fail without IAP headers)
  const meResult = await testEndpoint(
    'IAP User Info',
    `${BACKEND_URL}/api/iap/me`,
    'Gets current IAP user (requires X-Goog-IAP-JWT-Assertion header)'
  );
  
  // Test 3: Health Check
  const healthResult = await testEndpoint(
    'Backend Health',
    `${BACKEND_URL}/api/health`,
    'Checks if backend is accessible'
  );
  
  console.log('========================================');
  console.log('Test Summary');
  console.log('========================================\n');
  
  console.log('Expected Flow:');
  console.log('1. ✓ IAP Status returns { iap_enabled: true }');
  console.log(`   ${statusResult.success && statusResult.data?.iap_enabled ? '✓' : '✗'} Actual result`);
  console.log('');
  
  console.log('2. When accessed through Load Balancer with IAP:');
  console.log('   - IAP injects X-Goog-IAP-JWT-Assertion header');
  console.log('   - /api/iap/me returns user info');
  console.log('   - User sees chatbot UI');
  console.log('');
  
  console.log('3. When accessed without IAP headers (like this test):');
  console.log('   - /api/iap/me returns 401 Unauthorized');
  console.log(`   ${!meResult.success ? '✓' : '✗'} Actual result (expected to fail)`);
  console.log('   - Frontend redirects to /landing');
  console.log('');
  
  console.log('========================================');
  console.log('Diagnosis');
  console.log('========================================\n');
  
  if (statusResult.success && statusResult.data?.iap_enabled) {
    console.log('✓ Backend IAP is properly configured');
    console.log('');
    console.log('Next Steps:');
    console.log('1. Access the app through the load balancer:');
    console.log('   ' + BACKEND_URL);
    console.log('2. IAP will authenticate you with Google');
    console.log('3. Click "Get Started" on landing page');
    console.log('4. You should see the chatbot UI (not redirect to landing)');
    console.log('');
    console.log('If you still get redirected to landing:');
    console.log('- Check browser console for errors');
    console.log('- Verify X-Goog-IAP-JWT-Assertion header is present');
    console.log('- Check if /api/iap/me endpoint returns user data');
  } else {
    console.log('✗ Backend IAP configuration issue detected');
    console.log('');
    console.log('Possible Issues:');
    console.log('- IAP not enabled on backend service');
    console.log('- PROJECT_NUMBER or BACKEND_SERVICE_ID not set');
    console.log('- Backend not accessible through load balancer');
  }
}

// Run tests if executed directly
if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { testEndpoint, runTests };
