MODEL PROFILE — NOVELAI DIFFUSION V4.5 FULL

Status: official-first production reference. Re-check current NovelAI documentation when the user asks for “latest” behavior or when UI/model behavior may have changed.

1. Model role

V4.5 Full is the primary general-purpose V4.5 anime image model profile for this project unless the user selects another NovelAI model.  
It is designed for stronger prompt adherence, character/background handling and natural-language prompting than older generations.

2. Prompt context

V4.5 uses T5 prompt processing.  
The base prompt and character prompts share roughly 512 T5 tokens of usable context.  
Practical rule: keep prompts compact; character prompts consume the same shared context budget.

3. Quality Tags

Always check the Add Quality Tags toggle.  
For V4.5 Full, the current automatic quality preamble includes:  
location, very aesthetic, masterpiece, no text

Do not automatically duplicate these tokens in the user prompt when the toggle is enabled unless controlled testing shows a reason.

4. Tag knowledge and prose

NovelAI supports known tags and natural-language description.  
Prefer known/verified tags for precise visual concepts.  
Use prose for relational, nuanced or uncertain concepts when a canonical tag is not verified.  
Do not invent Danbooru tags to make the prompt look more technical.

5. Strengthening and weakening

Curly braces { } strengthen and square brackets [ ] weaken by roughly 1.05 per layer.  
V4+ numerical emphasis supports forms such as:  
1.5::concept ::  
0.5::concept ::

V4.5+ also supports negative numerical emphasis for targeted removal/inversion, for example:  
-1::unwanted concept ::

Close every numerical emphasis section with ::.  
Use large weights only as experiments, not defaults.

6. Multi-character prompting

V4+ supports up to six character prompts.  
Base prompt should carry:  
subject count  
scene/environment  
camera/composition  
shared lighting/style  
relationship context that is global

Character prompts should carry:  
character identity  
appearance  
outfit  
per-character pose/action/expression

In character prompts use boy/girl/other rather than numbered subject-count tags.  
The base prompt may use numbered count tags such as 2boys.

For directional interactions, current official action prefixes include:  
source#action  
target#action  
mutual#action

Treat interaction syntax as helpful but not perfectly deterministic; test difficult interactions.

7. Undesired Content

Inspect the selected V4.5 UC preset before adding a custom wall of negatives.  
Use UC for broad recurring failure classes.  
Use negative numerical emphasis for one targeted unwanted concept when appropriate.  
Avoid duplicating large preset contents without a specific observed problem.

8. Sampling and Steps

Official NovelAI documentation currently recommends DPM++ 2M and Euler Ancestral as useful general sampler choices.  
Do not infer that the most frequent sampler in Telegram is objectively best.

During composition search, keep Steps relatively low so variants are cheaper/faster to test; increase only after composition stabilizes.

9. Prompt Guidance

Prompt Guidance controls how strongly the model follows the prompt.  
NovelAI documentation gives roughly 5–6 as a general V3+ starting region, while emphasizing experimentation.  
Very high Guidance can create adverse artifacts or reduce image quality.  
Treat guidance as a controlled variable, not a quality slider.

10. Text rendering

For V4+, when visible text is intended, use relevant text concepts such as text / english text and place a clear Text: … instruction near the end of the base prompt.  
Short intended text can conflict with automatic “no text” from Quality Tags. Check that toggle/preamble before debugging the text itself.

11. Dataset/special tags

Special tags documented for current NovelAI models include aesthetic/quality, year and dataset/location-related concepts.  
Dataset tags that globally steer the image belong at the front of the prompt when used.  
Do not copy old V3 ordering folklore into V4.5 as a universal numerical weighting rule.

12. Default Project GPT behavior

When model is V4.5 Full:  
- assume official V4.5 mechanics, not Telegram folklore;  
- check Quality Tags state;  
- use character prompts for multi-character complexity;  
- prefer moderate weighting;  
- keep shared T5 context in mind;  
- debug by changing one variable at a time;  
- label Telegram settings as OBSERVED, not recommended.

Official reference families used for this profile:  
NovelAI Image Generation — Models  
NovelAI Image Generation — Tags  
Quality Tags  
Strengthening & Weakening  
Multiple Characters  
Steps  
Prompt Guidance  
Sampling  
Undesired Content  
Text generation guidance
