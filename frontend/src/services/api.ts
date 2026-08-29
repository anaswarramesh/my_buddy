import { DailySynthesisResponse, Idea, Task, DailyDensity } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

export const CoachPilotAPI = {
  async getDailySynthesis(): Promise<DailySynthesisResponse> {
    const res = await fetch(`${API_BASE_URL}/synthesis/daily`);
    if (!res.ok) throw new Error('Failed to fetch daily synthesis');
    return res.json();
  },

  async processVoiceThought(transcript: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/voice/process-thought`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript, user_id: 'default-user' }),
    });
    if (!res.ok) throw new Error('Failed to process voice thought');
    return res.json();
  },

  async getIdeas(): Promise<Idea[]> {
    const res = await fetch(`${API_BASE_URL}/ideas`);
    if (!res.ok) throw new Error('Failed to fetch ideas');
    return res.json();
  },

  async autoScheduleTask(taskId: string): Promise<Task> {
    const res = await fetch(`${API_BASE_URL}/tasks/${taskId}/auto-schedule`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to auto-schedule task');
    return res.json();
  },

  async executeNLPCommand(command: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/nlp/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, user_id: 'default-user' }),
    });
    if (!res.ok) throw new Error('Failed to execute NLP command');
    return res.json();
  },

  async getDensityForecast(days: number = 7): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/calendar/density?days=${days}`);
    if (!res.ok) throw new Error('Failed to fetch density forecast');
    return res.json();
  }
};
