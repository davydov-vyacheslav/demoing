#import "demo-maker.typ": *
#show: theme.with(logo: logo-path)

#title-slide([Demo Maker v0.1.4], subtitle: [Leaner, More Reliable, Better Prepared], author: [Slava - Demo Maker Team])

#pagebreak()

== Agenda

- PDF page generation - dependency reduction
- Build reliability - output delivery fix
- Audio normalisation - TTS format enforcement
- Live demo
- What's coming next

#pagebreak()

#section-slide([PDF Page Generation], sub: [Removing an unnecessary dependency])

#pagebreak()

== The Old Approach

- `split-pdf` command broke a PDF into one image per slide
- Required `poppler-utils` - a third-party system package
- `poppler-utils` had to be bundled into the Docker image

#v(gap-md)

#bq[Larger Docker images mean slower distribution and deployment]

#img("diagram showing Docker image containing split-pdf and poppler-utils alongside Marp")

#pagebreak()

== The Fix

- Marp - already used to generate the PDF - can produce per-page images directly
- `split-pdf` command has been removed
- `poppler-utils` dependency has been removed

#v(gap-md)

=== Result

- Smaller Docker image
- Faster deployment
- One less dependency to maintain

#pagebreak()

#section-slide([Build Reliability], sub: [Output files that always arrive])

#pagebreak()

== The Problem

- The `build` command merges assets and delivers a final file to an output folder
- The final copy step did not always complete
- Output file sometimes never reached its destination

#v(gap-md)

- A temporary working folder used during the merge was not being cleaned up
- Leftover files accumulated after each run

#pagebreak()

== The Fix

- Final file is now reliably delivered to the correct destination
- Temporary folder is removed once the build completes

#v(gap-md)

#bq[Builds are trustworthy - the output you expect is where you expect it, every time]

#pagebreak()

#section-slide([Audio Normalisation], sub: [Consistent input for TTS synthesis])

#pagebreak()

== Why Format Matters for TTS

- TTS (Text-To-Speech) tools are sensitive to reference audio format
- They expect: mono channel + 24 kHz sample rate
- Mismatched format produces degraded or inconsistent synthesis output

#v(gap-md)

#img("diagram showing audio file format requirements: mono channel, 24 kHz sample rate flowing into TTS engine")

#pagebreak()

== The New Normalise Command

- A new command accepts a reference audio file and normalises it automatically
- Converts to mono
- Sets sample rate to 24 kHz

#v(gap-md)

=== Benefit

- Removes a manual preparation step previously left to the operator
- TTS stage always receives audio in the correct format

#pagebreak()

#section-slide([Live Demo], sub: [Seeing the changes in practice])

#pagebreak()

#section-slide([What's Next], sub: [The road ahead])

#pagebreak()

== Whisper Integration

- Whisper transcribes spoken audio into text, feeding back into the workflow
- Two options under evaluation:

#v(gap-md)

=== WhisperKit (preferred candidate)
- Lightweight alternative, installable via Brew
- No Python dependencies

=== Faster-Whisper
- Remains available as a fallback

#pagebreak()

== Voice Generation Pipeline

- Defining and documenting the end-to-end steps to produce synthesised speech from text
- Lays the groundwork for a consistent, repeatable audio pipeline

#v(gap-md)

#img("diagram of end-to-end voice generation pipeline: text input, normalisation, TTS synthesis, audio output")

#pagebreak()

== Summary

- *PDF generation* - smaller image, fewer dependencies
- *Build reliability* - output is always delivered, temp files cleaned up
- *Audio normalisation* - TTS always receives correctly formatted input

#v(gap-md)

#bq[Demo Maker v0.1.4 is leaner, more predictable, and better prepared for the audio pipeline ahead]

#pagebreak()

#closing-slide([Thanks! Ciao.], sub: [Questions welcome], meta: [Slava - Demo Maker Team - v0.1.4])
