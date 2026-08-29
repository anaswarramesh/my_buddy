export type FrictionLevel = 'micro' | 'easy' | 'medium' | 'deep_work';
export type EnergyRequirement = 'creative' | 'deep_focus' | 'admin' | 'low_energy';
export type DensityLevel = 'light' | 'moderate' | 'dense' | 'overloaded';

export interface Idea {
  id: string;
  user_id: string;
  raw_transcript: string;
  title: string;
  summary?: string;
  category: string;
  feasibility_score: number;
  impact_score: number;
  friction_score: number;
  coaching_verdict?: string;
  primary_obstacle?: string;
  nudge_strategy?: string;
  status: string;
  created_at: string;
}

export interface Task {
  id: string;
  user_id: string;
  idea_id?: string;
  title: string;
  description?: string;
  is_starter_step: boolean;
  sequence_order: number;
  estimated_minutes: number;
  friction_level: FrictionLevel;
  energy_requirement: EnergyRequirement;
  priority: 'critical' | 'high' | 'medium' | 'low';
  is_scheduled: boolean;
  scheduled_start?: string;
  scheduled_end?: string;
  status: 'pending' | 'scheduled' | 'in_progress' | 'completed' | 'floated';
}

export interface CalendarEvent {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  is_all_day: boolean;
  is_fixed: boolean;
  event_category: string;
  cognitive_weight: number;
}

export interface FocusWindow {
  start_time: string;
  end_time: string;
  duration_minutes: number;
  suitability: 'deep_work' | 'starter_task' | 'admin';
}

export interface DailyDensity {
  score: number;
  level: DensityLevel;
  committed_minutes: number;
  meeting_count: number;
  available_focus_windows: FocusWindow[];
}

export interface DailySynthesisResponse {
  date: string;
  density: DailyDensity;
  today_events: CalendarEvent[];
  starter_tasks: Task[];
  scheduled_tasks: Task[];
  coaching_nudge: string;
}
