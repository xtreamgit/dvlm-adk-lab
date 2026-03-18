"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { User, Agent, apiClient } from '../lib/api-enhanced';
import ChatInterface from '../components/ChatInterface';
import UserProfilePanel from '../components/UserProfilePanel';
import WelcomeModal from '../components/WelcomeModal';
import CorpusSelector from '../components/CorpusSelector';
import AgentSwitcher from '../components/AgentSwitcher';
import Image from 'next/image';

// UserProfile type for legacy compatibility
type UserProfile = {
  name: string;
  preferences?: string;
};

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [showProfileSetup, setShowProfileSetup] = useState(false);
  const [chatInputValue, setChatInputValue] = useState('');
  const [selectedCorpora, setSelectedCorpora] = useState<string[]>([]);
  const [isSavingCorpora, setIsSavingCorpora] = useState(false);
  const [showChatInterface, setShowChatInterface] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReturningFromProfile, setIsReturningFromProfile] = useState(false);
  const [shouldAutoSubmit, setShouldAutoSubmit] = useState(false);
  const [isLoadingExistingSession, setIsLoadingExistingSession] = useState(false);
  const [savedChatState, setSavedChatState] = useState<{
    showChatInterface: boolean;
    chatInputValue: string;
    selectedCorpora: string[];
    sessionId: string | null;
  } | null>(null);
  const [currentAgent, setCurrentAgent] = useState<Agent | null>(null);
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(true);
  const [showWelcome, setShowWelcome] = useState(false);

  // Check for existing authentication on component mount; redirect to landing if not authenticated
  useEffect(() => {
    const loadUserData = async (userData: User) => {
      setUser(userData);
      setUserProfile({
        name: userData.full_name,
        preferences: ''
      });
      
      // Check if there's an existing session
      const existingSessionId = apiClient.getSessionId();
      if (existingSessionId) {
        setSessionId(existingSessionId);
        setShowChatInterface(true);
        setIsLoadingExistingSession(true);
      }
      
      // Load user's agents to get the current agent
      try {
        const myAgents = await apiClient.getMyAgents();
        setAvailableAgents(myAgents);
        if (myAgents.length > 0) {
          const defaultAgent = myAgents.find(a => a.is_default) || myAgents[0];
          setCurrentAgent(defaultAgent);
          console.log('✅ Loaded default agent:', defaultAgent.display_name);
        }
      } catch (err) {
        console.error('Failed to load user agents:', err);
      } finally {
        setIsLoadingAgents(false);
      }
      
      // Load saved corpus preferences
      try {
        const profile = await apiClient.getMyProfile();
        if (profile.profile?.preferences?.selected_corpora && Array.isArray(profile.profile.preferences.selected_corpora)) {
          setSelectedCorpora(profile.profile.preferences.selected_corpora as string[]);
          console.log('✅ Loaded saved corpus preferences:', profile.profile.preferences.selected_corpora);
        }
      } catch (err) {
        console.error('Failed to load corpus preferences:', err);
      }
      
      // Check if this is first-time user (check localStorage)
      const hasSeenWelcome = localStorage.getItem('hasSeenWelcome');
      if (!hasSeenWelcome) {
        setShowWelcome(true);
      }
      
      setIsLoading(false);
    };

    const checkAuth = async () => {
      try {
        // IAP authentication (behind load balancer)
        const iapUser = await apiClient.checkIapAuth();
        if (iapUser) {
          console.log('✅ IAP authenticated:', iapUser.email);
          await loadUserData(iapUser);
          return;
        }
        
        // Not authenticated: redirect to landing page
        router.push('/landing');
      } catch (error) {
        console.error('Auth verification failed:', error);
        router.push('/landing');
      }
    };

    checkAuth();
  }, [router]);

  const handleLogout = () => {
    apiClient.logout();
    router.push('/landing');
  };


  const handleUpdateProfile = () => {
    if (showChatInterface) {
      // Save current chat state before switching to profile
      setSavedChatState({
        showChatInterface,
        chatInputValue,
        selectedCorpora,
        sessionId
      });
    }
    setShowProfileSetup(true);
  };

  // Reset auto-submit flag after it's been used
  useEffect(() => {
    if (shouldAutoSubmit && showChatInterface) {
      // Reset the flag after a short delay to allow the ChatInterface to process it
      const timer = setTimeout(() => {
        setShouldAutoSubmit(false);
      }, 200);
      return () => clearTimeout(timer);
    }
  }, [shouldAutoSubmit, showChatInterface]);

  const handleCancelEdit = () => {
    setShowProfileSetup(false);
    
    // If there was a saved chat state, restore it completely
    if (savedChatState && savedChatState.sessionId) {
      setShowChatInterface(savedChatState.showChatInterface);
      setChatInputValue(savedChatState.chatInputValue);
      setSelectedCorpora(savedChatState.selectedCorpora);
      setSessionId(savedChatState.sessionId);
      setIsReturningFromProfile(true);
      setSavedChatState(null);
    }
  };

  const handleStartChat = async () => {
    if (chatInputValue.trim()) {
      // Ensure we have a session before starting chat
      if (!sessionId) {
        try {
          const session = await apiClient.createSession();
          setSessionId(session.session_id);
          console.log('Session created before starting chat:', session.session_id);
        } catch (error) {
          console.error('Failed to create session before chat:', error);
          return;
        }
      }
      
      setShouldAutoSubmit(true);
      setShowChatInterface(true);
    }
  };

  const handleDismissWelcome = () => {
    localStorage.setItem('hasSeenWelcome', 'true');
    setShowWelcome(false);
  };

  // Auto-save corpus selection to backend preferences
  const handleCorporaChange = async (newCorpora: string[]) => {
    setSelectedCorpora(newCorpora);
    
    // Don't save for guest users
    if (!user || user.username === 'guest') {
      return;
    }
    
    // Auto-save to backend
    if (!isSavingCorpora) {
      setIsSavingCorpora(true);
      try {
        await apiClient.updateProfile({
          preferences: {
            selected_corpora: newCorpora
          }
        });
        console.log('✅ Corpus selection saved:', newCorpora);
      } catch (error) {
        console.error('❌ Failed to save corpus selection:', error);
      } finally {
        setIsSavingCorpora(false);
      }
    }
  };

  const handleNewChat = async () => {
    setShowChatInterface(false);
    setChatInputValue('');
    setIsReturningFromProfile(false);
    setIsLoadingExistingSession(false);
    setShouldAutoSubmit(false);
    
    // Create a new session for the new chat
    try {
      // Reset the old session first
      apiClient.resetSession();
      
      // Create a new session
      const session = await apiClient.createSession();
      setSessionId(session.session_id);
      console.log('New session created for new chat:', session.session_id);
    } catch (error) {
      console.error('Failed to create new session:', error);
      setSessionId(null);
    }
  };

  // Poll for session ID updates
  useEffect(() => {
    const interval = setInterval(() => {
      const currentSessionId = apiClient.getSessionId();
      if (currentSessionId !== sessionId) {
        setSessionId(currentSessionId);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionId]);

  // Show loading screen while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Show profile setup if user wants to edit profile
  if (showProfileSetup) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-full max-w-2xl">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              User Profile
            </h2>
            <button
              onClick={handleCancelEdit}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="p-6">
            <UserProfilePanel onProfileUpdate={() => {
              // Refresh user data after profile update
              setShowProfileSetup(false);
            }} />
          </div>
        </div>
      </div>
    );
  }

  // Show chat interface if user has started chatting
  if (showChatInterface) {
    return (
      <>
        {showWelcome && user && (
          <WelcomeModal onDismiss={handleDismissWelcome} userName={user.full_name} />
        )}
      <div className="flex h-screen bg-gray-50">
        {/* Left Sidebar - Navigation and Corpus Selector */}
        <div className="w-80 bg-gray-100 border-r border-gray-200 flex flex-col">
          {/* USFS Logo and Title */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center space-x-3 mb-4">
              <Image 
                src="/fs-logo.svg" 
                alt="USDA Forest Service" 
                width={60} 
                height={40}
                className="h-10 w-auto"
              />
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Forest Service</h2>
                <p className="text-sm text-gray-600">U.S. DEPARTMENT OF AGRICULTURE</p>
              </div>
            </div>
          </div>
          {/* Navigation Menu */}
          <div className="p-4 space-y-2">
            {/* Session ID Display */}
            <div className="px-3 py-2 bg-gray-50 rounded-lg border">
              <div className="text-xs text-gray-500 mb-1">Session ID:</div>
              <div className="text-xs font-mono text-gray-700 break-all">
                {sessionId ? sessionId.slice(-4) : 'No active session'}
              </div>
            </div>
            
            <button 
              onClick={handleNewChat}
              className="w-full flex items-center space-x-3 p-3 text-left text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span className="font-medium">New Chat</span>
            </button>
            
            <button className="w-full flex items-center space-x-3 p-3 text-left text-gray-700 hover:bg-gray-200 rounded-lg transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span>Search Chats</span>
            </button>
            
            <button 
              onClick={() => router.push('/open-document')}
              className="w-full flex items-center space-x-3 p-3 text-left text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>List Documents</span>
            </button>
          </div>

          {/* Agent Selector */}
          <div className="p-4 border-t border-gray-200">
            <div className="text-base font-semibold text-gray-900 mb-2">Current Agent</div>
            <AgentSwitcher 
              currentAgent={currentAgent}
              availableAgents={availableAgents}
              isLoading={isLoadingAgents}
            />
          </div>

          {/* Corpus Selector */}
          <div className="p-4 border-t border-gray-200 flex-1 overflow-y-auto">
            <CorpusSelector 
              selectedCorpora={selectedCorpora}
              onCorporaChange={handleCorporaChange}
            />
          </div>

          {/* Chats Section */}
          <div className="p-4 border-t border-gray-200">
            <button className="w-full flex items-center space-x-3 p-3 text-left text-gray-700 hover:bg-gray-200 rounded-lg transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <span>Chats</span>
            </button>
          </div>

          {/* Profile Section */}
          <div className="p-4 border-t border-gray-200 text-white" style={{ backgroundColor: '#005440' }}>
            <button 
              onClick={handleUpdateProfile}
              className="w-full flex items-center space-x-3 p-3 text-left rounded-lg transition-colors mb-2"
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#004030'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span className="font-medium">Profile</span>
            </button>
            <button 
              onClick={handleLogout}
              className="w-full flex items-center space-x-3 p-3 text-left rounded-lg transition-colors"
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#004030'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span className="font-medium">Logout</span>
            </button>
          </div>
        </div>
        
        {/* Chat Interface */}
        <div className="flex-1">
          {userProfile && (
            <ChatInterface 
              userProfile={userProfile}
              onUpdateProfile={handleUpdateProfile}
              inputValue={chatInputValue}
              onInputChange={setChatInputValue}
              selectedCorpora={selectedCorpora}
              initialMessage={isReturningFromProfile ? '' : chatInputValue}
              shouldAutoSubmitInitial={shouldAutoSubmit && !isReturningFromProfile}
              onNewChat={handleNewChat}
              sessionId={sessionId}
              isReturningToSession={isReturningFromProfile || isLoadingExistingSession}
              user={user}
              currentAgent={currentAgent}
            />
          )}
        </div>
      </div>
      </>
    );
  }

  // Show landing page with USFS-RAG layout once profile is set
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Navigation and Corpus Selector */}
      <div className="w-80 bg-gray-100 border-r border-gray-200 flex flex-col">
        {/* USFS Logo and Title */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <Image 
              src="/fs-logo.svg" 
              alt="USDA Forest Service" 
              width={60} 
              height={40}
              className="h-10 w-auto"
            />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Forest Service</h2>
              <p className="text-sm text-gray-600">U.S. DEPARTMENT OF AGRICULTURE</p>
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <div className="p-4 space-y-2">
          {/* Session ID Display */}
          <div className="px-3 py-2 bg-gray-50 rounded-lg border">
            <div className="text-xs text-gray-500 mb-1">Session ID:</div>
            <div className="text-xs font-mono text-gray-700 break-all">
              {sessionId ? sessionId.slice(-4) : 'No active session'}
            </div>
          </div>
            
          <button 
            onClick={handleNewChat}
            className="w-full flex items-center space-x-3 p-3 text-left text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span className="font-medium">New Chat</span>
          </button>
          
          <button className="w-full flex items-center space-x-3 p-3 text-left text-gray-700 hover:bg-gray-200 rounded-lg transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span>Search Chats</span>
          </button>
          
          <button 
            onClick={() => router.push('/open-document')}
            className="w-full flex items-center space-x-3 p-3 text-left text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>List Documents</span>
          </button>
        </div>

        {/* Agent Selector */}
        <div className="p-4 border-t border-gray-200">
          <div className="text-base font-semibold text-gray-900 mb-2">Current Agent</div>
          <AgentSwitcher 
            currentAgent={currentAgent}
            availableAgents={availableAgents}
            isLoading={isLoadingAgents}
          />
        </div>

        {/* Corpus Selector */}
        <div className="p-4 border-t border-gray-200 flex-1 overflow-y-auto">
          <CorpusSelector 
            selectedCorpora={selectedCorpora}
            onCorporaChange={handleCorporaChange}
          />
        </div>

        {/* Chats Section */}
        <div className="p-4 border-t border-gray-200">
          <button className="w-full flex items-center space-x-3 p-3 text-left text-gray-700 hover:bg-gray-200 rounded-lg transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span>Chats</span>
          </button>
        </div>

        {/* Profile Section */}
        <div className="p-4 border-t border-gray-200 text-white" style={{ backgroundColor: '#005440' }}>
          <button 
            onClick={handleUpdateProfile}
            className="w-full flex items-center space-x-3 p-3 text-left rounded-lg transition-colors mb-2"
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#004030'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span className="font-medium">Profile</span>
          </button>
          <button 
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 p-3 text-left rounded-lg transition-colors"
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#004030'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </div>
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Header with USDA Forest Service Logo */}
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

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col justify-center items-center p-8">
          <div className="max-w-2xl w-full text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">
              What would you like to research today?
            </h1>
            
            <div className="relative">
              <input
                type="text"
                value={chatInputValue}
                onChange={(e) => setChatInputValue(e.target.value)}
                placeholder="Ask your question"
                className="w-full p-4 pr-24 text-lg border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && chatInputValue.trim()) {
                    handleStartChat();
                  }
                }}
              />
              <button 
                onClick={handleStartChat}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-white px-6 py-2 rounded-full transition-colors font-medium"
                style={{ backgroundColor: '#005440' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#006b52';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#005440';
                }}
              >
                Ask
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="bg-gray-200 p-4 text-center">
          <div className="flex items-center justify-center space-x-2">
            <Image 
              src="/fs-logo.svg" 
              alt="USDA Forest Service" 
              width={20} 
              height={16}
              className="h-4 w-auto"
            />
            <p className="text-sm text-gray-600">
              USFS-RAG can make mistakes. Always check important info.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}
