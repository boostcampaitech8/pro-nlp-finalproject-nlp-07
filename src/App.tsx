import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { ChatPage } from './pages/ChatPage';
import { LoadingScreen } from './components/Common/LoadingScreen';
import { userService } from './services/userService';
import './App.css';

const App: React.FC = () => {
  const [isInitializing, setIsInitializing] = useState(true);

  // 앱 시작 시 user_id 초기화
  useEffect(() => {
    const initializeUser = async () => {
      try {
        await userService.initializeUserId();
      } catch (error) {
        console.error('Failed to initialize user:', error);
      } finally {
        setIsInitializing(false);
      }
    };

    initializeUser();
  }, []);

  if (isInitializing) {
    return <LoadingScreen message="초기화 중..." />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/chat/:sessionId" element={<ChatPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
