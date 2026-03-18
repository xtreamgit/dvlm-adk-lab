/**
 * Shared type definitions.
 *
 * Note: The legacy ApiClient class (Bearer token auth, login/register) was
 * removed after migrating to IAP-only authentication. All API calls now go
 * through api-enhanced.ts which uses credentials: 'include' for IAP auth.
 */

export type UserProfile = {
  name: string;
  preferences?: string;
};

export type DocumentRetrievalResponse = {
  status: string;
  document: {
    id: string;
    name: string;
    corpus_id: number;
    corpus_name: string;
    file_type: string;
    size_bytes?: number;
    created_at?: string;
    updated_at?: string;
    source_uri?: string;
  };
  access?: {
    url: string;
    expires_at: string;
    valid_for_seconds: number;
  };
};

export type DocumentAccessLog = {
  id: number;
  user_id: number;
  corpus_id: number;
  document_name: string;
  document_file_id?: string;
  access_type: string;
  success: boolean;
  error_message?: string;
  source_uri?: string;
  accessed_at: string;
};
