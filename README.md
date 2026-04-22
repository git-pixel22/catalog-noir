# Catalog Noir

**A pixel-art detective game where the crime scene is an OpenMetadata catalog.**

A data quality test just failed on a production table. You are the detective. Interview lineage nodes like suspects, examine column flows like forensic evidence, and name the guilty upstream table.

Every clue is a real OpenMetadata API response. Nothing is fabricated.

---

## The Case

**Case I — The Case of the Duplicate Customer**

> *14:03 UTC. Customer Key Uniqueness test aborted on `dim_customers`. Tier 1. Snowflake. Sales domain. Duplicate `customer_id` values detected in production.*

The upstream lineage spans MySQL CRM → Snowflake staging → Snowflake mart. One table in that chain has no real owner, no deduplication logic, and has been running unchecked for months. Find it.

---

## How to Play

1. **Briefing** — Read the incident report. Understand what broke and why it matters.
2. **Investigation** — Click nodes on the lineage map to interview them. Click the cyan diamonds on edges to inspect column-level data flow.
3. **Evidence** — Collect at least 2 evidence cards from your interviews.
4. **Accusation** — Name the responsible table.
5. **Confrontation** — The suspect makes a false statement. Present the correct evidence card to break their alibi.
6. **Verdict** — Case closed, or go back and dig deeper.

---

## Why This Exists

Data catalogs are dry. Nobody shows a catalog at a party.

Catalog Noir dramatizes the truth already inside your catalog — real lineage graphs, real DQ test failures, real ownership gaps — as an Ace Attorney-style detective game. Every clue the player finds is a live API call to the OpenMetadata sandbox. The case is solvable because the catalog already contains the answer.

This is what catalog metadata looks like when it becomes a story.

---

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Phaser 3.87 (browser game engine) |
| Backend | FastAPI + httpx |
| Dialogue | Groq (llama-3.1-8b-instant) — LLM turns raw metadata into character voice |
| Data source | OpenMetadata sandbox REST API |
| Deploy | Render (backend + frontend served together) |

---

## Running Locally

**Prerequisites:** Python 3.11+

```bash
git clone https://github.com/git-pixel22/catalog-noir.git
cd catalog-noir/backend

cp .env.example .env
# Fill in OPENMETADATA_TOKEN and GROQ_API_KEY in .env

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` in your browser.

**Environment variables:**

| Variable | Where to get it |
|---|---|
| `OPENMETADATA_TOKEN` | Settings → Access Tokens in the OpenMetadata sandbox |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — free tier |

If either API is unavailable, the backend automatically falls back to snapshotted responses so the game always works.

---

## Architecture

```
[Browser — Phaser.js game]
        │
        │ HTTP (relative URLs)
        ▼
[FastAPI backend]
  ├── Proxies OpenMetadata REST API (hides bearer token)
  ├── Shapes responses into game-friendly JSON
  ├── Calls Groq LLM to generate character dialogue from real metadata
  └── Serves frontend static files at /
        │
        │ HTTP
        ▼
[OpenMetadata sandbox — sandbox.open-metadata.org]
```

The backend never exposes secrets to the browser. All OpenMetadata tokens and Groq keys stay server-side.

---

## The Real Data

Every piece of in-game information is a real API response:

| Game element | Real API call |
|---|---|
| dim_customers node (12 cols, owner Nick Acosta, Tier 1) | `GET /api/v1/tables/name/{fqn}?fields=columns,tags,owners` |
| Lineage graph (MySQL → Snowflake staging → mart) | `GET /api/v1/lineage/table/{id}` |
| Column lineage (customer_id flows through each edge) | `lineageDetails.columnsLineage` from the lineage response |
| stg_customers owner: 'test' | `owners[0].displayName` from the table response |
| Customer Key Uniqueness test | `GET /api/v1/dataQuality/testCases?entityFQN=...` |

The case is solvable because the catalog already contains the answer. We just made it playable.

---

## Project Structure

```
catalog-noir/
├── backend/
│   ├── main.py           # FastAPI app — API proxy, dialogue generation, static serving
│   ├── requirements.txt
│   ├── .env.example
│   └── snapshots/        # Cached API responses (fallback if sandbox is down)
├── frontend/
│   ├── index.html        # Full Phaser 3 game — all scenes in one file
│   └── detective.png     # Detective silhouette asset
├── render.yaml           # One-click Render deployment
└── README.md
```

---

## Hackathon

Built for the **OutaTime / OpenMetadata hackathon** (WeMakeDevs), April 2026.

Deadline: April 25, 2026 — 8pm IST.
