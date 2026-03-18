"use client";

import { useState, useEffect } from 'react';
import { DocumentRetrievalResponse } from '../lib/api';

interface DocumentViewerProps {
  document: DocumentRetrievalResponse;
  onClose: () => void;
}

export default function DocumentViewer({ document, onClose }: DocumentViewerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    const loadPdfViaProxy = async () => {
      try {
        // Get corpus_id, document_name, and source_uri from the document
        const corpusId = document.document.corpus_id;
        const documentName = document.document.name;
        const sourceUri = document.document.source_uri;
        
        if (!corpusId || !documentName) {
          setError('Missing corpus ID or document name');
          setIsLoading(false);
          return;
        }
        
        // Build proxy URL with optional source_uri to avoid duplicate lookups
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || '';
        let proxyUrl = `${backendUrl}/api/documents/proxy/${corpusId}/${encodeURIComponent(documentName)}`;
        
        // Add source_uri as query parameter if available (prevents 404 errors)
        if (sourceUri) {
          proxyUrl += `?source_uri=${encodeURIComponent(sourceUri)}`;
        }
        
        // Fetch PDF via proxy with IAP authentication (credentials: 'include')
        const response = await fetch(proxyUrl, {
          credentials: 'include',
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Failed to load PDF: ${response.status} - ${errorText}`);
        }
        
        // Create blob URL from response
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        setPdfUrl(blobUrl);
        setIsLoading(false);
      } catch (err) {
        console.error('Error loading PDF:', err);
        setError(err instanceof Error ? err.message : 'Failed to load document');
        setIsLoading(false);
      }
    };
    
    loadPdfViaProxy();
  }, [document]);
  
  // Cleanup blob URL when component unmounts or pdfUrl changes
  useEffect(() => {
    return () => {
      if (pdfUrl && pdfUrl.startsWith('blob:')) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [pdfUrl]);

  const handleDownload = () => {
    const url = pdfUrl || document.access?.url;
    if (url) {
      window.open(url, '_blank');
    }
  };

  const getFileExtension = () => {
    if (!document?.document?.name) return 'file';
    const name = document.document.name.toLowerCase();
    if (name.endsWith('.pdf')) return 'pdf';
    if (name.endsWith('.doc') || name.endsWith('.docx')) return 'word';
    if (name.endsWith('.txt')) return 'text';
    return 'file';
  };

  const fileType = getFileExtension();
  const isPdf = fileType === 'pdf';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-11/12 h-5/6 flex flex-col max-w-6xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900 truncate">
              {document.document.name}
            </h2>
            <p className="text-sm text-gray-500">
              Corpus: {document.document.corpus_name}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Download
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 bg-gray-50">
          {isLoading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading document...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-red-600">
                <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p className="text-lg font-medium">{error}</p>
              </div>
            </div>
          )}

          {!isLoading && !error && isPdf && pdfUrl && (
            <div className="h-full bg-white rounded shadow-inner">
              <iframe
                src={`${pdfUrl}#toolbar=1&navpanes=1&scrollbar=1`}
                className="w-full h-full border-0 rounded"
                title={document.document.name}
              />
            </div>
          )}

          {!isLoading && !error && !isPdf && (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="text-center max-w-md">
                <div className="mb-6">
                  <svg className="w-20 h-20 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Preview not available
                </h3>
                <p className="text-gray-600 mb-6">
                  This file type ({fileType}) cannot be previewed in the browser.
                  Click the Download button to view it locally.
                </p>
                <button
                  onClick={handleDownload}
                  className="px-6 py-3 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Download {document.document.name}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer Info */}
        {(document.document.created_at || document.access?.expires_at) && (
          <div className="p-3 border-t bg-gray-50 text-xs text-gray-500">
            <div className="flex justify-between">
              {document.document.created_at && (
                <span>Created: {new Date(document.document.created_at).toLocaleString()}</span>
              )}
              {document.access?.expires_at && (
                <span className="text-amber-600">
                  URL expires: {new Date(document.access.expires_at).toLocaleString()}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
