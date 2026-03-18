"use client";

import { useState, useEffect } from 'react';
import { apiClient, Corpus } from '../lib/api-enhanced';

interface CorpusSelectorProps {
  selectedCorpora: string[];
  onCorporaChange: (corpora: string[]) => void;
}

export default function CorpusSelector({ selectedCorpora, onCorporaChange }: CorpusSelectorProps) {
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCorpora = async () => {
      try {
        setLoading(true);
        const response = await apiClient.getAllCorporaWithAccess();
        
        // Deduplicate by ID (backend may return duplicates)
        const uniqueCorpora = response.reduce((acc, corpus) => {
          if (!acc.find(c => c.id === corpus.id)) {
            acc.push(corpus);
          }
          return acc;
        }, [] as typeof response);
        
        // Sort corpora alphabetically by display name
        const sortedCorpora = uniqueCorpora.sort((a, b) => 
          a.display_name.toLowerCase().localeCompare(b.display_name.toLowerCase())
        );
        setCorpora(sortedCorpora);
      } catch (err) {
        console.error('Failed to load corpora:', err);
        setError(err instanceof Error ? err.message : 'Failed to load corpora');
      } finally {
        setLoading(false);
      }
    };

    loadCorpora();
  }, []);

  // No longer needed with new API - removed unused function

  if (loading) {
    return (
      <div className="w-full">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded mb-2"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full">
        <div className="text-red-600">
          <h3 className="text-sm font-medium mb-1">Error Loading Corpora</h3>
          <p className="text-xs">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-gray-900 mb-2">
          Available Corpora
        </h3>
      </div>

      <div className="space-y-2">
        {/* Multi-select corpus list */}
        <div className="space-y-1">
          {corpora.map((corpus) => {
            const isSelected = selectedCorpora.includes(corpus.name);
            return (
              <div
                key={corpus.id}
                onClick={() => {
                  // Only allow selection if user has access
                  if (!corpus.has_access) return;
                  
                  if (isSelected) {
                    onCorporaChange(selectedCorpora.filter(name => name !== corpus.name));
                  } else {
                    onCorporaChange([...selectedCorpora, corpus.name]);
                  }
                }}
                className={`
                  flex items-center p-3 rounded-lg border transition-all
                  ${
                    !corpus.has_access
                      ? 'bg-gray-50 border-gray-200 opacity-60 cursor-not-allowed'
                      : isSelected
                      ? 'bg-blue-50 border-blue-400 hover:bg-blue-100 cursor-pointer'
                      : 'bg-white border-gray-300 hover:bg-gray-50 cursor-pointer'
                  }
                `}
              >
                <div className="flex items-center flex-1">
                  <div
                    className={`
                      w-5 h-5 mr-3 border-2 rounded flex items-center justify-center
                      ${
                        !corpus.has_access
                          ? 'bg-gray-200 border-gray-300'
                          : isSelected
                          ? 'bg-blue-500 border-blue-500'
                          : 'bg-white border-gray-400'
                      }
                    `}
                  >
                    {!corpus.has_access ? (
                      <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                    ) : isSelected ? (
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : null}
                  </div>
                  <div className="flex-1">
                    <p className={`text-sm font-medium ${
                      !corpus.has_access
                        ? 'text-gray-500'
                        : isSelected ? 'text-blue-900' : 'text-gray-900'
                    }`}>
                      {corpus.display_name}
                      {corpus.document_count !== undefined && (
                        <span className={`ml-2 text-xs font-normal ${
                          !corpus.has_access
                            ? 'text-gray-400'
                            : isSelected ? 'text-blue-600' : 'text-gray-500'
                        }`}>
                          ({corpus.document_count})
                        </span>
                      )}
                      {!corpus.has_access && (
                        <span className="ml-2 text-xs font-normal text-gray-400">
                          (No Access)
                        </span>
                      )}
                    </p>
                    {corpus.description && (
                      <p className={`text-xs mt-0.5 ${
                        !corpus.has_access
                          ? 'text-gray-400'
                          : isSelected ? 'text-blue-600' : 'text-gray-500'
                      }`}>
                        {corpus.description}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {!loading && corpora.length === 0 && (
          <div className="p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-xs text-yellow-700">
              No corpora found. You may need to create one first.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
