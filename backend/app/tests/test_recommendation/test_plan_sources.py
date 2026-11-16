from app.recommendation.job_matcher import JobMatcher
from app.recommendation.plan_generator import PlanGenerator


def test_campus_matches_follow_major_and_do_not_fabricate_sources():
    events = [
        {"id": "cs", "title": "Python Workshop", "description": "Python programming", "source": "rowdylink", "source_kind": "scraped", "source_label": "RowdyLink", "url": "https://rowdylink.utsa.edu/event/1", "type": "event"},
        {"id": "business", "title": "Accounting Networking", "description": "Accounting and finance", "source": "rowdylink", "type": "event"},
        {"id": "past", "title": "Python Old Event", "description": "Python", "source": "rowdylink", "expiration_date": "2020-01-01T00:00:00Z", "type": "event"},
    ]
    generator = PlanGenerator()
    cs = generator._match_campus_opportunities({"major": "Computer Science", "skills": ["python"]}, events)
    business = generator._match_campus_opportunities({"major": "Accounting", "career_interests": ["Finance"]}, events)
    assert [item["opportunity_id"] for item in cs] == ["cs"]
    assert [item["opportunity_id"] for item in business] == ["business"]
    assert cs[0]["source_label"] == "RowdyLink"
    assert "match_score" not in cs[0]


def test_plan_keeps_campus_sources_separate_from_handshake_jobs():
    plan = PlanGenerator().generate(student={"skills": ["python"]}, career_matches=[], job_matches=[], experience_matches=[], skill_gaps=[], include_resume_analysis=False, opportunities=[{"id": "event", "type": "event", "title": "Python Workshop", "source": "rowdylink"}], opportunity_source="handshake")
    assert len(plan["campus_matches"]) == 1
    assert plan["job_matches"] == []


def test_expired_jobs_are_not_recommended():
    matcher = JobMatcher()
    jobs = [
        {"id": "closed", "title": "Closed", "deadline": "2020-01-01"},
        {"id": "active", "title": "Active", "deadline": "2099-01-01"},
        {"id": "unknown", "title": "Unknown", "deadline": None},
    ]
    assert {item["opportunity_id"] for item in matcher.rank_opportunities({}, jobs)} == {"active", "unknown"}


def test_generic_goal_words_do_not_match_unrelated_campus_events():
    student = {"major": "Computer Science", "short_term_goal": "Find a software engineering internship", "skills": ["python"]}
    events = [
        {"id": "swim", "title": "Adult Swim Lessons", "description": "Find your next activity with our students", "type": "event"},
        {"id": "coding", "title": "Python Workshop", "description": "Build a Python project", "type": "event"},
    ]
    matches = PlanGenerator()._match_campus_opportunities(student, events)
    assert [event["opportunity_id"] for event in matches] == ["coding"]
