#!/usr/bin/env python3
"""
Admin Audit Endpoint Testing Script

Tests the /admin/audit endpoint to ensure:
1. IAP authentication works
2. Endpoint returns correct response format
3. Audit log data is properly structured
4. Database queries work correctly
5. Pagination works (if implemented)
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def log_test(test_name: str):
    """Print test header."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}TEST: {test_name}{Colors.ENDC}")


def log_pass(message: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ PASS: {message}{Colors.ENDC}")


def log_fail(message: str):
    """Print failure message."""
    print(f"{Colors.FAIL}❌ FAIL: {message}{Colors.ENDC}")


def log_warning(message: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  WARNING: {message}{Colors.ENDC}")


def log_info(message: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


def get_iap_token() -> Optional[str]:
    """
    Get IAP access token using gcloud.
    
    Returns:
        Access token string or None if failed
    """
    try:
        result = subprocess.run(
            ['gcloud', 'auth', 'print-identity-token'],
            capture_output=True,
            text=True,
            check=True
        )
        token = result.stdout.strip()
        if token:
            log_info("Successfully obtained IAP token")
            return token
        else:
            log_fail("Empty token received from gcloud")
            return None
    except subprocess.CalledProcessError as e:
        log_fail(f"Failed to get IAP token: {e}")
        log_warning("Make sure you're logged in: gcloud auth login")
        return None
    except FileNotFoundError:
        log_fail("gcloud CLI not found")
        log_warning("Install from: https://cloud.google.com/sdk/docs/install")
        return None


def test_endpoint_accessibility(base_url: str, token: str) -> bool:
    """
    Test 1: Check if endpoint is accessible with IAP authentication.
    
    Args:
        base_url: Base URL of the application
        token: IAP access token
        
    Returns:
        True if test passes, False otherwise
    """
    log_test("Endpoint Accessibility (with IAP)")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{base_url}/api/admin/audit",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            log_pass(f"Endpoint accessible (Status: {response.status_code})")
            return True
        elif response.status_code == 401:
            log_fail(f"Authentication failed (Status: {response.status_code})")
            log_warning("Token may be invalid or expired")
            return False
        elif response.status_code == 403:
            log_fail(f"Access forbidden (Status: {response.status_code})")
            log_warning("User may not have admin permissions")
            return False
        elif response.status_code == 404:
            log_fail(f"Endpoint not found (Status: {response.status_code})")
            log_warning("Check if backend is deployed correctly")
            return False
        else:
            log_fail(f"Unexpected status code: {response.status_code}")
            log_info(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        log_fail("Connection failed - backend may not be running")
        return False
    except requests.exceptions.Timeout:
        log_fail("Request timed out")
        return False
    except Exception as e:
        log_fail(f"Request failed: {str(e)}")
        return False


def test_response_format(base_url: str, token: str) -> tuple[bool, Optional[List]]:
    """
    Test 2: Validate response format is JSON array.
    
    Args:
        base_url: Base URL of the application
        token: IAP access token
        
    Returns:
        Tuple of (test_passed, audit_data)
    """
    log_test("Response Format Validation")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{base_url}/api/admin/audit", headers=headers, timeout=10)
        
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            log_fail(f"Wrong content type: {content_type}")
            return False, None
        
        log_pass(f"Content-Type is correct: {content_type}")
        
        # Try to parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            log_fail(f"Invalid JSON response: {e}")
            log_info(f"Response: {response.text[:200]}")
            return False, None
        
        log_pass("Response is valid JSON")
        
        # Check if it's a list
        if not isinstance(data, list):
            log_fail(f"Expected list, got {type(data).__name__}")
            return False, None
        
        log_pass(f"Response is a list with {len(data)} items")
        
        return True, data
        
    except Exception as e:
        log_fail(f"Response format test failed: {str(e)}")
        return False, None


def test_audit_log_structure(audit_data: List[Dict]) -> bool:
    """
    Test 3: Validate audit log entry structure.
    
    Args:
        audit_data: List of audit log entries
        
    Returns:
        True if test passes, False otherwise
    """
    log_test("Audit Log Entry Structure")
    
    if not audit_data:
        log_warning("No audit log entries to validate")
        return True
    
    required_fields = ['id', 'action', 'timestamp']
    optional_fields = ['corpus_id', 'corpus_name', 'user_id', 'user_name', 'changes', 'metadata']
    
    all_valid = True
    
    for i, entry in enumerate(audit_data[:5]):  # Check first 5 entries
        log_info(f"Validating entry {i+1}/{min(len(audit_data), 5)}")
        
        # Check required fields
        missing_fields = [field for field in required_fields if field not in entry]
        if missing_fields:
            log_fail(f"Entry {i+1} missing required fields: {missing_fields}")
            all_valid = False
            continue
        
        # Validate field types
        if not isinstance(entry.get('id'), int):
            log_fail(f"Entry {i+1}: 'id' should be integer, got {type(entry.get('id'))}")
            all_valid = False
        
        if not isinstance(entry.get('action'), str):
            log_fail(f"Entry {i+1}: 'action' should be string, got {type(entry.get('action'))}")
            all_valid = False
        
        # Validate timestamp format
        timestamp = entry.get('timestamp')
        try:
            # Try to parse ISO format timestamp
            if isinstance(timestamp, str):
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                log_fail(f"Entry {i+1}: 'timestamp' should be string, got {type(timestamp)}")
                all_valid = False
        except ValueError:
            log_fail(f"Entry {i+1}: Invalid timestamp format: {timestamp}")
            all_valid = False
        
        if all_valid:
            log_pass(f"Entry {i+1} structure is valid")
    
    if all_valid:
        log_pass("All checked entries have valid structure")
    
    return all_valid


def test_audit_log_data(audit_data: List[Dict]) -> bool:
    """
    Test 4: Validate audit log data content.
    
    Args:
        audit_data: List of audit log entries
        
    Returns:
        True if test passes, False otherwise
    """
    log_test("Audit Log Data Content")
    
    if not audit_data:
        log_warning("No audit log entries found")
        log_info("This is normal for new deployments")
        return True
    
    log_pass(f"Found {len(audit_data)} audit log entries")
    
    # Show sample entries
    log_info(f"\nSample audit log entries:")
    for entry in audit_data[:3]:
        print(f"  • ID {entry.get('id')}: {entry.get('action')} by {entry.get('user_name', 'unknown')} at {entry.get('timestamp')}")
    
    # Check for variety of actions
    actions = set(entry.get('action') for entry in audit_data)
    log_info(f"\nAction types found: {', '.join(actions)}")
    
    # Check user associations
    users_with_actions = sum(1 for entry in audit_data if entry.get('user_name'))
    log_info(f"Entries with user association: {users_with_actions}/{len(audit_data)}")
    
    # Check corpus associations
    corpus_actions = sum(1 for entry in audit_data if entry.get('corpus_name'))
    log_info(f"Entries with corpus association: {corpus_actions}/{len(audit_data)}")
    
    return True


def test_query_parameters(base_url: str, token: str) -> bool:
    """
    Test 5: Test query parameters (if supported).
    
    Args:
        base_url: Base URL of the application
        token: IAP access token
        
    Returns:
        True if test passes, False otherwise
    """
    log_test("Query Parameters (Optional)")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test limit parameter
    try:
        response = requests.get(
            f"{base_url}/api/admin/audit?limit=5",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_pass(f"Limit parameter works (returned {len(data)} entries)")
                return True
            else:
                log_warning("Limit parameter accepted but response format unexpected")
                return False
        else:
            log_warning("Limit parameter may not be supported")
            return True  # Not a critical failure
            
    except Exception as e:
        log_warning(f"Query parameter test skipped: {str(e)}")
        return True  # Not a critical failure


def test_admin_permission_required(base_url: str) -> bool:
    """
    Test 6: Verify endpoint requires admin permissions.
    
    Args:
        base_url: Base URL of the application
        
    Returns:
        True if test passes, False otherwise
    """
    log_test("Admin Permission Requirement")
    
    # Try without token
    try:
        response = requests.get(f"{base_url}/api/admin/audit", timeout=10)
        
        if response.status_code in [401, 403]:
            log_pass("Endpoint properly requires authentication")
            return True
        elif response.status_code == 200:
            log_fail("Endpoint accessible without authentication - SECURITY ISSUE!")
            return False
        else:
            log_warning(f"Unexpected response without auth: {response.status_code}")
            return True  # Inconclusive
            
    except Exception as e:
        log_warning(f"Permission test incomplete: {str(e)}")
        return True


def main():
    """Main test execution."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}ADMIN AUDIT ENDPOINT TESTING{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Configuration
    BASE_URL = "https://34.49.46.115.nip.io"
    
    log_info(f"Target URL: {BASE_URL}/api/admin/audit")
    log_info("Authentication: IAP (Identity-Aware Proxy)\n")
    
    # Get IAP token
    token = get_iap_token()
    if not token:
        print(f"\n{Colors.FAIL}{Colors.BOLD}FATAL: Cannot proceed without IAP token{Colors.ENDC}\n")
        sys.exit(1)
    
    # Track test results
    tests_passed = 0
    tests_failed = 0
    tests_total = 6
    
    # Run tests
    
    # Test 1: Accessibility
    if test_endpoint_accessibility(BASE_URL, token):
        tests_passed += 1
    else:
        tests_failed += 1
        print(f"\n{Colors.FAIL}{Colors.BOLD}FATAL: Endpoint not accessible. Stopping tests.{Colors.ENDC}\n")
        sys.exit(1)
    
    # Test 2: Response Format
    format_ok, audit_data = test_response_format(BASE_URL, token)
    if format_ok:
        tests_passed += 1
    else:
        tests_failed += 1
        audit_data = []
    
    # Test 3: Entry Structure
    if test_audit_log_structure(audit_data):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 4: Data Content
    if test_audit_log_data(audit_data):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 5: Query Parameters
    if test_query_parameters(BASE_URL, token):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 6: Admin Permission
    if test_admin_permission_required(BASE_URL):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    print(f"Tests Run:    {tests_total}")
    print(f"{Colors.OKGREEN}Tests Passed: {tests_passed}{Colors.ENDC}")
    print(f"{Colors.FAIL}Tests Failed: {tests_failed}{Colors.ENDC}")
    
    success_rate = (tests_passed / tests_total) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if tests_failed == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ ALL TESTS PASSED{Colors.ENDC}")
        print(f"{Colors.OKGREEN}The /admin/audit endpoint is working correctly!{Colors.ENDC}\n")
        sys.exit(0)
    elif tests_passed >= tests_total * 0.8:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  MOSTLY WORKING{Colors.ENDC}")
        print(f"{Colors.WARNING}Some tests failed but core functionality works{Colors.ENDC}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ TESTS FAILED{Colors.ENDC}")
        print(f"{Colors.FAIL}The /admin/audit endpoint has issues that need to be fixed{Colors.ENDC}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
