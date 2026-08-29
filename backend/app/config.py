import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "CoachPilot AI")
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./coach_pilot.db")
    
    # LLM Settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    llm_provider: str = os.getenv("LLM_PROVIDER", "simulation")
    
    # Productivity Rules
    work_day_start_hour: int = 9  # 9:00 AM
    work_day_end_hour: int = 18   # 6:00 PM
    work_window_minutes: int = 540 # 9 hours
    context_switch_penalty_mins: int = 15 # Minutes penalty per meeting transition
    max_density_threshold: float = 0.75 # Threshold above which day is crowded
    
    # User Default Timezone
    default_timezone: str = "UTC"

settings = Settings()
