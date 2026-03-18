"use client";

import { useState, useRef, useEffect } from 'react';
import { Message, apiClient } from '../lib/api-enhanced';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Image from 'next/image';
import DocumentViewer from './DocumentViewer';
import { useDocumentRetrieval } from '../hooks/useDocumentRetrieval';

// UserProfile type for legacy compatibility
type UserProfile = {
  name: string;
  preferences?: string;
};

type User = {
  full_name: string;
};

type Agent = {
  display_name: string;
};

interface ChatInterfaceProps {
  userProfile: UserProfile;
  onUpdateProfile: () => void;
  inputValue?: string;
  onInputChange?: (value: string) => void;
  selectedCorpora?: string[];
  initialMessage?: string;
  shouldAutoSubmitInitial?: boolean;
  onNewChat?: () => void;
  sessionId?: string | null;
  isReturningToSession?: boolean;
  user?: User | null;
  currentAgent?: Agent | null;
}

export default function ChatInterface({ userProfile, onUpdateProfile, inputValue = '', onInputChange, selectedCorpora = [], initialMessage, shouldAutoSubmitInitial = false, onNewChat, sessionId, isReturningToSession = false, user, currentAgent }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [localInputValue, setLocalInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasProcessedInitialMessage, setHasProcessedInitialMessage] = useState(false);
  const [hasLoadedHistory, setHasLoadedHistory] = useState(false);
  const { retrieveDocument, closeDocument, currentDocument, isRetrieving } = useDocumentRetrieval();

  // Use controlled input if provided, otherwise use local state
  const currentInputValue = onInputChange ? inputValue : localInputValue;
  const handleInputChange = onInputChange || setLocalInputValue;
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat history on component mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await apiClient.getChatHistory();
        const formattedMessages: Message[] = [];
        
        history.forEach((item) => {
          formattedMessages.push({
            text: item.content,
            sender: item.role === 'user' ? 'user' : 'agent',
            timestamp: new Date(item.timestamp),
          });
        });
        
        setMessages(formattedMessages);
      } catch (err) {
        console.error('Failed to load chat history:', err);
      }
    };

    // Load history if we have a session ID and haven't loaded it yet
    if (sessionId && !hasLoadedHistory) {
      setHasLoadedHistory(true);
      loadHistory();
    }
  }, [sessionId, hasLoadedHistory]);

  // Set initial message in input field if provided and auto-submit only when explicitly requested
  useEffect(() => {
    if (initialMessage && initialMessage.trim() && !hasProcessedInitialMessage) {
      setHasProcessedInitialMessage(true);
      if (onInputChange) {
        onInputChange(initialMessage);
      } else {
        setLocalInputValue(initialMessage);
      }
      
      // Only auto-submit if explicitly requested
      if (shouldAutoSubmitInitial) {
        setTimeout(() => {
          const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
          const form = document.querySelector('form');
          if (form) {
            form.dispatchEvent(submitEvent);
          }
        }, 100);
      }
    }
  }, [initialMessage, hasProcessedInitialMessage, onInputChange, shouldAutoSubmitInitial]);

  const noCorporaSelected = !selectedCorpora || selectedCorpora.length === 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentInputValue.trim() || isLoading) return;

    // Require at least one corpus to be selected
    if (noCorporaSelected) {
      setError('Please select at least one corpus before sending a message.');
      return;
    }

    const userMessage: Message = { 
      text: currentInputValue, 
      sender: 'user',
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    handleInputChange('');
    setIsLoading(true);
    setError(null);

    try {
      // Send the message with selected corpora
      const agentMessage = await apiClient.sendMessage(userMessage.text, userProfile, selectedCorpora);
      setMessages(prev => [...prev, agentMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
      setError(errorMessage);
      setMessages(prev => [...prev, { 
        text: `Error: ${errorMessage}`, 
        sender: 'agent',
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = async (action: string) => {
    handleInputChange(action);
    // Trigger form submission
    const event = new Event('submit', { bubbles: true, cancelable: true });
    document.querySelector('form')?.dispatchEvent(event);
  };

  const handleNewChatClick = () => {
    // Clear messages and reset session
    setMessages([]);
    setError(null);
    setHasProcessedInitialMessage(false);
    apiClient.resetSession();
    
    // Call parent's new chat handler
    if (onNewChat) {
      onNewChat();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 p-4 flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900"><strong>USFS Retrieval Augmented Generation (RAG)</strong></h2>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">Hello, {user?.full_name || 'Guest'}!</span>
          {selectedCorpora.length > 0 && (
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              Corpus: {selectedCorpora.join(', ')}
            </span>
          )}
          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
            Agent: {currentAgent?.display_name || 'default'}
          </span>
        </div>
      </header>


      {/* Messages */}
      <main className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div 
              className={`rounded-lg px-4 py-3 max-w-3xl ${
                msg.sender === 'user'
                  ? 'text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
              }`}
              style={msg.sender === 'user' ? { backgroundColor: '#005440' } : undefined}
            >
              {msg.sender === 'user' ? (
                <div>
                  <p>{msg.text}</p>
                  {msg.timestamp && (
                    <p className="text-xs text-gray-300 mt-1">
                      {msg.timestamp.toLocaleTimeString()}
                    </p>
                  )}
                </div>
              ) : (
                <div>
                  <ReactMarkdown 
                    className="prose prose-sm dark:prose-invert max-w-none"
                    remarkPlugins={[remarkGfm]}
                    components={{
                      a: ({ node, ...props }) => (
                        <a
                          {...props}
                          style={{ 
                            color: '#005440', 
                            fontWeight: 'bold',
                            textDecoration: 'underline'
                          }}
                          target="_blank"
                          rel="noopener noreferrer"
                        />
                      ),
                    }}>
                    {msg.text}
                  </ReactMarkdown>
                  {msg.timestamp && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      {msg.timestamp.toLocaleTimeString()}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-lg px-4 py-3 max-w-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        {error && (
          <div className="flex justify-start">
            <div className="rounded-lg px-4 py-3 max-w-lg bg-red-500 text-white">
              <p className="font-medium">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </main>

      {/* Document Viewer Modal */}
      {currentDocument && (
        <DocumentViewer
          document={currentDocument}
          onClose={closeDocument}
        />
      )}

      {/* Input */}
      <footer className="bg-white dark:bg-gray-800 p-4 border-t border-gray-200 dark:border-gray-700">
        <form onSubmit={handleSubmit} className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              value={currentInputValue}
              onChange={(e) => handleInputChange(e.target.value)}
              placeholder="Type your message..."
              rows={1}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white resize-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !currentInputValue.trim() || noCorporaSelected}
            className="px-6 py-3 text-white rounded-lg focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors border-2"
            style={{
              backgroundColor: '#005440',
              borderColor: '#005440',
              ...(isLoading || !currentInputValue.trim() ? {} : { ':hover': { backgroundColor: '#004030' } })
            }}
            onMouseEnter={(e) => {
              if (!isLoading && currentInputValue.trim() && !noCorporaSelected) {
                e.currentTarget.style.backgroundColor = '#004030';
              }
            }}
            onMouseLeave={(e) => {
              if (!isLoading && currentInputValue.trim() && !noCorporaSelected) {
                e.currentTarget.style.backgroundColor = '#005440';
              }
            }}
          >
            Send
          </button>
        </form>
        {noCorporaSelected ? (
          <p className="text-xs text-amber-600 mt-2 font-medium">
            Please select at least one corpus from the sidebar to start chatting.
          </p>
        ) : (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        )}
      </footer>
    </div>
  );
}
