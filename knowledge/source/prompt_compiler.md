PROMPT COMPILER — BLOCKS, CONFLICTS & BUDGET  
Updated: 2026-08-17

GOAL  
Compile a controllable NovelAI prompt from researched intent. The compiler should prefer a small number of high-confidence controls over an unbounded wall of synonyms.

0\. PRECOMPILE CHECK  
Resolve model/version.  
Check Add Quality Tags toggle when relevant.  
Check whether the request is single-character or multi-character.  
If an existing character/franchise is named, research identity before compilation.  
Resolve unknown/canonical tag questions before pretending they are tags.  
For bot UI questions, keep wrapper steps separate from model prompt construction.

1\. BLOCK ORDER  
Use this logical representation even if the final output is a comma-separated prompt:  
A. STYLE / MEDIUM / RENDERING  
B. GLOBAL SCENE / LOCATION / TIME  
C. SUBJECT COUNT / SUBJECT TYPE  
D. CHARACTER IDENTITY  
E. APPEARANCE  
F. OUTFIT / ACCESSORIES  
G. EXPRESSION \+ EYE/MOUTH STATE  
H. ACTION / INTERACTION  
I. POSE / POSTURE  
J. CAMERA / FRAMING / VIEW ANGLE  
K. LIGHTING / EFFECTS  
L. SMALL CRITICAL DETAILS  
Do not force every block to be present.

STYLE PLACEMENT NOTE  
Official NovelAI art-style guidance says strong style tags should be close enough to the beginning to influence the image. If the target style is washed out, check conflicts with Add Quality Tags / very aesthetic / aesthetic before escalating weights.

2\. MULTI-CHARACTER SPLIT  
BASE PROMPT:  
\- global scene  
\- subject counts  
\- global style/rendering  
\- shared lighting/environment  
\- global interaction context if needed  
CHARACTER PROMPTS:  
\- per-character identity  
\- appearance  
\- outfit  
\- expression  
\- character-specific action/pose  
For V4/V4.5, use character prompt boxes when available; the alternate documented syntax may use | separators. Do not use legacy V3 Prompt Mixing semantics for |.  
For directed actions, use official source\# / target\# / mutual\# syntax when useful.

3\. EVIDENCE-GATED TOKEN CLASSES  
CLASS A — VERIFIED\_NAI\_DOC  
May be used as known NovelAI vocabulary when semantically correct.  
CLASS B — VERIFIED\_TAG\_SOURCE  
Canonical booru vocabulary; may be proposed as a tag, but NovelAI knowledge remains separate unless independently verified.  
CLASS C — PROSE\_COMMUNITY\_CONCEPT  
Descriptive phrase not confirmed as canonical tag. Keep as prose if useful; never label it a Danbooru tag.  
CLASS D — EXPERIMENTAL/MESH  
Community or A/B-tested recipe. Preserve provenance and do not treat weights as universal.  
CLASS E — UNKNOWN  
Research or omit/use prose fallback. Never invent canonical status.

4\. DEDUPLICATION PASS  
Collapse exact duplicates.  
Collapse formatting-only variants.  
Remove redundant synonyms when one stronger/clearer control exists.  
Keep two similar concepts only if they control different dimensions.  
Examples:  
\- smile \+ parted\_lips can coexist: expression \+ mouth state.  
\- from\_above \+ looking\_down can coexist: camera \+ gaze/head direction.  
\- close-up \+ portrait may be redundant depending on target framing; keep the more precise intended framing.  
\- realistic \+ photorealistic may compete/redundantly oversteer; use intentionally, not automatically together.

5\. CONFLICT MATRIX  
HARD / NEAR-HARD CONFLICTS — flag before compilation:  
\- closed\_eyes vs eye-color/gaze controls that require visible eyes  
\- open\_mouth vs closed\_mouth  
\- standing vs sitting vs lying vs kneeling when only one posture is intended  
\- monochrome vs strongly specified non-grey color palette, unless intentional selective color  
\- single-subject count vs multiple-character requirements  
\- from\_behind vs face-detail requirements when the face must be visible  
\- profile vs frontal face requirement

SOFT CONFLICTS — can coexist but often dilute control:  
\- multiple competing camera/framing tags  
\- multiple rendering styles with incompatible visual goals  
\- heavy Quality Tags/aesthetic pressure vs a very specific stylization  
\- multiple strong weighted regions  
\- detailed busy background vs strict character/detail focus  
\- strong depth-of-field/background blur with details that must remain readable in background

SEMANTIC NON-CONFLICTS — do not incorrectly remove:  
\- smile \+ parted\_lips  
\- smirk \+ closed\_mouth when visual target supports it  
\- looking\_at\_viewer \+ from\_below  
\- looking\_down \+ from\_above  
\- standing \+ upper\_body (posture \+ framing)  
\- black\_hair \+ short\_hair (color \+ length)

6\. CAMERA SEMANTIC CHECK  
Separate:  
FRAMING — close-up, portrait, upper body, cowboy shot, full body, pov.  
VIEW ANGLE — from above, from below, from side, from behind, profile.  
SUBJECT GAZE/HEAD — looking at viewer, looking at another, looking up/down.  
Do not replace one category with another.

7\. EXPRESSION SEMANTIC CHECK  
Separate:  
EMOTION/EXPRESSION — smile, smirk, blush, etc.  
MOUTH STATE — open\_mouth, closed\_mouth, parted\_lips, tongue\_out.  
EYE STATE — closed\_eyes, half-closed\_eyes, etc.  
RELATIONAL GAZE — eye\_contact, looking\_at\_another.  
Compatible controls from different categories may be combined.

8\. LIGHTING / EFFECT NORMALIZATION  
Before emitting a phrase as a Danbooru tag, check the Lighting/Effects Normalization table.  
Known prose/community phrases such as cinematic lighting, rim lighting, soft lighting, dramatic lighting and volumetric lighting must not be presented as canonical booru tags unless later verified.  
Where precise semantics matter, use separately verified concepts such as backlighting, sidelighting, sunlight, light rays, sunbeam, depth of field, bokeh, film grain, bloom, lens flare, soft focus, etc., only when they actually match the requested effect.  
Do not substitute a nearby verified tag merely to avoid prose.

9\. WEIGHTING PASS  
First attempt: unweighted high-confidence prompt.  
Only add emphasis when:  
\- an important concept is repeatedly ignored;  
\- a style must overcome competing style pressure;  
\- controlled A/B evidence supports the adjustment.  
Official V4+ numeric emphasis: NUMBER::content ::.  
V4.5+ may use negative numerical emphasis for targeted removal.  
Brackets { } / \[ \] remain available focus controls.  
Never inherit extreme community weights without testing.

10\. QUALITY-TAG PASS  
If Add Quality Tags is ON, avoid duplicating the model-specific automatic quality block unless deliberate.  
If a strong style target is being overridden, test Quality Tags OFF or reduce competing aesthetic pressure before adding more style synonyms.

11\. UNDESIRED CONTENT PASS  
Use UC for broad recurring unwanted features and model/preset-level exclusions.  
Use targeted negative emphasis for a specific concept when appropriate on supported models.  
Do not create giant generic negative walls by default.  
Check preset interactions: a requested visual effect may conflict with a UC preset.

12\. BUDGET POLICY  
The V4.5 model context is finite; base \+ character prompts share the available T5 context.  
Default compiler goal: concise enough that every major token has a reason to exist.  
Budget priority:  
1\. subject identity/count  
2\. critical appearance/character separation  
3\. required action/pose  
4\. camera/framing  
5\. core style  
6\. required environment/light  
7\. decorative effects/details  
When trimming, remove low-impact decoration and synonyms before critical identity/action controls.

13\. MINIMAL-PATCH MODE  
For /fix, do not regenerate the whole prompt unless structurally broken.  
Return:  
KEEP — blocks already working.  
REMOVE — conflicts/redundancy.  
CHANGE — minimal substitutions/weight adjustments.  
ADD — only missing controls needed for the diagnosed failure.  
TEST — one controlled next-generation change.  
Lock Seed where possible.

14\. COMPILER OUTPUT  
MODEL  
ASSUMPTIONS / TOGGLES  
VERIFIED CONTROLS  
BASE PROMPT  
CHARACTER PROMPT(S), if needed  
UNDESIRED CONTENT  
SETTINGS STATUS: OFFICIAL / OBSERVED / EXPERIMENTAL  
CONFLICTS REMOVED  
UNCERTAIN / PROSE FALLBACKS  
NEXT A/B TEST

15\. FAILURE RULE  
If an exact canonical tag cannot be confirmed, the compiler must prefer honest prose over a fabricated booru tag.  
If two sources disagree, current official NovelAI documentation wins on model mechanics; verified tag-source metadata wins on Danbooru naming/semantics; Telegram remains evidence of wrapper/community behavior, not authority over either.  
