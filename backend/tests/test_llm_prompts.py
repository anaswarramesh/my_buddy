import pytest
from app.services.llm_service import LLMService

@pytest.mark.asyncio
async def test_prompt_a_big_idea_triage():
    transcript = "I want to launch an AI automated customer onboarding SaaS for fintech startups."
    res = await LLMService.classify_and_coach(transcript)
    assert res.classification == "BIG_IDEA"
    assert res.confidence > 0.85
    assert res.idea_analysis is not None
    assert res.idea_analysis.feasibility_score >= 1
    assert res.idea_analysis.friction_score >= 1
    assert res.idea_analysis.coaching_verdict is not None
    assert res.coaching_nudge is not None

@pytest.mark.asyncio
async def test_prompt_a_immediate_task_triage():
    transcript = "Email Sarah the revised quarterly budget spreadsheet."
    res = await LLMService.classify_and_coach(transcript)
    assert res.classification == "IMMEDIATE_TASK"
    assert len(res.extracted_tasks) >= 1
    assert res.extracted_tasks[0].estimated_minutes > 0

@pytest.mark.asyncio
async def test_prompt_b_starter_decomposition():
    title = "AI Legal Ingestion Bot"
    summary = "Summarizes client claims before attorney consultations."
    tasks = await LLMService.decompose_idea(title, summary)
    assert len(tasks) >= 3
    # Verify Step 1 is Micro-Ignition (<= 15 minutes)
    step_1 = tasks[0]
    assert step_1.is_starter_step is True
    assert step_1.estimated_minutes <= 15
    assert step_1.friction_level == "micro"

@pytest.mark.asyncio
async def test_prompt_c_nlp_reschedule():
    command = "Clear my Thursday afternoon and float those tasks to next week."
    density_snapshots = []
    tasks = [{"id": "t-1", "title": "Draft pitch deck", "friction": "medium"}]
    res = await LLMService.analyze_density_and_nlp(command, density_snapshots, tasks)
    assert "Thursday" in res.summary_of_changes
    assert len(res.mutations) >= 1
