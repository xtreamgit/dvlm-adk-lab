"use client";

interface Document {
  file_id: string;
  display_name: string;
  file_type: string;
  created_at?: string;
  size_bytes?: number;
}

interface DocumentPreviewProps {
  document: Document | null;
  thumbnailUrl: string | null;
  generatingThumbnail: boolean;
  onOpenDocument: () => void;
  onDownload: () => void;
}

export default function DocumentPreview({
  document,
  thumbnailUrl,
  generatingThumbnail,
  onOpenDocument,
  onDownload
}: DocumentPreviewProps) {
  if (!document) {
    return (
      <div className="w-96 bg-white border-l border-gray-200 flex items-center justify-center">
        <div className="text-center p-8">
          <svg className="mx-auto h-16 w-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="mt-4 text-sm text-gray-500">
            Select a document to preview
          </p>
        </div>
      </div>
    );
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'numeric',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return 'Unknown';
    }
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  const formatTimestamp = (dateString?: string) => {
    if (!dateString) return '';
    try {
      return new Date(dateString).toLocaleString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return '';
    }
  };

  return (
    <div className="w-96 bg-white border-l border-gray-200 flex flex-col h-full">
      {/* Document Preview Area */}
      <div className="flex-1 p-6 flex flex-col">
        {/* Thumbnail */}
        <div className="mb-6 bg-emerald-900 rounded-lg p-4 flex items-center justify-center" style={{ minHeight: '320px' }}>
          {generatingThumbnail ? (
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white mb-2"></div>
              <p className="text-sm text-white">Generating preview...</p>
            </div>
          ) : thumbnailUrl ? (
            <img 
              src={thumbnailUrl} 
              alt={document.display_name}
              className="max-w-full max-h-full object-contain rounded"
            />
          ) : (
            <div className="text-center">
              <svg className="mx-auto h-16 w-16 text-white opacity-50" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
              </svg>
              <p className="mt-2 text-sm text-white opacity-75">No preview available</p>
            </div>
          )}
        </div>

        {/* Document Title */}
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          {document.display_name}
        </h3>

        {/* Metadata */}
        <div className="space-y-2 mb-6">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Type:</span>
            <span className="text-gray-900 font-medium">{document.file_type.toUpperCase()} Document</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Size:</span>
            <span className="text-gray-900 font-medium">{formatSize(document.size_bytes)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Date:</span>
            <span className="text-gray-900 font-medium">{formatDate(document.created_at)}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={onOpenDocument}
            className="w-full py-3 px-4 bg-emerald-700 hover:bg-emerald-800 text-white font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
          >
            Open Document
          </button>
          <button
            onClick={onDownload}
            className="w-full py-3 px-4 bg-white border-2 border-gray-300 hover:border-gray-400 text-gray-700 font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
          >
            Download
          </button>
        </div>
      </div>

      {/* Footer Timestamp */}
      {document.created_at && (
        <div className="border-t border-gray-200 px-6 py-4 text-center">
          <p className="text-xs text-gray-500">
            {formatTimestamp(document.created_at)}
          </p>
        </div>
      )}
    </div>
  );
}
