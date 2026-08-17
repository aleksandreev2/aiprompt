from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


@dataclass(frozen=True)
class TagRecord:
    canonical_tag: str
    evidence_type: str
    model_applicability: str
    source_url: str
    notes: str


def norm(value: str) -> str:
    value = value.strip().lower().replace("_", " ")
    return " ".join(value.split())


class KnowledgeBase:
    def __init__(self, root: Path):
        self.root = root
        self.tags: list[TagRecord] = []
        self.by_norm: dict[str, TagRecord] = {}
        self.reference_text = ""
        self.prompt_dialect = ""
        self._load()

    def _load(self) -> None:
        # Repository-friendly format: the verified core may be split into several
        # small CSV shards under knowledge/tags/. A single verified_tags.csv is
        # still supported for local exports/backward compatibility.
        tag_dir = self.root / "tags"
        csv_paths = sorted(tag_dir.glob("*.csv")) if tag_dir.exists() else []
        if not csv_paths:
            csv_paths = [self.root / "verified_tags.csv"]

        for csv_path in csv_paths:
            if not csv_path.exists():
                continue
            with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    if not row.get("canonical_tag"):
                        continue
                    record = TagRecord(
                        canonical_tag=row.get("canonical_tag", "").strip(),
                        evidence_type=row.get("evidence_type", "").strip(),
                        model_applicability=row.get("model_applicability", "").strip(),
                        source_url=row.get("source_url", "").strip(),
                        notes=row.get("notes", "").strip(),
                    )
                    self.tags.append(record)
                    self.by_norm[norm(record.canonical_tag)] = record

        source_dir = self.root / "source"
        chunks = []
        for name in (
            "model_profile_v45.md",
            "prompt_compiler.md",
            "knowledge_map.md",
            "telegram_prompt_dialect.md",
        ):
            p = source_dir / name
            if p.exists():
                text = p.read_text(encoding="utf-8", errors="replace")
                chunks.append(text)
                if name == "telegram_prompt_dialect.md":
                    self.prompt_dialect = text.strip()
        self.reference_text = "\n\n---\n\n".join(chunks)

    def resolve(self, text: str) -> TagRecord | None:
        return self.by_norm.get(norm(text))

    @staticmethod
    def is_uc_record(rec: TagRecord) -> bool:
        evidence = rec.evidence_type.upper()
        return (
            "UC_CONCEPT" in evidence
            or "_AND_UC" in evidence
            or evidence.startswith("DOCUMENTED_UC")
        )

    def select_tags(self, intent: str, limit: int = 8) -> list[TagRecord]:
        """Return only verified vocabulary that genuinely matches user wording.

        This verified lookup is intentionally narrow and is never used as an
        allowlist. Corpus-observed prompt patterns live in a separate runtime
        reference so evidence classes do not get mixed together.
        """
        if limit <= 0:
            return []

        intent_norm = norm(intent)
        intent_phrase = " ".join(TOKEN_RE.findall(intent_norm))
        padded_intent = f" {intent_phrase} "
        scored: list[tuple[int, TagRecord]] = []
        seen_norms: set[str] = set()

        for rec in self.tags:
            tag_norm = norm(rec.canonical_tag)
            tag_phrase = " ".join(TOKEN_RE.findall(tag_norm))
            if not tag_phrase or tag_phrase in seen_norms:
                continue

            if f" {tag_phrase} " in padded_intent or tag_phrase == intent_phrase:
                score = 100 + len(tag_phrase)
                preferred = self.by_norm.get(tag_phrase, rec)
                scored.append((score, preferred))
                seen_norms.add(tag_phrase)

        scored.sort(key=lambda x: (-x[0], x[1].canonical_tag))
        return [rec for _, rec in scored[:limit]]

    @staticmethod
    def format_tag_context(records: list[TagRecord]) -> str:
        return "\n".join(
            f"- {r.canonical_tag} | {r.evidence_type} | {r.notes}" for r in records
        )
