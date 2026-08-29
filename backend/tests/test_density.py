from datetime import date, datetime, time
from app.services.density_service import DensityService

def test_empty_day_density():
    today = date.today()
    events = []
    res = DensityService.calculate_day_density(today, events)
    assert res.density_score == 0.0
    assert res.density_level == "light"
    assert len(res.available_focus_windows) == 1
    assert res.available_focus_windows[0].duration_minutes == 540 # 9 hrs = 540 mins

def test_moderate_day_density():
    today = date.today()
    events = [
        {
            "start_time": datetime.combine(today, time(9, 30)),
            "end_time": datetime.combine(today, time(10, 30)),
            "cognitive_weight": 1.0,
            "is_all_day": False
        },
        {
            "start_time": datetime.combine(today, time(14, 0)),
            "end_time": datetime.combine(today, time(15, 0)),
            "cognitive_weight": 1.5,
            "is_all_day": False
        }
    ]
    res = DensityService.calculate_day_density(today, events)
    # Event 1: 60m * 1.0 = 60
    # Event 2: 60m * 1.5 = 90
    # Context switch: 2 * 15m = 30m
    # Total: 180m / 540m = 0.33 -> light/moderate
    assert res.density_score == 0.33
    assert res.meeting_count == 2
    assert res.total_committed_minutes == 120
    assert len(res.available_focus_windows) >= 2

def test_overloaded_day_density():
    today = date.today()
    events = [
        {
            "start_time": datetime.combine(today, time(9, 0)),
            "end_time": datetime.combine(today, time(13, 0)),
            "cognitive_weight": 1.5,
            "is_all_day": False
        },
        {
            "start_time": datetime.combine(today, time(13, 30)),
            "end_time": datetime.combine(today, time(17, 30)),
            "cognitive_weight": 1.5,
            "is_all_day": False
        }
    ]
    res = DensityService.calculate_day_density(today, events)
    # Exceeds max 1.0 load
    assert res.density_score == 1.0
    assert res.density_level == "overloaded"
