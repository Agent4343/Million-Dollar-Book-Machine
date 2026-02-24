#!/usr/bin/env python3
"""
Seed script: Create and run a dark romance book project.

Usage:
    # On Railway / locally with ANTHROPIC_API_KEY set:
    python seed_dark_romance.py

    # Or with a custom server URL:
    BOOK_SERVER=https://your-app.railway.app python seed_dark_romance.py

This creates the "Vow of Ruin" project and starts the full pipeline.
"""

import json
import os
import sys
import time

import requests

BASE = os.environ.get("BOOK_SERVER", "http://localhost:3000")
PASSWORD = os.environ.get("APP_PASSWORD", "")

if not PASSWORD:
    print("ERROR: Set APP_PASSWORD environment variable")
    sys.exit(1)

session = requests.Session()

# --- Auth ---
print(f"Connecting to {BASE}...")
r = session.post(f"{BASE}/api/auth/login", json={"password": PASSWORD})
if not r.ok:
    print(f"Login failed: {r.status_code} {r.text}")
    sys.exit(1)
print("Authenticated.")

# --- Check LLM ---
r = session.get(f"{BASE}/api/system/llm-status")
llm = r.json()
if not llm.get("enabled"):
    print("WARNING: LLM not enabled. Set ANTHROPIC_API_KEY for real content.")
    print("Continuing in demo mode...\n")
else:
    print(f"LLM ready: {llm['model']}")
    if llm.get("opus_enabled"):
        print(f"  Opus enabled for creative agents (higher cost)")
    else:
        print(f"  Using Sonnet for all agents (cost-optimized)")

# --- Create Project ---
PROJECT = {
    "title": "Vow of Ruin",
    "genre": "Dark Romance",
    "target_word_count": 85000,
    "description": (
        "A headstrong prosecutor is forced into an arranged marriage with the "
        "ruthless heir of a rival crime family to seal a blood truce\u2014but she "
        "is secretly building a case to destroy his empire from within, and he knows it."
    ),
    "comparable_titles": [
        "Twisted Love by Ana Huang",
        "Haunting Adeline by H.D. Carlton",
        "Den of Vipers by K.A. Knight",
        "Corrupt by Penelope Douglas",
        "Ruthless People by J.J. McAvoy",
    ],
    "themes": [
        "Power and surrender",
        "Trust vs. betrayal",
        "Revenge vs. forgiveness",
        "Found family in dark places",
        "The cost of loyalty",
        "Love as both weapon and salvation",
    ],
    "target_audience": (
        "Women 18-45 who read dark romance, BookTok and Bookstagram audience, "
        "fans of Rina Kent, Penelope Douglas, Ana Huang, and Danielle Lori"
    ),
    "tone": "Dark, intense, emotionally raw, morally complex, sensual with sharp wit",
    "additional_constraints": {
        "sub_genre": "Mafia Dark Romance / Arranged Marriage",
        "concept_hook": (
            "A headstrong prosecutor is forced into an arranged marriage with the "
            "ruthless heir of a rival crime family to seal a blood truce\u2014but she "
            "is secretly building a case to destroy his empire from within, and he knows it."
        ),
        "protagonist_description": (
            "Sera Marchetti, 27, a fierce federal prosecutor with a personal vendetta "
            "against organized crime. Her mother was killed in a mob hit when she was 12. "
            "Whip-smart, emotionally guarded, refuses to be a victim. Uses her legal mind "
            "as her weapon. Deeply lonely beneath the armor."
        ),
        "love_interest_description": (
            "Dante Valeri, 31, heir to the Valeri crime syndicate. Terrifyingly intelligent, "
            "controlled violence, possessive but not abusive. Has his own code of honor. "
            "Scarred\u2014literally and figuratively\u2014from being groomed for brutality "
            "since childhood. Sees Sera as both a threat and the only person who has ever "
            "challenged him as an equal."
        ),
        "central_conflict": (
            "Sera must choose between destroying Dante and the empire that killed her mother "
            "or surrendering to the devastating connection between them. Dante must decide if "
            "protecting Sera is worth burning down everything his family built. Both are "
            "playing each other\u2014until neither can tell where the game ends and the "
            "truth begins."
        ),
        "steam_level": (
            "High \u2014 explicit but emotionally driven. Tension-first, not gratuitous. "
            "Every intimate scene must advance character development or shift the power dynamic."
        ),
        "content_warnings": (
            "Violence (organized crime context), explicit sexual content, morally grey "
            "characters, themes of captivity and control, references to parental death, "
            "blood and injury"
        ),
        "pov": "Dual first-person POV alternating Sera and Dante chapters",
        "setting": (
            "Modern-day Boston and coastal Maine. Old-money crime families operating behind "
            "legitimate business fronts. Gothic mansions, underground fight rings, federal "
            "courthouses, harbor-front warehouses."
        ),
        "series_potential": (
            "Book 1 of Bloodline Vows series. Each book follows a different couple within "
            "the interconnected crime families. Book 2: Dante's younger sister + Sera's FBI "
            "partner. Book 3: The rival family's enforcer + a witness in protection."
        ),
        "reader_promise": (
            "A slow-burn arranged marriage between enemies where both are playing a dangerous "
            "game, with scorching chemistry, gut-punch twists, and a hard-won HEA."
        ),
        "tropes": [
            "Arranged marriage",
            "Enemies to lovers",
            "Morally grey MMC",
            "Touch her and die",
            "Who did this to you",
            "Only soft for her",
            "Forced proximity",
            "He falls first but she falls harder",
            "Dual POV",
            "Mafia romance",
        ],
        "ending_type": "HEA \u2014 Happily Ever After, earned through sacrifice",
        "chapter_count": 28,
        # --- Publishing metadata ---
        "author_name": "V. Marchetti",
        "pen_name": "V. Marchetti",
        "series_name": "Bloodline Vows",
        "series_number": 1,
        "publisher_name": "Marchetti Press",
        "dedication": (
            "For every woman who was told she was too much.\n"
            "You were always exactly enough."
        ),
        "about_author": (
            "V. Marchetti writes dark romance for readers who like their love stories "
            "with teeth. When not crafting morally questionable heroes, she can be found "
            "consuming dangerous amounts of espresso and arguing with fictional characters. "
            "Vow of Ruin is the first book in the Bloodline Vows series."
        ),
        "newsletter_cta": (
            "Join the Inner Circle for exclusive bonus scenes, early cover reveals, "
            "and a FREE prequel novella."
        ),
        "newsletter_url": "https://vmarchetti.com/innercircle",
        "acknowledgements": (
            "To the readers who crave stories that make them feel everything\u2014"
            "this one is for you."
        ),
        # --- Amazon KDP optimization ---
        "amazon_keywords_target": [
            "dark romance arranged marriage",
            "mafia romance books",
            "enemies to lovers dark romance",
            "morally grey hero romance",
            "possessive hero romance",
            "organized crime romance",
            "dark romance series",
        ],
        "bisac_categories_target": ["FIC027310", "FIC027020"],
    },
}

print(f"\nCreating project: {PROJECT['title']}...")
r = session.post(f"{BASE}/api/projects", json=PROJECT)
if not r.ok:
    print(f"Create failed: {r.status_code} {r.text}")
    sys.exit(1)

data = r.json()
project_id = data["project_id"]
print(f"Project created: {project_id}")
print(f"  {data['message']}")

# --- Start Pipeline ---
print(f"\nStarting full pipeline...")
r = session.post(f"{BASE}/api/projects/{project_id}/run-job", json={"max_iterations": 200})
if not r.ok:
    print(f"Run failed: {r.status_code} {r.text}")
    sys.exit(1)

job = r.json()
job_id = job["job_id"]
print(f"Pipeline job started: {job_id}")

# --- Poll Progress ---
print("\nMonitoring progress (Ctrl+C to detach \u2014 pipeline continues in background):\n")
last_agent = None
try:
    while True:
        time.sleep(8)
        r = session.get(f"{BASE}/api/jobs/{job_id}")
        if not r.ok:
            print(f"  Poll error: {r.status_code}")
            continue

        status = r.json()
        job_status = status.get("status", "unknown")
        progress = status.get("progress", {})
        current = progress.get("last_agent") or progress.get("current_agent", "?")

        if current != last_agent:
            last_agent = current
            layer = progress.get("current_layer", "?")
            gate = "PASS" if progress.get("last_gate_passed") else ""
            remaining = progress.get("available_agents_count", "?")
            print(f"  Layer {layer} | Agent: {current:30s} {gate}  (remaining: {remaining})")

        if job_status in ("succeeded", "failed", "blocked", "cancelled"):
            print(f"\n{'='*60}")
            print(f"Pipeline finished: {job_status.upper()}")
            if job_status == "succeeded":
                print(f"\nYour book is ready! Export it:")
                print(f"  EPUB:  GET {BASE}/api/projects/{project_id}/export/epub")
                print(f"  DOCX:  GET {BASE}/api/projects/{project_id}/export/docx")
                print(f"\nOr open the web UI and click 'Kindle/EPUB (.epub)' to download.")
            elif job_status == "failed":
                print(f"Error: {status.get('error', 'unknown')}")
                print(f"\nTo resume: POST {BASE}/api/jobs/{job_id}/resume")
            elif job_status == "blocked":
                print(f"Blocked: {status.get('error', 'unknown')}")
            print(f"{'='*60}")
            break

except KeyboardInterrupt:
    print(f"\n\nDetached. Pipeline continues in background.")
    print(f"  Check status:  GET {BASE}/api/jobs/{job_id}")
    print(f"  Project ID:    {project_id}")
    print(f"  Cancel:        POST {BASE}/api/jobs/{job_id}/cancel")

print(f"\nProject ID: {project_id}")
print(f"Job ID:     {job_id}")
