"use client";

import { useState } from 'react';

interface WelcomeModalProps {
  onDismiss: () => void;
  userName: string;
}

export default function WelcomeModal({ onDismiss, userName }: WelcomeModalProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: `Welcome, ${userName}!`,
      content: "Let's take a quick tour of ADK RAG Assistant to help you get started.",
      icon: (
        <svg className="w-16 h-16 mx-auto" style={{ color: '#005440' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
        </svg>
      )
    },
    {
      title: "Query Multiple Knowledge Bases",
      content: "Select one or more corpora from the sidebar to query across different knowledge sources simultaneously. Currently available: AI Books, Design, Management, and Test Corpus.",
      icon: (
        <svg className="w-16 h-16 mx-auto" style={{ color: '#005440' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      )
    },
    {
      title: "Multi-Agent Architecture",
      content: "Your queries are processed by parallel agents that search across all selected corpora simultaneously for faster, more comprehensive results.",
      icon: (
        <svg className="w-16 h-16 mx-auto" style={{ color: '#005440' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      )
    },
    {
      title: "Your Conversations are Saved",
      content: "All your chat sessions are automatically saved and accessible across devices. You can continue conversations anytime from the sidebar history.",
      icon: (
        <svg className="w-16 h-16 mx-auto" style={{ color: '#005440' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      )
    }
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onDismiss();
    }
  };

  const handleSkip = () => {
    onDismiss();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-lg w-full p-8 relative">
        {/* Close button */}
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Content */}
        <div className="text-center">
          {steps[currentStep].icon}
          <h2 className="text-2xl font-bold text-gray-900 mt-4 mb-3">
            {steps[currentStep].title}
          </h2>
          <p className="text-gray-600 mb-8">
            {steps[currentStep].content}
          </p>

          {/* Progress dots */}
          <div className="flex justify-center space-x-2 mb-6">
            {steps.map((_, index) => (
              <div
                key={index}
                className={`h-2 w-2 rounded-full transition-colors`}
                style={index === currentStep ? { backgroundColor: '#005440' } : { backgroundColor: '#d1d5db' }}
              />
            ))}
          </div>

          {/* Actions */}
          <div className="flex justify-between items-center">
            <button
              onClick={handleSkip}
              className="text-gray-500 hover:text-gray-700"
            >
              Skip tour
            </button>
            <button
              onClick={handleNext}
              className="px-6 py-2 text-white rounded-lg transition-colors"
              style={{ backgroundColor: '#005440' }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#004030'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#005440'}
            >
              {currentStep < steps.length - 1 ? 'Next' : 'Get Started'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
