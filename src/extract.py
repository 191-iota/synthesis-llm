import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from llm import ask

EXTRACT_PROMPT = """You are extracting ALL important information from a document belonging to the topic "{topic}".

Extract everything that helps someone understand:
- What needs to be done (tasks, assignments, deliverables, requirements, submissions)
- When things happen (deadlines, milestones, scheduled events, exam dates, meetings)
- How things relate (prerequisites, dependencies, sequences, what must come before what)
- Who is involved (instructors, contacts, team members, responsible parties)
- What things ARE (module descriptions, learning objectives, grading criteria, weightings, rules)
- Current progress or status indicators (completion %, grades, pass/fail criteria)
- Resources and materials (required readings, tools, links, platforms)

For each item, return a JSON array of objects:
{{
  "item": "what this is about — be specific and complete",
  "type": "task" | "deadline" | "milestone" | "info" | "resource" | "person" | "rule" | "dependency",
  "date": "YYYY-MM-DD or null",
  "urgency": "high" | "medium" | "low" | "info",
  "detail": "additional context, explanation, or nuance (1-2 sentences)",
  "depends_on": "what must be completed before this, or null",
  "people": ["names of people involved, if any"],
  "source_quote": "exact phrase from document (max 25 words)",
  "weight": "grading weight or importance if mentioned, e.g. '40%', or null"
}}

Be thorough. Extract EVERYTHING that would help someone build a complete mental model of this topic.
If nothing relevant exists, return: []
Return ONLY valid JSON. No explanation, no markdown."""

REEXTRACT_PROMPT = """You previously extracted these items from a document for topic "{topic}":

{previous_items}

Re-read the document carefully. Find anything you MISSED:
- Subtle requirements buried in paragraphs
- Implied dependencies (X must be done before Y)
- Grading criteria, pass/fail rules, weightings
- Contact info, office hours, platform details
- Dates mentioned in passing
- Context that helps understand other items better

Return a JSON array of ONLY NEW items (same format).
If you found everything, return: []
Return ONLY valid JSON."""


def _shard(documents, shard_size):
    shards = []
    for doc in documents:
        text, path = doc["text"], doc["path"]
        if len(text) <= shard_size:
            shards.append({"text": text, "sources": [path]})
        else:
            start = 0
            while start < len(text):
                end = start + shard_size
                if end < len(text):
                    nl = text.rfind('\n\n', start, end)
                    if nl > start + shard_size // 2:
                        end = nl
                shards.append({"text": text[start:end], "sources": [path]})
                start = end
    return shards


def _parse_json(text):
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[-1]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        s, e = text.find('['), text.rfind(']')
        if s >= 0 and e > s:
            try:
                return json.loads(text[s:e+1])
            except json.JSONDecodeError:
                pass
    return []


def _items_match(a, b):
    a_w = set(a.get("item", "").lower().split())
    b_w = set(b.get("item", "").lower().split())
    if not a_w or not b_w:
        return False
    return len(a_w & b_w) / max(len(a_w), len(b_w)) > 0.5


def _dedupe(items):
    unique = []
    for item in items:
        if not any(_items_match(item, u) for u in unique):
            unique.append(item)
    return unique


def _process_shard(i, shard, topic_name, cfg, total):
    # Pass 1: main extraction
    resp = ask(EXTRACT_PROMPT.format(topic=topic_name), shard["text"], cfg)
    pass1 = _parse_json(resp)
    for item in pass1:
        item["_sources"] = shard["sources"]

    # Pass 2: re-extraction for missed items
    prev = json.dumps(pass1, indent=2) if pass1 else "[]"
    resp2 = ask(
        REEXTRACT_PROMPT.format(topic=topic_name, previous_items=prev),
        shard["text"], cfg
    )
    pass2 = _parse_json(resp2)
    for item in pass2:
        item["_sources"] = shard["sources"]

    a_items = pass1 + pass2
    print(f"    shard {i+1}/{total}: {len(pass1)}+{len(pass2)} items")

    # Confirmation pass
    resp_b = ask(EXTRACT_PROMPT.format(topic=topic_name), shard["text"], cfg)
    b_items = _parse_json(resp_b)
    for item in b_items:
        item["_sources"] = shard["sources"]

    return a_items, b_items


def extract(documents, topic_name, cfg):
    shards = _shard(documents, cfg.get("shard_size", 75000))
    print(f"  {len(shards)} shards")
    if not shards:
        return []

    run_a = []
    run_b = []
    workers = 1

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_process_shard, i, shard, topic_name, cfg, len(shards)): i
            for i, shard in enumerate(shards)
        }
        for future in as_completed(futures):
            a_items, b_items = future.result()
            run_a.extend(a_items)
            run_b.extend(b_items)

    confirmed = []
    for a_item in run_a:
        if any(_items_match(a_item, b_item) for b_item in run_b):
            confirmed.append(a_item)

    # For info/resource/person types, be more lenient — keep even unconfirmed
    # since these are contextual and less likely to be hallucinated
    info_types = {"info", "resource", "person", "rule"}
    unconfirmed_info = [
        i for i in run_a
        if i.get("type") in info_types
        and i.get("source_quote", "").strip()
        and not any(_items_match(i, c) for c in confirmed)
    ]
    confirmed.extend(unconfirmed_info)

    grounded = [i for i in confirmed if i.get("source_quote", "").strip()]
    final = _dedupe(grounded)

    print(f"  Extraction: {len(run_a)} raw -> {len(confirmed)} confirmed -> {len(final)} final")
    return final
