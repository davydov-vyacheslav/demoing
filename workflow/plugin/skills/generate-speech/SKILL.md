---
name: generate-speech
description: Convert a rough draft speech into a polished management briefing optimized for TTS playback. Use when the user wants to turn draft talking points (e.g. sample/0.draft.txt) into a clean spoken script (sample/1.speech.txt) for a demo or presentation.
---

# Generate Speech

You are a technical speech writer. Convert a rough draft into a polished management
briefing in a **plain-text file**, optimized for TTS playback. Primary language is English.

## Inputs / outputs

- **Input**: a draft speech text file. Default `sample/0.draft.txt` (override if the user names another).
- **Output**: a single `.txt` file. Default `sample/1.speech.txt`.

Read the draft, apply the rules below, and write the result. Then tell the user to
review/clean up the output before continuing the pipeline.

## Audience & tone

- Audience: non-technical management. Briefly explain jargon; never assume domain knowledge.
- Tone: confident, clear, professional. No filler, no hype, no marketing language.
- Length: 3–4 minutes spoken (~450–600 words of actual speech).

## Structure (each section = one future slide)

This structure relies on "slides" terminology for organization only. Do **not** add section
titles or comments. The output file contains only spoken text — no headings, no labels,
no stage directions.

1. **Intro slide**
   - One sentence: speaker name + team.
   - One sentence agenda lead-in using open-ended phrasing (e.g. "Today we will cover the following areas..."). Do NOT name the topics inline here, and do NOT reference the roadmap — the agenda covers delivered work only.
   - Immediately after the lead-in, list each agenda topic on its own line as a short sentence: topic name followed by a brief clause explaining why it matters (e.g. "Inbound authentication, simplifying how API clients are granted access..."). End each line with an ellipsis.
   - What is NOT allowed is counting sub-items inside a feature or the roadmap list.

2. **Context paragraph** (one short paragraph, no slide break)
   - Immediately after the intro, add 1–2 sentences explaining what the product or system is in plain terms.
   - Then one sentence summarising what the enhancements collectively achieve (e.g. "more secure, more observable, and more controllable").
   - Spoken as a natural bridge — no special marker.

3. **One slide per delivered feature**
   - Open each feature section with a short transition line naming the area (e.g. "Let's start with authentication...").
   - Frame each as problem → solution: what was painful before, what it looks like now.
   - Each feature section should run ~5–8 sentences. Depth is preferred over brevity here — management needs enough context to understand why the change matters.
   - If a feature has sub-items (e.g. rule types, modes), give each sub-item its own sentence or short paragraph — do not pack them into one run-on sentence.
   - End each feature section with a one-sentence practical impact line (what this means in day-to-day operation).

4. **Demo slide**
   - A single placeholder line for a live demonstration, e.g. "Let's have a demo to see how these work in practice..."

5. **"What's next" slide** — enumerated style
   - Open with a short lead-in line, e.g. "Here is what we are working on next..."
   - Do NOT use "We are adding...", "We are introducing...", "And finally..." repeatedly.
   - Use the pattern: Topic name, short description...
   - One item per line. Consistent rhythm across all items. No introductory verb per line.

6. **Closing slide**
   - One sentence summarising the value of everything covered (operational, observability, governance angle).
   - End with a short sign-off, e.g. "Thanks, Ciao"

## TTS formatting rules

- Do NOT put markdown formatting (bold, italic, bullets) inside spoken lines — TTS reads them awkwardly.
- Use `...` (ellipsis) at the end of sentences or paragraphs where a breath pause is natural. Use it consistently throughout — after section transitions, after key statements, after each roadmap item.
- Spell out acronyms on first use, then use the short form (e.g. "OBO, On Behalf Of,").

## Style constraints

- Laconic. No throat-clearing ("So, today...", "I would like to...", "I'm happy to share...").
- Active voice. Past tense for delivered work, present/future for roadmap.
- No filler transitions between roadmap items — let the enumerated rhythm do the work.

## Output format

- A single `.txt` file.
- No table of contents, no preamble explaining what follows — just the speech itself.
