import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppLayout } from '../components/Layout/AppLayout';
import { CustomScenarioModal } from '../components/Common/CustomScenarioModal';
import { LoadingScreen } from '../components/Common/LoadingScreen';
import { sessionService } from '../services/sessionService';
import { userService } from '../services/userService';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [showCustomModal, setShowCustomModal] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const handleSelectScenario = async (persona: string, situation: string) => {
    setIsCreating(true);

    try {
      const userId = userService.getUserId();
      if (!userId) {
        throw new Error('User ID not found');
      }

      console.log('Creating session...', { userId, persona, situation });

      const sessionResponse = await sessionService.createSession(
        userId,
        persona,
        situation
      );

      console.log('Session created:', sessionResponse);

      navigate(`/chat/${sessionResponse.session_id}`, {
        state: { persona, situation }
      });
    } catch (error) {
      console.error('Failed to create session:', error);
      alert('세션 생성에 실패했습니다. 다시 시도해주세요.');
      setIsCreating(false);
    }
  };

  const handleCustomCreate = () => {
    setShowCustomModal(true);
  };

  const handleCustomSubmit = (persona: string, situation: string) => {
    setShowCustomModal(false);
    handleSelectScenario(persona, situation);
  };

  const handleSettings = () => {
    console.log('Settings clicked');
  };

  if (isCreating) {
    return <LoadingScreen message="대화 준비 중..." />;
  }

  return (
    <>
      <AppLayout
        messages={[]} // ✅ 빈 배열
        chatHistories={[]} // ✅ 빈 배열
        currentChatId={null} // ✅ null
        isWaitingForResponse={false}
        inputValue=""
        onInputChange={() => {}} // ✅ 빈 함수
        onSendMessage={() => {}} // ✅ 빈 함수
        onNewChat={() => navigate('/')} // ✅ 홈으로 (새로고침 효과)
        onSelectChat={() => {}} // ✅ 빈 함수
        onSettings={handleSettings}
        onSelectScenario={handleSelectScenario}
        onCustomCreate={handleCustomCreate}
        showScenarioSetup={true} // ✅ 시나리오 선택 화면 표시
      />

      {showCustomModal && (
        <CustomScenarioModal
          onSubmit={handleCustomSubmit}
          onClose={() => setShowCustomModal(false)}
        />
      )}
    </>
  );
};
