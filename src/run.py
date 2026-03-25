#!/usr/bin/env python3
"""Usage: python run.py [--generate|--serve|--live|--live-teams]"""
import sys, os, json, yaml
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

DIR = Path(__file__).parent
INDEX = DIR / "index.html"

def load_config():
    with open(DIR / "config.yaml") as f:
        return yaml.safe_load(f)

def generate():
    from ingest import ingest
    from extract import extract
    from synthesize import synthesize
    from render import render
    cfg = load_config()
    reports = []
    for topic in cfg.get("topics", []):
        name = topic["name"]
        paths = topic.get("paths", [])
        print(f"\n{'='*50}\nTopic: {name}\n{'='*50}")
        print("Ingesting...")
        docs = ingest(paths, cfg)
        if not docs:
            reports.append({
                "name": name,
                "data": {
                    "status_summary": "No documents found.",
                    "risk_level": "unknown",
                    "items": [],
                    "recommended_sequence": [],
                    "blockers": []
                }
            })
            continue
        print("Extracting...")
        items = extract(docs, name, cfg)
        print("Synthesizing...")
        report_json = synthesize(name, items, cfg)
        data = json.loads(report_json)
        reports.append({"name": name, "data": data})
    print("\nRendering...")
    render(reports, str(INDEX))
    print("Done.")

def live(cfg):
    """Live transcription mode: capture mic → transcribe → extract → synthesize → render."""
    from transcribe import LiveTranscriber
    from extract import extract
    from synthesize import synthesize
    from render import render

    live_cfg = cfg.get("live", {})
    language = live_cfg.get("language", "de")
    prompt = live_cfg.get("initial_prompt", "")
    model_size = live_cfg.get("model_size", "large-v3")
    chunk_seconds = live_cfg.get("chunk_seconds", 15)
    topic_name = live_cfg.get("topic_name", "Live Lecture")

    print(f"\n{'='*50}")
    print(f"Live Transcription: {topic_name}")
    print(f"Language: {language} | Model: {model_size} | Chunk: {chunk_seconds}s")
    print(f"{'='*50}")

    t = LiveTranscriber(
        language=language,
        initial_prompt=prompt,
        model_size=model_size,
        chunk_seconds=chunk_seconds,
    )
    t.start()

    print("\n  Press Enter to stop transcription...\n")
    try:
        input()
    except KeyboardInterrupt:
        pass

    t.stop()
    docs = t.as_documents(topic_name)

    if not docs or not docs[0]["text"]:
        print("No speech detected.")
        return

    print(f"\n  Transcript: {len(docs[0]['text'])} chars")
    print("Extracting...")
    items = extract(docs, topic_name, cfg)
    print("Synthesizing...")
    report_json = synthesize(topic_name, items, cfg)
    data = json.loads(report_json)
    reports = [{"name": topic_name, "data": data}]
    print("Rendering...")
    render(reports, str(INDEX))
    print("Done.")


def live_teams(cfg):
    """Live Teams/Zoom/Meet mode: capture system audio loopback → transcribe → extract → synthesize → render.

    Automatically detects the system loopback device — no manual device selection needed.
    On Windows and Linux this works out of the box.  On macOS, install BlackHole first:
        brew install blackhole-2ch
    """
    from transcribe import LiveTranscriber
    from extract import extract
    from synthesize import synthesize
    from render import render

    live_cfg = cfg.get("live", {})
    language = live_cfg.get("language", "de")
    prompt = live_cfg.get("initial_prompt", "")
    model_size = live_cfg.get("model_size", "large-v3")
    chunk_seconds = live_cfg.get("chunk_seconds", 15)
    topic_name = live_cfg.get("topic_name", "Live Lecture")

    print(f"\n{'='*50}")
    print(f"Live Teams Transcription: {topic_name}")
    print(f"Language: {language} | Model: {model_size} | Chunk: {chunk_seconds}s")
    print(f"Capturing system audio output (loopback)...")
    print(f"{'='*50}")

    t = LiveTranscriber(
        language=language,
        initial_prompt=prompt,
        model_size=model_size,
        chunk_seconds=chunk_seconds,
        loopback=True,
    )
    t.start()

    print("\n  Press Enter to stop transcription...\n")
    try:
        input()
    except KeyboardInterrupt:
        pass

    t.stop()
    docs = t.as_documents(topic_name)

    if not docs or not docs[0]["text"]:
        print("No audio detected.")
        return

    print(f"\n  Transcript: {len(docs[0]['text'])} chars")
    print("Extracting...")
    items = extract(docs, topic_name, cfg)
    print("Synthesizing...")
    report_json = synthesize(topic_name, items, cfg)
    data = json.loads(report_json)
    reports = [{"name": topic_name, "data": data}]
    print("Rendering...")
    render(reports, str(INDEX))
    print("Done.")

def serve(cfg):
    os.chdir(DIR)
    host, port = cfg.get("host", "0.0.0.0"), cfg.get("port", 8899)
    server = HTTPServer((host, port), SimpleHTTPRequestHandler)
    print(f"\nServing at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    cfg = load_config()
    args = set(sys.argv[1:])
    if "--serve" in args:
        if not INDEX.exists():
            print("No index.html. Run without --serve first.")
            sys.exit(1)
        serve(cfg)
    elif "--live-teams" in args:
        live_teams(cfg)
        if "--serve" not in args:
            serve(cfg)
    elif "--live" in args:
        live(cfg)
        if "--serve" not in args:
            serve(cfg)
    elif "--generate" in args:
        generate()
    else:
        generate()
        serve(cfg)