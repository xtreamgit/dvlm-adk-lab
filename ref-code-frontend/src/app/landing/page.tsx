"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'motion/react';
import { apiClient } from '../../lib/api-enhanced';
import { FadeIn, FadeInView, StaggerChildren, StaggerItem, HoverCard, AnimatedCounter, PageTransition } from '@/components/motion/AnimatedComponents';

export default function LandingPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  // Check if already authenticated via IAP
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const iapUser = await apiClient.checkIapAuth();
        if (iapUser) {
          console.log('✅ IAP authenticated:', iapUser.email);
          router.push('/');
          return;
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAuth();
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-green-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className="text-center"
        >
          <div className="w-12 h-12 mx-auto mb-4 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: '#005440', borderTopColor: 'transparent' }} />
          <div className="text-gray-500 text-sm">Loading...</div>
        </motion.div>
      </div>
    );
  }

  return (
    <PageTransition className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-emerald-50/30 relative overflow-hidden">
      {/* Subtle animated background blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute -top-40 -right-40 w-96 h-96 rounded-full opacity-[0.07]"
          style={{ background: 'radial-gradient(circle, #005440 0%, transparent 70%)' }}
          animate={{ x: [0, 30, 0], y: [0, -20, 0] }}
          transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute top-1/2 -left-32 w-80 h-80 rounded-full opacity-[0.05]"
          style={{ background: 'radial-gradient(circle, #005440 0%, transparent 70%)' }}
          animate={{ x: [0, -20, 0], y: [0, 30, 0] }}
          transition={{ duration: 25, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute -bottom-20 right-1/3 w-72 h-72 rounded-full opacity-[0.04]"
          style={{ background: 'radial-gradient(circle, #005440 0%, transparent 70%)' }}
          animate={{ x: [0, 25, 0], y: [0, -15, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      {/* Navigation */}
      <FadeIn direction="down" duration={0.4}>
        <nav className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-50 border-b border-gray-100">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-2">
                <motion.svg
                  className="w-8 h-8"
                  style={{ color: '#005440' }}
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  whileHover={{ rotate: 15, scale: 1.1 }}
                  transition={{ type: 'spring', stiffness: 300 }}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </motion.svg>
                <span className="text-xl font-bold text-gray-900">ADK RAG Assistant</span>
              </div>
              <span className="text-sm text-gray-500">Sign in via your organization account</span>
            </div>
          </div>
        </nav>
      </FadeIn>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 relative">
        <div className="text-center">
          <FadeIn direction="up" delay={0.1} duration={0.6}>
            <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 mb-6 tracking-tight">
              Multi-Corpus{' '}
              <span className="relative">
                <span style={{ color: '#005440' }}>RAG Assistant</span>
                <motion.span
                  className="absolute -bottom-1 left-0 h-1 rounded-full"
                  style={{ backgroundColor: '#005440' }}
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 0.8, delay: 0.8, ease: 'easeOut' }}
                />
              </span>
            </h1>
          </FadeIn>
          <FadeIn direction="up" delay={0.3} duration={0.6}>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Query multiple knowledge bases simultaneously with AI-powered intelligence.
              Secure, enterprise-grade retrieval augmented generation for your organization.
            </p>
          </FadeIn>
          <FadeIn direction="up" delay={0.5} duration={0.6}>
            <p className="text-gray-400 text-sm">
              Access is managed through Google IAP. If you are not automatically signed in,
              please contact your administrator.
            </p>
          </FadeIn>
        </div>

        {/* Features Grid */}
        <StaggerChildren staggerDelay={0.12} className="mt-24 grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />,
              iconBg: '#f0f9f6',
              iconColor: '#005440',
              title: 'Multi-Corpus Access',
              desc: 'Query across multiple knowledge bases including AI Books, Design Docs, and Management Resources simultaneously.',
            },
            {
              icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />,
              iconBg: '#f0fdf4',
              iconColor: '#16a34a',
              title: 'Parallel Execution',
              desc: 'Multi-agent architecture executes queries in parallel for faster, more comprehensive results.',
            },
            {
              icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />,
              iconBg: '#f0f9f6',
              iconColor: '#005440',
              title: 'Secure Access Control',
              desc: 'Organization-restricted access with OAuth authentication and granular corpus-level permissions.',
            },
            {
              icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />,
              iconBg: '#fff7ed',
              iconColor: '#ea580c',
              title: 'Conversation History',
              desc: 'Persistent chat history and session management. Pick up where you left off across devices.',
            },
          ].map((feature) => (
            <StaggerItem key={feature.title}>
              <HoverCard className="bg-white/80 backdrop-blur-sm p-6 rounded-2xl shadow-sm border border-gray-100 h-full cursor-default">
                <motion.div
                  className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                  style={{ backgroundColor: feature.iconBg }}
                  whileHover={{ rotate: 5, scale: 1.1 }}
                  transition={{ type: 'spring', stiffness: 300 }}
                >
                  <svg className="w-6 h-6" style={{ color: feature.iconColor }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {feature.icon}
                  </svg>
                </motion.div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{feature.desc}</p>
              </HoverCard>
            </StaggerItem>
          ))}
        </StaggerChildren>

        {/* Key Benefits Section */}
        <FadeInView direction="up" delay={0.1}>
          <div className="mt-24 bg-white/80 backdrop-blur-sm rounded-2xl shadow-sm border border-gray-100 p-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
              Built for Enterprise Knowledge Workers
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              {[
                { value: 4, suffix: '+', label: 'Knowledge Bases' },
                { text: 'Multi-Agent', label: 'Architecture' },
                { text: 'Secure', label: 'OAuth Protected' },
              ].map((stat, i) => (
                <motion.div
                  key={stat.label}
                  className="text-center"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: i * 0.15 }}
                >
                  <div className="text-4xl font-bold mb-2" style={{ color: '#005440' }}>
                    {stat.value !== undefined ? (
                      <><AnimatedCounter value={stat.value} style={{ color: '#005440' }} />{stat.suffix}</>
                    ) : (
                      stat.text
                    )}
                  </div>
                  <div className="text-gray-500">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </FadeInView>

        {/* CTA Section */}
        <FadeInView direction="up" delay={0.1}>
          <div className="mt-24 text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Ready to get started?
            </h2>
            <p className="text-xl text-gray-500 mb-8">
              Sign in with your organization account to access all features.
            </p>
            <motion.button
              onClick={() => router.push('/')}
              className="px-8 py-3.5 text-lg font-medium text-white rounded-xl shadow-lg hover:shadow-xl transition-shadow"
              style={{ backgroundColor: '#005440' }}
              whileHover={{ scale: 1.05, boxShadow: '0 20px 40px rgba(0,84,64,0.25)' }}
              whileTap={{ scale: 0.97 }}
            >
              Go to Chatbot
            </motion.button>
            <p className="text-gray-400 mt-4 text-sm">
              Authentication is handled automatically via Google IAP when accessing through your organization URL.
            </p>
          </div>
        </FadeInView>
      </div>

      {/* Footer */}
      <footer className="bg-white/80 backdrop-blur-sm border-t border-gray-100 mt-24 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center text-sm text-gray-400">
            <div> 2026 ADK Multi-Agent RAG. All rights reserved.</div>
            <div className="flex space-x-6">
              <a href="#" className="hover:text-gray-600 transition-colors">Documentation</a>
              <a href="#" className="hover:text-gray-600 transition-colors">Support</a>
              <a href="#" className="hover:text-gray-600 transition-colors">Privacy</a>
            </div>
          </div>
        </div>
      </footer>
    </PageTransition>
  );
}
