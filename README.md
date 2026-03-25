# synthesis_llm

Point it at a folder of documents and it gives you a single interactive HTML briefing that tells you where you stand, what's coming up and what to do next.

<img width="1200" height="1461" alt="image" src="https://github.com/user-attachments/assets/e1dff283-92fe-44fb-8f41-84d14e8bdab1" />

## How it works

The pipeline has four stages that run sequentially.

**Ingest** walks through all configured paths and reads everything it can. PDFs go through `pdftotext`, DOCX through `pandoc`, and anything that isn't binary gets read as plain text. It also supports cloning GitHub repos if you prefix the path with `github:user/repo`.

**Extract** takes the ingested documents, shards them into chunks and sends each one through a two-pass LLM extraction. The first pass pulls out items, the second pass re-reads the same document looking for anything the first pass missed. Then a separate confirmation pass runs independently, and only items that both passes agree on and that have a grounded source quote actually make it through. This is what keeps hallucinations out.

**Synthesize** collects all confirmed items and asks the LLM to produce a structured JSON briefing with a status summary, risk level, each item with its date and urgency and dependencies, a recommended action sequence, any blockers, and key rules or constraints from the documents. Past deadlines are assumed done unless the documents explicitly say otherwise, so it doesn't panic about things you've already handled.

**Render** takes that JSON and generates a self-contained HTML file with a vertical timeline where a TODAY line separates what's behind from what's ahead, expandable cards for each item, a game plan section and a collapsible drawer for context like rules and people. No frameworks and no build step, just open the file in a browser.

## Setup

```bash
pip install pyyaml httpx --break-system-packages
export ANTHROPIC_API_KEY=sk-ant-...
```

### Live Transcription (optional)

To use the real-time Whisper transcription mode you need a few extra dependencies.

**System prerequisites:**

```bash
# macOS
brew install portaudio

# Debian / Ubuntu
sudo apt install libportaudio2
```

**Python dependencies:**

```bash
pip install faster-whisper sounddevice numpy
```

## Config

```yaml
api_key_env: ANTHROPIC_API_KEY
model: claude-sonnet-4-20250514
shard_size: 75000

topics:
  - name: My Project
    paths:
      - /path/to/docs
      - github:user/repo
```

Each topic gets its own section in the briefing. You can add as many as you want and each one will be processed independently.

## Run

```bash
python3 run.py              # generate and serve
python3 run.py --generate   # generate only
python3 run.py --serve      # serve existing
python3 run.py --live       # live mic transcription → report → serve
```

The output is an `index.html` that you can either serve on `localhost:8899` or just open directly.

## Live Transcription

`--live` opens the microphone, transcribes in real-time using [faster-whisper](https://github.com/SYSTRAN/faster-whisper), and feeds the result straight into the existing `extract → synthesize → render` pipeline. No audio files are ever written to disk.

```
[Microphone] → LiveTranscriber → [in-memory transcript]
                                         ↓
                               extract → synthesize → render → index.html
```

**Run:**

```bash
python3 run.py --live      # starts mic, press Enter to stop, then generates report and serves
```

On first run, faster-whisper will download the `large-v3` model (~3 GB). Subsequent runs reuse the cached model.

**Config** (`config.yaml`):

```yaml
live:
  language: de              # BCP-47 language code; "de" covers Standard German and Swiss German
  initial_prompt: "Grüezi, hüt bespräche mer d'Vorlesig..."  # seeds the decoder with dialect vocabulary
  model_size: large-v3      # whisper model to use
  chunk_seconds: 15         # transcribe every N seconds of captured audio
  topic_name: "Live Lecture" # name used in the generated report
```

**Swiss German dialect support:** faster-whisper uses the `language: de` code for all German variants. Seeding the decoder with `initial_prompt` text written in Swiss German (e.g. `"Grüezi, hüt bespräche mer..."`) biases the model toward dialect-specific vocabulary and spelling, improving accuracy for Swiss German speakers.

**Privacy:** no audio is ever saved to disk. All audio is processed in memory and discarded once the transcript is produced.

## Cost

Each topic with N document shards makes roughly 3N + 1 API calls since every shard goes through extract, re-extract and confirm, plus one synthesize call at the end. On Anthropic API Tier 1 you're limited to 8k output tokens per minute, so keep `workers = 1` in `extract.py` to avoid getting rate limited. The retry logic in `llm.py` handles 429s with exponential backoff if it does happen.

## Files

```
run.py         orchestrator
ingest.py      file walker and text extraction
extract.py     two-pass LLM extraction with confirmation
synthesize.py  LLM synthesis into structured JSON
render.py      JSON into interactive HTML
llm.py         API client with credential scrubbing and retry
transcribe.py  real-time Whisper mic transcription (--live mode)
config.yaml    paths and settings
```

## License

MIT
