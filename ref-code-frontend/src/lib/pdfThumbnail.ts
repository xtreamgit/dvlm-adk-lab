/**
 * PDF Thumbnail Generation Utility
 * Generates thumbnail images from PDF documents using pdf.js
 * 
 * NOTE: This module should only be used on the client side
 */

// Dynamic import to avoid SSR issues
let pdfjsLib: typeof import('pdfjs-dist') | null = null;
let pdfjsInitPromise: Promise<typeof import('pdfjs-dist')> | null = null;

// Initialize PDF.js only in browser environment
if (typeof window !== 'undefined') {
  pdfjsInitPromise = import('pdfjs-dist').then((pdfjs) => {
    pdfjsLib = pdfjs;
    // Use unpkg CDN as fallback (more reliable than cdnjs)
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
    console.log('[PDF.js] Worker initialized:', pdfjsLib.GlobalWorkerOptions.workerSrc);
    return pdfjs;
  });
}

/**
 * Ensure PDF.js is fully initialized before use
 */
async function ensurePdfjsLoaded(): Promise<typeof import('pdfjs-dist')> {
  if (pdfjsLib) {
    return pdfjsLib;
  }
  
  if (pdfjsInitPromise) {
    console.log('[PDF.js] Waiting for initialization...');
    return await pdfjsInitPromise;
  }
  
  // Fallback: initialize now if not already started
  console.log('[PDF.js] Initializing on-demand...');
  const pdfjs = await import('pdfjs-dist');
  pdfjsLib = pdfjs;
  pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
  return pdfjs;
}

interface ThumbnailOptions {
  maxWidth?: number;
  maxHeight?: number;
  scale?: number;
  headers?: Record<string, string>;
}

/**
 * Generate a thumbnail from a PDF URL
 * @param url - The URL of the PDF document
 * @param options - Thumbnail generation options
 * @returns Promise resolving to a base64 data URL of the thumbnail image
 */
export async function generatePdfThumbnail(
  url: string,
  options: ThumbnailOptions = {}
): Promise<string> {
  // Ensure we're in browser environment
  if (typeof window === 'undefined') {
    throw new Error('generatePdfThumbnail can only be called in browser environment');
  }

  // Ensure pdfjs is fully loaded (fixes race condition)
  const pdfjs = await ensurePdfjsLoaded();

  const {
    maxWidth = 280,
    maxHeight = 380,
    scale = 1.5
  } = options;

  try {
    console.log('[PDF Thumbnail] Loading PDF from URL:', url.substring(0, 100) + '...');
    
    // Determine if this is a proxy URL that requires authentication
    const isProxyUrl = url.includes('/api/documents/proxy/');
    
    // For proxy URLs, fetch the PDF first with IAP auth (credentials: 'include')
    // then pass it to PDF.js as binary data to avoid CORS/auth issues
    let pdfData: string | ArrayBuffer | Uint8Array = url;
    
    if (isProxyUrl || options.headers) {
      console.log('[PDF Thumbnail] Fetching PDF with authentication...');
      console.log('[PDF Thumbnail] URL:', url);
      
      const response = await fetch(url, {
        headers: options.headers,
        credentials: 'include',
      });
      
      console.log('[PDF Thumbnail] Response status:', response.status, response.statusText);
      console.log('[PDF Thumbnail] Response headers:', {
        'content-type': response.headers.get('content-type'),
        'content-length': response.headers.get('content-length'),
      });
      
      if (!response.ok) {
        // Try to get error message from JSON response
        let errorMessage = `${response.status} ${response.statusText}`;
        try {
          const errorData = await response.json();
          console.error('[PDF Thumbnail] Error response:', errorData);
          errorMessage = errorData.detail || errorMessage;
        } catch {
          // Not JSON, use status text
        }
        throw new Error(`Failed to fetch PDF: ${errorMessage}`);
      }
      
      // Check content type
      const contentType = response.headers.get('content-type');
      if (contentType && !contentType.includes('application/pdf')) {
        console.error('[PDF Thumbnail] Unexpected content type:', contentType);
        throw new Error(`Expected PDF but got ${contentType}`);
      }
      
      const arrayBuffer = await response.arrayBuffer();
      pdfData = new Uint8Array(arrayBuffer);
      
      // Log first few bytes to verify it's a PDF
      const firstBytes = Array.from(pdfData.slice(0, 10)).map(b => String.fromCharCode(b)).join('');
      console.log('[PDF Thumbnail] First 10 bytes:', firstBytes);
      console.log('[PDF Thumbnail] Starts with %PDF:', firstBytes.startsWith('%PDF'));
      console.log('[PDF Thumbnail] PDF fetched successfully, size:', arrayBuffer.byteLength, 'bytes');
    }
    
    // Load the PDF document with timeout
    // Use correct property: 'data' for binary, 'url' for URL strings
    const loadingTask = typeof pdfData === 'string'
      ? pdfjs.getDocument({
          url: pdfData,
          isEvalSupported: false,
          verbosity: 0,
        })
      : pdfjs.getDocument({
          data: pdfData,
          isEvalSupported: false,
          verbosity: 0,
        });
    
    // Add timeout for loading (30 seconds)
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error('PDF loading timeout (30s)')), 30000);
    });
    
    const pdf = await Promise.race([loadingTask.promise, timeoutPromise]);
    console.log('[PDF Thumbnail] PDF loaded successfully, pages:', pdf.numPages);

    // Get the first page
    const page = await pdf.getPage(1);
    console.log('[PDF Thumbnail] First page retrieved');

    // Calculate viewport
    const viewport = page.getViewport({ scale });

    // Create canvas
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    if (!context) {
      throw new Error('Could not get canvas context');
    }

    // Calculate dimensions to fit within max bounds while preserving aspect ratio
    let width = viewport.width;
    let height = viewport.height;

    if (width > maxWidth) {
      height = (height * maxWidth) / width;
      width = maxWidth;
    }

    if (height > maxHeight) {
      width = (width * maxHeight) / height;
      height = maxHeight;
    }

    canvas.width = width;
    canvas.height = height;

    // Render PDF page to canvas
    const renderViewport = page.getViewport({ scale: width / viewport.width });
    const renderContext = {
      canvasContext: context,
      viewport: renderViewport,
      canvas: canvas
    };

    await page.render(renderContext).promise;

    // Convert canvas to data URL
    const dataUrl = canvas.toDataURL('image/png', 0.8);

    // Cleanup
    pdf.destroy();

    return dataUrl;
  } catch (error) {
    console.error('[PDF Thumbnail] Error generating PDF thumbnail:', error);
    console.error('[PDF Thumbnail] Error type:', error instanceof Error ? error.constructor.name : typeof error);
    console.error('[PDF Thumbnail] Error message:', error instanceof Error ? error.message : String(error));
    console.error('[PDF Thumbnail] Error stack:', error instanceof Error ? error.stack : 'No stack trace');
    
    // Re-throw with more context
    if (error instanceof Error) {
      // Check for specific error types
      if (error.message.includes('timeout')) {
        throw new Error('PDF loading timed out. The file may be too large or network is slow.');
      } else if (error.message.includes('fetch')) {
        throw new Error('Failed to fetch PDF. Please check your network connection.');
      } else if (error.message.includes('CORS')) {
        throw new Error('CORS error loading PDF. The file may not be accessible.');
      }
      throw new Error(`Failed to generate PDF thumbnail: ${error.message}`);
    }
    throw new Error('Failed to generate PDF thumbnail: Unknown error');
  }
}

/**
 * Generate thumbnail with retry logic for transient failures
 */
export async function generatePdfThumbnailWithRetry(
  url: string,
  options: ThumbnailOptions = {},
  maxRetries: number = 2
): Promise<string> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        console.log(`[PDF Thumbnail] Retry attempt ${attempt}/${maxRetries}`);
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
      
      return await generatePdfThumbnail(url, options);
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      // Don't retry on certain errors
      if (lastError.message.includes('CORS') || 
          lastError.message.includes('not accessible') ||
          lastError.message.includes('browser environment')) {
        throw lastError;
      }
      
      // Continue to next retry
      if (attempt < maxRetries) {
        console.warn(`[PDF Thumbnail] Attempt ${attempt + 1} failed, retrying...`);
      }
    }
  }
  
  throw lastError || new Error('Failed to generate thumbnail after retries');
}

/**
 * Generate thumbnail with caching
 */
export class ThumbnailCache {
  private cache: Map<string, string> = new Map();

  async getThumbnail(url: string, options?: ThumbnailOptions): Promise<string> {
    const cacheKey = `${url}-${JSON.stringify(options)}`;
    
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }

    const thumbnail = await generatePdfThumbnail(url, options);
    this.cache.set(cacheKey, thumbnail);
    
    return thumbnail;
  }

  clear(): void {
    this.cache.clear();
  }

  remove(url: string): void {
    // Remove all entries for this URL regardless of options
    const keysToDelete: string[] = [];
    this.cache.forEach((_, key) => {
      if (key.startsWith(url)) {
        keysToDelete.push(key);
      }
    });
    keysToDelete.forEach(key => this.cache.delete(key));
  }
}
