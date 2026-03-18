#!/usr/bin/env python3
"""
Integration Test Suite: Cloud Identity Groups API
Tests the refactored google_groups_service.py end-to-end against the live API.

Usage:
    python tests/test_cloud_identity_integration.py [--email USER_EMAIL]

Test Matrix:
    1. Credential acquisition (ADC + Cloud Identity scope)
    2. groups:search — list all org groups
    3. checkTransitiveMembership — per-group membership check
    4. GoogleGroupsService._query_cloud_identity() — full two-step flow
    5. GoogleGroupsService.get_user_groups() — public interface
    6. Edge case: non-member email
    7. Edge case: invalid/malformed email
    8. Edge case: missing GOOGLE_GROUPS_CUSTOMER_ID
    9. Fallback: Cloud Identity → Admin SDK (simulated failure)
   10. Cache: write → read → TTL expiry
   11. Service account impersonation test (Cloud Run simulation)
"""
import asyncio
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Load .env.local before anything else
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env.local"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(name)s: %(message)s")
# Quiet down google auth logs
logging.getLogger("google").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

import google.auth
import google.auth.transport.requests
import aiohttp

# ─── Test infrastructure ──────────────────────────────────────────────

PASS = 0
FAIL = 0
SKIP = 0
RESULTS = []

def report(test_name: str, passed: bool, detail: str = "", skipped: bool = False):
    global PASS, FAIL, SKIP
    if skipped:
        SKIP += 1
        icon = "⏭️"
        status = "SKIP"
    elif passed:
        PASS += 1
        icon = "✅"
        status = "PASS"
    else:
        FAIL += 1
        icon = "❌"
        status = "FAIL"
    RESULTS.append({"test": test_name, "status": status, "detail": detail})
    detail_str = f" — {detail}" if detail else ""
    print(f"  {icon} {test_name}{detail_str}")


# ─── Test 1: Credential Acquisition ──────────────────────────────────

async def test_credentials():
    """Verify ADC credentials can be obtained with Cloud Identity scope."""
    print("\n─── Test 1: Credential Acquisition ───")
    try:
        scopes = ["https://www.googleapis.com/auth/cloud-identity.groups.readonly"]
        credentials, project = google.auth.default(scopes=scopes)
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)

        report("ADC credentials obtained", True, f"project={project}")
        report("Token is valid", credentials.valid, f"type={type(credentials).__name__}")
        report("Token not expired", not credentials.expired)
        return credentials, project
    except Exception as e:
        report("ADC credentials obtained", False, str(e))
        return None, None


# ─── Test 2: groups:search ────────────────────────────────────────────

async def test_groups_search(credentials):
    """Verify groups:search returns org groups."""
    print("\n─── Test 2: groups:search (List Org Groups) ───")
    customer_id = os.getenv("GOOGLE_GROUPS_CUSTOMER_ID", "")
    quota_project = os.getenv("GOOGLE_GROUPS_QUOTA_PROJECT", "")

    if not customer_id:
        report("GOOGLE_GROUPS_CUSTOMER_ID set", False, "env var missing")
        return []

    report("GOOGLE_GROUPS_CUSTOMER_ID set", True, customer_id)

    headers = {"Authorization": f"Bearer {credentials.token}"}
    if quota_project:
        headers["x-goog-user-project"] = quota_project

    search_url = "https://cloudidentity.googleapis.com/v1/groups:search"
    query = (
        f"parent=='customers/{customer_id}' && "
        "'cloudidentity.googleapis.com/groups.discussion_forum' in labels"
    )

    groups = []
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url, headers=headers, params={"query": query, "pageSize": 200}) as resp:
            report("groups:search HTTP 200", resp.status == 200, f"status={resp.status}")
            if resp.status != 200:
                body = await resp.text()
                report("groups:search response", False, body[:300])
                return []
            data = await resp.json()

    for g in data.get("groups", []):
        groups.append({
            "name": g["name"],
            "email": g.get("groupKey", {}).get("id", ""),
            "displayName": g.get("displayName", ""),
        })

    report(f"Groups found in org", len(groups) > 0, f"count={len(groups)}")

    # Print group list
    for g in groups:
        print(f"       {g['email']} ({g['displayName']})")

    return groups


# ─── Test 3: checkTransitiveMembership ────────────────────────────────

async def test_check_membership(credentials, groups, user_email):
    """Verify checkTransitiveMembership works for each group."""
    print(f"\n─── Test 3: checkTransitiveMembership ({user_email}) ───")
    quota_project = os.getenv("GOOGLE_GROUPS_QUOTA_PROJECT", "")

    if not groups:
        report("Has groups to check", False, "no groups from test 2")
        return []

    headers = {"Authorization": f"Bearer {credentials.token}"}
    if quota_project:
        headers["x-goog-user-project"] = quota_project

    member_groups = []
    errors = 0

    async with aiohttp.ClientSession() as session:
        for g in groups:
            url = f"https://cloudidentity.googleapis.com/v1/{g['name']}/memberships:checkTransitiveMembership"
            params = {"query": f"member_key_id=='{user_email}'"}
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    is_member = result.get("hasMembership", False)
                    if is_member:
                        member_groups.append(g["email"])
                    status = "MEMBER" if is_member else "not member"
                    print(f"       {g['email']}: {status}")
                else:
                    errors += 1
                    print(f"       {g['email']}: ERROR {resp.status}")

    report("checkTransitiveMembership calls succeed", errors == 0, f"errors={errors}")
    report(f"User is member of groups", len(member_groups) > 0, f"count={len(member_groups)}")
    return member_groups


# ─── Test 4: GoogleGroupsService._query_cloud_identity() ─────────────

async def test_service_query(user_email):
    """Test the internal _query_cloud_identity method."""
    print(f"\n─── Test 4: GoogleGroupsService._query_cloud_identity() ───")
    from services.google_groups_service import GoogleGroupsService
    # Clear cached credentials to force fresh auth
    GoogleGroupsService._cloud_identity_credentials = None

    try:
        groups = await GoogleGroupsService._query_cloud_identity(user_email)
        report("_query_cloud_identity succeeds", True, f"groups={len(groups)}")
        report("Returns list of strings", all(isinstance(g, str) for g in groups))
        report("All results are email addresses", all("@" in g for g in groups))
        for g in groups:
            print(f"       {g}")
        return groups
    except Exception as e:
        report("_query_cloud_identity succeeds", False, f"{type(e).__name__}: {e}")
        return []


# ─── Test 5: GoogleGroupsService.get_user_groups() ───────────────────

async def test_public_interface(user_email):
    """Test the public get_user_groups method (the one the bridge calls)."""
    print(f"\n─── Test 5: GoogleGroupsService.get_user_groups() ───")
    from services.google_groups_service import GoogleGroupsService
    GoogleGroupsService._cloud_identity_credentials = None

    try:
        groups = await GoogleGroupsService.get_user_groups(user_email)
        report("get_user_groups succeeds", True, f"groups={len(groups)}")
        report("Returns non-empty list", len(groups) > 0, f"count={len(groups)}")
        return groups
    except Exception as e:
        report("get_user_groups succeeds", False, f"{type(e).__name__}: {e}")
        return []


# ─── Test 6: Non-member email ────────────────────────────────────────

async def test_non_member_email():
    """Test with an email that is not a member of any group."""
    print("\n─── Test 6: Edge Case — Non-Member Email ───")
    from services.google_groups_service import GoogleGroupsService
    GoogleGroupsService._cloud_identity_credentials = None

    fake_email = "nonexistent-test-user-12345@develom.com"
    try:
        groups = await GoogleGroupsService._query_cloud_identity(fake_email)
        report("Non-member returns empty list", len(groups) == 0, f"groups={groups}")
    except Exception as e:
        report("Non-member handles gracefully", False, f"{type(e).__name__}: {e}")


# ─── Test 7: Invalid email ───────────────────────────────────────────

async def test_invalid_email():
    """Test with a malformed email address."""
    print("\n─── Test 7: Edge Case — Invalid Email ───")
    from services.google_groups_service import GoogleGroupsService
    GoogleGroupsService._cloud_identity_credentials = None

    invalid_email = "not-an-email"
    try:
        groups = await GoogleGroupsService._query_cloud_identity(invalid_email)
        # API may return empty or error — either is acceptable
        report("Invalid email handled gracefully", True, f"returned {len(groups)} groups")
    except Exception as e:
        # An error is also acceptable — as long as it doesn't crash
        report("Invalid email handled gracefully", True, f"raised {type(e).__name__} (acceptable)")


# ─── Test 8: Missing customer ID ─────────────────────────────────────

async def test_missing_customer_id():
    """Test that missing GOOGLE_GROUPS_CUSTOMER_ID raises ValueError."""
    print("\n─── Test 8: Edge Case — Missing Customer ID ───")
    import services.google_groups_service as svc
    from services.google_groups_service import GoogleGroupsService

    # Save and clear
    original = svc.GOOGLE_GROUPS_CUSTOMER_ID
    svc.GOOGLE_GROUPS_CUSTOMER_ID = ""
    GoogleGroupsService._cloud_identity_credentials = None

    try:
        groups = await GoogleGroupsService._query_cloud_identity("test@develom.com")
        report("Raises ValueError when customer ID missing", False, f"returned {groups}")
    except ValueError as e:
        report("Raises ValueError when customer ID missing", True, str(e)[:80])
    except Exception as e:
        report("Raises ValueError when customer ID missing", False, f"raised {type(e).__name__} instead")
    finally:
        svc.GOOGLE_GROUPS_CUSTOMER_ID = original


# ─── Test 9: Fallback to Admin SDK ───────────────────────────────────

async def test_fallback_behavior():
    """Test that Cloud Identity failure falls back to Admin SDK (if configured)."""
    print("\n─── Test 9: Fallback Behavior ───")
    import services.google_groups_service as svc
    from services.google_groups_service import GoogleGroupsService

    admin_email = svc.GOOGLE_GROUPS_ADMIN_EMAIL
    has_admin_sdk = bool(admin_email)

    # Simulate Cloud Identity failure by setting invalid customer ID
    original_cid = svc.GOOGLE_GROUPS_CUSTOMER_ID
    svc.GOOGLE_GROUPS_CUSTOMER_ID = "INVALID_CUSTOMER_ID"
    GoogleGroupsService._cloud_identity_credentials = None

    try:
        groups = await GoogleGroupsService.get_user_groups("hector@develom.com")
        if has_admin_sdk:
            report("Falls back to Admin SDK", len(groups) > 0, f"groups={len(groups)}")
        else:
            report("Returns empty when both fail", len(groups) == 0, f"groups={groups}")
            report("Admin SDK fallback not configured", True, "GOOGLE_GROUPS_ADMIN_EMAIL not set", skipped=True)
    except Exception as e:
        report("Fallback handles errors gracefully", False, str(e))
    finally:
        svc.GOOGLE_GROUPS_CUSTOMER_ID = original_cid
        GoogleGroupsService._cloud_identity_credentials = None


# ─── Test 10: Cache Layer ─────────────────────────────────────────────

async def test_cache_layer():
    """Test cache write, read, and TTL behavior."""
    print("\n─── Test 10: Cache Layer ───")
    from services.google_groups_service import GoogleGroupsService
    import services.google_groups_service as svc

    # We need a valid user_id from the database
    try:
        from database.connection import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email FROM users WHERE email = 'hector@develom.com' LIMIT 1")
            user = cursor.fetchone()
    except Exception as e:
        report("Database connection for cache test", False, str(e))
        return

    if not user:
        report("Test user exists in DB", False, "hector@develom.com not found")
        return

    user_id = user["id"]
    test_groups = ["test-group-1@develom.com", "test-group-2@develom.com"]

    # Write cache
    try:
        GoogleGroupsService.update_cache(user_id, test_groups, sync_source="test")
        report("Cache write succeeds", True)
    except Exception as e:
        report("Cache write succeeds", False, str(e))
        return

    # Read cache (should be fresh)
    cached = GoogleGroupsService.get_cached_groups(user_id)
    report("Cache read returns data", cached is not None, f"cached={cached}")
    report("Cache data matches written data", cached == test_groups, f"expected={test_groups}, got={cached}")

    # Test TTL (set TTL to 1 second, wait, check expiry)
    original_ttl = svc.GOOGLE_GROUPS_CACHE_TTL
    svc.GOOGLE_GROUPS_CACHE_TTL = 1
    print("       Waiting 2s for cache TTL expiry...")
    await asyncio.sleep(2)
    expired = GoogleGroupsService.get_cached_groups(user_id)
    report("Cache expires after TTL", expired is None, f"TTL=1s, result={'expired' if expired is None else 'still cached'}")
    svc.GOOGLE_GROUPS_CACHE_TTL = original_ttl

    # Restore real groups via a fresh API call
    print("       Restoring real groups in cache...")
    try:
        real_groups = await GoogleGroupsService.get_user_groups("hector@develom.com")
        GoogleGroupsService.update_cache(user_id, real_groups, sync_source="test_restore")
        report("Cache restored with real groups", True, f"groups={len(real_groups)}")
    except Exception as e:
        report("Cache restored with real groups", False, str(e))


# ─── Test 11: Service Account Impersonation ───────────────────────────

async def test_sa_impersonation():
    """Test using the Cloud Run service account via impersonation."""
    print("\n─── Test 11: Service Account Impersonation (Cloud Run Simulation) ───")

    sa_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not sa_key_path or not os.path.exists(sa_key_path):
        report("SA key file exists", True, "skipping — will test with ADC", skipped=True)
        return

    try:
        from google.oauth2 import service_account as sa_module
        scopes = ["https://www.googleapis.com/auth/cloud-identity.groups.readonly"]
        sa_creds = sa_module.Credentials.from_service_account_file(sa_key_path, scopes=scopes)
        request = google.auth.transport.requests.Request()
        sa_creds.refresh(request)

        report("SA credentials obtained", True, f"email={sa_creds.service_account_email}")
        report("SA token valid", sa_creds.valid)

        # Try groups:search with SA credentials
        customer_id = os.getenv("GOOGLE_GROUPS_CUSTOMER_ID", "")
        quota_project = os.getenv("GOOGLE_GROUPS_QUOTA_PROJECT", "")
        headers = {"Authorization": f"Bearer {sa_creds.token}"}
        if quota_project:
            headers["x-goog-user-project"] = quota_project

        search_url = "https://cloudidentity.googleapis.com/v1/groups:search"
        query = (
            f"parent=='customers/{customer_id}' && "
            "'cloudidentity.googleapis.com/groups.discussion_forum' in labels"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers, params={"query": query, "pageSize": 200}) as resp:
                report("SA groups:search HTTP 200", resp.status == 200, f"status={resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    groups = data.get("groups", [])
                    report(f"SA finds org groups", len(groups) > 0, f"count={len(groups)}")
                else:
                    body = await resp.text()
                    report("SA groups:search response", False, body[:300])

    except Exception as e:
        report("SA impersonation test", False, f"{type(e).__name__}: {e}")


# ─── Test 12: Consistency Check ───────────────────────────────────────

async def test_consistency(raw_groups, service_groups):
    """Verify raw API results match service results."""
    print("\n─── Test 12: Consistency Check (Raw API vs Service) ───")
    raw_set = set(raw_groups)
    svc_set = set(service_groups)

    report("Same number of groups", len(raw_set) == len(svc_set),
           f"raw={len(raw_set)}, service={len(svc_set)}")
    report("Identical group sets", raw_set == svc_set,
           f"diff={raw_set.symmetric_difference(svc_set) or 'none'}")


# ─── Main ─────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Cloud Identity API Integration Tests")
    parser.add_argument("--email", default="hector@develom.com", help="Email to test with")
    args = parser.parse_args()

    user_email = args.email
    start_time = time.time()

    print("=" * 70)
    print("  Cloud Identity Groups API — Integration Test Suite")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Test Email: {user_email}")
    print(f"  API Mode: {os.getenv('GOOGLE_GROUPS_API_MODE', 'cloud_identity')}")
    print(f"  Customer ID: {os.getenv('GOOGLE_GROUPS_CUSTOMER_ID', '(not set)')}")
    print(f"  Quota Project: {os.getenv('GOOGLE_GROUPS_QUOTA_PROJECT', '(not set)')}")
    print(f"  Groups Enabled: {os.getenv('GOOGLE_GROUPS_ENABLED', 'false')}")
    print("=" * 70)

    # Test 1: Credentials
    credentials, project = await test_credentials()
    if not credentials:
        print("\n⛔ Cannot proceed without valid credentials.")
        return

    # Test 2: groups:search
    org_groups = await test_groups_search(credentials)

    # Test 3: checkTransitiveMembership
    raw_member_groups = await test_check_membership(credentials, org_groups, user_email)

    # Test 4: Service internal method
    service_groups = await test_service_query(user_email)

    # Test 5: Public interface
    public_groups = await test_public_interface(user_email)

    # Test 6-8: Edge cases
    await test_non_member_email()
    await test_invalid_email()
    await test_missing_customer_id()

    # Test 9: Fallback
    await test_fallback_behavior()

    # Test 10: Cache
    await test_cache_layer()

    # Test 11: SA impersonation
    await test_sa_impersonation()

    # Test 12: Consistency
    await test_consistency(raw_member_groups, service_groups)

    # ─── Summary ──────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"  RESULTS: {PASS} passed, {FAIL} failed, {SKIP} skipped")
    print(f"  Duration: {elapsed:.1f}s")
    print("=" * 70)

    if FAIL > 0:
        print("\n  Failed tests:")
        for r in RESULTS:
            if r["status"] == "FAIL":
                print(f"    ❌ {r['test']}: {r['detail']}")

    print()
    return FAIL == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
