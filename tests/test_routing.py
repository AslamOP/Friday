"""Verify all 8 agents route correctly via the orchestrator."""

import pytest


@pytest.fixture(scope="module")
def orch():
    import asyncio
    from friday.core.orchestrator import get_orchestrator

    o = get_orchestrator()
    from friday.agents.mentor import MentorAgent
    from friday.agents.planner import PlannerAgent
    from friday.agents.software_engineer import SoftwareEngineerAgent
    from friday.agents.research_scientist import ResearchScientistAgent
    from friday.agents.automation_engineer import AutomationEngineerAgent
    from friday.agents.knowledge_manager import KnowledgeManagerAgent
    from friday.agents.study import StudyAgent
    from friday.agents.gaming_assistant import GamingAssistantAgent

    for a in [
        MentorAgent(), PlannerAgent(), SoftwareEngineerAgent(),
        ResearchScientistAgent(), AutomationEngineerAgent(),
        KnowledgeManagerAgent(), StudyAgent(), GamingAssistantAgent(),
    ]:
        o.register_agent(a)
    return o


@pytest.mark.asyncio
class TestRouting:
    """Each input should route to the correct agent via intent matching."""

    @pytest.mark.parametrize("input_text,expected_agent", [
        ("Build a billing system API", "software_engineer"),
        ("Plan the project timeline for Q3", "planner"),
        ("Explain how quantum computing works", "study"),
        ("Research the latest papers on LLMs", "research_scientist"),
        ("Find my notes about Docker", "knowledge_manager"),
        ("Challenge my assumption that Python is faster", "mentor"),
        ("Automate the deployment pipeline", "automation_engineer"),
        ("What are the best gaming settings for Cyberpunk", "gaming_assistant"),
    ])
    async def test_routes_to_correct_agent(self, orch, input_text, expected_agent):
        intent = await orch.intent_parser.parse(input_text)
        agent = await orch.agent_router.route(intent)
        assert agent.name == expected_agent, (
            f"'{input_text}' routed to '{agent.name}' instead of '{expected_agent}'"
        )

    async def test_chat_falls_back_to_default(self, orch):
        intent = await orch.intent_parser.parse("Hello, how are you?")
        agent = await orch.agent_router.route(intent)
        assert agent.name == "default"
        assert intent.type == "chat"

    async def test_all_intent_types_mapped(self, orch):
        """Every known intent type should map to exactly one agent."""
        intent_types = {
            "code": "software_engineer",
            "plan": "planner",
            "study": "study",
            "knowledge": "knowledge_manager",
            "research": "research_scientist",
            "challenge": "mentor",
            "automate": "automation_engineer",
            "gaming": "gaming_assistant",
        }
        from friday.core.intent_parser import Intent
        for intent_type, expected_agent in intent_types.items():
            intent = Intent(type=intent_type, confidence=0.8)
            agent = await orch.agent_router.route(intent)
            assert agent.name == expected_agent, (
                f"Intent '{intent_type}' routed to '{agent.name}' instead of '{expected_agent}'"
            )
