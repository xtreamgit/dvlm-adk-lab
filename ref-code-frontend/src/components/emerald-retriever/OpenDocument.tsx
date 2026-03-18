"use client";

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-enhanced';
import { useDocumentRetrieval } from '@/hooks/useDocumentRetrieval';
import { generatePdfThumbnail } from '@/lib/pdfThumbnail';
import CorpusSidebar from './CorpusSidebar';
import DocumentListPanel from './DocumentListPanel';
import DocumentPreview from './DocumentPreview';
import DocumentViewer from '../DocumentViewer';

interface Corpus {
  id: number;
  name: string;
  display_name: string;
  has_access?: boolean;
}

interface Document {
  file_id: string;
  display_name: string;
  file_type: string;
  created_at?: string;
  size_bytes?: number;
}

export default function EmeraldRetriever() {
  // State for corpora
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [loadingCorpora, setLoadingCorpora] = useState(true);
  const [selectedCorpusId, setSelectedCorpusId] = useState<number | null>(null);
  
  // State for documents
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  
  // State for thumbnail
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);
  const [generatingThumbnail, setGeneratingThumbnail] = useState(false);
  
  // Document retrieval hook
  const { retrieveDocument, closeDocument, currentDocument } = useDocumentRetrieval();

  // Load corpora on mount
  useEffect(() => {
    loadCorpora();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load documents when corpus changes
  useEffect(() => {
    if (selectedCorpusId) {
      loadDocuments(selectedCorpusId);
    }
  }, [selectedCorpusId]);

  // Generate thumbnail when document is selected (DISABLED FOR NOW)
  useEffect(() => {
    // Thumbnail generation disabled - just clear the thumbnail
    setThumbnailUrl(null);
    setGeneratingThumbnail(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDocument]);

  const loadCorpora = async () => {
    try {
      setLoadingCorpora(true);
      const data = await apiClient.getAllCorporaWithAccess();
      setCorpora(data);
      
      // Auto-select first accessible corpus
      if (data.length > 0 && !selectedCorpusId) {
        const firstAccessible = data.find((c: Corpus) => c.has_access !== false);
        if (firstAccessible) {
          setSelectedCorpusId(firstAccessible.id);
        }
      }
    } catch (error) {
      console.error('Failed to load corpora:', error);
    } finally {
      setLoadingCorpora(false);
    }
  };

  const loadDocuments = async (corpusId: number) => {
    try {
      setLoadingDocuments(true);
      setDocuments([]);
      setSelectedDocument(null);
      
      const response = await apiClient.listCorpusDocuments(corpusId);
      const docs = response.documents || [];
      setDocuments(docs);

      // Auto-select first document by default
      if (docs.length > 0) {
        setSelectedDocument(docs[0]);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
      setDocuments([]);
    } finally {
      setLoadingDocuments(false);
    }
  };

  const generateThumbnail = async (document: Document) => {
    // Only generate thumbnails for PDFs
    if (document.file_type.toLowerCase() !== 'pdf') {
      console.log('Document is not a PDF, skipping thumbnail generation');
      setThumbnailUrl(null);
      setGeneratingThumbnail(false);
      return;
    }

    try {
      setGeneratingThumbnail(true);
      setThumbnailUrl(null);

      console.log('Retrieving document for thumbnail:', document.display_name);
      
      // Retrieve document with signed URL
      const response = await retrieveDocument(
        selectedCorpusId!,
        document.display_name,
        true
      );

      console.log('Document retrieval response:', response);

      if (response.access?.url) {
        console.log('Generating thumbnail from URL:', response.access.url);
        // Generate thumbnail from signed URL
        const thumbnail = await generatePdfThumbnail(response.access.url, {
          maxWidth: 260,
          maxHeight: 360
        });
        console.log('Thumbnail generated successfully');
        setThumbnailUrl(thumbnail);
      } else {
        console.error('No URL in response:', response);
      }
    } catch (error) {
      console.error('Failed to generate thumbnail:', error);
      console.error('Error details:', error instanceof Error ? error.message : error);
      setThumbnailUrl(null);
    } finally {
      setGeneratingThumbnail(false);
    }
  };

  const handleSelectCorpus = (corpusId: number) => {
    const corpus = corpora.find(c => c.id === corpusId);
    if (corpus && corpus.has_access === false) return;
    setSelectedCorpusId(corpusId);
    setSelectedDocument(null);
  };

  const handleSelectDocument = (document: Document) => {
    setSelectedDocument(document);
  };

  const handleOpenDocumentFromList = async (document: Document) => {
    if (!selectedCorpusId) return;
    setSelectedDocument(document);

    try {
      await retrieveDocument(
        selectedCorpusId,
        document.display_name,
        true
      );
    } catch (error) {
      console.error('Failed to open document:', error);
    }
  };

  const handleOpenDocument = async () => {
    if (!selectedDocument || !selectedCorpusId) return;

    try {
      await retrieveDocument(
        selectedCorpusId,
        selectedDocument.display_name,
        true
      );
    } catch (error) {
      console.error('Failed to open document:', error);
    }
  };

  const handleDownload = async () => {
    if (!selectedDocument || !selectedCorpusId) return;

    try {
      const response = await retrieveDocument(
        selectedCorpusId,
        selectedDocument.display_name,
        true
      );

      if (response.access?.url) {
        // Trigger download
        const link = document.createElement('a');
        link.href = response.access.url;
        link.download = selectedDocument.display_name;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (error) {
      console.error('Failed to download document:', error);
    }
  };

  const selectedCorpusName = corpora.find(c => c.id === selectedCorpusId)?.display_name || 
                            corpora.find(c => c.id === selectedCorpusId)?.name || 
                            'Unknown';

  return (
    <>
      <div className="h-screen flex flex-col bg-white">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm">
          <h1 className="text-xl font-bold text-gray-900">Document Browser</h1>
        </div>

        {/* Three-column layout */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Corpus Sidebar */}
          <CorpusSidebar
            corpora={corpora}
            selectedCorpusId={selectedCorpusId}
            onSelectCorpus={handleSelectCorpus}
            loading={loadingCorpora}
          />

          {/* Middle: Document List */}
          <DocumentListPanel
            corpusName={selectedCorpusName}
            documents={documents}
            selectedDocumentId={selectedDocument?.file_id || null}
            onSelectDocument={handleSelectDocument}
            onOpenDocument={handleOpenDocumentFromList}
            loading={loadingDocuments}
          />

          {/* Right: Document Preview */}
          <DocumentPreview
            document={selectedDocument}
            thumbnailUrl={thumbnailUrl}
            generatingThumbnail={generatingThumbnail}
            onOpenDocument={handleOpenDocument}
            onDownload={handleDownload}
          />
        </div>
      </div>

      {/* Document Viewer Modal */}
      {currentDocument && (
        <DocumentViewer
          document={currentDocument}
          onClose={closeDocument}
        />
      )}
    </>
  );
}
