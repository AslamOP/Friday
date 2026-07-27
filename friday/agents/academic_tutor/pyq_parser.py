import re
from dataclasses import dataclass, field
from pathlib import Path
from friday.memory.knowledge_graph import KnowledgeGraph
@dataclass
class PYQEntry:
    question: str = ""; year: int = 0; subject: str = ""; topic: str = ""; marks: int = 0
TOPICS = {
    "Operating Systems": ["deadlock","scheduling","memory","page","process","thread"],
    "DBMS": ["normalization","sql","query","index","transaction","acid","b+ tree"],
    "Networks": ["tcp","ip","udp","http","dns","routing","osi","subnet"],
}
class PYQParser:
    def __init__(self): self._kg = KnowledgeGraph()
    async def parse_pdf(self, path):
        import fitz
        p = Path(path) if isinstance(path, str) else path
        if not p.exists(): return []
        doc = fitz.open(str(p)); text = "\n".join(page.get_text() for page in doc); doc.close()
        entries, cur = [], ""; year = self._year(text); subject = self._subject(text)
        for line in text.split("\n"):
            line = line.strip()
            if not line: continue
            m = re.match(r"^(?:Q\.?\s*|\d+[\.\)])\s*(.+)", line, re.IGNORECASE)
            if m:
                if cur.strip():
                    e = self._build(cur.strip(), year, subject)
                    if e: entries.append(e)
                cur = m.group(1)
            else: cur += " " + line
        if cur.strip():
            e = self._build(cur.strip(), year, subject)
            if e: entries.append(e)
        for e in entries: self._store(e, p.name)
        return entries
    def _build(self, q, y, s):
        if len(q) < 10: return None
        m = re.search(r"(\d+)\s*marks?", q, re.IGNORECASE)
        return PYQEntry(question=q[:500], year=y, subject=s, topic=self._topic(q), marks=int(m.group(1)) if m else 0)
    def _store(self, e, src):
        qid = f"pyq:{src}:{e.year}:{hash(e.question) % 10000}"
        self._kg.add_entity(qid, "pyq_question", {"question": e.question[:200], "year": e.year, "subject": e.subject, "topic": e.topic})
        sid = f"subject:{e.subject.lower().replace(' ','_')}"
        if not self._kg.query_entity(sid): self._kg.add_entity(sid, "subject", {"name": e.subject})
        self._kg.add_relation(qid, sid, "belongs_to")
    def _year(self, text):
        ys = re.findall(r"\b(20\d{2})\b", text)
        return max(int(y) for y in ys if 2020 <= int(y) <= 2030) if ys else 0
    def _subject(self, text):
        t = text.lower()
        scores = {s: sum(2 for kw in kws if kw in t) for s, kws in TOPICS.items()}
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "General"
    def _topic(self, text):
        t = text.lower()
        for s, kws in TOPICS.items():
            for kw in kws:
                if kw in t: return kw.title()
        return "General"
