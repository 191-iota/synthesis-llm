import os, re, time, httpx
from math import log2

_CRED_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|secret|token|password|passwd|pwd|auth|credential|private[_-]?key)\s*[:=]\s*\S+'),
    re.compile(r'(?i)bearer\s+\S+'),
    re.compile(r'ghp_[A-Za-z0-9_]{36,}'),
    re.compile(r'sk-[A-Za-z0-9]{20,}'),
    re.compile(r'-----BEGIN\s+(RSA\s+)?PRIVATE KEY-----[\s\S]*?-----END'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'(?i)(mysql|postgres|mongodb|redis)://\S+:\S+@'),
]

_HEX_OR_B64 = re.compile(r'(?<!\w)[A-Za-z0-9+/=_-]{40,}(?!\w)')

def _high_entropy(s):
    if len(s) < 20:
        return False
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    entropy = -sum((f / len(s)) * log2(f / len(s)) for f in freq.values())
    return entropy > 4.5

def scrub(text):
    for pat in _CRED_PATTERNS:
        text = pat.sub('[REDACTED]', text)
    for match in _HEX_OR_B64.finditer(text):
        if _high_entropy(match.group()):
            text = text.replace(match.group(), '[REDACTED]')
    return text

def ask(prompt, context, cfg, max_retries=5):
    api_key = os.environ.get(cfg.get('api_key_env', 'ANTHROPIC_API_KEY'))
    if not api_key:
        raise RuntimeError(f"Set {cfg.get('api_key_env', 'ANTHROPIC_API_KEY')} env var")

    for attempt in range(max_retries):
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": cfg.get("model", "claude-sonnet-4-20250514"),
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": f"{prompt}\n\n---\n\n{scrub(context)}"}],
            },
            timeout=120,
        )
        if r.status_code == 429:
            # Parse retry-after header or use exponential backoff
            retry_after = r.headers.get("retry-after")
            if retry_after:
                wait = float(retry_after)
            else:
                wait = min(2 ** attempt * 10, 120)  # 10s, 20s, 40s, 80s, 120s
            print(f"    Rate limited. Waiting {wait:.0f}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait)
            continue
        if r.status_code != 200:
            print(f"API error {r.status_code}: {r.text[:500]}")
        r.raise_for_status()
        return r.json()["content"][0]["text"]

    raise RuntimeError(f"Rate limited after {max_retries} retries")
