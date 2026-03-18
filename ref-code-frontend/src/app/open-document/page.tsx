"use client";

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-enhanced';

// Dynamically import EmeraldRetriever with no SSR to avoid pdfjs-dist issues
const EmeraldRetriever = dynamic(
  () => import('@/components/emerald-retriever/EmeraldRetriever'),
  { ssr: false }
);

export default function OpenDocumentPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = await apiClient.checkIapAuth();
        if (user) {
          setAuthChecked(true);
        } else {
          router.push('/landing');
        }
      } catch {
        router.push('/landing');
      }
    };

    if (mounted) {
      checkAuth();
    }
  }, [mounted, router]);

  if (!mounted || !authChecked) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-700 mb-2"></div>
          <p className="text-sm text-gray-600">Loading Document Browser...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Back to App Link */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <button
          onClick={() => router.push('/')}
          className="flex items-center gap-3 text-gray-700 hover:text-gray-900 transition-colors"
        >
          <span className="text-2xl">←</span>
          <span className="text-lg font-normal">Back to App</span>
        </button>
      </div>
      
      <EmeraldRetriever />
    </div>
  );
}
