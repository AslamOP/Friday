import pytest
from friday.core.agent_bus import AgentBus, AgentMessage


@pytest.fixture(autouse=True)
def reset():
    AgentBus._instance = None
    yield
    AgentBus._instance = None


class TestAgentBus:
    def test_send_to_recipient(self):
        bus = AgentBus()
        msg_id = bus.send("alice", "hello", recipient="bob")
        assert msg_id is not None
        msgs = bus.receive("bob")
        assert len(msgs) == 1
        assert msgs[0].content == "hello"
        assert msgs[0].sender == "alice"

    def test_receive_clears_inbox_by_default(self):
        bus = AgentBus()
        bus.send("alice", "msg1", recipient="bob")
        bus.send("alice", "msg2", recipient="bob")
        assert len(bus.receive("bob")) == 2
        assert len(bus.receive("bob")) == 0

    def test_receive_without_clear(self):
        bus = AgentBus()
        bus.send("alice", "msg", recipient="bob")
        assert len(bus.receive("bob", clear=False)) == 1
        assert len(bus.receive("bob", clear=False)) == 1

    def test_broadcast_to_topic(self):
        bus = AgentBus()
        bus.subscribe("agent1", "updates")
        bus.subscribe("agent2", "updates")
        bus.send("broadcaster", "alert!", topic="updates")
        assert len(bus.receive("agent1")) == 1
        assert len(bus.receive("agent2")) == 1

    def test_sender_does_not_receive_own_broadcast(self):
        bus = AgentBus()
        bus.subscribe("agent1", "news")
        bus.send("agent1", "self", topic="news")
        assert len(bus.receive("agent1")) == 0

    def test_message_fields(self):
        bus = AgentBus()
        mid = bus.send("alice", "data msg", recipient="bob", topic="test",
                       reply_to="orig", data={"key": "val"})
        msgs = bus.receive("bob")
        m = msgs[0]
        assert m.id == mid
        assert m.sender == "alice"
        assert m.recipient == "bob"
        assert m.topic == "test"
        assert m.reply_to == "orig"
        assert m.data == {"key": "val"}

    def test_count(self):
        bus = AgentBus()
        assert bus.count() == 0
        bus.send("a", "1", recipient="b")
        bus.send("a", "2", recipient="c")
        assert bus.count() == 2

    def test_unsubscribe(self):
        bus = AgentBus()
        bus.subscribe("agent1", "alerts")
        bus.unsubscribe("agent1", "alerts")
        bus.send("admin", "test", topic="alerts")
        assert len(bus.receive("agent1")) == 0
