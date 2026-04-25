# Rich Info Panel — Design Spec
**Date:** 2026-04-25
**Branch:** `feature/rich-info-panel` (new branch, do not touch `main`)

---

## Context

The current MapScene has a right-side evidence panel and a centred dialogue box. When a node is clicked, only the dialogue opens — there is no way to inspect raw metadata (health, owner, columns, test status, dependencies, diagnostics) without going through the interview flow. The goal is to add an always-accessible metadata view inspired by the Data City OPS prototype, while preserving the detective game mechanics and existing visual style (rectangular nodes, badge strips, pixel-art aesthetic).

---

## What Changes

### Visual style: unchanged
Node shapes, colors, badge strips, edge lines, fonts, and overall aesthetic stay exactly as they are now. No building icons, no animated dots.

### Two new floating panels replace the old fixed panels

| Old | New |
|-----|-----|
| Evidence panel — right edge, fixed, always visible | Rich info panel — floating right, `top:40, right:20, w:210, h:510` |
| Dialogue box — centred bottom, appears on node click | Dialogue box — floating bottom-left, `bottom:20, left:20, w:440, h:200`, appears only on INTERVIEW |

---

## Interaction Model

```
Click node
  └─► Rich info panel populates with node metadata (instant, no dialogue)
      └─► INTERVIEW button (bottom of panel, hidden for victim node)
            └─► Dialogue box appears at bottom-left
                  └─► COLLECT EVIDENCE / NEXT / DISMISS (existing logic)
                        └─► DISMISS: dialogue closes, rich info stays open
                        └─► COLLECT EVIDENCE: adds to evidence board

No node selected / after dismiss
  └─► Rich info panel shows EVIDENCE BOARD (all collected cards)
```

The victim node (`dim_customers`) has no INTERVIEW button — it is inspectable but not interviewable.

---

## Rich Info Panel Content (node selected)

All fields sourced from `this.liveData[node.key]` (already fetched by `_fetchNodeData`) plus NODE_DEFS:

| Field | Source |
|-------|--------|
| Building type / name | `node.badge` + `node.label` from NODE_DEFS |
| FQN | `node.fqn` from NODE_DEFS |
| Status dot + label | Add `status` + `statusColor` fields to NODE_DEFS (game-authored: NOMINAL / ABANDONED / CRITICAL / CONGESTED) |
| Health bar % | Add `healthPct` field to NODE_DEFS (game-authored: 95 / 35 / 15 / 45) |
| Owner | `liveData[key].owners[0].displayName` (falls back to NODE_DEFS `owner` field) |
| Columns | `liveData[key].columns[]` names (first 6, then "+N more") |
| Last test | `liveData[key].testResult` (PASS / ABORTED · HH:MM, color-coded green/red) |
| Dependencies | Derived from EDGE_DEFS: inbound edges → this node, outbound → from this node. Badge: OK / DUPLICATE (game-authored per edge) |
| Diagnostic | Add `diagnostic` field to NODE_DEFS |

**New fields to add to each NODE_DEF:**
```js
{ status, statusColor, healthPct, diagnostic, edgeBadges: { toKey: 'OK'|'DUPLICATE' } }
```

---

## Rich Info Panel Content (no node selected — Evidence Board)

Displays:
- Header: `EVIDENCE (N items)`
- Each evidence card: `evidenceTitle` (gold) + `evidenceText` (grey)
- If 0 items: "No evidence collected."
- If 2+ items: MAKE ACCUSATION button (same logic as current accuse button, just rendered inside the panel)

The current standalone `_buildEvidencePanel()` and `_buildAccuseButton()` are removed. Their logic moves into the rich info panel's evidence-board render.

---

## Implementation Plan (files to change)

**Single file:** `frontend/index.html`

### NODE_DEFS additions (~lines 50–120)
Add `status`, `statusColor`, `healthPct`, `diagnostic`, `edgeBadges` to each of the 4 node objects.

### New method: `_buildRichInfoPanel()` (replaces `_buildEvidencePanel`)
- Draws the floating panel background + gradient top bar using Phaser Graphics (all-Phaser, matching existing codebase — no DOM)
- Renders default evidence board state
- Called from `create()`

### New method: `_showRichInfo(nodeDef)`
- Populates the panel with node metadata
- Called from node `pointerdown` handler (replacing direct dialogue open)
- Shows INTERVIEW button (hidden for victim)

### New method: `_showEvidenceBoard()`
- Renders evidence cards + optional MAKE ACCUSATION button
- Called when: no node selected, DISMISS pressed, scene re-entered

### Modified: `_buildNode()` pointerdown handler
- Was: `this._openDialogue(nodeDef)`
- Now: `this._showRichInfo(nodeDef)` (dialogue only opens via INTERVIEW)

### Modified: `_buildDialogueBox()`
- Reposition from centred-bottom to `bottom:20, left:20, w:440`
- Add INTERVIEW trigger wiring

### Removed: `_buildAccuseButton()` (logic absorbed into evidence board)

---

## Rendering approach

Match existing Phaser style throughout:
- Panel backgrounds: `graphics.fillStyle(0x08080f)` + `graphics.strokeRect` with `0x2a2a4a` border
- Top accent bar: thin rect filled with gradient approximation (`0x4466ff` → `0xaa44ff`)  
- Text: `FONT_BODY` (VT323) for all body, `FONT_TITLE` (Press Start 2P) for section headers
- Status colors: NOMINAL `0x00ff88`, ABANDONED `0xaa44ff`, CRITICAL `0xff2244`, CONGESTED `0xffcc00`
- Health bar: `graphics.fillRect` on a dark track
- Column chips: small dark rects with body text
- Evidence cards: `0x12122a` fill, `0x2a3a6a` border

---

## Out of scope
- Node shape changes (stays rectangular)
- Animated data flow dots on edges
- Any other scene changes (Briefing, Accusation, Confront, Verdict)

---

## Verification
1. `uvicorn main:app` — game loads at `http://localhost:PORT`
2. Click each node → rich info panel populates with correct metadata, no dialogue opens
3. Click INTERVIEW → dialogue appears at bottom-left, rich info stays visible
4. Collect evidence → DISMISS → evidence board shows collected cards
5. Victim node (dim_customers) → rich info shows, no INTERVIEW button
6. Collect 2+ evidence → MAKE ACCUSATION appears in evidence board
7. Existing game flow (accusation → confront → verdict) unaffected
