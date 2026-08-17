from __future__ import annotations

import csv
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def norm(value: str) -> str:
    value = str(value or "").strip().lower().replace("_", " ")
    return " ".join(value.split())


def _phrase(value: str) -> str:
    return " ".join(TOKEN_RE.findall(norm(value)))


def phrase_present(haystack: str, needle: str) -> bool:
    h = _phrase(haystack)
    n = _phrase(needle)
    return bool(n) and (f" {n} " in f" {h} " or h == n)


def _split_aliases(value: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in str(value or "").split("|") if x.strip())


@dataclass(frozen=True)
class TagRecord:
    canonical_tag: str
    evidence_type: str
    model_applicability: str
    source_url: str
    notes: str


@dataclass(frozen=True)
class ConceptRecord:
    canonical: str
    category: str
    evidence: str
    aliases_ru: tuple[str, ...]
    aliases_en: tuple[str, ...]
    source: str
    notes: str

    @property
    def aliases(self) -> tuple[str, ...]:
        return (self.canonical, *self.aliases_ru, *self.aliases_en)


@dataclass(frozen=True)
class RuleRecord:
    rule_id: str
    triggers: tuple[str, ...]
    categories: tuple[str, ...]
    guidance: str
    priority: int
    source: str


@dataclass(frozen=True)
class ExampleRecord:
    example_id: str
    triggers: tuple[str, ...]
    categories: tuple[str, ...]
    pattern: str
    evidence: str
    source: str


@dataclass(frozen=True)
class RetrievedCandidate:
    canonical: str
    category: str
    evidence: str
    source: str
    notes: str
    score: float
    matched_by: str
    required: bool = False


@dataclass(frozen=True)
class RetrievalPack:
    candidates: tuple[RetrievedCandidate, ...]
    rules: tuple[RuleRecord, ...]
    examples: tuple[ExampleRecord, ...]
    locks: dict[str, str]

    @property
    def required(self) -> tuple[RetrievedCandidate, ...]:
        return tuple(x for x in self.candidates if x.required)

    def format_for_model(self) -> str:
        lines: list[str] = ["RETRIEVAL / INTENT PACK"]

        if self.required:
            lines.append("REQUIRED USER CONCEPTS — preserve all:")
            for item in self.required:
                lines.append(
                    f"- {item.canonical} | {item.category} | {item.evidence}"
                )

        suggested = [x for x in self.candidates if not x.required]
        if suggested:
            lines.append("SUGGESTED CONTROLS — use only when they help:")
            for item in suggested:
                lines.append(
                    f"- {item.canonical} | {item.category} | {item.evidence}"
                )

        lines.append("LOCKS:")
        for key, value in self.locks.items():
            lines.append(f"- {key}: {value}")

        if self.rules:
            lines.append("RELEVANT SEMANTIC RULES:")
            for rule in self.rules:
                lines.append(f"- {rule.guidance}")

        if self.examples:
            lines.append("RELEVANT CONSTRUCTION PATTERNS — structure only, not canonical proof:")
            for example in self.examples:
                lines.append(f"- {example.pattern}")

        return "\n".join(lines)


class KnowledgeBase:
    def __init__(self, root: Path):
        self.root = root
        self.tags: list[TagRecord] = []
        self.by_norm: dict[str, TagRecord] = {}
        self.concepts: list[ConceptRecord] = []
        self.concept_by_norm: dict[str, ConceptRecord] = {}
        self.rules: list[RuleRecord] = []
        self.rule_by_id: dict[str, RuleRecord] = {}
        self.examples: list[ExampleRecord] = []
        self.example_by_id: dict[str, ExampleRecord] = {}
        self.reference_text = ""
        self.prompt_dialect = ""
        self._fts: sqlite3.Connection | None = None
        self._load()

    def _load(self) -> None:
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

        retrieval_dir = self.root / "retrieval"
        concepts_path = retrieval_dir / "concepts.csv"
        if concepts_path.exists():
            with concepts_path.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    canonical = row.get("canonical", "").strip()
                    if not canonical:
                        continue
                    rec = ConceptRecord(
                        canonical=canonical,
                        category=row.get("category", "other").strip() or "other",
                        evidence=row.get("evidence", "UNKNOWN").strip() or "UNKNOWN",
                        aliases_ru=_split_aliases(row.get("aliases_ru", "")),
                        aliases_en=_split_aliases(row.get("aliases_en", "")),
                        source=row.get("source", "").strip(),
                        notes=row.get("notes", "").strip(),
                    )
                    self.concepts.append(rec)
                    for alias in rec.aliases:
                        self.concept_by_norm[norm(alias)] = rec

        rules_path = retrieval_dir / "rules.csv"
        if rules_path.exists():
            with rules_path.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    rule_id = row.get("rule_id", "").strip()
                    if not rule_id:
                        continue
                    rec = RuleRecord(
                        rule_id=rule_id,
                        triggers=_split_aliases(row.get("triggers", "")),
                        categories=_split_aliases(row.get("categories", "")),
                        guidance=row.get("guidance", "").strip(),
                        priority=int(row.get("priority", "0") or 0),
                        source=row.get("source", "").strip(),
                    )
                    self.rules.append(rec)
                    self.rule_by_id[rule_id] = rec

        examples_path = retrieval_dir / "examples.csv"
        if examples_path.exists():
            with examples_path.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    example_id = row.get("example_id", "").strip()
                    if not example_id:
                        continue
                    rec = ExampleRecord(
                        example_id=example_id,
                        triggers=_split_aliases(row.get("triggers", "")),
                        categories=_split_aliases(row.get("categories", "")),
                        pattern=row.get("pattern", "").strip(),
                        evidence=row.get("evidence", "").strip(),
                        source=row.get("source", "").strip(),
                    )
                    self.examples.append(rec)
                    self.example_by_id[example_id] = rec

        source_dir = self.root / "source"
        chunks = []
        for name in (
            "model_profile_v45.md",
            "prompt_compiler.md",
            "knowledge_map.md",
            "telegram_prompt_dialect.md",
            "community_research_sources.md",
        ):
            p = source_dir / name
            if p.exists():
                text = p.read_text(encoding="utf-8", errors="replace")
                chunks.append(text)
                if name == "telegram_prompt_dialect.md":
                    self.prompt_dialect = text.strip()
        self.reference_text = "\n\n---\n\n".join(chunks)
        self._build_fts()

    def _build_fts(self) -> None:
        try:
            conn = sqlite3.connect(":memory:")
            conn.execute(
                "CREATE VIRTUAL TABLE search USING fts5(kind UNINDEXED, key UNINDEXED, body, tokenize='unicode61')"
            )
        except sqlite3.OperationalError:
            self._fts = None
            return

        for rec in self.tags:
            conn.execute(
                "INSERT INTO search(kind, key, body) VALUES (?, ?, ?)",
                ("tag", norm(rec.canonical_tag), f"{rec.canonical_tag} {rec.notes}"),
            )
        for rec in self.concepts:
            conn.execute(
                "INSERT INTO search(kind, key, body) VALUES (?, ?, ?)",
                (
                    "concept",
                    norm(rec.canonical),
                    " ".join((rec.canonical, *rec.aliases_ru, *rec.aliases_en, rec.notes)),
                ),
            )
        for rec in self.rules:
            conn.execute(
                "INSERT INTO search(kind, key, body) VALUES (?, ?, ?)",
                ("rule", rec.rule_id, " ".join((*rec.triggers, rec.guidance))),
            )
        for rec in self.examples:
            conn.execute(
                "INSERT INTO search(kind, key, body) VALUES (?, ?, ?)",
                ("example", rec.example_id, " ".join((*rec.triggers, rec.pattern))),
            )
        conn.commit()
        self._fts = conn

    def resolve(self, text: str) -> TagRecord | None:
        return self.by_norm.get(norm(text))

    def resolve_concept(self, text: str) -> ConceptRecord | None:
        return self.concept_by_norm.get(norm(text))

    def resolve_any(self, text: str) -> TagRecord | ConceptRecord | None:
        return self.resolve(text) or self.resolve_concept(text)

    @staticmethod
    def is_uc_record(rec: TagRecord) -> bool:
        evidence = rec.evidence_type.upper()
        return (
            "UC_CONCEPT" in evidence
            or "_AND_UC" in evidence
            or evidence.startswith("DOCUMENTED_UC")
        )

    def _fts_hits(self, intent: str, limit: int = 30) -> list[tuple[str, str]]:
        if self._fts is None:
            return []
        tokens = []
        seen = set()
        for token in TOKEN_RE.findall(norm(intent)):
            token = token.strip("-")
            if len(token) < 3 or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
        if not tokens:
            return []
        query = " OR ".join(f'"{token}"' for token in tokens[:24])
        try:
            rows = self._fts.execute(
                "SELECT kind, key FROM search WHERE search MATCH ? ORDER BY bm25(search) LIMIT ?",
                (query, int(limit)),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        return [(str(kind), str(key)) for kind, key in rows]

    def _locks(self, intent: str, required: list[RetrievedCandidate]) -> dict[str, str]:
        text = norm(intent)
        required_categories = {x.category for x in required}

        def has_any(values: tuple[str, ...]) -> bool:
            return any(phrase_present(text, x) for x in values)

        appearance = (
            "USER_SPECIFIED"
            if has_any(
                (
                    "волос", "глаз", "кожа", "груд", "бедр", "рост", "телослож",
                    "hair", "eyes", "skin", "breasts", "hips", "body type",
                )
            )
            else "UNSPECIFIED_DO_NOT_INVENT"
        )
        outfit = (
            "USER_SPECIFIED"
            if has_any(("одет", "одеж", "рубаш", "плать", "юбк", "брюк", "бель", "wearing", "shirt", "dress", "skirt", "pants", "outfit"))
            else "UNSPECIFIED_DO_NOT_INVENT"
        )
        style = (
            "USER_SPECIFIED"
            if has_any(("стиль", "аниме", "реалист", "фото", "манхва", "style", "anime", "realistic", "photo"))
            else "UNSPECIFIED_DO_NOT_INVENT"
        )
        camera = (
            "USER_SPECIFIED"
            if "camera" in required_categories
            else "UNSPECIFIED_NO_DECORATIVE_CAMERA"
        )
        lighting = (
            "USER_SPECIFIED"
            if "lighting" in required_categories or has_any(("свет", "освещ", "lighting", "backlight", "rim light"))
            else "UNSPECIFIED_DO_NOT_INVENT"
        )
        partner_gender = (
            "USER_SPECIFIED"
            if has_any(("1boy", "парень", "мужчина", "male partner", "man behind", "другая девушка", "женщина сзади"))
            else "UNSPECIFIED_DO_NOT_INFER"
        )
        return {
            "appearance": appearance,
            "outfit": outfit,
            "style": style,
            "camera": camera,
            "lighting": lighting,
            "partner_gender": partner_gender,
        }

    def retrieve(self, intent: str, limit: int = 10) -> RetrievalPack:
        limit = max(0, min(int(limit), 24))
        scored: dict[str, RetrievedCandidate] = {}

        def add_candidate(
            canonical: str,
            category: str,
            evidence: str,
            source: str,
            notes: str,
            score: float,
            matched_by: str,
            required: bool,
        ) -> None:
            key = norm(canonical)
            current = scored.get(key)
            candidate = RetrievedCandidate(
                canonical=canonical,
                category=category,
                evidence=evidence,
                source=source,
                notes=notes,
                score=score,
                matched_by=matched_by,
                required=required,
            )
            if current is None or (candidate.required, candidate.score) > (current.required, current.score):
                scored[key] = candidate

        for rec in self.tags:
            if phrase_present(intent, rec.canonical_tag):
                add_candidate(
                    rec.canonical_tag,
                    "verified",
                    rec.evidence_type,
                    rec.source_url,
                    rec.notes,
                    260 + len(_phrase(rec.canonical_tag)),
                    "verified-exact",
                    True,
                )

        for rec in self.concepts:
            matched_alias = ""
            for alias in sorted(rec.aliases, key=lambda x: len(_phrase(x)), reverse=True):
                if phrase_present(intent, alias):
                    matched_alias = alias
                    break
            if matched_alias:
                add_candidate(
                    rec.canonical,
                    rec.category,
                    rec.evidence,
                    rec.source,
                    rec.notes,
                    320 + len(_phrase(matched_alias)),
                    f"alias:{matched_alias}",
                    True,
                )

        fts_hits = self._fts_hits(intent, limit=max(20, limit * 4))
        for idx, (kind, key) in enumerate(fts_hits):
            score = 90 - idx
            if kind == "tag":
                rec = self.by_norm.get(key)
                if rec:
                    add_candidate(
                        rec.canonical_tag,
                        "verified",
                        rec.evidence_type,
                        rec.source_url,
                        rec.notes,
                        score,
                        "fts5",
                        False,
                    )
            elif kind == "concept":
                rec = self.concept_by_norm.get(key)
                if rec:
                    add_candidate(
                        rec.canonical,
                        rec.category,
                        rec.evidence,
                        rec.source,
                        rec.notes,
                        score,
                        "fts5",
                        False,
                    )

        ordered = sorted(
            scored.values(),
            key=lambda x: (-int(x.required), -x.score, x.canonical),
        )
        required = [x for x in ordered if x.required]
        suggested = [x for x in ordered if not x.required]
        candidate_limit = max(limit, len(required))
        candidates = tuple((required + suggested)[:candidate_limit])

        active_rules: list[RuleRecord] = []
        active_categories = {x.category for x in candidates}
        for rule in self.rules:
            trigger_match = not rule.triggers or any(phrase_present(intent, t) for t in rule.triggers)
            category_match = not rule.categories or "all" in rule.categories or bool(active_categories.intersection(rule.categories))
            if trigger_match and category_match:
                active_rules.append(rule)
        active_rules.sort(key=lambda r: (-r.priority, r.rule_id))
        active_rules = active_rules[:8]

        example_scores: list[tuple[int, ExampleRecord]] = []
        for example in self.examples:
            score = sum(1 for t in example.triggers if phrase_present(intent, t))
            if score:
                example_scores.append((score, example))
        example_scores.sort(key=lambda x: (-x[0], x[1].example_id))
        selected_examples = tuple(x[1] for x in example_scores[:3])

        locks = self._locks(intent, required)
        return RetrievalPack(
            candidates=candidates,
            rules=tuple(active_rules),
            examples=selected_examples,
            locks=locks,
        )

    def select_tags(self, intent: str, limit: int = 8) -> list[TagRecord]:
        """Compatibility helper backed by the multilingual retrieval engine."""
        if limit <= 0:
            return []
        pack = self.retrieve(intent, limit=limit)
        out: list[TagRecord] = []
        seen: set[str] = set()
        for item in pack.candidates:
            rec = self.resolve(item.canonical)
            if rec is None:
                continue
            key = norm(rec.canonical_tag)
            if key in seen:
                continue
            seen.add(key)
            out.append(rec)
            if len(out) >= limit:
                break
        return out

    @staticmethod
    def format_tag_context(records: list[TagRecord]) -> str:
        return "\n".join(
            f"- {r.canonical_tag} | {r.evidence_type} | {r.notes}" for r in records
        )
