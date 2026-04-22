# UI Rehaul — Catalog Noir
**Date:** 2026-04-22  
**Branch:** ui-polish  
**Deadline:** 2026-04-25 20:00 IST

---

## Overview

Full visual pass on the Phaser 3 game (900×600 canvas). Adds pixel art character sprites for all 4 table characters, redesigns the interview popup and confrontation scene in an Ace Attorney style, applies a consistent dark noir palette with blue/purple accents, adds ambient sound, and adds scene fade transitions.

Everything stays in `frontend/index.html` and `frontend/assets/` — no new backend changes required.

---

## 1. Character Sprites

### Approach
All 4 characters drawn programmatically via Phaser `RenderTexture` using a pixel color-map (2D array of hex colors per pixel, 16×20 grid). Zero image files required as fallback. When a PNG exists at the configured path, Phaser loads it instead.

### Asset config (top of index.html)
```js
const CHARACTERS = {
  dim_customers:    { url: '/assets/dim_customers.png',    fallback: 'procedural' },
  stg_customers:    { url: '/assets/stg_customers.png',    fallback: 'procedural' },
  customers:        { url: '/assets/customers.png',        fallback: 'procedural' },
  customer_metrics: { url: '/assets/customer_metrics.png', fallback: 'procedural' },
}
```

Phaser tries `loader.image(key, url)`. On load failure (`loaderror` event), it falls back to the procedural RenderTexture. Swapping in real art requires only dropping a PNG in `frontend/assets/` — no code change.

### Character designs (procedural fallback)

All characters wear the **same dark charcoal suit (#2a2a3a)** with cream collar (#f0ead8). Differentiated by posture, expression, and accessories only — no role-colour coding.

| Character | Posture | Expression | Accessory | Distinguishing feature |
|---|---|---|---|---|
| dim_customers | Slumped arms | Red ✕ eyes, downturned mouth | Red tie (askew) | Sweat drop |
| stg_customers | Arms crossed | Shifty sideways eyes, smirk | Navy tie | Green pocket square |
| customers | Upright, arms open | Wide direct eyes, neutral | Blue tie (straight) | — |
| customer_metrics | Shrugging, arms raised | Raised brows, open mouth | Grey tie | White ? badge |

### Contrast strategy
- Cream shirt collar = bright anchor on dark background
- Skin-tone face = natural top contrast
- 1px `#444455` silhouette outline = readable against `#050508`
- No suit colour maps to role (mystery intact)

### Sizes
- **Small (40×50px):** used in MapScene interview popup portrait area
- **Large (80×100px):** used in ConfrontScene standing figure

---

## 2. MapScene — Interview Popup Redesign

### Current
Plain rectangle, gold border, no portrait, monospace text.

### New layout
```
┌─────────────────────────────────────────┐  ← 2px border #4466ff
█ gradient bar (blue→purple→blue)         █  ← 2px top accent
│ [64px portrait] │ ▶ character name      │
│   (small sprite)│   #ffdd88 bold        │
│                 │   metadata line #aaaacc│
│                 │   dialogue text #ccccff│
│                 │   typewriter cursor █  │
│                 │   [COLLECT] [CLOSE]    │
└─────────────────────────────────────────┘
```

- Portrait area: 64px wide, dark `#060610`, sprite sits at bottom edge
- Speaker name: `#ffdd88`, bold, prefixed with `▶`
- Metadata line (service/tier/cols): `#aaaacc`, smaller
- Dialogue text: `#ccccff`
- Typewriter cursor: `█` in `#4466ff`, blinks
- COLLECT EVIDENCE button: `#1a1a3a` bg, `#4466ff` border, `#88aaff` text
- CLOSE button: `#111` bg, `#333` border, `#666` text

---

## 3. ConfrontScene Redesign

### Current
Plain text dialogue box, two evidence card buttons side by side, no character visual.

### New layout
```
─ CONFRONTATION ─   (blue label, letter-spaced)

[80px standing    ] [ ▶ stg_customers          ]
[  sprite         ] [   dialogue text #ccccff  ]
[  left-aligned   ] [   typewriter cursor       ]
[  bottom-anchored] [                          ]
                    [ PRESENT EVIDENCE:        ]
                    [ [GHOST OWNERSHIP] [...]  ]
```

- Scene background: radial gradient `#0d0820 → #050508` (subtle purple glow behind character)
- Character stands left side, bottom-anchored, 80×100px
- Dialogue box: `#0a0a16` bg, `2px #4466ff` border, gradient top bar
- Evidence card buttons: styled same as new interview popup buttons

---

## 4. Aesthetic — All Scenes

### Palette additions (on top of existing)
| Token | Value | Usage |
|---|---|---|
| `--accent-blue` | `#4466ff` | Dialogue borders, buttons, cursor |
| `--accent-purple` | `#aa44ff` | Gradient accents |
| `--text-dialogue` | `#ccccff` | Dialogue body text |
| `--text-speaker` | `#ffdd88` | Speaker name labels |
| `--text-meta` | `#aaaacc` | Metadata subtitles |

Existing gold (`#e8c97e`) kept for node labels, evidence card headers, title text.

### Map nodes
- Border width: 1px → **2px**
- Add Phaser `Graphics` inner glow (semi-transparent fill matching border colour)
- Label font: same monospace, weight bumped

### BriefingScene
- Add 40px letterbox bars top and bottom (black `#000000`)
- "CASE I" header: letter-spacing 3px, `#4466ff`
- Incident card: `2px #4466ff` border, gradient top bar

### AccusationScene
- Mini portrait (24×30px) beside each suspect name in the list

### VerdictScene
- "CASE CLOSED" in large text with a brief white flash animation on entry

---

## 5. Scene Transitions

All scene changes get a **400ms black camera fade** (Phaser `cameras.main.fadeOut` / `fadeIn`). Applied to:
- Briefing → Map
- Map → Confront
- Confront → Map (return)
- Map → Accusation
- Accusation → Verdict

---

## 6. Ambient Sound

A synthesized noir piano loop starts when MapScene loads and runs continuously until game end. Built entirely in Web Audio API (no audio files):

- Bass pulse: sine wave ~55Hz, every 2 seconds, short envelope
- Sparse melody: 3–4 note motif, pentatonic minor, notes every 1.5–3s random offset
- Low-pass filter: ~800Hz cutoff for muffled underground-bar feel
- Master volume: low (~0.12) so it doesn't compete with SFX

Loop restarts cleanly every ~8 seconds.

---

## 7. What Does NOT Change

- Backend (`main.py`) — no changes
- Game logic (evidence collection, accusation flow, verdict conditions)
- Node definitions, edge definitions, confrontation logic
- Detective silhouette image (`detective.png`)
- Existing SFX engine (typewriter, evidenceStamp, objection, caseClosed, etc.)
- Canvas dimensions (900×600)

---

## Implementation Notes

- All changes in `frontend/index.html` (single file) + new `frontend/assets/` directory
- Character procedural textures generated in Phaser `preload()` via `RenderTexture`
- Asset loading uses `this.load.image()` with `loaderror` fallback to procedural
- Ambient loop starts in MapScene `create()`, stored as `this.ambientLoop` on the MapScene instance; stopped in scene `shutdown` event
- Transitions use Phaser built-in camera effects — no external libraries
- Estimated implementation time: 12–14 hours
