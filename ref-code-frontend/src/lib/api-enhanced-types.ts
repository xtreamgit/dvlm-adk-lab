/**
 * Type definitions for API responses
 */

// Admin types
export interface AdminCorpusDetail {
  id: number;
  name: string;
  display_name: string;
  description: string;
  gcs_bucket: string;
  vertex_corpus_id: string | null;
  is_active: boolean;
  created_at: string;
  metadata?: Record<string, unknown>;
  groups_with_access?: Array<{
    group_id: number;
    group_name: string;
    permission: string;
  }>;
  recent_activity?: unknown[];
  document_count?: number;
}

export interface AuditLogEntry {
  id: number;
  corpus_id: number;
  corpus_name?: string;
  user_id: number;
  user_name?: string;
  action: string;
  changes: string | Record<string, unknown>;
  metadata: string | Record<string, unknown>;
  timestamp: string;
}

export interface BulkOperationResult {
  success: boolean;
  message: string;
  affected_count?: number;
  errors?: string[];
}

export interface SyncResult {
  success: boolean;
  message: string;
  added?: number;
  updated?: number;
  deactivated?: number;
}

export interface AdminUserDetail {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  groups?: string[];
  roles?: string[];
}

export interface GroupDetail {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  member_count?: number;
  corpora_access?: Array<{
    corpus_id: number;
    corpus_name: string;
    permission: string;
  }>;
}

export interface ApiResponse<T = unknown> {
  status?: string;
  message?: string;
  data?: T;
}
