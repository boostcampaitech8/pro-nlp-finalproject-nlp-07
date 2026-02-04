export interface CoachIntervention {
  message_id: string;
  user_message: string;
  coach_feedback: string;
  signals: string[];
  timestamp: string;
}

export interface Suggestion {
  task: string;
  description: string;
}

export interface FinalFeedback {
  suggestions: Suggestion[];
}

export interface SessionFeedback {
  session_id: string;
  persona_name: string;
  total_turns: number;
  coach_interventions: number;
  intervention_rate: number;
  interventions: CoachIntervention[];
  final_feedback: FinalFeedback;
}
