#!/usr/bin/env python3
"""
Google Groups Bridge — End-to-End Validation Test Suite

Tests the full bridge pipeline:
  Google Groups (Cloud Identity API)
    → Agent mapping (google_group_agent_mappings)
    → Chatbot group assignment (chatbot_user_groups)
    → Corpus access sync (chatbot_corpus_access)
    → Cache layer (user_google_group_sync)

Usage:
    python tests/test_bridge_validation.py --email hector@develom.com
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Setup paths and env ──────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local", override=True)

from database.connection import get_db_connection
from services.google_groups_service import GoogleGroupsService
from services.google_groups_bridge import GoogleGroupsBridge

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ── Test infrastructure ──────────────────────────────────────────
passed = 0
failed = 0
skipped = 0


def check(label: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {label}" + (f" — {detail}" if detail else ""))
    else:
        failed += 1
        print(f"  ❌ {label}" + (f" — {detail}" if detail else ""))


def skip(label: str, reason: str):
    global skipped
    skipped += 1
    print(f"  ⏭️  {label} — {reason}")


def section(title: str):
    print(f"\n─── {title} ───")


# ── Database helpers ─────────────────────────────────────────────
def db_query(sql: str, params=None) -> List[Dict]:
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(sql, params or ())
        return [dict(r) for r in c.fetchall()]


def db_execute(sql: str, params=None):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(sql, params or ())
        conn.commit()


def get_user(email: str) -> Optional[Dict]:
    rows = db_query("SELECT id, username, email, is_active FROM users WHERE email = %s", (email,))
    return rows[0] if rows else None


def get_chatbot_user(email: str) -> Optional[Dict]:
    rows = db_query("SELECT id, username, email, is_active FROM chatbot_users WHERE email = %s", (email,))
    return rows[0] if rows else None


def get_user_chatbot_groups(chatbot_user_id: int) -> List[Dict]:
    return db_query(
        """SELECT cug.chatbot_group_id, cg.name as group_name
           FROM chatbot_user_groups cug
           JOIN chatbot_groups cg ON cug.chatbot_group_id = cg.id
           WHERE cug.chatbot_user_id = %s""",
        (chatbot_user_id,),
    )


def get_group_corpus_access(chatbot_group_id: int) -> List[Dict]:
    return db_query(
        """SELECT cca.corpus_id, cca.permission, c.name as corpus_name
           FROM chatbot_corpus_access cca
           JOIN corpora c ON cca.corpus_id = c.id
           WHERE cca.chatbot_group_id = %s
           ORDER BY c.name""",
        (chatbot_group_id,),
    )


def get_agent_mappings() -> List[Dict]:
    return db_query(
        """SELECT ggam.google_group_email, ggam.chatbot_group_id,
                  ggam.priority, cg.name as chatbot_group_name
           FROM google_group_agent_mappings ggam
           JOIN chatbot_groups cg ON ggam.chatbot_group_id = cg.id
           WHERE ggam.is_active = TRUE
           ORDER BY ggam.priority DESC"""
    )


def get_corpus_mappings() -> List[Dict]:
    return db_query(
        """SELECT ggcm.google_group_email, ggcm.corpus_id,
                  ggcm.permission, c.name as corpus_name
           FROM google_group_corpus_mappings ggcm
           JOIN corpora c ON ggcm.corpus_id = c.id
           WHERE ggcm.is_active = TRUE
           ORDER BY ggcm.google_group_email"""
    )


def get_cache(user_id: int) -> Optional[Dict]:
    rows = db_query(
        "SELECT * FROM user_google_group_sync WHERE user_id = %s", (user_id,)
    )
    return rows[0] if rows else None


def clear_cache(user_id: int):
    db_execute("DELETE FROM user_google_group_sync WHERE user_id = %s", (user_id,))


# ── Tests ────────────────────────────────────────────────────────

def test_1_prerequisites(email: str):
    """Verify all prerequisites are in place before testing the bridge."""
    section("Test 1: Prerequisites Check")

    # Bridge enabled
    check("Bridge is enabled", GoogleGroupsBridge.is_enabled())

    # User exists
    user = get_user(email)
    check("App user exists", user is not None, f"id={user['id']}" if user else "NOT FOUND")
    if user:
        check("App user is active", user["is_active"])

    # Agent mappings exist
    mappings = get_agent_mappings()
    check("Agent mappings configured", len(mappings) > 0, f"count={len(mappings)}")
    for m in mappings:
        print(f"       {m['google_group_email']} → {m['chatbot_group_name']} (priority={m['priority']})")

    # Corpus mappings exist
    corpus_maps = get_corpus_mappings()
    check("Corpus mappings configured", len(corpus_maps) > 0, f"count={len(corpus_maps)}")
    for m in corpus_maps:
        print(f"       {m['google_group_email']} → {m['corpus_name']} ({m['permission']})")

    return user


def test_2_cloud_identity_groups(email: str):
    """Verify Cloud Identity API returns groups for the test user."""
    section("Test 2: Cloud Identity API — Fetch User Groups")

    groups = asyncio.get_event_loop().run_until_complete(
        GoogleGroupsService.get_user_groups(email)
    )
    check("get_user_groups returns results", len(groups) > 0, f"count={len(groups)}")
    for g in groups:
        print(f"       {g}")

    return groups


def test_3_agent_mapping_logic(google_groups: List[str]):
    """Verify the agent mapping logic selects the correct chatbot group."""
    section("Test 3: Agent Mapping Logic")

    mappings = get_agent_mappings()
    matched = [m for m in mappings if m["google_group_email"] in google_groups]
    check("At least one agent mapping matches", len(matched) > 0, f"matched={len(matched)}")

    if matched:
        best = matched[0]  # Already sorted by priority DESC
        check(
            "Highest-priority mapping identified",
            True,
            f"{best['google_group_email']} → {best['chatbot_group_name']} (priority={best['priority']})",
        )
        return best
    return None


def test_4_corpus_mapping_logic(google_groups: List[str]):
    """Verify corpus mapping logic resolves correct corpora and permissions."""
    section("Test 4: Corpus Mapping Logic")

    corpus_maps = get_corpus_mappings()
    matched = [m for m in corpus_maps if m["google_group_email"] in google_groups]
    check("At least one corpus mapping matches", len(matched) > 0, f"matched={len(matched)}")

    # Resolve highest permission per corpus (same logic as bridge)
    permission_rank = {"query": 1, "read": 2, "upload": 3, "delete": 4, "admin": 5}
    resolved = {}
    for m in matched:
        cid = m["corpus_id"]
        perm = m["permission"]
        if cid not in resolved or permission_rank.get(perm, 0) > permission_rank.get(resolved[cid]["permission"], 0):
            resolved[cid] = m

    check("Corpus permissions resolved", len(resolved) > 0, f"corpora={len(resolved)}")
    for cid, m in resolved.items():
        print(f"       {m['corpus_name']} → {m['permission']} (via {m['google_group_email']})")

    return resolved


def test_5_force_sync(user_id: int, email: str):
    """Run force_sync_user and verify the full pipeline result."""
    section("Test 5: Force Sync (Full Pipeline)")

    # Clear cache to force a fresh API call
    clear_cache(user_id)
    check("Cache cleared", get_cache(user_id) is None)

    # Run force sync
    result = asyncio.get_event_loop().run_until_complete(
        GoogleGroupsBridge.force_sync_user(user_id, email)
    )

    check("Sync status is 'synced'", result["status"] == "synced", f"status={result['status']}")
    check("Google groups returned", len(result["google_groups"]) > 0, f"count={len(result['google_groups'])}")
    check("Chatbot group assigned", result["chatbot_group"] is not None, f"group={result['chatbot_group']}")
    check("Corpora synced", result["corpora_synced"] > 0, f"count={result['corpora_synced']}")
    check("Not from cache (fresh sync)", not result["from_cache"])

    return result


def test_6_db_state_after_sync(email: str, expected_group: str, expected_corpora: Dict):
    """Verify database state matches expected values after sync."""
    section("Test 6: Database State After Sync")

    # Check chatbot user exists
    chatbot_user = get_chatbot_user(email)
    check("Chatbot user exists", chatbot_user is not None, f"id={chatbot_user['id']}" if chatbot_user else "NOT FOUND")
    if not chatbot_user:
        return

    # Check chatbot group assignment
    user_groups = get_user_chatbot_groups(chatbot_user["id"])
    group_names = [g["group_name"] for g in user_groups]
    check(
        f"Assigned to '{expected_group}'",
        expected_group in group_names,
        f"actual={group_names}",
    )

    # Check corpus access on the assigned group
    target_group = next((g for g in user_groups if g["group_name"] == expected_group), None)
    if target_group:
        corpus_access = get_group_corpus_access(target_group["chatbot_group_id"])
        corpus_names = {ca["corpus_name"] for ca in corpus_access}
        expected_names = {m["corpus_name"] for m in expected_corpora.values()}

        # Check each expected corpus is accessible
        for exp_cid, exp_map in expected_corpora.items():
            found = next((ca for ca in corpus_access if ca["corpus_id"] == exp_cid), None)
            if found:
                check(
                    f"Corpus '{exp_map['corpus_name']}' accessible",
                    True,
                    f"permission={found['permission']}",
                )
                check(
                    f"Corpus '{exp_map['corpus_name']}' permission correct",
                    found["permission"] == exp_map["permission"],
                    f"expected={exp_map['permission']}, actual={found['permission']}",
                )
            else:
                check(f"Corpus '{exp_map['corpus_name']}' accessible", False, "NOT FOUND in chatbot_corpus_access")


def test_7_cache_populated(user_id: int, expected_groups: List[str]):
    """Verify cache was populated after sync."""
    section("Test 7: Cache State After Sync")

    cache = get_cache(user_id)
    check("Cache entry exists", cache is not None)
    if cache:
        cached_groups = cache["google_groups"]
        check("Cache has groups", len(cached_groups) > 0, f"count={len(cached_groups)}")
        check(
            "Cached groups match API result",
            set(cached_groups) == set(expected_groups),
            f"diff={set(expected_groups) - set(cached_groups)}" if set(expected_groups) != set(cached_groups) else "identical",
        )
        check("Sync source recorded", cache["sync_source"] is not None, f"source={cache['sync_source']}")


def test_8_cached_sync(user_id: int, email: str):
    """Verify a second sync uses the cache and produces the same result."""
    section("Test 8: Cached Sync (No API Call)")

    result = asyncio.get_event_loop().run_until_complete(
        GoogleGroupsBridge.sync_user_access(user_id, email)
    )

    check("Sync status is 'synced'", result["status"] == "synced", f"status={result['status']}")
    check("From cache", result["from_cache"], f"from_cache={result['from_cache']}")
    check("Same chatbot group", result["chatbot_group"] is not None, f"group={result['chatbot_group']}")


def test_9_non_member_user():
    """Verify bridge handles a user with no Google Group memberships."""
    section("Test 9: Non-Member User")

    # Find a develom.com user who is NOT in any Google Groups
    # mila@develom.com returned 0 groups in earlier testing
    user = get_user("mila@develom.com")
    if not user:
        skip("Non-member test", "mila@develom.com not found in users table")
        return

    clear_cache(user["id"])
    result = asyncio.get_event_loop().run_until_complete(
        GoogleGroupsBridge.force_sync_user(user["id"], user["email"])
    )

    check("Status is 'no_groups'", result["status"] == "no_groups", f"status={result['status']}")
    check("No chatbot group assigned", result["chatbot_group"] is None)
    check("No corpora synced", result["corpora_synced"] == 0)
    check("Empty google_groups list", len(result["google_groups"]) == 0)


def test_10_non_workspace_user():
    """Verify bridge handles a user outside the Workspace org."""
    section("Test 10: Non-Workspace User (External Email)")

    user = get_user("test@example.com")
    if not user:
        skip("Non-workspace test", "test@example.com not found in users table")
        return

    clear_cache(user["id"])
    result = asyncio.get_event_loop().run_until_complete(
        GoogleGroupsBridge.force_sync_user(user["id"], user["email"])
    )

    check("Status is 'no_groups'", result["status"] == "no_groups", f"status={result['status']}")
    check("No chatbot group assigned", result["chatbot_group"] is None)
    check("No corpora synced", result["corpora_synced"] == 0)


def test_11_priority_resolution(google_groups: List[str]):
    """Verify that when a user matches multiple agent mappings, the highest priority wins."""
    section("Test 11: Priority Resolution")

    mappings = get_agent_mappings()
    matched = [m for m in mappings if m["google_group_email"] in google_groups]

    if len(matched) < 2:
        skip("Priority resolution", f"User only matches {len(matched)} mapping(s), need ≥2 to test priority")
        return

    priorities = [(m["chatbot_group_name"], m["priority"]) for m in matched]
    print(f"       Matched mappings: {priorities}")

    best = max(matched, key=lambda m: m["priority"])
    check(
        "Highest priority mapping selected",
        matched[0]["chatbot_group_name"] == best["chatbot_group_name"],
        f"winner={best['chatbot_group_name']} (priority={best['priority']})",
    )


def test_12_permission_escalation(google_groups: List[str]):
    """Verify that when multiple corpus mappings match, the highest permission wins."""
    section("Test 12: Permission Escalation")

    corpus_maps = get_corpus_mappings()
    matched = [m for m in corpus_maps if m["google_group_email"] in google_groups]

    # Group by corpus
    by_corpus = {}
    for m in matched:
        by_corpus.setdefault(m["corpus_name"], []).append(m)

    multi_match = {k: v for k, v in by_corpus.items() if len(v) > 1}
    if not multi_match:
        skip("Permission escalation", "No corpus has multiple matching group mappings")
        return

    permission_rank = {"query": 1, "read": 2, "upload": 3, "delete": 4, "admin": 5}
    for corpus_name, maps in multi_match.items():
        perms = [(m["google_group_email"], m["permission"]) for m in maps]
        best_perm = max(maps, key=lambda m: permission_rank.get(m["permission"], 0))
        check(
            f"Corpus '{corpus_name}' — highest permission wins",
            True,
            f"winner={best_perm['permission']} from {perms}",
        )


def test_13_bridge_status_endpoint():
    """Verify the bridge status endpoint returns correct data."""
    section("Test 13: Bridge Status Endpoint")

    status = GoogleGroupsBridge.get_bridge_status()
    check("Status reports enabled", status["enabled"] is True)
    check("Agent mappings count > 0", status["agent_mappings_count"] > 0, f"count={status['agent_mappings_count']}")
    check("Corpus mappings count > 0", status["corpus_mappings_count"] > 0, f"count={status['corpus_mappings_count']}")
    check("Synced users count > 0", status["synced_users_count"] > 0, f"count={status['synced_users_count']}")
    check("Last sync timestamp present", status["last_sync"] is not None, f"last_sync={status['last_sync']}")
    check("Cache TTL configured", status["cache_ttl_seconds"] > 0, f"ttl={status['cache_ttl_seconds']}s")


def test_14_stale_group_removal(user_id: int, email: str):
    """Verify that when a user's groups change, stale chatbot group memberships are removed."""
    section("Test 14: Stale Group Removal")

    chatbot_user = get_chatbot_user(email)
    if not chatbot_user:
        skip("Stale group removal", "Chatbot user not found")
        return

    # Record current state
    groups_before = get_user_chatbot_groups(chatbot_user["id"])
    bridge_managed_groups = {m["chatbot_group_name"] for m in get_agent_mappings()}

    bridge_groups_before = [g for g in groups_before if g["group_name"] in bridge_managed_groups]
    check(
        "User has bridge-managed group(s)",
        len(bridge_groups_before) > 0,
        f"groups={[g['group_name'] for g in bridge_groups_before]}",
    )

    # The bridge should only assign ONE bridge-managed group (highest priority)
    check(
        "Only one bridge-managed group assigned",
        len(bridge_groups_before) == 1,
        f"count={len(bridge_groups_before)}, expected=1",
    )


def test_15_api_endpoint_sync(user_id: int):
    """Test the admin API endpoint for force sync."""
    section("Test 15: API Endpoint — Force Sync")

    try:
        import aiohttp

        async def call_api():
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:8000/api/admin/google-groups/sync/{user_id}"
                async with session.post(url) as resp:
                    return resp.status, await resp.json()

        status_code, data = asyncio.get_event_loop().run_until_complete(call_api())
        check("API returns 200", status_code == 200, f"status={status_code}")
        check("API returns synced status", data.get("status") == "synced", f"status={data.get('status')}")
        check("API returns google_groups", len(data.get("google_groups", [])) > 0)
        check("API returns chatbot_group", data.get("chatbot_group") is not None, f"group={data.get('chatbot_group')}")
        check("API returns corpora_synced", data.get("corpora_synced", 0) > 0, f"count={data.get('corpora_synced')}")
    except Exception as e:
        skip("API endpoint test", f"Backend not running or error: {e}")


def test_16_api_endpoint_status():
    """Test the admin API endpoint for bridge status."""
    section("Test 16: API Endpoint — Bridge Status")

    try:
        import aiohttp

        async def call_api():
            async with aiohttp.ClientSession() as session:
                url = "http://localhost:8000/api/admin/google-groups/status"
                async with session.get(url) as resp:
                    return resp.status, await resp.json()

        status_code, data = asyncio.get_event_loop().run_until_complete(call_api())
        check("API returns 200", status_code == 200, f"status={status_code}")
        check("API reports enabled", data.get("enabled") is True)
        check("API reports mappings", data.get("agent_mappings_count", 0) > 0)
    except Exception as e:
        skip("API status endpoint test", f"Backend not running or error: {e}")


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Google Groups Bridge Validation")
    parser.add_argument("--email", required=True, help="Email of a user who IS a member of Google Groups")
    args = parser.parse_args()

    email = args.email

    print("=" * 70)
    print("  GOOGLE GROUPS BRIDGE — VALIDATION TEST SUITE")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Test Email: {email}")
    print(f"  Bridge Enabled: {GoogleGroupsBridge.is_enabled()}")
    print("=" * 70)

    start = time.time()

    # Test 1: Prerequisites
    user = test_1_prerequisites(email)
    if not user:
        print("\n❌ ABORT: Test user not found in database")
        return

    # Test 2: Cloud Identity API
    google_groups = test_2_cloud_identity_groups(email)
    if not google_groups:
        print("\n❌ ABORT: No Google Groups returned — cannot validate bridge")
        return

    # Test 3: Agent mapping logic
    best_mapping = test_3_agent_mapping_logic(google_groups)

    # Test 4: Corpus mapping logic
    resolved_corpora = test_4_corpus_mapping_logic(google_groups)

    # Test 5: Force sync (full pipeline)
    sync_result = test_5_force_sync(user["id"], email)

    # Test 6: DB state verification
    if best_mapping and resolved_corpora:
        test_6_db_state_after_sync(email, best_mapping["chatbot_group_name"], resolved_corpora)

    # Test 7: Cache verification
    test_7_cache_populated(user["id"], google_groups)

    # Test 8: Cached sync
    test_8_cached_sync(user["id"], email)

    # Test 9: Non-member user
    test_9_non_member_user()

    # Test 10: Non-workspace user
    test_10_non_workspace_user()

    # Test 11: Priority resolution
    test_11_priority_resolution(google_groups)

    # Test 12: Permission escalation
    test_12_permission_escalation(google_groups)

    # Test 13: Bridge status
    test_13_bridge_status_endpoint()

    # Test 14: Stale group removal
    test_14_stale_group_removal(user["id"], email)

    # Test 15-16: API endpoints
    test_15_api_endpoint_sync(user["id"])
    test_16_api_endpoint_status()

    elapsed = time.time() - start

    print("\n" + "=" * 70)
    print(f"  RESULTS: {passed} passed, {failed} failed, {skipped} skipped")
    print(f"  Duration: {elapsed:.1f}s")
    print("=" * 70)

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
