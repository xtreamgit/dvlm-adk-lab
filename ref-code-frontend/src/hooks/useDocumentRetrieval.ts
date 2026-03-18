import { useState } from 'react';
import { apiClient } from '../lib/api-enhanced';

export interface DocumentRetrievalResponse {
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
    source_uri?: string;  // GCS URI to avoid duplicate lookups
  };
  access?: {
    url: string;
    expires_at: string;
    valid_for_seconds: number;
  };
}

export function useDocumentRetrieval() {
  const [isRetrieving, setIsRetrieving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentDocument, setCurrentDocument] = useState<DocumentRetrievalResponse | null>(null);

  const retrieveDocument = async (corpusId: number, documentName: string, generateSignedUrl: boolean = true) => {
    setIsRetrieving(true);
    setError(null);
    
    try {
      const document = await apiClient.retrieveDocument(corpusId, documentName, generateSignedUrl);
      setCurrentDocument(document);
      return document;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to retrieve document';
      setError(errorMessage);
      throw err;
    } finally {
      setIsRetrieving(false);
    }
  };

  const closeDocument = () => {
    setCurrentDocument(null);
    setError(null);
  };

  return {
    retrieveDocument,
    closeDocument,
    isRetrieving,
    error,
    currentDocument,
  };
}
