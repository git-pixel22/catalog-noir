from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Catalog Noir")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = os.getenv("OPENMETADATA_BASE_URL", "https://sandbox.open-metadata.org")
TOKEN = os.getenv("OPENMETADATA_TOKEN", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

_OM_HEADERS = {"Authorization": f"Bearer {TOKEN}"}
_TABLE_FIELDS = "columns,tableConstraints,tags,owners,followers,usageSummary,testSuite"

_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.get("/", include_in_schema=False)
async def serve_game():
    return FileResponse(os.path.join(_FRONTEND, "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/table/{fqn:path}")
async def get_table(fqn: str):
    url = f"{BASE_URL}/api/v1/tables/name/{fqn}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, headers=_OM_HEADERS, params={"fields": _TABLE_FIELDS})
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/lineage/table/{fqn:path}")
async def get_lineage(fqn: str):
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{BASE_URL}/api/v1/tables/name/{fqn}",
            headers=_OM_HEADERS,
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        table_id = r.json()["id"]

        r2 = await client.get(
            f"{BASE_URL}/api/v1/lineage/table/{table_id}",
            headers=_OM_HEADERS,
            params={"upstreamDepth": 2, "downstreamDepth": 1},
        )
    if r2.status_code != 200:
        raise HTTPException(status_code=r2.status_code, detail=r2.text)

    raw = r2.json()
    entity = raw.get("entity", {})

    nodes = [{"id": entity["id"], "name": entity["name"],
               "fqn": entity["fullyQualifiedName"], "isCenter": True}]
    for n in raw.get("nodes", []):
        nodes.append({"id": n["id"], "name": n["name"],
                       "fqn": n["fullyQualifiedName"], "isCenter": False})

    edges = []
    for e in raw.get("upstreamEdges", []):
        edges.append({"from": e["fromEntity"], "to": e["toEntity"],
                       "direction": "upstream",
                       "columns": e.get("lineageDetails", {}).get("columnsLineage", [])})
    for e in raw.get("downstreamEdges", []):
        edges.append({"from": e["fromEntity"], "to": e["toEntity"],
                       "direction": "downstream",
                       "columns": e.get("lineageDetails", {}).get("columnsLineage", [])})

    return {"nodes": nodes, "edges": edges}


@app.get("/api/tests/table/{fqn:path}")
async def get_tests(fqn: str):
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{BASE_URL}/api/v1/dataQuality/testCases",
            headers=_OM_HEADERS,
            params={"entityFQN": fqn, "limit": 20, "fields": "testCaseResult"},
        )
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    data = r.json()
    return {
        "total": data.get("paging", {}).get("total", 0),
        "tests": [
            {
                "name": t["name"],
                "entityLink": t.get("entityLink", ""),
                "status": t.get("testCaseResult", {}).get("testCaseStatus"),
            }
            for t in data.get("data", [])
        ],
    }


@app.post("/api/dialogue")
async def get_dialogue(body: dict):
    name = body.get("name", "")
    service = body.get("serviceType", "Unknown")
    owner = body.get("owner", "Unknown")
    cols = body.get("columnCount", 0)
    role = body.get("role", "suspect")
    description = body.get("description", "")[:200]

    if not GROQ_KEY:
        return {"lines": _scripted_fallback(name, role, owner, cols, service), "source": "scripted"}

    case_context = (
        "CASE: A Customer Key Uniqueness DQ test aborted on dim_customers (Snowflake, Tier 1). "
        "Duplicate customer_ids are flowing through the lineage: "
        "customers (MySQL/CRM, owner: Ashish Gupta) -> stg_customers (Snowflake, owner: 'test') -> dim_customers. "
        "The GUILTY party is stg_customers: it has no real owner, no deduplication logic, "
        "and passes customer_id through unchecked. "
        "customers (raw) is INNOCENT: it has a customers_customer_id_unique test and Ashish Gupta as owner. "
        "customer_metrics is DOWNSTREAM: it just consumes dim_customers output, not a cause."
    )
    role_instruction = {
        "suspect": (
            "This character is THE GUILTY PARTY. Write 3 lines where they are defensive but "
            "each line accidentally reveals a damning fact. "
            "Line 1: mention that the owner field says 'test' - nobody real claimed them. "
            "Line 2: admit they pass customer_id through without checking for duplicates. "
            "Line 3: deflect blame to the raw source while implying their transformation has no rules. "
            "Do NOT use generic noir phrases. Every line must contain a specific metadata fact."
        ),
        "source": (
            "This character is INNOCENT. They should be confident and point the detective upstream or downstream. "
            "Their lines must reference real facts: they have a uniqueness test, a real owner (Ashish Gupta), "
            "and their data was clean when it left them. Point the detective at stg_customers."
        ),
        "downstream": (
            "This character is A VICTIM, not a cause. They consume bad data from dim_customers. "
            "Their lines should express confusion and point the detective upstream. "
            "Reference that their metrics are wrong because of what they receive, not what they do."
        ),
        "victim": (
            "This character is the crime scene. They are in distress. "
            "Reference the aborted test, the duplicate customer_ids, and point at the upstream lineage."
        ),
    }.get(role, "This character should speak evasively but reference their real metadata.")

    system = (
        "You are writing dialogue for a pixel-art detective game called Catalog Noir. "
        "Each database table is a character being interviewed. "
        "CRITICAL RULE: every line must contain a real, specific clue from the metadata. "
        "NO generic noir atmosphere without metadata facts. "
        "The player must be able to solve the case using the information in these lines. "
        "Tone: terse, slightly noir. Each line under 90 characters. "
        "Return exactly 3 lines, one per line, no numbering, no quotes, no extra text."
    )
    prompt = (
        f"CASE CONTEXT: {case_context}\n\n"
        f"CHARACTER INSTRUCTIONS: {role_instruction}\n\n"
        f"Character name: {name}\n"
        f"Service: {service}\n"
        f"Owner: {owner}\n"
        f"Columns: {cols}\n"
        f"Description: {description}\n\n"
        "Write 3 dialogue lines. Each must reference specific metadata facts from above:"
    )

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "max_tokens": 300,
                "temperature": 0.75,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
        )

    if r.status_code != 200:
        return {"lines": _scripted_fallback(name, role, owner, cols, service), "source": "scripted"}

    text = r.json()["choices"][0]["message"]["content"].strip()
    lines = [l.strip() for l in text.split("\n") if l.strip()][:3]
    fallback = _scripted_fallback(name, role, owner, cols, service)
    while len(lines) < 3:
        lines.append(fallback[len(lines)])
    return {"lines": lines, "source": "llm"}


def _scripted_fallback(name: str, role: str, owner: str, cols: int, service: str) -> list[str]:
    if role == "victim":
        return [
            f"I'm {name}. Tier 1. {cols} columns. The test just... aborted.",
            f"Owner is {owner}. But lately it feels like nobody's watching.",
            "Something upstream changed. I can feel it in my customer_id column.",
        ]
    if role == "downstream":
        return [
            f"I'm {name}. I just consume what comes through. I didn't cause this.",
            f"I run on {service}. My job is metrics, not data quality.",
            "Check upstream. The contamination didn't start with me.",
        ]
    return [
        f"I'm {name}. {service}. {cols} columns. I transform the raw data.",
        f"My owner? It says '{owner}'. That's... a placeholder. Nobody claimed me.",
        "I pass data through. What happens before me isn't my problem.",
    ]
