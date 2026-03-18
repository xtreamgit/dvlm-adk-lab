"use client";

import { useState, useEffect } from 'react';
import { useDocumentRetrieval } from '../hooks/useDocumentRetrieval';
import { apiClient } from '@/lib/api-enhanced';
import DocumentViewer from './DocumentViewer';

interface Corpus {
  id: number;
  name: string;
  display_name: string;
}

interface DocumentRetrievalPanelProps {
  defaultCorpusId?: number;
  preselectedCorpusName?: string;
  preselectedDocumentName?: string;
}

interface Document {
  file_id: string;
  display_name: string;
  file_type: string;
  created_at?: string;
}

export default function DocumentRetrievalPanel({ defaultCorpusId = 1, preselectedCorpusName, preselectedDocumentName }: DocumentRetrievalPanelProps) {
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [loadingCorpora, setLoadingCorpora] = useState(true);
  const [corpusId, setCorpusId] = useState(defaultCorpusId.toString());
  const [documentName, setDocumentName] = useState('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const { retrieveDocument, closeDocument, currentDocument, isRetrieving, error } = useDocumentRetrieval();

  useEffect(() => {
    loadCorpora();
  }, []);

  useEffect(() => {
    if (preselectedCorpusName && corpora.length > 0) {
      const matchedCorpus = corpora.find(
        c => c.name === preselectedCorpusName || c.display_name === preselectedCorpusName
      );
      if (matchedCorpus) {
        setCorpusId(matchedCorpus.id.toString());
        loadDocuments(matchedCorpus.id);
      }
    }
  }, [preselectedCorpusName, corpora]);

  // Auto-fill document name and auto-retrieve when document is pre-selected
  useEffect(() => {
    if (preselectedDocumentName && documents.length > 0) {
      // Find matching document in the list
      const matchedDoc = documents.find(
        d => d.display_name === preselectedDocumentName
      );
      if (matchedDoc) {
        setDocumentName(matchedDoc.display_name);
        // Auto-retrieve the document with signed URL generation enabled
        retrieveDocument(parseInt(corpusId), matchedDoc.display_name, true);
      } else {
        // If not found in list, still set the name for manual retrieval
        setDocumentName(preselectedDocumentName);
      }
    }
  }, [preselectedDocumentName, documents, corpusId]);

  useEffect(() => {
    if (corpusId) {
      loadDocuments(parseInt(corpusId));
    }
  }, [corpusId]);

  const loadCorpora = async () => {
    try {
      setLoadingCorpora(true);
      const data = await apiClient.getAllCorporaWithAccess();
      setCorpora(data);
    } catch (err) {
      console.error('Failed to load corpora:', err);
    } finally {
      setLoadingCorpora(false);
    }
  };

  const loadDocuments = async (selectedCorpusId: number) => {
    try {
      setLoadingDocuments(true);
      setDocuments([]);
      const data = await apiClient.listCorpusDocuments(selectedCorpusId);
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Failed to load documents:', err);
      setDocuments([]);
    } finally {
      setLoadingDocuments(false);
    }
  };

  const handleRetrieve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!documentName.trim() || !corpusId) return;

    try {
      await retrieveDocument(parseInt(corpusId), documentName, true);
    } catch (err) {
      console.error('Failed to retrieve document:', err);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Document Retrieval Test</h2>
      
      <form onSubmit={handleRetrieve} className="space-y-4">
        <div>
          <label htmlFor="corpusId" className="block text-sm font-medium text-gray-700 mb-2">
            Corpus
          </label>
          <select
            id="corpusId"
            value={corpusId}
            onChange={(e) => setCorpusId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
            disabled={loadingCorpora}
          >
            <option value="">Select a corpus...</option>
            {corpora.map((corpus) => (
              <option key={corpus.id} value={corpus.id}>
                {corpus.display_name || corpus.name}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            {loadingCorpora ? 'Loading corpora...' : 'Select the corpus containing the document'}
          </p>
        </div>

        <div>
          <label htmlFor="documentName" className="block text-sm font-medium text-gray-700 mb-2">
            Document Name
          </label>
          <input
            type="text"
            id="documentName"
            value={documentName}
            onChange={(e) => setDocumentName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Hands-On Large Language Models.pdf"
            required
          />
          <p className="mt-1 text-xs text-gray-500">Enter the exact document name including extension</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-600">
              <strong>Error:</strong> {error}
            </p>
          </div>
        )}

        <button
          type="submit"
          disabled={isRetrieving || !documentName.trim()}
          className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRetrieving ? 'Retrieving...' : 'Retrieve Document'}
        </button>
      </form>

      {/* Document List */}
      {corpusId && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Documents in Corpus</h3>
          {loadingDocuments ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-sm text-gray-600">Loading documents...</p>
            </div>
          ) : documents.length > 0 ? (
            <div className="border border-gray-200 rounded-md overflow-hidden">
              <div className="max-h-96 overflow-y-auto">
                {documents.map((doc) => (
                  <button
                    key={doc.file_id}
                    onClick={() => {
                      setDocumentName(doc.display_name);
                      retrieveDocument(parseInt(corpusId), doc.display_name, true);
                    }}
                    disabled={isRetrieving}
                    className="w-full text-left px-4 py-3 hover:bg-blue-50 border-b border-gray-100 last:border-b-0 transition-colors flex items-center justify-between group disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 group-hover:text-blue-600">{doc.display_name}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {doc.file_type.toUpperCase()} • {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Unknown date'}
                      </p>
                    </div>
                    <svg className="w-5 h-5 text-gray-400 group-hover:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-center py-8 text-gray-500">No documents found in this corpus</p>
          )}
        </div>
      )}

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">How to use:</h3>
        <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
          <li>Select the corpus from the dropdown to see available documents</li>
          <li>Click on any document from the list to instantly preview/download it</li>
          <li>Or type the document name manually and click &quot;Retrieve Document&quot;</li>
          <li>PDF files will preview in-browser, others will show download option</li>
        </ol>
      </div>

      {currentDocument && (
        <DocumentViewer
          document={currentDocument}
          onClose={closeDocument}
        />
      )}
    </div>
  );
}
