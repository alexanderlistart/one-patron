# ONE PATRON — Brand Standard v1.0

## Core idea

The current mark is an unfinished cycle. A perfect gold ring is interrupted at three o'clock by one blue point. The point remains separate while ONE PATRON is unresolved. The ring must not be closed in current communications.

The symbol contains exactly twenty-two elements:

- 21 gold arc segments: Major Arcana I–XXI;
- 1 blue point in the break: Arcana 0, The Fool, outside the sequence.

This structure is fixed. Do not let an image generator redraw or reinterpret it.

## Master geometry

Use the outside diameter of the gold ring as `D`.

- Form: a mathematically perfect circle, never hand-drawn, oval, tilted, or shown in perspective.
- Gold ring: exactly 21 equal arc segments.
- Main break: 32 degrees, centered precisely at three o'clock.
- Gold stroke: 5.3% of `D`, with clean radial cuts at the segment ends.
- Blue point: 9% of `D` in diameter.
- Point position: centered on the ring's centerline at three o'clock.
- The point never touches either gold end.
- Orientation is fixed. Never rotate or mirror the mark.

## Primary horizontal lockup

- Mark is always on the left; `ONE PATRON` is always on the right.
- Wordmark: uppercase `ONE PATRON` only.
- Typeface: Avenir Next Medium, weight 500.
- Cross-platform fallback: Inter Medium 500, then Helvetica Neue.
- Tracking: `0.22em`.
- Text must never be bold, italic, condensed, outlined, or stacked.
- Wordmark cap height: approximately 34% of `D`.
- Clear horizontal distance from ring edge to the first letter: 38% of `D`.
- Mark and wordmark are optically centered on the same horizontal axis.
- Clear space around the full lockup: at least 35% of `D` on every side.

## Color system

Primary dark application:

- Obsidian background: `#0B0C0E`
- Patron Gold: `#D6A74B`
- Fool Blue: `#65C9FF`
- Wordmark Ivory: `#F3EFE7`

Optional digital highlights, used sparingly and never as new colors:

- Gold highlight: `#F0CF7A`
- Gold shadow: `#A56F26`
- Blue glow: the same `#65C9FF` at low opacity and small radius

Light application:

- Wordmark: `#17181A`
- Gold: `#B98224`
- Blue: `#168FC6`
- Preferred light ground: `#F4F1EA`

The dark application is the primary identity. The light application is functional, not a separate aesthetic.

## Standard placement on future visuals

Use the horizontal lockup as a quiet signature, normally in the lower-left corner on the calmest available area.

| Canvas | Lockup width | Outer margin |
|---|---:|---:|
| 1080 × 1080 | 300 px | 54 px |
| 1536 × 1024 | 360 px | 64 px |
| 1920 × 1080 | 420 px | 80 px |

For other sizes, use 28% of canvas width on square work and 23–24% on landscape work. Never render the full lockup below 160 px wide or the standalone mark below 28 px.

Use the standalone mark, without the words, for avatars and very small icons.

## Workflow for generated images

Do not ask an image model to reproduce this mark. Generate the artwork without branding while reserving a calm area for the signature. Overlay the supplied SVG or PNG master afterward at the standard size. This preserves the 21 segments, exact gap, point, typography, and spacing.

Prompt instruction for the artwork stage:

> Leave a calm, low-detail area in the lower-left corner for the ONE PATRON horizontal brand lockup. Do not draw, imitate, spell, or invent any logo or brand text inside the generated image.

## Do not

- change the number of segments;
- convert the ring into one continuous stroke;
- close the break before the work is complete;
- move, enlarge, or recolor the blue point;
- place the point inside the circle;
- use rainbow, neon-gold, or crypto-interface styling;
- add tarot labels, numerals, slogans, or explanatory text to the mark;
- use shadows, bevels, metallic 3D extrusion, or large glow effects;
- place the lockup over a face, a key story object, or a visually noisy area.

## Master files

- `one-patron-mark-master.svg`: transparent standalone vector mark.
- `one-patron-lockup-on-dark.svg`: transparent horizontal lockup for dark imagery.
- `one-patron-lockup-on-light.svg`: transparent horizontal lockup for light imagery.
- `one-patron-lockup-preview-dark.svg`: primary lockup on the standard obsidian ground.
- `one-patron-avatar-dark.svg`: square profile-image master.
