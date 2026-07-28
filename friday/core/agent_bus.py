import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("friday.agent_bus")


@dataclass
class AgentMessage:
    id: str = ""
    sender: str = ""
    recipient: str = ""  # "" = broadcast
    topic: str = "general"
    content: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    reply_to: str = ""
    created_at: str = ""


class AgentBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_inboxes"):
            return
        self._inboxes: dict[str, list[AgentMessage]] = defaultdict(list)
        self._subscriptions: dict[str, set[str]] = defaultdict(set)

    def subscribe(self, agent_name: str, topic: str = "general"):
        self._subscriptions[topic].add(agent_name)
        logger.debug("Agent '%s' subscribed to '%s'", agent_name, topic)

    def unsubscribe(self, agent_name: str, topic: str = "general"):
        self._subscriptions[topic].discard(agent_name)

    def send(self, sender: str, content: str, recipient: str = "",
             topic: str = "general", reply_to: str = "",
             data: dict | None = None) -> str:
        msg = AgentMessage(
            id=uuid.uuid4().hex[:8],
            sender=sender,
            recipient=recipient,
            topic=topic,
            content=content,
            data=data or {},
            reply_to=reply_to,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        if recipient:
            self._inboxes[recipient].append(msg)
        elif topic:
            for agent in self._subscriptions.get(topic, set()):
                if agent != sender:
                    self._inboxes[agent].append(msg)
        logger.info("Message %s: %s -> %s (%s)", msg.id[:6], sender, recipient or f"topic:{topic}", topic)
        return msg.id

    def receive(self, agent_name: str, clear: bool = True) -> list[AgentMessage]:
        msgs = list(self._inboxes.get(agent_name, []))
        if clear:
            self._inboxes[agent_name] = []
        return msgs

    def request_reply(self, sender: str, recipient: str, content: str,
                      topic: str = "general", timeout: float = 10.0) -> str:
        msg_id = self.send(sender, content, recipient=recipient, topic=topic)
        return msg_id

    def count(self) -> int:
        return sum(len(msgs) for msgs in self._inboxes.values())
