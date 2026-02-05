export interface SessionFeedback {
  session_id: string;
  persona_name?: string;
  total_turns: number;
  coach_interventions: number;
  intervention_rate: number;
  interventions: CoachIntervention[];
  final_feedback: FinalFeedback;
  generated_at?: string;
}

export interface CoachIntervention {
  message_id: string;
  user_message: string;
  coach_feedback: string;
  signals: string[];
  timestamp: string;
}

// ✅ 백엔드 피드백 구조
export interface FinalFeedback {
  user_profile: UserProfile;
  conversation_summary: string;
  feedback: DetailedFeedback;
}

export interface UserProfile {
  traits: string[];
  tendencies: string[];
  risk_signals: string[];
}

export interface DetailedFeedback {
  user_tendency_summary: string;
  situation_response_evaluation: SituationEvaluation;
  sentence_expression_evaluation: ExpressionEvaluation;
  next_action_guide: NextActionGuide;
}

export interface SituationEvaluation {
  score: number;
  good_points: string[];
  improve_points: string[];
  notes: string;
}

export interface ExpressionEvaluation {
  good_points: string[];
  improve_points: string[];
  rewrite_examples: string[];
}

export interface NextActionGuide {
  copyable_lines: string[];
  next_drills: string[];
  homework: string[];
}
