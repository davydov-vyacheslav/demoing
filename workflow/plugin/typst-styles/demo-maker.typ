
#let logo-path = "logo.svg"

// ── Colours ───────────────────────────────────────────────────────────────────
#let orange      = rgb("#f58220")
#let dark-orange = rgb("#cc6600")
#let muted       = rgb("#888888")

// ── Helpers ───────────────────────────────────────────────────────────────────

// Image placeholder — replaces <!-- image suggestion: ... --> comments
#let img(note) = block(
  width: 100%, height: 68pt,
  fill: rgb("#fff8f0"),
  stroke: (left: 4pt + orange),
  radius: (right: 3pt),
  inset: (left: 14pt, y: 12pt),
)[
  #set text(size: 10pt, fill: muted, style: "italic")
  #emph([Image placeholder: #note])
]

// Blockquote — replaces > ...
#let bq(content) = block(
  width: 100%,
  stroke: (left: 4pt + orange),
  inset: (left: 16pt, y: 8pt),
)[
  #set text(fill: rgb("#555555"), style: "italic")
  #content
]

// ── Spacing tokens ────────────────────────────────────────────────────────────
#let gap-xs = 0.4em
#let gap-sm = 0.5em
#let gap-md = 0.8em
#let gap-lg = 1.2em

// ── Slide layout helpers ──────────────────────────────────────────────────────

// Title slide
// Usage: #title-slide([My Title], subtitle: [Subtitle], author: [Name])
#let title-slide(title, subtitle: none, author: none) = align(horizon + center)[
  #text(size: 2.4em, weight: "bold")[#title]
  #if subtitle != none { v(gap-sm); text(size: 1.1em, fill: muted)[#subtitle] }
  #v(gap-lg)
  #line(length: 40%, stroke: 2pt + orange)
  #if author != none { v(gap-sm); text(size: 0.8em, fill: muted)[#author] }
]

// Interstitial / section slide
// Usage: #section-slide([Live Demo], sub: [optional subtitle])
#let section-slide(title, sub: none) = align(horizon + center)[
  #text(size: 2em, weight: "bold", fill: orange)[#title]
  #if sub != none { v(gap-sm); text(size: 0.9em, fill: muted)[#sub] }
]

// Closing slide
// Usage: #closing-slide([Thanks!], sub: [Ciao 👋], meta: [Team · v0.1.4])
#let closing-slide(title, sub: none, meta: none) = align(horizon + center)[
  #text(size: 2.6em, weight: "bold")[#title]
  #if sub  != none { v(gap-xs); text(size: 1.2em,  fill: orange)[#sub] }
  #if meta != none { v(gap-lg); text(size: 0.75em, fill: muted)[#meta] }
]

// ── Theme entry point ─────────────────────────────────────────────────────────
// logo: path to an SVG/PNG file, or none (default)
#let theme(logo: none, body) = {
  set page(
//    paper:  "a4",          // 210×297mm portrait
    height: 297mm,
    width: 167mm,
    flipped: true,
    margin: (top: 68pt, bottom: 44pt, left: 60pt, right: 60pt),
    fill:   white,

    // Logo: left-top corner, matching Marp CSS background-position
    background: if logo != none {
      place(
        left + top,
        dx: 2pt,
        dy: 8pt,
        image(logo, width: 64pt, fit: "contain"),
      )
    },

    footer: context [
      #set text(size: 10pt, fill: muted)
      #h(1fr)
      #counter(page).display() / #counter(page).final().first()
    ],
    footer-descent: 14pt,
  )

  set text(
    font: ("Liberation Sans"), // , "Arial", "Helvetica"
    size: 18pt,
    fill: rgb("#222222"),
  )
  set par(leading: 0.7em)
  set list(spacing: 0.75em, indent: 0pt)

  show heading.where(level: 2): it => block(below: 12pt)[
    #set align(center)
    #set text(size: 1.45em, fill: orange, weight: "bold")
    #it.body
    #v(-4pt)
    #line(length: 100%, stroke: 2.5pt + orange)
  ]
  show heading.where(level: 3): it => block(above: 12pt, below: 6pt)[
    #set text(size: 1.05em, fill: dark-orange, weight: "bold")
    #it.body
  ]
  show strong: set text(fill: dark-orange)
  show link:   set text(fill: orange)

  body
}
