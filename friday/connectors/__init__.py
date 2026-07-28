"""Data source connectors for Deep Research."""

from friday.connectors._stubs import (
    Attachment,
    BaseConnector,
    Document,
    SyncStatus,
)
from friday.connectors.store import KnowledgeStore

__all__ = ["Attachment", "BaseConnector", "Document", "KnowledgeStore", "SyncStatus"]

# Auto-register built-in connectors
import friday.connectors.obsidian  # noqa: F401

try:
    import friday.connectors.gmail  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.gmail_imap  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.gdrive  # noqa: F401
except ImportError:
    pass  # httpx may not be installed

try:
    import friday.connectors.notion  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.granola  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.gcontacts  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.imessage  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.apple_notes  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.apple_music  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.apple_contacts  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.slack_connector  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.outlook  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.gcalendar  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.dropbox  # noqa: F401
except ImportError:
    pass  # httpx may not be installed

try:
    import friday.connectors.whatsapp  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.oura  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.apple_health  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.strava  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.spotify  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.google_tasks  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.weather  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.github_notifications  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.hackernews  # noqa: F401
except ImportError:
    pass

try:
    import friday.connectors.news_rss  # noqa: F401
except ImportError:
    pass
