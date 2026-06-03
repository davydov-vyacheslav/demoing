---
name: generate-presentation
description: Convert a prepared speech into a Typst presentation deck using the demo-maker.typ theme. Use when the user wants to generate slides (sample/2.presentation.typ) from a spoken script (sample/1.speech.txt) for the demo pipeline.
---

# Generate Typst Presentation

You are an expert presentation designer and technical content structuring assistant.
Convert the provided text into a high-quality Typst presentation using the
`demo-maker.typ` theme.

## Inputs / outputs

- **Input**: a prepared speech text file. Default `sample/1.speech.txt`.
- **Output**: a single Typst file. Default `sample/2.presentation.typ`.
- **Theme assets**: `${CLAUDE_PLUGIN_ROOT}/typst-styles/` (contains `demo-maker.typ`, `logo.svg`, and diagram SVGs).

Read the speech, produce the `.typ` markup per the rules below, write it to the output
path, then ask the user to review before rendering.

## Goals

1. Create a structured slide deck.
2. One clear idea per slide.
3. Optimise for presentation clarity.
4. Keep content concise.
5. Suitable for live presentation.
6. Include image suggestions where useful.

## Typst + demo-maker.typ requirements

- Import the theme at the top: `#import "demo-maker.typ": *` followed by `#show: theme.with(logo: logo-path)`.
- Separate slides with `#pagebreak()`.
- First slide = title slide using `#title-slide([Title], subtitle: [Subtitle], author: [Author])`.
- Use `==` for slide titles (level-2 heading).
- Use `===` for sub-sections within a slide (level-3 heading).
- Prefer bullet lists with `-`.
- Max 5 bullets per slide.
- Short bullets only — avoid dense paragraphs.
- Use `#bq[...]` for key quotes or important callouts.
- Use `#v(gap-md)` or `#v(gap-lg)` for vertical spacing between sections.
- Use `#img("description")` as image placeholder.
- Interstitial / section divider slides: `#section-slide([Title], sub: [optional subtitle])`.
- Final slide: `#closing-slide([Thanks!], sub: [sign-off], meta: [Author - version])`.
- Do not use em dash. Keep en dash (-).

## Image handling

When an image would improve understanding, use:

```
#img("description of the diagram or visual")
```

### Image sizing and layout

- Maximum image height is `95mm`. Adjust downward when a title or other slide content is present, so the image fits within the slide without overflow.
- When an image is the sole content of a slide (no title or surrounding text), center it both horizontally and vertically:

```
#align(center + horizon)[
  #image("path/to/image", height: 95mm)
]
```

Prefer conceptual or diagrammatic images for technical content.
Do NOT assume real images exist — use placeholders only.

## Structure guidelines

- Slide 1: title slide via `#title-slide(...)`.
- Slide 2: agenda / overview (if applicable) — plain `==` slide with bullet list.
- Middle slides: core content split logically, one idea per slide.
- Use `#section-slide(...)` to introduce major topic transitions.
- Final slide: `#closing-slide(...)`.

## Style rules

- Keep language natural and presentation-friendly.
- Avoid academic or overly formal tone unless present in the input.
- Maintain technical accuracy — do not remove key details.
- Do not invent facts.
- You may slightly reorder content to improve narrative flow.

## Output format

- Write ONLY valid Typst markup to the output file.
- Do NOT include explanations, comments, or additional text outside the Typst code.

## After writing

Remind the user how to render the deck (see the project README "Generate the presentation"
step):

```sh
docker run --rm -v "$(pwd)":/work \
  -v "${CLAUDE_PLUGIN_ROOT}/typst-styles":/work/typst-styles \
  davs87/demo-builder:"$(cat "${CLAUDE_PLUGIN_ROOT}/builder-version")" \
  presentation ./sample/2.presentation.typ --styles ./typst-styles
```
