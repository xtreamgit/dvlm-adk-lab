"""
Google Groups Service — queries Cloud Identity Groups API for user group memberships.

Primary method: Cloud Identity Groups API (cloudidentity.googleapis.com)
  - Two-step: groups:search to list org groups, then checkTransitiveMembership per group
  - Supports transitive (nested) group memberships
  - Requires only Cloud Identity API enabled + GOOGLE_GROUPS_CUSTOMER_ID
  - NO domain-wide delegation needed, NO special admin roles needed

Fallback method: Admin SDK Directory API (admin.googleapis.com)
  - Used when GOOGLE_GROUPS_API_MODE=admin_sdk (legacy) or Cloud Identity fails
  - Requires domain-wide delegation + GOOGLE_GROUPS_ADMIN_EMAIL

This service is used by the Google Groups Bridge to automatically assign chatbot
groups and corpus access based on org group membership.

Requirements (Cloud Identity — default):
- Cloud Identity API enabled on the GCP project
- Service account granted "Group Reader" role at org level
- GOOGLE_GROUPS_ENABLED=true

Requirements (Admin SDK — fallback/legacy):
- Admin SDK API enabled on the GCP project
- Service account with domain-wide delegation enabled in Google Admin Console
- Scopes authorized: https://www.googleapis.com/auth/admin.directory.group.readonly
- GOOGLE_GROUPS_ADMIN_EMAIL=<admin-user>@<domain> (user to impersonate for API calls)
"""

import os
import json
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode

import google.auth
import google.auth.iam
import google.auth.transport.requests
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# Configuration
GOOGLE_GROUPS_ENABLED = os.getenv("GOOGLE_GROUPS_ENABLED", "false").lower() == "true"
GOOGLE_GROUPS_CACHE_TTL = int(os.getenv("GOOGLE_GROUPS_CACHE_TTL", "300"))  # seconds
GOOGLE_GROUPS_ADMIN_EMAIL = os.getenv("GOOGLE_GROUPS_ADMIN_EMAIL", "")  # admin user to impersonate (Admin SDK only)

# API mode: "cloud_identity" (default, recommended) or "admin_sdk" (legacy)
GOOGLE_GROUPS_API_MODE = os.getenv("GOOGLE_GROUPS_API_MODE", "cloud_identity").lower()

# Customer ID for Cloud Identity groups:search (find via: gcloud organizations describe ORG_ID --format="value(owner.directoryCustomerId)")
GOOGLE_GROUPS_CUSTOMER_ID = os.getenv("GOOGLE_GROUPS_CUSTOMER_ID", "")

# GCP project for quota billing (required when using user ADC locally)
GOOGLE_GROUPS_QUOTA_PROJECT = os.getenv("GOOGLE_GROUPS_QUOTA_PROJECT", os.getenv("GOOGLE_CLOUD_PROJECT", ""))

CLOUD_IDENTITY_SCOPES = ["https://www.googleapis.com/auth/cloud-identity.groups.readonly"]
ADMIN_SDK_SCOPES = ["https://www.googleapis.com/auth/admin.directory.group.readonly"]


class GoogleGroupsService:
    """Service for querying user group memberships via Cloud Identity or Admin SDK."""

    _cloud_identity_credentials = None
    _admin_sdk_credentials = None

    @staticmethod
    def is_enabled() -> bool:
        """Check if Google Groups integration is enabled."""
        return GOOGLE_GROUPS_ENABLED

    @staticmethod
    async def get_user_groups(user_email: str) -> List[str]:
        """
        Get a user's Google Group memberships.
        Returns a list of group email addresses the user belongs to.

        Uses Cloud Identity API by default (no delegation needed).
        Falls back to Admin SDK if configured or if Cloud Identity fails.
        """
        if not GOOGLE_GROUPS_ENABLED:
            logger.debug("Google Groups integration is disabled")
            return []

        try:
            if GOOGLE_GROUPS_API_MODE == "admin_sdk":
                # Legacy mode: use Admin SDK with domain-wide delegation
                logger.debug(f"Using Admin SDK (legacy) for {user_email}")
                return await GoogleGroupsService._query_admin_sdk(user_email)
            else:
                # Default: use Cloud Identity API
                logger.debug(f"Using Cloud Identity API for {user_email}")
                return await GoogleGroupsService._query_cloud_identity(user_email)
        except Exception as e:
            logger.error(f"Failed to query Google Groups for {user_email} via {GOOGLE_GROUPS_API_MODE}: {e}")

            # If Cloud Identity failed and Admin SDK is available, try fallback
            if GOOGLE_GROUPS_API_MODE != "admin_sdk" and GOOGLE_GROUPS_ADMIN_EMAIL:
                logger.info(f"Falling back to Admin SDK for {user_email}")
                try:
                    return await GoogleGroupsService._query_admin_sdk(user_email)
                except Exception as fallback_err:
                    logger.error(f"Admin SDK fallback also failed for {user_email}: {fallback_err}")

            return []

    # ─── Cloud Identity API (primary) ────────────────────────────────────

    @staticmethod
    def _get_cloud_identity_credentials():
        """
        Get credentials for Cloud Identity Groups API.
        Uses Application Default Credentials — no delegation needed.
        The service account just needs "Groups Reader" role at org level.
        """
        if (GoogleGroupsService._cloud_identity_credentials
                and GoogleGroupsService._cloud_identity_credentials.valid):
            return GoogleGroupsService._cloud_identity_credentials

        credentials, _ = google.auth.default(scopes=CLOUD_IDENTITY_SCOPES)
        request = GoogleAuthRequest()
        if not credentials.valid:
            credentials.refresh(request)

        GoogleGroupsService._cloud_identity_credentials = credentials
        logger.debug("Obtained Cloud Identity API credentials")
        return credentials

    @staticmethod
    async def _query_cloud_identity(user_email: str) -> List[str]:
        """
        Query Cloud Identity Groups API for user's group memberships.

        Two-step approach (no Groups Reader admin role needed):
        1. List all groups in the org via groups:search
        2. Check transitive membership for each group via checkTransitiveMembership

        Requires:
        - GOOGLE_GROUPS_CUSTOMER_ID set to the Workspace customer ID
        - Cloud Identity API enabled
        - SA (or user) with basic org membership (no special admin role)
        """
        import aiohttp

        if not GOOGLE_GROUPS_CUSTOMER_ID:
            raise ValueError(
                "GOOGLE_GROUPS_CUSTOMER_ID not set. "
                "Find it via: gcloud organizations describe ORG_ID "
                "--format='value(owner.directoryCustomerId)'"
            )

        credentials = GoogleGroupsService._get_cloud_identity_credentials()

        headers = {
            "Authorization": f"Bearer {credentials.token}",
        }
        # Add quota project header for local ADC (user credentials)
        if GOOGLE_GROUPS_QUOTA_PROJECT:
            headers["x-goog-user-project"] = GOOGLE_GROUPS_QUOTA_PROJECT

        # Step 1: List all groups in the org
        search_url = "https://cloudidentity.googleapis.com/v1/groups:search"
        search_query = (
            f"parent=='customers/{GOOGLE_GROUPS_CUSTOMER_ID}' && "
            "'cloudidentity.googleapis.com/groups.discussion_forum' in labels"
        )

        all_groups = []
        async with aiohttp.ClientSession() as session:
            page_token = None
            while True:
                params = {"query": search_query, "view": "BASIC", "pageSize": 200}
                if page_token:
                    params["pageToken"] = page_token

                async with session.get(search_url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error(f"Cloud Identity groups:search failed ({resp.status}): {body[:500]}")
                        raise RuntimeError(f"Cloud Identity groups:search {resp.status}: {body[:500]}")
                    data = await resp.json()

                for g in data.get("groups", []):
                    all_groups.append({
                        "name": g["name"],
                        "email": g.get("groupKey", {}).get("id", ""),
                    })

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

            logger.debug(f"Cloud Identity: found {len(all_groups)} groups in org, checking membership for {user_email}")

            # Step 2: Check transitive membership for each group
            group_emails = []
            for g in all_groups:
                group_resource = g["name"]  # e.g. "groups/02afmg284hehq74"
                check_url = (
                    f"https://cloudidentity.googleapis.com/v1/"
                    f"{group_resource}/memberships:checkTransitiveMembership"
                )
                check_params = {"query": f"member_key_id=='{user_email}'"}

                async with session.get(check_url, headers=headers, params=check_params) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("hasMembership", False):
                            group_emails.append(g["email"])
                    else:
                        logger.warning(
                            f"Cloud Identity checkTransitiveMembership failed for "
                            f"{g['email']} ({resp.status})"
                        )

        logger.info(
            f"Cloud Identity: {user_email} belongs to {len(group_emails)}/{len(all_groups)} "
            f"groups (transitive): {group_emails}"
        )
        return group_emails

    # ─── Admin SDK Directory API (fallback/legacy) ───────────────────────

    @staticmethod
    def _get_admin_sdk_credentials():
        """
        Get credentials with domain-wide delegation for Admin SDK.
        The SA impersonates GOOGLE_GROUPS_ADMIN_EMAIL to call Admin SDK.

        On Cloud Run, google.auth.default() returns compute_engine.Credentials
        which lack a .signer. We use google.auth.iam.Signer to sign JWTs
        via the IAM signBlob API instead.
        """
        if (GoogleGroupsService._admin_sdk_credentials
                and GoogleGroupsService._admin_sdk_credentials.valid):
            return GoogleGroupsService._admin_sdk_credentials

        if not GOOGLE_GROUPS_ADMIN_EMAIL:
            raise ValueError(
                "GOOGLE_GROUPS_ADMIN_EMAIL not set. "
                "Required for Admin SDK domain-wide delegation."
            )

        # Get the default SA credentials
        source_credentials, _ = google.auth.default()

        # Refresh so we have a valid token for IAM signing
        request = GoogleAuthRequest()
        if not source_credentials.valid:
            source_credentials.refresh(request)

        # Get the SA email — works for both local SA key and Cloud Run metadata
        sa_email = getattr(source_credentials, "service_account_email", None)
        if not sa_email:
            sa_email = source_credentials.signer_email if hasattr(source_credentials, "signer_email") else None
        if not sa_email:
            # Fallback: query metadata server
            import requests as http_req
            resp = http_req.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email",
                headers={"Metadata-Flavor": "Google"}, timeout=5
            )
            sa_email = resp.text

        # Use IAM-based signer (works on Cloud Run without a local key file)
        iam_signer = google.auth.iam.Signer(
            request=request,
            credentials=source_credentials,
            service_account_email=sa_email,
        )

        # Create delegated credentials that impersonate the admin user
        delegated = service_account.Credentials(
            signer=iam_signer,
            service_account_email=sa_email,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=ADMIN_SDK_SCOPES,
            subject=GOOGLE_GROUPS_ADMIN_EMAIL,
        )
        delegated.refresh(request)
        GoogleGroupsService._admin_sdk_credentials = delegated
        return delegated

    @staticmethod
    async def _query_admin_sdk(user_email: str) -> List[str]:
        """
        Query Admin SDK Directory API for user's group memberships (legacy).
        Uses domain-wide delegation to impersonate an admin user.

        API: GET https://admin.googleapis.com/admin/directory/v1/groups?userKey={email}
        """
        import aiohttp

        credentials = GoogleGroupsService._get_admin_sdk_credentials()

        base_url = "https://admin.googleapis.com/admin/directory/v1/groups"
        params = {"userKey": user_email}

        headers = {
            "Authorization": f"Bearer {credentials.token}",
        }

        group_emails = []
        page_token = None

        async with aiohttp.ClientSession() as session:
            while True:
                if page_token:
                    params["pageToken"] = page_token

                async with session.get(base_url, headers=headers, params=params) as resp:
                    if resp.status == 403:
                        body = await resp.text()
                        logger.error(
                            f"Admin SDK 403 for {user_email}. "
                            f"SA={credentials.service_account_email}, "
                            f"subject={GOOGLE_GROUPS_ADMIN_EMAIL}. "
                            f"Body: {body[:2000]}"
                        )
                        return []
                    elif resp.status == 400:
                        body = await resp.text()
                        logger.error(f"Admin SDK bad request for {user_email}: {body[:500]}")
                        return []
                    elif resp.status != 200:
                        body = await resp.text()
                        logger.error(f"Admin SDK error {resp.status}: {body[:500]}")
                        return []

                    data = await resp.json()

                groups = data.get("groups", [])
                for group in groups:
                    email = group.get("email", "")
                    if email:
                        group_emails.append(email)

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        logger.info(f"Admin SDK: found {len(group_emails)} Google Groups for {user_email}: {group_emails}")
        return group_emails

    @staticmethod
    def get_cached_groups(user_id: int) -> Optional[List[str]]:
        """
        Get cached Google Groups for a user if the cache is still fresh.
        Returns None if cache is stale or doesn't exist.
        """
        from database.connection import get_db_connection

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT google_groups, last_synced_at
                    FROM user_google_group_sync
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return None

                last_synced = row["last_synced_at"]
                if isinstance(last_synced, str):
                    last_synced = datetime.fromisoformat(last_synced)

                cache_age = (datetime.utcnow() - last_synced).total_seconds()
                if cache_age > GOOGLE_GROUPS_CACHE_TTL:
                    logger.debug(f"Cache expired for user {user_id} (age: {cache_age:.0f}s)")
                    return None

                groups = row["google_groups"]
                if isinstance(groups, str):
                    groups = json.loads(groups)
                return groups

        except Exception as e:
            logger.warning(f"Failed to read group cache for user {user_id}: {e}")
            return None

    @staticmethod
    def update_cache(user_id: int, google_groups: List[str], sync_source: str = "login"):
        """Update the cached Google Groups for a user."""
        from database.connection import get_db_connection

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO user_google_group_sync (user_id, google_groups, last_synced_at, sync_source)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        google_groups = EXCLUDED.google_groups,
                        last_synced_at = CURRENT_TIMESTAMP,
                        sync_source = EXCLUDED.sync_source
                    """,
                    (user_id, json.dumps(google_groups), sync_source),
                )
                conn.commit()
                logger.debug(f"Updated group cache for user {user_id}: {google_groups}")
        except Exception as e:
            logger.warning(f"Failed to update group cache for user {user_id}: {e}")
