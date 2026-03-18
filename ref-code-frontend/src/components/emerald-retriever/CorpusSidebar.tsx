"use client";

import Image from 'next/image';

interface Corpus {
  id: number;
  name: string;
  display_name: string;
  has_access?: boolean;
}

interface CorpusSidebarProps {
  corpora: Corpus[];
  selectedCorpusId: number | null;
  onSelectCorpus: (corpusId: number) => void;
  loading: boolean;
}

export default function CorpusSidebar({ 
  corpora, 
  selectedCorpusId, 
  onSelectCorpus,
  loading 
}: CorpusSidebarProps) {
  return (
    <div className="w-60 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Logo Section */}
      <div className="p-4 flex justify-center border-b border-gray-200">
        <div className="w-16 h-16 relative">
          <Image
            src="/fs-logo.jpg"
            alt="USFS Logo"
            fill
            className="object-contain"
          />
        </div>
      </div>

      {/* Corpus List Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="text-sm font-semibold text-gray-700 tracking-wide">
          CORPUS
        </h2>
      </div>

      {/* Corpus List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-sm text-gray-500">Loading corpora...</div>
        ) : corpora.length === 0 ? (
          <div className="p-4 text-sm text-gray-500">No corpora available</div>
        ) : (
          <div className="py-2">
            {corpora.map((corpus) => {
              const isSelected = selectedCorpusId === corpus.id;
              const hasAccess = corpus.has_access !== false;
              return (
                <button
                  key={corpus.id}
                  onClick={() => hasAccess && onSelectCorpus(corpus.id)}
                  className={`
                    w-full px-4 py-3 text-left flex items-center gap-3 transition-colors
                    ${!hasAccess
                      ? 'opacity-50 cursor-not-allowed border-l-4 border-transparent'
                      : isSelected 
                        ? 'bg-emerald-50 text-emerald-900 border-l-4 border-emerald-700' 
                        : 'hover:bg-gray-50 text-gray-700 border-l-4 border-transparent'
                    }
                  `}
                  disabled={!hasAccess}
                  title={!hasAccess ? 'No access to this corpus' : undefined}
                >
                  {/* Folder or Lock Icon */}
                  {hasAccess ? (
                    <svg 
                      className={`w-5 h-5 flex-shrink-0 ${isSelected ? 'text-emerald-700' : 'text-gray-400'}`}
                      fill="currentColor" 
                      viewBox="0 0 20 20"
                    >
                      <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                    </svg>
                  ) : (
                    <svg
                      className="w-5 h-5 flex-shrink-0 text-gray-300"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                    </svg>
                  )}
                  
                  {/* Corpus Name */}
                  <span className={`text-sm font-medium ${
                    !hasAccess ? 'text-gray-400' : isSelected ? 'text-emerald-900' : 'text-gray-700'
                  }`}>
                    {corpus.display_name || corpus.name}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
