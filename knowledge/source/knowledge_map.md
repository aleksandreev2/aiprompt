PROJECT KNOWLEDGE MAP — READ ORDER & PROMOTION

Purpose: prevent raw Telegram material from silently becoming production truth.

READ ORDER FOR PROJECT GPT

TIER 0 — SYSTEM  
06\_PROMPT\_SYSTEM  
\- 00\_GPT\_INSTRUCTIONS — PASTE INTO PROJECT (\<8000)  
\- 01\_COMMAND\_MODES\_AND\_OUTPUT\_SCHEMA — Project GPT  
These control behavior and output shape.

TIER 1 — TRUSTED PRODUCTION KNOWLEDGE  
03\_CLEANED\_KNOWLEDGE  
Read relevant files only:  
\- 00\_VERIFIED\_NOVELAI\_CORE — V4.5/V4  
\- 01\_BOT\_SPECIFIC\_RULES — Telegram Evidence  
\- 02\_PROMPT\_ENGINEERING\_PLAYBOOK — Cleaned  
\- 03\_COMPOSITION\_CAMERA\_LIGHTING — Cleaned Library  
\- 04\_CHARACTER\_OUTFIT\_POSE — Cleaned Library  
\- 05\_FAILURE\_MODES\_AND\_DEBUGGING — Evidence  
\- 06\_MODEL\_PROFILE — NovelAI V4.5 Full  
\- 03\_CURATED\_KNOWLEDGE\_INDEX — Telegram → NovelAI

TIER 2 — VERIFIED TAG LOOKUP  
04\_TAG\_DATABASE  
1\. 01\_VERIFIED\_TAG\_CORE — NovelAI \+ Danbooru  
2\. 00\_TAG\_VALIDATION\_QUEUE — 12.9K Telegram Candidates  
3\. 01\_TAG\_RESEARCH\_PROTOCOL — Danbooru → NovelAI

The validation queue is staging. UNVERIFIED rows must never be treated as production truth.

TIER 3 — CURRENT EXTERNAL RESEARCH  
Use active web research when:  
\- current NovelAI behavior/settings matter;  
\- project cache, normalization libraries and verified core cannot resolve the tag;  
\- alias/deprecation/implication is uncertain;  
\- character canon is still uncertain after checking 07\_CHARACTER\_REFERENCES;  
\- a Telegram claim conflicts with current documentation.

TIER 4 — RAW EVIDENCE  
00\_PROJECT\_CONTROL / corpus indexes and source references  
01\_INBOX\_TELEGRAM\_EXPORT  
02\_RAW\_GUIDES\_AND\_MEDIA  
Use only for provenance, context and discovering claims.  
Never use raw frequency as evidence of correctness.

TIER 5 — ARCHIVE  
99\_ARCHIVE  
Do not use unless explicitly recovering historical context.

PROMOTION PIPELINE

RAW  
↓  
PARSED  
↓  
DEDUPLICATED  
↓  
CLASSIFIED  
↓  
QUARANTINE / KEEP  
↓  
CLAIM EXTRACTION  
↓  
EXTERNAL OR OFFICIAL VERIFICATION  
↓  
EVIDENCE LABEL  
↓  
CURATED KNOWLEDGE  
↓  
VERIFIED CORE where appropriate

PROMOTION RULES

To VERIFIED\_OFFICIAL:  
Current official NovelAI source must support the claim.

To VERIFIED\_TAG\_SOURCE:  
Canonical tag source must show the tag/alias/deprecation/implication.  
This does not prove NovelAI model knowledge.

To OBSERVED:  
Direct generation card, bot output or reproducible observed behavior.  
Observation must include model/settings/date when available.

To BOT\_SPECIFIC:  
Direct admin/bot evidence supports behavior belonging to the Telegram bot rather than NovelAI itself.

To COMMUNITY\_GUIDE:  
Useful instructional claim without sufficient independent verification.

To EXPERIMENTAL:  
Style mesh, weighting recipe, anecdotal setting or result requiring A/B testing.

To REJECTED:  
Joke, misinformation, contradiction, irrelevant chatter, duplicate with no useful delta, or material that should not enter the supported production workflow.

CONFLICT RESOLUTION

Official current NovelAI documentation beats old Telegram advice for NovelAI mechanics.  
Canonical tag metadata beats guessed tag spelling.  
Observed bot behavior beats assumptions about what the bot does, but does not redefine NovelAI.  
Newer model-specific evidence beats older model-general folklore when model versions differ.

DUPLICATION POLICY

Exact duplicate:  
keep one canonical instance \+ count/source references.

Near duplicate:  
keep canonical text \+ record meaningful delta.

Prompt variant:  
keep only when the changed variable teaches something reusable (weight, sampler, framing, style block, failure).

QUALITY GATE BEFORE PROMPT USE

A prompt element may enter final output when at least one is true:  
\- VERIFIED\_OFFICIAL;  
\- VERIFIED\_TAG\_SOURCE and semantically appropriate;  
\- known natural-language concept supported by current NovelAI prompting;  
\- OBSERVED/BOT\_SPECIFIC/EXPERIMENTAL and explicitly labeled when the user is testing it.

Never silently upgrade EXPERIMENTAL to VERIFIED.

MAINTENANCE

When NovelAI releases/changes a model:  
\- re-check model profile;  
\- quality tags;  
\- context/token behavior;  
\- multi-character syntax;  
\- weighting syntax;  
\- UC presets;  
\- sampler/settings recommendations.  
Do not rewrite Telegram history; update current production knowledge and mark old advice with applicability/version notes.

ROUTING EXTENSION — 2026-08-17

TIER 0 / SYSTEM EXECUTION  
06\_PROMPT\_SYSTEM additionally contains:  
\- 02\_MESH\_SYSTEM — Protocol, Validation & Failure Control  
\- 03\_PROMPT\_COMPILER — Blocks, Conflicts & Budget  
Research/validation must pass through the Prompt Compiler before final prompt output. /mesh must use the Mesh System. /fix must use Minimal Patch behavior from the compiler plus Failure Modes.

TIER 1 / CLEANED KNOWLEDGE  
03\_CLEANED\_KNOWLEDGE additionally contains:  
\- 07\_BOT\_WORKFLOW\_AND\_SETTINGS — Evidence  
Use it for wrapper-specific menus, result-card fields, saved characters, Vibes/meta-tags and observed settings. Apply freshness rules; wrapper evidence never overrides official NovelAI mechanics.

TIER 2 / TAG & SEMANTIC LOOKUP  
04\_TAG\_DATABASE read order is now:  
1\. 01\_VERIFIED\_TAG\_CORE — NovelAI \+ Danbooru  
2\. 02\_OFFICIAL\_STYLE\_EFFECTS\_LIBRARY — NovelAI  
3\. 03\_LIGHTING\_EFFECTS\_NORMALIZATION — Verified & Prose  
4\. 04\_EXPRESSION\_GAZE\_POSE\_NORMALIZATION — Verified & Semantic  
5\. 00\_TAG\_VALIDATION\_QUEUE — staging / long tail  
6\. 01\_TAG\_RESEARCH\_PROTOCOL — verification procedure  
Use normalization tables before inventing synonyms. PROSE\_\* entries are valid descriptive fallbacks but must never be presented as canonical Danbooru tags.  
TAG\_SOURCE\_OBSERVED\_MIRROR is weaker than primary VERIFIED\_TAG\_SOURCE and should normally trigger primary-source research before promotion to fast core.

CHARACTER CACHE  
07\_CHARACTER\_REFERENCES / 00\_CHARACTER\_REFERENCE\_SYSTEM — Research Cards  
For a named existing character, consult the card cache before researching from zero. Preserve canonical identity separately from scene overrides. Never infer age from appearance or from prose such as “mature”; age/status requires independent evidence.

AUTOMATION / RE-INGESTION  
09\_TOOLS\_AUTOMATION contains:  
\- NovelAI\_Telegram\_Ingestion\_Toolkit.zip  
\- 00\_TELEGRAM\_INGESTION\_RUNBOOK — Re-run & Promotion  
For future Telegram exports, use this pipeline instead of reconstructing ingestion logic manually. New exports augment the existing verified knowledge base; they do not reset it.

REGRESSION GATE  
08\_TESTS\_AND\_FAILURES / 00\_REGRESSION\_TESTS — Prompt System is mandatory before promotion of a new global rule or semantic normalization. Add a regression case when a newly discovered failure mode could recur.

CURRENT VALIDATION MILESTONE  
As of 2026-08-17, rows 1–200 of 00\_TAG\_VALIDATION\_QUEUE contain no raw UNVERIFIED statuses. Every top-frequency candidate has been classified as official NovelAI vocabulary, primary/secondary tag-source evidence, prose/normalization, experimental mesh content, quarantine, or another explicit non-production state.

MILESTONE UPDATE — 2026-08-17  
Top 400 candidate rows (Validation\_Queue rows 2–401) now contain 0 raw UNVERIFIED statuses in the verification\_status column. Rows 202–401 were independently re-scanned after classification and returned zero matches. Lower-confidence states such as TAG\_RESEARCH\_REQUIRED, PROSE\_\*, CREATOR\_LIKE\_TOKEN\_RESEARCH\_REQUIRED and TAG\_SOURCE\_OBSERVED\_MIRROR remain intentionally outside the fast production core. The fast core has been expanded with only official NovelAI controls and high-utility verified tag-source concepts.

EVIDENCE UPGRADE RULE  
A cautious classification may be upgraded when stronger evidence arrives. Example: wind moved from prose-only to VERIFIED\_TAG\_SOURCE after current tag-source evidence was found.

GPT INSTRUCTIONS SIZE RULE  
The only text intended for the GPT Instructions field is 06\_PROMPT\_SYSTEM / 00\_GPT\_INSTRUCTIONS — PASTE INTO PROJECT (\<8000). The extended project rulebook is reference knowledge inside Drive and must not be pasted into the limited Instructions field.

PROJECT\_ROOT\_LOCK UPDATE — 2026-08-17  
The canonical root for all NovelAI prompt work is NOVELAI\_PROMPT\_LAB. Project-domain tasks must consult this folder before general model memory or external research. Use the smallest authoritative file rather than reading the entire corpus. External web is a verifier/gap-filler after cache lookup, not the default project memory.

CURRENT VALIDATION MILESTONE — TOP 1000  
Validation\_Queue rows 2–1001 contain no raw UNVERIFIED status after the top-1000 routing pass. Rows 602–1001 were converted from raw uncertainty into explicit routing states before further promotion. TAG\_RESEARCH\_REQUIRED remains staging, not verified truth; it tells the project to research only when that term is actually needed. Production prompt generation should prefer Fast Core and specialized normalization libraries instead of scanning the long-tail queue by default.
