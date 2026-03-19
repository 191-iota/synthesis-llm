#!/usr/bin/env python3
"""Usage: python run.py [--generate|--serve]"""
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
    elif "--generate" in args:
        generate()
    else:
        generate()
        serve(cfg)