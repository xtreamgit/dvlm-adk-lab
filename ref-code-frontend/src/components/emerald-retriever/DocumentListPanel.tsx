"use client";

import { useState, useMemo } from 'react';

interface Document {
  file_id: string;
  display_name: string;
  file_type: string;
  created_at?: string;
  size_bytes?: number;
}

interface DocumentListPanelProps {
  corpusName: string;
  documents: Document[];
  selectedDocumentId: string | null;
  onSelectDocument: (document: Document) => void;
  onOpenDocument: (document: Document) => void;
  loading: boolean;
}

export default function DocumentListPanel({
  corpusName,
  documents,
  selectedDocumentId,
  onSelectDocument,
  onOpenDocument,
  loading
}: DocumentListPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // Real-time search filtering
  const filteredDocuments = useMemo(() => {
    if (!searchQuery.trim()) return documents;
    
    const query = searchQuery.toLowerCase();
    return documents.filter(doc => 
      doc.display_name.toLowerCase().includes(query)
    );
  }, [documents, searchQuery]);

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown date';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'numeric',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return 'Unknown date';
    }
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="flex-1 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header with Search */}
      <div className="border-b border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Documents in {corpusName}
        </h2>
        
        {/* Search Bar */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg 
              className="h-5 w-5 text-gray-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" 
              />
            </svg>
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={`Search in ${corpusName}...`}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-700"></div>
            <p className="mt-2 text-sm text-gray-600">Loading documents...</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="mt-2 text-sm text-gray-500">
              {searchQuery ? 'No documents found matching your search' : 'No documents found in this corpus'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredDocuments.map((doc) => {
              const isSelected = selectedDocumentId === doc.file_id;
              return (
                <button
                  key={doc.file_id}
                  onClick={() => onSelectDocument(doc)}
                  onDoubleClick={() => onOpenDocument(doc)}
                  className={`
                    w-full text-left p-4 rounded-lg border-2 transition-all
                    ${isSelected 
                      ? 'bg-emerald-50 border-emerald-700 shadow-sm' 
                      : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'
                    }
                  `}
                >
                  <div className="flex items-start gap-3">
                    {/* PDF Icon */}
                    <div className={`flex-shrink-0 ${isSelected ? 'text-emerald-700' : 'text-gray-400'}`}>
                      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    
                    {/* Document Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className={`font-medium text-sm mb-1 ${isSelected ? 'text-emerald-900' : 'text-gray-900'}`}>
                        {doc.display_name}
                      </h3>
                      <p className="text-xs text-gray-500">
                        {doc.file_type.toUpperCase()} • {formatDate(doc.created_at)} • {formatSize(doc.size_bytes)}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
