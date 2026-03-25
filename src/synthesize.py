import json
from llm import ask
from datetime import date as _date

SYNTH_PROMPT = """Today's date is {today}. You are generating a strategic briefing for the topic: "{topic}"

Below are all confirmed items extracted from source documents — tasks, deadlines, info, resources, rules, dependencies, and people.

CRITICAL ASSUMPTION: If an item's deadline has ALREADY PASSED, assume it was completed on time UNLESS the documents contain explicit evidence that it was NOT done (e.g. "missing", "incomplete", "not submitted", "failed", "pending"). Most people meet their deadlines. Do not panic about past dates.

Return ONLY a JSON object with this exact structure:
{{
  "status_summary": "2-3 sentence executive summary focusing on what's AHEAD, not what's behind. Be forward-looking.",
  "risk_level": "critical" | "warning" | "on_track" | "unknown",
  "context": "2-3 sentences explaining what this topic IS — the big picture for someone seeing it fresh",
  "items": [
    {{
      "title": "short action title",
      "detail": "1-2 sentence explanation with full context",
      "date": "YYYY-MM-DD or null",
      "end_date": "YYYY-MM-DD or null (for ranges/periods)",
      "urgency": "high" | "medium" | "low" | "info",
      "status": "done" | "due_soon" | "upcoming" | "ongoing" | "no_date" | "behind",
      "category": "deadline" | "deliverable" | "blocker" | "milestone" | "task" | "info" | "resource" | "rule",
      "depends_on": "title of another item this depends on, or null",
      "people": ["relevant people"],
      "weight": "grading weight if applicable, or null",
      "source_file": "filename",
      "source_quote": "evidence quote"
    }}
  ],
  "people": [
    {{"name": "Person Name", "role": "their role or relevance"}}
  ],
  "recommended_sequence": [
    "First do X — because Y",
    "Then do Z — because W"
  ],
  "blockers": ["blocker description"],
  "key_rules": ["important rules, grading criteria, or constraints to keep in mind"]
}}

Rules for status assignment:
- date < {today} with NO evidence of failure -> "done" (assume completed)
- date < {today} with EXPLICIT evidence of failure/non-completion -> "behind" (genuinely missed)
- date within 7 days of {today} -> "due_soon"
- date > 7 days from {today} -> "upcoming"
- no date -> "no_date"

Other rules:
- Order items by date (chronological). Done items still appear for context but are not urgent.
- The recommended_sequence should ONLY include items that still need action (due_soon, upcoming, behind). Do not tell the user to do things that are already done.
- Only flag blockers that are CURRENT obstacles, not resolved past issues.
- risk_level should reflect the ACTUAL situation: if everything past is done and next deadlines are manageable, that's "on_track", not "critical".
- Be concrete. Use names, dates, percentages.
- Do NOT invent items. Only use what is provided.
- If an item is "behind", you may add a brief note in the recommended_sequence about catching up.
- Return ONLY valid JSON."""


TRANSCRIPT_SYNTH_PROMPT = """You are analyzing a transcript of spoken content (lecture, interview, meeting, or conversation) about: "{topic}"

Below is the raw timestamped transcript text.

IMPORTANT: This is NOT a project document. Do NOT look for tasks, deadlines, or project statuses.
Instead:
- Extract themes and topics discussed, not tasks or deliverables
- Preserve who said what (speaker attribution)
- Reference timestamps from the [MM:SS] markers in the transcript
- Identify key claims and factual statements made
- Summarize the content for someone who wasn't there
- Note any content warnings if sensitive topics are discussed (violence, illegal activities, trauma, etc.)

Return ONLY a JSON object with this exact structure:
{{
  "title": "descriptive title for what was discussed",
  "summary": "3-5 sentence summary of the key points discussed",
  "topics": [
    {{
      "heading": "topic or theme discussed",
      "summary": "what was said about this topic",
      "timestamps": ["MM:SS"],
      "key_quotes": ["exact quote from transcript"]
    }}
  ],
  "people": [
    {{"name": "Person", "role": "their role in the discussion", "mentions": ["what they said or was said about them"]}}
  ],
  "key_claims": [
    {{
      "claim": "specific factual claim or statement made",
      "speaker": "who said it or null",
      "timestamp": "MM:SS or null",
      "source_quote": "exact quote"
    }}
  ],
  "takeaways": ["key insight or conclusion from the discussion"],
  "content_warnings": ["any sensitive topics discussed, if applicable"]
}}

- Be concrete. Use names and timestamps where available.
- Do NOT invent content. Only use what is in the transcript.
- Return ONLY valid JSON."""


def synthesize_transcript(topic_name, items, cfg):
    if not items:
        return json.dumps({
            "title": f"Transcript: {topic_name}",
            "summary": f"No content extracted from transcript for {topic_name}.",
            "topics": [],
            "people": [],
            "key_claims": [],
            "takeaways": [],
            "content_warnings": []
        })

    lines = []
    for i, item in enumerate(items, 1):
        sources = ", ".join(item.get("_sources", ["unknown"]))
        quote = item.get("source_quote", "")
        item_type = item.get("type", "info")
        detail = item.get("detail", "")
        people = ", ".join(item.get("people", []))
        lines.append(
            f'{i}. [{item_type.upper()}] {item.get("item", "?")}\n'
            f'   Detail: {detail}\n'
            f'   People: {people or "none mentioned"}\n'
            f'   Source: {sources}\n'
            f'   Quote: "{quote}"'
        )
    context = "\n\n".join(lines)
    raw = ask(TRANSCRIPT_SYNTH_PROMPT.format(topic=topic_name), context, cfg)

    raw = raw.strip()
    if raw.startswith('```'):
        raw = raw.split('\n', 1)[-1]
        if raw.endswith('```'):
            raw = raw[:-3]
        raw = raw.strip()
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed)
    except json.JSONDecodeError:
        s, e = raw.find('{'), raw.rfind('}')
        if s >= 0 and e > s:
            try:
                parsed = json.loads(raw[s:e+1])
                return json.dumps(parsed)
            except json.JSONDecodeError:
                pass
        return json.dumps({
            "title": f"Transcript: {topic_name}",
            "summary": raw[:500],
            "topics": [],
            "people": [],
            "key_claims": [],
            "takeaways": [],
            "content_warnings": []
        })


def synthesize(topic_name, items, cfg):
    if not items:
        return json.dumps({
            "status_summary": f"No actionable items found in source documents for {topic_name}.",
            "risk_level": "unknown",
            "context": "",
            "items": [],
            "people": [],
            "recommended_sequence": [],
            "blockers": [],
            "key_rules": []
        })

    lines = []
    for i, item in enumerate(items, 1):
        sources = ", ".join(item.get("_sources", ["unknown"]))
        d = item.get("date") or "no date"
        urgency = item.get("urgency", "unknown")
        quote = item.get("source_quote", "")
        item_type = item.get("type", "task")
        detail = item.get("detail", "")
        depends = item.get("depends_on", "")
        people = ", ".join(item.get("people", []))
        weight = item.get("weight", "")
        lines.append(
            f'{i}. [{urgency.upper()}] [{item_type.upper()}] {item.get("item", "?")}\n'
            f'   Date: {d}\n'
            f'   Detail: {detail}\n'
            f'   Depends on: {depends or "nothing"}\n'
            f'   People: {people or "none mentioned"}\n'
            f'   Weight: {weight or "not specified"}\n'
            f'   Source: {sources}\n'
            f'   Evidence: "{quote}"'
        )
    context = "\n\n".join(lines)
    raw = ask(SYNTH_PROMPT.format(topic=topic_name, today=_date.today().isoformat()), context, cfg)

    raw = raw.strip()
    if raw.startswith('```'):
        raw = raw.split('\n', 1)[-1]
        if raw.endswith('```'):
            raw = raw[:-3]
        raw = raw.strip()
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed)
    except json.JSONDecodeError:
        s, e = raw.find('{'), raw.rfind('}')
        if s >= 0 and e > s:
            try:
                parsed = json.loads(raw[s:e+1])
                return json.dumps(parsed)
            except json.JSONDecodeError:
                pass
        return json.dumps({
            "status_summary": raw[:500],
            "risk_level": "unknown",
            "context": "",
            "items": [],
            "people": [],
            "recommended_sequence": [],
            "blockers": [],
            "key_rules": []
        })