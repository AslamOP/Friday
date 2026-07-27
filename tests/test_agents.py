"""Verify all agent modules can be imported and instantiated."""

import pytest


def test_mentor_agent():
    from friday.agents.mentor import MentorAgent
    assert MentorAgent is not None
    agent = MentorAgent()
    assert hasattr(agent, "handle")
    assert hasattr(agent, "name")


def test_planner_agent():
    from friday.agents.planner import PlannerAgent
    agent = PlannerAgent()
    assert agent is not None


def test_software_engineer_agent():
    from friday.agents.software_engineer import SoftwareEngineerAgent
    agent = SoftwareEngineerAgent()
    assert agent is not None


def test_research_scientist_agent():
    from friday.agents.research_scientist import ResearchScientistAgent
    agent = ResearchScientistAgent()
    assert agent is not None


def test_automation_engineer_agent():
    from friday.agents.automation_engineer import AutomationEngineerAgent
    agent = AutomationEngineerAgent()
    assert agent is not None


def test_knowledge_manager_agent():
    from friday.agents.knowledge_manager import KnowledgeManagerAgent
    agent = KnowledgeManagerAgent()
    assert agent is not None


def test_study_agent():
    from friday.agents.study import StudyAgent
    agent = StudyAgent()
    assert agent is not None


def test_gaming_assistant_agent():
    from friday.agents.gaming_assistant import GamingAssistantAgent
    agent = GamingAssistantAgent()
    assert agent is not None


def test_base_agent():
    from friday.agents.base import BaseAgent
    assert BaseAgent is not None


def test_all_agents_have_prompts():
    agent_dirs = [
        "mentor", "planner", "software_engineer", "research_scientist",
        "automation_engineer", "knowledge_manager", "study", "gaming_assistant",
    ]
    for d in agent_dirs:
        module = __import__(f"friday.agents.{d}.prompts", fromlist=[""])
        assert hasattr(module, "SYSTEM_PROMPT") or hasattr(module, "system_prompt")
