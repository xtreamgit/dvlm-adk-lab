"""
User repository for database operations.
"""

import json
from typing import Optional, List, Dict
from datetime import datetime, timezone

from ..connection import get_db_connection


class UserRepository:
    """Repository for user-related database operations."""

    @staticmethod
    def _derive_username_from_email(email: str) -> str:
        """Derive a stable username from an email for legacy schemas.

        Some older PostgreSQL schemas still include a NOT NULL `username` column.
        """
        if not email:
            return "user"
        local = email.split("@", 1)[0].strip()
        return local or "user"
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # Note: get_by_username removed - username column no longer exists
    # Use get_by_email instead (email is now the primary identifier)
    
    @staticmethod
    def get_by_email(email: str, active_only: bool = True) -> Optional[Dict]:
        """Get user by email. By default, only returns active users."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM users WHERE email = %s AND is_active = TRUE", (email,))
            else:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_by_google_id(google_id: str) -> Optional[Dict]:
        """Get user by Google ID (from IAP authentication)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE google_id = %s", (google_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def create(email: str, full_name: str, google_id: Optional[str] = None) -> Dict:
        """Create a new user (IAP authentication only).
        
        Args:
            email: User's email address (primary identifier)
            full_name: User's full name
            google_id: Google ID from IAP (optional)
        
        Returns:
            Created user dictionary
        """
        created_at = datetime.now(timezone.utc).isoformat()
        updated_at = created_at
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users (email, full_name, google_id, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (email, full_name, google_id, True, created_at, updated_at))
                result = cursor.fetchone()
            except Exception as e:
                # Backward compatibility: some schemas still require username.
                try:
                    import psycopg2
                except Exception:
                    raise

                if isinstance(e, psycopg2.errors.NotNullViolation) and "username" in str(e):
                    conn.rollback()
                    username = UserRepository._derive_username_from_email(email)
                    cursor.execute("""
                        INSERT INTO users (username, email, full_name, google_id, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (username, email, full_name, google_id, True, created_at, updated_at))
                    result = cursor.fetchone()
                else:
                    raise
            user_id = result['id'] if isinstance(result, dict) else result[0]
            conn.commit()
        
        return UserRepository.get_by_id(user_id)
    
    @staticmethod
    def create_iap_user(email: str, full_name: str, google_id: str) -> Dict:
        """Create a new user from IAP authentication.
        
        Note: This is now the same as create() - kept for backward compatibility.
        """
        return UserRepository.create(email=email, full_name=full_name, google_id=google_id)
    
    @staticmethod
    def update(user_id: int, **kwargs) -> Optional[Dict]:
        """Update user fields."""
        if not kwargs:
            return UserRepository.get_by_id(user_id)
        
        # Add updated_at timestamp
        kwargs['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Build UPDATE query
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s", values)
            conn.commit()
        
        return UserRepository.get_by_id(user_id)
    
    @staticmethod
    def update_last_login(user_id: int) -> bool:
        """Update the last login timestamp."""
        last_login = datetime.now(timezone.utc).isoformat()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = %s WHERE id = %s", (last_login, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def exists(email: str) -> bool:
        """Check if a user exists by email."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE email = %s LIMIT 1", (email,))
            return cursor.fetchone() is not None
    
    @staticmethod
    def get_profile(user_id: int) -> Optional[Dict]:
        """Get user profile."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                profile = dict(row)
                # Parse JSON preferences
                if profile.get('preferences'):
                    try:
                        profile['preferences'] = json.loads(profile['preferences'])
                    except (json.JSONDecodeError, TypeError):
                        profile['preferences'] = {}
                return profile
            return None
    
    @staticmethod
    def create_profile(user_id: int, theme: str = 'light', language: str = 'en', 
                       timezone: str = 'UTC', preferences: Optional[Dict] = None) -> Dict:
        """Create user profile."""
        preferences_json = json.dumps(preferences) if preferences else None
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_profiles (user_id, theme, language, timezone, preferences)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, theme, language, timezone, preferences_json))
            conn.commit()
        
        return UserRepository.get_profile(user_id)
    
    @staticmethod
    def update_profile(user_id: int, **kwargs) -> Optional[Dict]:
        """Update user profile."""
        if not kwargs:
            return UserRepository.get_profile(user_id)
        
        # Convert preferences dict to JSON string
        if 'preferences' in kwargs and kwargs['preferences'] is not None:
            kwargs['preferences'] = json.dumps(kwargs['preferences'])
        
        # Build UPDATE query
        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE user_profiles SET {set_clause} WHERE user_id = %s", values)
            conn.commit()
        
        return UserRepository.get_profile(user_id)
    
    @staticmethod
    def get_all(active_only: bool = True) -> List[Dict]:
        """Get all users, optionally filtering by active status."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM users WHERE is_active = TRUE ORDER BY created_at DESC")
            else:
                cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update_password(user_id: int, hashed_password: str) -> bool:
        """Deprecated: password auth removed — IAP handles all authentication."""
        return False
