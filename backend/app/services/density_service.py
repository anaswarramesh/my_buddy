from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Tuple
import json
from app.config import settings
from app.schemas.density import FocusWindow, DailyDensityResponse

class DensityService:
    @staticmethod
    def calculate_day_density(
        target_date: date,
        events: List[Any],
        work_start_hour: int = settings.work_day_start_hour,
        work_end_hour: int = settings.work_day_end_hour,
        work_window_minutes: int = settings.work_window_minutes,
        switch_penalty: int = settings.context_switch_penalty_mins
    ) -> DailyDensityResponse:
        """
        Calculates daily density score:
        D(d) = min(1.0, (sum(T_i * W_i) + N * C_switch) / T_work_window)
        Also extracts available focus windows during work hours.
        """
        work_start_dt = datetime.combine(target_date, time(work_start_hour, 0))
        work_end_dt = datetime.combine(target_date, time(work_end_hour, 0))

        # Filter events for this day that overlap work window
        day_events = []
        for ev in events:
            # Handle both model objects and dicts
            ev_start = ev.start_time if hasattr(ev, 'start_time') else ev['start_time']
            ev_end = ev.end_time if hasattr(ev, 'end_time') else ev['end_time']
            weight = float(ev.cognitive_weight if hasattr(ev, 'cognitive_weight') else ev.get('cognitive_weight', 1.0))
            is_all_day = ev.is_all_day if hasattr(ev, 'is_all_day') else ev.get('is_all_day', False)

            # Strip tzinfo for consistent local comparison
            ev_start = ev_start.replace(tzinfo=None) if ev_start.tzinfo else ev_start
            ev_end = ev_end.replace(tzinfo=None) if ev_end.tzinfo else ev_end

            if is_all_day:
                # All day events take up substantial load
                day_events.append({
                    "start": work_start_dt,
                    "end": work_end_dt,
                    "duration_mins": work_window_minutes,
                    "weight": weight
                })
                continue

            # Check overlap with work window
            if ev_end > work_start_dt and ev_start < work_end_dt:
                clamped_start = max(ev_start, work_start_dt)
                clamped_end = min(ev_end, work_end_dt)
                duration = int((clamped_end - clamped_start).total_seconds() / 60)
                if duration > 0:
                    day_events.append({
                        "start": clamped_start,
                        "end": clamped_end,
                        "duration_mins": duration,
                        "weight": weight
                    })

        # Sort events by start time
        day_events.sort(key=lambda x: x["start"])

        # Calculate committed time and weighted load
        total_committed_minutes = sum(e["duration_mins"] for e in day_events)
        meeting_count = len(day_events)
        weighted_minutes_sum = sum(e["duration_mins"] * e["weight"] for e in day_events)
        context_switching_penalty = meeting_count * switch_penalty

        raw_load = weighted_minutes_sum + context_switching_penalty
        density_score = min(1.0, round(raw_load / work_window_minutes, 2))

        # Categorize density level
        if density_score < 0.45:
            density_level = "light"
        elif density_score < 0.70:
            density_level = "moderate"
        elif density_score < 0.85:
            density_level = "dense"
        else:
            density_level = "overloaded"

        # Calculate free focus windows
        focus_windows = DensityService._find_free_windows(
            work_start_dt,
            work_end_dt,
            day_events
        )

        return DailyDensityResponse(
            date=target_date,
            density_score=density_score,
            density_level=density_level,
            total_committed_minutes=total_committed_minutes,
            meeting_count=meeting_count,
            available_focus_windows=focus_windows
        )

    @staticmethod
    def _find_free_windows(
        work_start: datetime,
        work_end: datetime,
        sorted_events: List[Dict[str, Any]]
    ) -> List[FocusWindow]:
        free_windows = []
        current_cursor = work_start

        # Merge overlapping events first
        merged_blocks: List[Tuple[datetime, datetime]] = []
        for ev in sorted_events:
            s, e = ev["start"], ev["end"]
            if not merged_blocks:
                merged_blocks.append((s, e))
            else:
                prev_s, prev_e = merged_blocks[-1]
                if s <= prev_e:
                    merged_blocks[-1] = (prev_s, max(prev_e, e))
                else:
                    merged_blocks.append((s, e))

        for block_start, block_end in merged_blocks:
            if block_start > current_cursor:
                gap_mins = int((block_start - current_cursor).total_seconds() / 60)
                if gap_mins >= 15:
                    suitability = "deep_work" if gap_mins >= 45 else ("starter_task" if gap_mins >= 20 else "admin")
                    free_windows.append(FocusWindow(
                        start_time=current_cursor.strftime("%H:%M"),
                        end_time=block_start.strftime("%H:%M"),
                        duration_minutes=gap_mins,
                        suitability=suitability
                    ))
            current_cursor = max(current_cursor, block_end)

        if current_cursor < work_end:
            gap_mins = int((work_end - current_cursor).total_seconds() / 60)
            if gap_mins >= 15:
                suitability = "deep_work" if gap_mins >= 45 else ("starter_task" if gap_mins >= 20 else "admin")
                free_windows.append(FocusWindow(
                    start_time=current_cursor.strftime("%H:%M"),
                    end_time=work_end.strftime("%H:%M"),
                    duration_minutes=gap_mins,
                    suitability=suitability
                ))

        return free_windows
