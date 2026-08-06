#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "raw-material" / "youtube" / "transcript-index.json"
CONCEPTS = ROOT / "analysis" / "concepts" / "concept-atlas.json"
EVIDENCE = ROOT / "analysis" / "evidence" / "evidence-ledger.json"

THEMES = [
    {
        "id": "humanoid-robotics",
        "name": "Humanoid Robotics",
        "keywords": ["humanoid", "humanoids", "robot", "robots", "robotics"],
        "definition": "Humanoid robotics is the effort to build general-purpose robots shaped for human environments and work routines.",
        "problem": "Factories, warehouses, homes, and public spaces are built around human bodies, tools, and assumptions.",
        "first": "If the environment is human-shaped, a robot with compatible mobility, manipulation, perception, and safety behavior can reuse existing infrastructure instead of requiring every workplace to be rebuilt.",
    },
    {
        "id": "physical-ai",
        "name": "Physical AI",
        "keywords": ["physical ai", "embodied", "embodiment", "motion", "world", "real world"],
        "definition": "Physical AI is AI that must act in the real world, where perception, control, uncertainty, latency, safety, and hardware constraints matter.",
        "problem": "Text systems can retry cheaply; physical systems must handle friction, delay, contact, failures, and safety boundaries.",
        "first": "An embodied system closes the loop from sensing to planning to action to observation. Intelligence is judged by whether the loop works under physical constraints.",
    },
    {
        "id": "robot-scaling",
        "name": "Scaling Robot Deployment",
        "keywords": ["scale", "scaling", "deployment", "deploy", "fleet", "operations"],
        "definition": "Scaling robot deployment means moving from impressive demos to repeatable field operation across customers, sites, and tasks.",
        "problem": "A single robot demo can hide installation cost, maintenance burden, edge cases, and unit economics.",
        "first": "Deployment scales only when hardware reliability, software updates, support operations, safety validation, and customer workflow integration improve together.",
    },
    {
        "id": "language-to-action",
        "name": "Language To Action",
        "keywords": ["language", "instruction", "commands", "motion", "action", "natural language"],
        "definition": "Language-to-action connects human instructions to robot perception, planning, motion, and tool use.",
        "problem": "Humans want to describe goals in ordinary language, while robots need grounded states, coordinates, constraints, and executable policies.",
        "first": "The system must translate a symbolic or linguistic goal into a grounded action plan, then continuously check whether the physical world matches the plan.",
    },
    {
        "id": "robot-data",
        "name": "Robot Data And Learning",
        "keywords": ["data", "training", "learn", "learning", "simulation", "teleoperation"],
        "definition": "Robot data is the collection of demonstrations, sensor traces, simulations, failures, and field logs that teaches embodied systems what to do.",
        "problem": "Robotics lacks the internet-scale natural data advantage that language models had.",
        "first": "A robot learns from trajectories, not just labels. Useful data must connect observations, actions, outcomes, and context.",
    },
    {
        "id": "robot-hardware",
        "name": "Robot Hardware And Components",
        "keywords": ["hardware", "component", "actuator", "sensor", "manufacturing", "supply chain"],
        "definition": "Robot hardware includes the actuators, sensors, compute, batteries, materials, and manufacturing systems that turn AI into embodied work.",
        "problem": "A clever policy cannot overcome weak actuators, poor sensing, fragile mechanisms, or uneconomic manufacturing.",
        "first": "Physical capability is bounded by hardware: force, precision, endurance, cost, repairability, and manufacturability.",
    },
    {
        "id": "robot-business",
        "name": "Robot Business Models",
        "keywords": ["business", "market", "customer", "roi", "cost", "commercial", "product"],
        "definition": "Robot business models decide who pays, what workflow is improved, how reliability is guaranteed, and how value exceeds deployment cost.",
        "problem": "Robots can be technically impressive while failing to create a purchaseable, maintainable product.",
        "first": "A robot company sells an operational outcome, not a robot demo. The economics must include uptime, integration, support, safety, and labor substitution or augmentation.",
    },
    {
        "id": "robot-safety",
        "name": "Robot Safety And Trust",
        "keywords": ["safety", "trust", "risk", "reliable", "reliability", "human"],
        "definition": "Robot safety and trust cover the controls, validation, norms, and operational practices that make humans willing to share space and work with robots.",
        "problem": "Physical failures can damage property or harm people, so acceptable error rates are much lower than in software-only systems.",
        "first": "Safety is a systems property: perception, motion constraints, fail-safes, human factors, monitoring, and accountability must work together.",
    },
    {
        "id": "agentic-ai-workflows",
        "name": "Agentic AI Workflows",
        "keywords": ["agent", "agents", "workflow", "automation", "processing", "tools"],
        "definition": "Agentic AI workflows use models and tools to perform multi-step work across software, documents, web data, and operations.",
        "problem": "Many valuable tasks require search, state, tool use, verification, and repeated decisions rather than one answer.",
        "first": "An agentic workflow is a feedback loop: plan, act, observe, verify, and revise until a useful operational state is reached.",
    },
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z-]{2,}", text.lower())


def excerpt(text: str, keywords: list[str]) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    lower = compact.lower()
    hit_positions = [lower.find(keyword) for keyword in keywords if lower.find(keyword) >= 0]
    start = min(hit_positions) if hit_positions else 0
    start = max(0, start - 80)
    snippet = compact[start : start + 190]
    snippet = re.sub(r"\s+", " ", snippet).strip()
    return snippet


def title_case_topic(title: str) -> str:
    clean = re.sub(r"\|.*$", "", title)
    clean = re.sub(r"\([^)]*\)", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def main() -> int:
    rows = load_json(INDEX)
    available = [row for row in rows if row.get("transcript_status") == "available"]
    theme_hits: dict[str, list[dict[str, Any]]] = defaultdict(list)
    evidence: list[dict[str, Any]] = []

    for row in available:
        text = (ROOT / row["clean_txt"]).read_text(encoding="utf-8", errors="ignore")
        haystack = f"{row['title']} {text}".lower()
        for theme in THEMES:
            score = sum(haystack.count(keyword) for keyword in theme["keywords"])
            if score <= 0:
                continue
            theme_hits[theme["id"]].append({"row": row, "score": score, "text": text})

    concepts: list[dict[str, Any]] = []
    for theme in THEMES:
        hits = sorted(theme_hits.get(theme["id"], []), key=lambda item: item["score"], reverse=True)
        if not hits:
            continue
        ev_ids = []
        for rank, hit in enumerate(hits[:3], start=1):
            row = hit["row"]
            snippet = excerpt(hit["text"], theme["keywords"])
            ev_id = f"{theme['id']}-{rank:02d}"
            ev_ids.append(ev_id)
            evidence.append(
                {
                    "id": ev_id,
                    "lecture_index": int(row["index"]),
                    "video_id": row["id"],
                    "title": f"{theme['name']} in {title_case_topic(row['title'])}",
                    "url": row["url"],
                    "quote": snippet,
                    "source_tier": "youtube-caption",
                    "evidence_type": "title/transcript keyword support",
                    "supports_concepts": [theme["id"]],
                    "why_span_matters": f"This talk is one of the strongest transcript matches for {theme['name'].lower()} in the MACHINA Summit playlist.",
                }
            )
        concepts.append(
            {
                "id": theme["id"],
                "name": theme["name"],
                "theme": "physical-ai and robotics",
                "plain_language_definition": theme["definition"],
                "ordinary_problem": theme["problem"],
                "naive_picture": "The naive view is that a polished demo or a larger model is enough to make the capability real.",
                "why_naive_fails": "Robotics and agentic systems fail in integration: data, hardware, deployment, verification, safety, cost, and customer workflows all interact.",
                "first_principles": theme["first"],
                "what_breaks_without_it": "Without this concept, it is easy to confuse a narrow prototype with a repeatable system that can operate in real environments.",
                "course_role": f"This theme organizes summit talks related to {theme['name'].lower()} and gives us a first-pass route for later deep dives.",
                "evidence_ids": ev_ids,
            }
        )

    title_words = Counter()
    for row in rows:
        title_words.update(word for word in words(row["title"]) if word not in {"machina", "summit", "with", "from", "today", "beyond"})

    CONCEPTS.write_text(json.dumps(concepts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    EVIDENCE.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "analysis" / "title-keywords.json").write_text(
        json.dumps(title_words.most_common(60), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(concepts)} concepts, {len(evidence)} evidence anchors from {len(available)} transcripts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
