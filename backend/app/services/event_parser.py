import re
from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, Any

class EventParserService:
    @staticmethod
    def parse_event_from_text(transcript: str, base_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Extracts meeting / event schedule details (title, start datetime, end datetime)
        from natural language voice transcripts.
        """
        if not base_date:
            base_date = date.today()

        text = transcript.strip()
        lower = text.lower()

        # Check if text contains scheduling or meeting intent
        event_keywords = [
            "meeting", "call", "appointment", "sync", "catchup", "interview", 
            "review", "lunch", "dinner", "standup", "session", "schedule", "calendar",
            "at ", "tomorrow", "tonight", "this afternoon", "this morning"
        ]
        has_event_kw = any(kw in lower for kw in event_keywords)
        has_time_kw = bool(re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)|\d{1,2}\s*(?:am|pm)|at\s+\d{1,2})\b", lower))

        if not (has_event_kw or has_time_kw):
            return None

        # 1. Determine Target Date
        target_date = base_date
        if "tomorrow" in lower:
            target_date = base_date + timedelta(days=1)
        elif "day after tomorrow" in lower:
            target_date = base_date + timedelta(days=2)
        else:
            weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for idx, day_name in enumerate(weekdays):
                if day_name in lower:
                    days_ahead = (idx - base_date.weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    target_date = base_date + timedelta(days=days_ahead)
                    break

        # 2. Determine Start Time
        time_match = re.search(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", lower)
        hour = 10 # default to 10:00 AM
        minute = 0
        if time_match:
            h_str, m_str, am_pm = time_match.groups()
            h = int(h_str)
            m = int(m_str) if m_str else 0
            if am_pm == "pm" and h < 12:
                h += 12
            elif am_pm == "am" and h == 12:
                h = 0
            elif not am_pm and h < 8: # e.g. "at 3" typically means 3 PM in workday context
                h += 12
            hour, minute = h, m
        elif "afternoon" in lower:
            hour, minute = 14, 0
        elif "morning" in lower:
            hour, minute = 10, 0
        elif "evening" in lower:
            hour, minute = 18, 0

        # 3. Determine Duration
        duration_mins = 45
        if "1 hour" in lower or "one hour" in lower or "60 min" in lower:
            duration_mins = 60
        elif "30 min" in lower or "half hour" in lower:
            duration_mins = 30
        elif "15 min" in lower:
            duration_mins = 15
        elif "90 min" in lower:
            duration_mins = 90

        # 4. Clean and Standardize Event Title
        clean_title = re.sub(
            r"^(please\s+|can\s+you\s+|schedule\s+(a\s+)?|add\s+(a\s+)?|book\s+(a\s+)?|create\s+(a\s+)?|set\s+up\s+a\s+|set\s+up\s+)",
            "",
            text,
            flags=re.IGNORECASE
        )
        clean_title = re.sub(
            r"\b(tomorrow|today|yesterday|on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
            "",
            clean_title,
            flags=re.IGNORECASE
        )
        clean_title = re.sub(r"\b(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", "", clean_title, flags=re.IGNORECASE)
        clean_title = re.sub(r"\b(for\s+(?:\d+|one|a|an)\s*(?:mins?|minutes?|hours?))\b", "", clean_title, flags=re.IGNORECASE)
        clean_title = re.sub(r"\s+", " ", clean_title).strip(" .,-")

        if not clean_title or len(clean_title) < 2:
            clean_title = "Scheduled Meeting"
        clean_title = clean_title[0].upper() + clean_title[1:]

        start_dt = datetime.combine(target_date, time(hour, minute))
        end_dt = start_dt + timedelta(minutes=duration_mins)

        # Estimate cognitive weight
        cognitive_weight = 1.0
        if any(w in lower for w in ["review", "interview", "quarterly", "strategy", "contract", "investor"]):
            cognitive_weight = 1.5
        elif any(w in lower for w in ["quick", "standup", "catchup", "coffee", "chat"]):
            cognitive_weight = 0.8

        return {
            "title": clean_title,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "target_date": target_date,
            "cognitive_weight": cognitive_weight
        }
