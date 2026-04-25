# Rich Info Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a floating right-side metadata panel to MapScene that displays node information (health, owner, columns, dependencies, diagnostics) on click, with a separate interview dialogue triggered by an INTERVIEW button inside the panel.

**Architecture:** Single-file implementation in `frontend/index.html`. NODE_DEFS are enhanced with new game-authored metadata fields. MapScene gains three new methods: `_buildRichInfoPanel()` (creates the floating panel UI), `_showRichInfo(nodeDef)` (populates it with node data), and `_showEvidenceBoard()` (shows collected evidence inside the panel). Existing dialogue and evidence logic is repositioned to work with the new panel structure. Node clicks now trigger metadata display instead of dialogue.

**Tech Stack:** Phaser 3.87 (Graphics API for panel rendering), VT323 + Press Start 2P fonts, no external dependencies.

---

## File Structure

**Single file modified:** `/home/pixel/Hackathon/catalog-noir/frontend/index.html`

| Section | Lines | Changes |
|---------|-------|---------|
| NODE_DEFS | ~50–120 | Add `status`, `statusColor`, `healthPct`, `diagnostic`, `edgeBadges` fields to 4 nodes |
| MapScene.init() | ~536–543 | Add `this.richPanel`, `this.richPanelContainer`, `this.richMode` state vars |
| MapScene.create() | ~545–590 | Call `_buildRichInfoPanel()` instead of `_buildEvidencePanel()` and `_buildAccuseButton()` |
| MapScene._buildNode() | ~666–700 | Change pointerdown from `_openDialogue()` to `_showRichInfo()` |
| MapScene._buildRichInfoPanel() | new, ~1020–1100 | New method — creates floating panel structure |
| MapScene._showRichInfo() | new, ~1102–1180 | New method — populates panel with node metadata |
| MapScene._showEvidenceBoard() | new, ~1182–1250 | New method — renders evidence list + MAKE ACCUSATION button |
| MapScene._buildDialogueBox() | ~1252–1280 (modified) | Reposition to bottom-left floating; update positioning logic |
| MapScene._openDialogue() | ~1282+ (modify) | Remove or mark as called only from INTERVIEW button |

---

## Tasks

### Task 1: Create Feature Branch

- [ ] **Step 1: Create and switch to feature branch**

```bash
cd /home/pixel/Hackathon/catalog-noir
git checkout -b feature/rich-info-panel
```

Expected: Branch created, confirmed by `git status` showing `On branch feature/rich-info-panel`

---

### Task 2: Enhance NODE_DEFS with New Fields

**Files:** `frontend/index.html` lines 50–120

- [ ] **Step 1: Read current NODE_DEFS structure**

Locate the `const NODE_DEFS = [...]` array. Each object has: `key`, `fqn`, `label`, `role`, `x`, `y`, `color`, `badge`, `evidenceTitle`, `evidenceText`.

- [ ] **Step 2: Add new fields to NODE_DEFS**

For each of the 4 node objects, add:
- `status` — one of: "NOMINAL", "ABANDONED", "CRITICAL", "CONGESTED"
- `statusColor` — hex string matching the status (e.g., `"#00ff88"` for NOMINAL)
- `healthPct` — number 0–100 (e.g., 95, 35, 15, 45)
- `diagnostic` — string describing the node's health issue
- `edgeBadges` — object mapping target/source node keys to status strings ("OK" or "DUPLICATE")

Replace the NODE_DEFS array with:

```js
const NODE_DEFS = [
  {
    key: "customers",
    fqn: "acme_nexus_raw_data.acme_raw.crm.customers",
    label: "customers (raw)",
    role: "source",
    x: 130, y: 390,
    color: 0x00ffcc,
    badge: "SOURCE",
    evidenceTitle: "Raw Source Unchanged",
    evidenceText: "No transformations applied. Data flows directly to staging.",
    status: "NOMINAL",
    statusColor: "#00ff88",
    healthPct: 95,
    diagnostic: "Raw MySQL ingestion. Uniqueness test on customer_id passes.",
    edgeBadges: { "stg_customers": "OK" }
  },
  {
    key: "stg_customers",
    fqn: "acme_nexus_analytics.ANALYTICS.STAGING.stg_customers",
    label: "stg_customers",
    role: "suspect",
    x: 240, y: 200,
    color: 0xff44aa,
    badge: "STAGING",
    evidenceTitle: "Ghost Owner Card",
    evidenceText: "Owner field set to 'test' — unclaimed table. No maintenance or monitoring.",
    status: "ABANDONED",
    statusColor: "#ff44ff",
    healthPct: 35,
    diagnostic: "Transformation logic is unaudited. Owner field is a placeholder ('test'). No deduplication is applied.",
    edgeBadges: { "dim_customers": "DUPLICATE" }
  },
  {
    key: "dim_customers",
    fqn: "acme_nexus_analytics.ANALYTICS.MARTS.dim_customers",
    label: "dim_customers",
    role: "victim",
    x: 450, y: 330,
    color: 0xff2244,
    badge: "VICTIM",
    evidenceTitle: "Test Abort Evidence",
    evidenceText: "Tier 1 mart. Customer Key Uniqueness test ABORTED at 14:03.",
    status: "CRITICAL",
    statusColor: "#ff2244",
    healthPct: 15,
    diagnostic: "Tier 1 mart. Customer Key Uniqueness test ABORTED at 14:03.",
    edgeBadges: { "customer_metrics": "DUPLICATE" }
  },
  {
    key: "customer_metrics",
    fqn: "acme_nexus_analytics.ANALYTICS.METRICS.customer_metrics",
    label: "customer_metrics",
    role: "downstream",
    x: 640, y: 200,
    color: 0xffaa00,
    badge: "DOWNSTREAM",
    evidenceTitle: "Inflated Metrics",
    evidenceText: "Aggregates are inflated by duplicates from upstream — metrics are unreliable.",
    status: "CONGESTED",
    statusColor: "#ffcc00",
    healthPct: 45,
    diagnostic: "Aggregates from dim_customers. Inflated by upstream duplicates.",
    edgeBadges: {}
  }
];
```

- [ ] **Step 3: Commit**

```bash
git add frontend/index.html
git commit -m "enhance NODE_DEFS with status, health, and diagnostic fields"
```

---

### Task 3: Add Rich Panel State to MapScene.init()

**Files:** `frontend/index.html` lines 536–543 (MapScene.init method)

- [ ] **Step 1: Locate MapScene.init()**

Find the `init() { this.evidence = []; ... }` method inside the MapScene class.

- [ ] **Step 2: Add rich panel state variables**

After the existing `this.evidence = [];` and other state vars, add:

```js
    this.richPanelContainer = null;  // Phaser container for the floating panel
    this.richMode = "none";           // "none" | "info" | "evidence"
    this.richCurrentNode = null;      // Currently selected node key
```

- [ ] **Step 3: Commit**

```bash
git add frontend/index.html
git commit -m "add rich panel state variables to MapScene.init"
```

---

### Task 4: Build _buildRichInfoPanel() Method

**Files:** `frontend/index.html` — insert new method before `_buildDialogueBox()` (around line 1020)

- [ ] **Step 1: Create the method skeleton**

Insert this method into the MapScene class (before any existing dialogue/evidence methods):

```js
  _buildRichInfoPanel() {
    const panelX = W - 20 - 210;  // right: 20, width: 210
    const panelY = 40;            // top: 40
    const panelW = 210, panelH = 510;

    const ctr = this.add.container(0, 0).setDepth(10);
    this.richPanelContainer = ctr;

    // Background
    const bg = this.add.graphics();
    bg.fillStyle(0x08080f, 0.98);
    bg.fillRect(panelX, panelY, panelW, panelH);
    bg.lineStyle(1, 0x2a2a4a, 0.8);
    bg.strokeRect(panelX, panelY, panelW, panelH);
    ctr.add(bg);

    // Top accent bar (gradient approx)
    const bar = this.add.graphics();
    bar.fillStyle(0x4466ff, 0.8);
    bar.fillRect(panelX, panelY, panelW / 2, 3);
    bar.fillStyle(0xaa44ff, 0.8);
    bar.fillRect(panelX + panelW / 2, panelY, panelW / 2, 3);
    ctr.add(bar);

    // Content area (will be populated by _showRichInfo or _showEvidenceBoard)
    const contentZone = this.add.zone(panelX, panelY + 20, panelW, panelH - 20).setOrigin(0, 0);
    ctr.add(contentZone);

    // Store panel metadata for later reference
    ctr.x = 0;
    ctr.y = 0;
    ctr.panelX = panelX;
    ctr.panelY = panelY;
    ctr.panelW = panelW;
    ctr.panelH = panelH;

    // Show default state (evidence board empty)
    this._showEvidenceBoard();
  }
```

- [ ] **Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "add _buildRichInfoPanel method"
```

---

### Task 5: Implement _showRichInfo() Method

**Files:** `frontend/index.html` — insert after `_buildRichInfoPanel()` (around line 1102)

- [ ] **Step 1: Create _showRichInfo() method**

```js
  _showRichInfo(nodeDef) {
    this.richMode = "info";
    this.richCurrentNode = nodeDef.key;

    const ctr = this.richPanelContainer;
    const px = ctr.panelX, py = ctr.panelY, pw = ctr.panelW;

    // Clear previous content (destroy all children except bg/bar)
    ctr.getAll().forEach((obj, idx) => {
      if (idx > 1) obj.destroy();  // Keep bg (0) and bar (1)
    });

    const contentY = py + 20;
    const fontSize = 7;
    const lineHeight = 12;
    let currentY = contentY + 8;

    // Building type
    this.add.text(px + 10, currentY, `${nodeDef.status}`.toUpperCase(), {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#9090b8", letterSpacing: 1,
    }).setOrigin(0, 0);
    currentY += lineHeight;

    // Node name
    this.add.text(px + 10, currentY, nodeDef.label, {
      fontFamily: FONT_TITLE, fontSize: "11px", color: "#ffffff",
    }).setOrigin(0, 0);
    currentY += lineHeight + 2;

    // FQN
    const fqnText = this.add.text(px + 10, currentY, nodeDef.fqn, {
      fontFamily: FONT_BODY, fontSize: `${fontSize - 1}px`, color: "#5060a0", wordWrap: { width: pw - 20 },
    }).setOrigin(0, 0);
    currentY += 20;

    // Status dot + label
    const statusGfx = this.add.graphics();
    const dotX = px + 10, dotY = currentY + 3;
    statusGfx.fillStyle(parseInt(nodeDef.statusColor.slice(1), 16), 0.9);
    statusGfx.fillCircle(dotX, dotY, 3.5);
    this.add.text(dotX + 10, currentY, nodeDef.status, {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: nodeDef.statusColor, letterSpacing: 1,
    }).setOrigin(0, 0);
    currentY += lineHeight + 2;

    // Health bar
    this.add.text(px + 10, currentY, "HEALTH", {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#5060a0", letterSpacing: 2,
    }).setOrigin(0, 0);
    currentY += lineHeight;

    const healthTrackGfx = this.add.graphics();
    healthTrackGfx.fillStyle(0x1a1a2a, 0.8);
    healthTrackGfx.fillRect(px + 10, currentY, pw - 20, 5);
    const healthColor = nodeDef.statusColor === "#00ff88" ? 0x00cc66 : 
                        nodeDef.statusColor === "#ff44ff" ? 0xaa44ff :
                        nodeDef.statusColor === "#ff2244" ? 0xff2244 : 0xffcc00;
    healthTrackGfx.fillStyle(healthColor, 0.9);
    healthTrackGfx.fillRect(px + 10, currentY, (pw - 20) * (nodeDef.healthPct / 100), 5);
    currentY += 8;

    this.add.text(px + 10, currentY, `${nodeDef.healthPct}% operational`, {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#9090b8",
    }).setOrigin(0, 0);
    currentY += lineHeight + 2;

    // Owner
    this.add.text(px + 10, currentY, "OWNER", {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#5060a0", letterSpacing: 2,
    }).setOrigin(0, 0);
    currentY += lineHeight;

    const owner = this.liveData[nodeDef.key]?.owners?.[0]?.displayName || "Unknown";
    this.add.text(px + 10, currentY, owner, {
      fontFamily: FONT_BODY, fontSize: "10px", color: "#e8c97e",
    }).setOrigin(0, 0);
    currentY += lineHeight + 2;

    // Columns
    this.add.text(px + 10, currentY, `COLUMNS (${this.liveData[nodeDef.key]?.columns?.length || 0})`, {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#5060a0", letterSpacing: 2,
    }).setOrigin(0, 0);
    currentY += lineHeight;

    const cols = this.liveData[nodeDef.key]?.columns || [];
    cols.slice(0, 4).forEach(col => {
      this.add.text(px + 10, currentY, col.name || col, {
        fontFamily: FONT_BODY, fontSize: `${fontSize - 1}px`, color: "#aaaacc",
        background: { color: "#1a1a2a", padding: { x: 3, y: 1 } },
      }).setOrigin(0, 0);
      currentY += lineHeight - 2;
    });
    currentY += 2;

    // Last test
    this.add.text(px + 10, currentY, "LAST TEST", {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#5060a0", letterSpacing: 2,
    }).setOrigin(0, 0);
    currentY += lineHeight;

    const testText = this.liveData[nodeDef.key]?.testResult || "PASS";
    const testColor = testText.includes("PASS") ? "#00ff88" : "#ff4444";
    this.add.text(px + 10, currentY, testText, {
      fontFamily: FONT_BODY, fontSize: "10px", color: testColor, fontStyle: "bold",
    }).setOrigin(0, 0);
    currentY += lineHeight + 3;

    // Dependencies
    this.add.text(px + 10, currentY, "DEPENDENCIES", {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#5060a0", letterSpacing: 2,
    }).setOrigin(0, 0);
    currentY += lineHeight;

    this.add.text(px + 10, currentY, "← INBOUND", {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#6070a0",
    }).setOrigin(0, 0);
    currentY += lineHeight - 2;

    const inbound = EDGE_DEFS.find(e => e.to === nodeDef.key);
    if (inbound) {
      const badge = nodeDef.edgeBadges?.[EDGE_DEFS.findIndex(e => e === inbound)] || "";
      this.add.text(px + 10, currentY, `${NODE_DEFS.find(n => n.key === inbound.from)?.label || inbound.from} ${badge}`, {
        fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#ccccff",
      }).setOrigin(0, 0);
    } else {
      this.add.text(px + 10, currentY, "none", {
        fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#404060",
      }).setOrigin(0, 0);
    }
    currentY += lineHeight;

    this.add.text(px + 10, currentY, "→ OUTBOUND", {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#6070a0",
    }).setOrigin(0, 0);
    currentY += lineHeight - 2;

    const outbound = EDGE_DEFS.find(e => e.from === nodeDef.key);
    if (outbound) {
      this.add.text(px + 10, currentY, `${NODE_DEFS.find(n => n.key === outbound.to)?.label || outbound.to}`, {
        fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#ccccff",
      }).setOrigin(0, 0);
    } else {
      this.add.text(px + 10, currentY, "none", {
        fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#404060",
      }).setOrigin(0, 0);
    }
    currentY += lineHeight + 2;

    // Diagnostic
    this.add.text(px + 10, currentY, "DIAGNOSTIC", {
      fontFamily: FONT_BODY, fontSize: `${fontSize}px`, color: "#5060a0", letterSpacing: 2,
    }).setOrigin(0, 0);
    currentY += lineHeight;

    this.add.text(px + 10, currentY, nodeDef.diagnostic, {
      fontFamily: FONT_BODY, fontSize: `${fontSize - 1}px`, color: "#9090b8",
      wordWrap: { width: pw - 20 }, lineSpacing: 2,
    }).setOrigin(0, 0);
    currentY += lineHeight + 8;

    // INTERVIEW button (not for victim node)
    if (nodeDef.role !== "victim") {
      const btnGfx = this.add.graphics();
      const btnX = px + 10, btnY = currentY, btnW = pw - 20, btnH = 18;
      btnGfx.fillStyle(0x1a1a3a, 0.9);
      btnGfx.fillRect(btnX, btnY, btnW, btnH);
      btnGfx.lineStyle(1, 0x4466ff, 0.7);
      btnGfx.strokeRect(btnX, btnY, btnW, btnH);

      const btnText = this.add.text(btnX + btnW / 2, btnY + btnH / 2, "▶ INTERVIEW", {
        fontFamily: FONT_BODY, fontSize: "9px", color: "#aabbff", letterSpacing: 2, align: "center",
      }).setOrigin(0.5, 0.5).setInteractive({ useHandCursor: true });

      btnText.on("pointerdown", () => {
        this._openDialogue(nodeDef);
      });

      btnText.on("pointerover", () => {
        btnGfx.clear();
        btnGfx.fillStyle(0x22224a, 0.9);
        btnGfx.fillRect(btnX, btnY, btnW, btnH);
        btnGfx.lineStyle(1, 0x4466ff, 0.8);
        btnGfx.strokeRect(btnX, btnY, btnW, btnH);
      });

      btnText.on("pointerout", () => {
        btnGfx.clear();
        btnGfx.fillStyle(0x1a1a3a, 0.9);
        btnGfx.fillRect(btnX, btnY, btnW, btnH);
        btnGfx.lineStyle(1, 0x4466ff, 0.7);
        btnGfx.strokeRect(btnX, btnY, btnW, btnH);
      });
    }
  }
```

- [ ] **Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "implement _showRichInfo method with full node metadata display"
```

---

### Task 6: Implement _showEvidenceBoard() Method

**Files:** `frontend/index.html` — insert after `_showRichInfo()` (around line 1182)

- [ ] **Step 1: Create _showEvidenceBoard() method**

```js
  _showEvidenceBoard() {
    this.richMode = "evidence";
    this.richCurrentNode = null;

    const ctr = this.richPanelContainer;
    const px = ctr.panelX, py = ctr.panelY, pw = ctr.panelW, ph = ctr.panelH;

    // Clear previous content (destroy all children except bg/bar)
    ctr.getAll().forEach((obj, idx) => {
      if (idx > 1) obj.destroy();
    });

    const contentY = py + 20;
    let currentY = contentY + 8;

    // Header
    this.add.text(px + 10, currentY, `EVIDENCE (${this.evidence.length})`, {
      fontFamily: FONT_BODY, fontSize: "11px", color: "#e8c97e", letterSpacing: 1,
    }).setOrigin(0, 0);
    currentY += 16;

    // Evidence cards
    if (this.evidence.length === 0) {
      this.add.text(px + 10, currentY, "No evidence collected.", {
        fontFamily: FONT_BODY, fontSize: "9px", color: "#5060a0", wordWrap: { width: pw - 20 },
      }).setOrigin(0, 0);
    } else {
      this.evidence.forEach(ev => {
        // Card background
        const cardGfx = this.add.graphics();
        cardGfx.fillStyle(0x12122a, 0.8);
        cardGfx.fillRect(px + 6, currentY, pw - 12, 36);
        cardGfx.lineStyle(1, 0x2a3a6a, 0.6);
        cardGfx.strokeRect(px + 6, currentY, pw - 12, 36);

        // Title
        this.add.text(px + 10, currentY + 4, ev.title, {
          fontFamily: FONT_BODY, fontSize: "8px", color: "#e8c97e",
        }).setOrigin(0, 0);

        // Text
        this.add.text(px + 10, currentY + 14, ev.text, {
          fontFamily: FONT_BODY, fontSize: "7px", color: "#9090b8", wordWrap: { width: pw - 20 },
        }).setOrigin(0, 0);

        currentY += 40;
      });
    }

    // MAKE ACCUSATION button (if 2+ evidence)
    if (this.evidence.length >= 2) {
      currentY += 8;
      const accGfx = this.add.graphics();
      const accX = px + 6, accY = currentY, accW = pw - 12, accH = 20;
      accGfx.fillStyle(0x1a1a3a, 0.9);
      accGfx.fillRect(accX, accY, accW, accH);
      accGfx.lineStyle(1, 0xff2244, 0.8);
      accGfx.strokeRect(accX, accY, accW, accH);

      const accText = this.add.text(accX + accW / 2, accY + accH / 2, "MAKE ACCUSATION", {
        fontFamily: FONT_BODY, fontSize: "8px", color: "#ff8888", letterSpacing: 1, align: "center",
      }).setOrigin(0.5, 0.5).setInteractive({ useHandCursor: true });

      accText.on("pointerdown", () => {
        this.scene.start("AccusationScene");
      });

      accText.on("pointerover", () => {
        accGfx.clear();
        accGfx.fillStyle(0x220a0a, 0.9);
        accGfx.fillRect(accX, accY, accW, accH);
        accGfx.lineStyle(1, 0xff2244, 0.9);
        accGfx.strokeRect(accX, accY, accW, accH);
      });

      accText.on("pointerout", () => {
        accGfx.clear();
        accGfx.fillStyle(0x1a1a3a, 0.9);
        accGfx.fillRect(accX, accY, accW, accH);
        accGfx.lineStyle(1, 0xff2244, 0.8);
        accGfx.strokeRect(accX, accY, accW, accH);
      });
    }
  }
```

- [ ] **Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "implement _showEvidenceBoard method"
```

---

### Task 7: Modify Node Click Handler

**Files:** `frontend/index.html` — find `_buildNode()` method (around line 666) and modify the pointerdown handler

- [ ] **Step 1: Locate _buildNode pointerdown handler**

Find this section in `_buildNode()`:

```js
    const zone = this.add.zone(x, y, bw, bh).setInteractive({ useHandCursor: true }).setDepth(2);
    zone.on("pointerdown", () => {
      this._openDialogue(nodeDef);
    });
```

- [ ] **Step 2: Replace with new handler**

Change `this._openDialogue(nodeDef)` to `this._showRichInfo(nodeDef)`:

```js
    const zone = this.add.zone(x, y, bw, bh).setInteractive({ useHandCursor: true }).setDepth(2);
    zone.on("pointerdown", () => {
      this._showRichInfo(nodeDef);
    });
```

- [ ] **Step 3: Commit**

```bash
git add frontend/index.html
git commit -m "modify node click handler to show rich info instead of dialogue"
```

---

### Task 8: Reposition Dialogue Box to Bottom-Left Floating

**Files:** `frontend/index.html` — find `_buildDialogueBox()` method (around line 1252)

- [ ] **Step 1: Locate _buildDialogueBox() method**

Find the method that currently creates a centered dialogue box.

- [ ] **Step 2: Replace positioning logic**

Change the box position from centered to bottom-left floating. Replace the `pw`, `ph`, `px`, `py` calculations:

```js
  _buildDialogueBox() {
    if (this._dialogueBox) this._dialogueBox.destroy();

    const pw = 440, ph = 200;      // Changed from ~580x220
    const px = 20, py = H - 20 - ph;  // bottom-left: left:20, bottom:20
```

Also update the container initialization if needed to match these new dimensions.

- [ ] **Step 3: Verify text and button positioning**

Ensure all child elements (speaker name, metadata, dialogue text, buttons) are positioned relative to the new `px`, `py` coordinates. They should scale or reposition proportionally.

- [ ] **Step 4: Commit**

```bash
git add frontend/index.html
git commit -m "reposition dialogue box to bottom-left floating layout"
```

---

### Task 9: Update MapScene.create() to Call New Methods

**Files:** `frontend/index.html` — find MapScene.create() method (around line 545–590)

- [ ] **Step 1: Locate evidence panel and accuse button calls**

Find these lines:
```js
    this._buildEvidencePanel();
    this._buildAccuseButton();
```

- [ ] **Step 2: Replace with new call**

Replace both lines with:
```js
    this._buildRichInfoPanel();
```

- [ ] **Step 3: Commit**

```bash
git add frontend/index.html
git commit -m "update create method to call _buildRichInfoPanel instead of evidence and accuse methods"
```

---

### Task 10: Remove Old Methods

**Files:** `frontend/index.html` — locate and remove `_buildEvidencePanel()` and `_buildAccuseButton()` methods

- [ ] **Step 1: Find _buildEvidencePanel() method**

Search for `_buildEvidencePanel() {` and identify its full extent.

- [ ] **Step 2: Delete _buildEvidencePanel()**

Remove the entire method.

- [ ] **Step 3: Find _buildAccuseButton() method**

Search for `_buildAccuseButton() {` and identify its full extent.

- [ ] **Step 4: Delete _buildAccuseButton()**

Remove the entire method.

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html
git commit -m "remove old _buildEvidencePanel and _buildAccuseButton methods"
```

---

### Task 11: Test Rich Info Panel Display

**Manual testing — no code changes, verification only**

- [ ] **Step 1: Start the backend server**

```bash
cd /home/pixel/Hackathon/catalog-noir/backend
uvicorn main:app --port 8765 &
```

Expected: Server starts, listening on port 8765

- [ ] **Step 2: Open game in browser**

Navigate to `http://localhost:8765/`

- [ ] **Step 3: Test node click → rich info display**

Click on each node (customers, stg_customers, dim_customers, customer_metrics) in sequence.

Expected for each:
- Rich info panel populates with correct node name, status color, health bar, owner, columns
- INTERVIEW button appears at bottom (except for dim_customers victim node)
- Dialogue box does NOT appear
- Previous node's metadata is replaced by new node's metadata

- [ ] **Step 4: Commit test observations**

```bash
git add frontend/index.html
git commit -m "verified rich info panel displays on node click"
```

---

### Task 12: Test Interview Dialogue Flow

**Manual testing**

- [ ] **Step 1: Game still running from Task 11**

- [ ] **Step 2: Click a non-victim node (e.g., stg_customers)**

Expected: Rich info panel shows, INTERVIEW button visible

- [ ] **Step 3: Click INTERVIEW button**

Expected:
- Dialogue box appears at bottom-left (floating, not centered)
- Rich info panel remains visible on the right
- Dialogue content is correct for that node
- COLLECT EVIDENCE, NEXT, DISMISS buttons are visible

- [ ] **Step 4: Click COLLECT EVIDENCE**

Expected: Evidence is added to `this.evidence` array

- [ ] **Step 5: Click DISMISS**

Expected:
- Dialogue box closes
- Rich info panel stays open showing node metadata
- Can click INTERVIEW again to re-open dialogue

- [ ] **Step 6: Click a different node**

Expected:
- Rich info panel updates to new node's metadata
- Dialogue closes (if open)

- [ ] **Step 7: Try clicking victim node (dim_customers)**

Expected:
- Rich info panel shows with status CRITICAL
- NO INTERVIEW button
- Cannot interview the victim

- [ ] **Step 8: Commit test observations**

```bash
git add frontend/index.html
git commit -m "verified interview dialogue flow and interactions"
```

---

### Task 13: Test Evidence Board

**Manual testing**

- [ ] **Step 1: Collect evidence from 2+ nodes**

Click nodes, click INTERVIEW, click COLLECT EVIDENCE on each.

- [ ] **Step 2: Click with no node selected**

Expected: Rich info panel shows EVIDENCE board with collected cards

- [ ] **Step 3: Verify MAKE ACCUSATION button appears**

Once 2+ evidence collected, the button should appear in the evidence board.

- [ ] **Step 4: Click MAKE ACCUSATION**

Expected: Game transitions to AccusationScene (existing flow continues)

- [ ] **Step 5: Commit test observations**

```bash
git add frontend/index.html
git commit -m "verified evidence board and accusation flow"
```

---

### Task 14: Test Accusation Flow (End-to-End)

**Manual testing — full game flow**

- [ ] **Step 1: Play through the game**

Collect evidence from stg_customers (the correct suspect), make accusation, go through confront scene, verify guilty verdict.

Expected: Existing game flow is unaffected. Only the UI layout has changed.

- [ ] **Step 2: Play again with wrong accusation**

Collect evidence from a different node, try accusing it. Should get "wrong" verdict.

Expected: Wrong accusation flow still works.

- [ ] **Step 3: Commit final verification**

```bash
git add frontend/index.html
git commit -m "verified full game flow end-to-end"
```

---

## Self-Review

**Spec Coverage:**
- ✅ Rich info panel (floating right) — Task 4
- ✅ Node metadata display (health, owner, columns, test, deps, diagnostic) — Task 5
- ✅ Evidence board display — Task 6
- ✅ Interview button triggering dialogue — Task 5/8
- ✅ Dialogue repositioned to bottom-left — Task 8
- ✅ Node click behavior changed — Task 7
- ✅ Victim node handling (no interview button) — Task 5
- ✅ Branch creation — Task 1
- ✅ Testing — Tasks 11–14

**Placeholder scan:** None found. All code steps include actual implementation.

**Type consistency:** 
- Panel container: `this.richPanelContainer`
- Mode: `this.richMode` ("none", "info", "evidence")
- Current node: `this.richCurrentNode`
- All references use same names throughout tasks

**No gaps identified.** Plan covers all spec requirements.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-25-rich-info-panel.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task (1–2 tasks per message), you review the result, fast iteration. Slower wall-clock time but thorough validation.

**2. Inline Execution** — Execute all tasks in this session using superpowers:executing-plans, with checkpoints after logical groups (e.g., after all data changes, after all new methods, after all tests). Faster for a straightforward plan like this.

Which approach would you prefer?