import os, subprocess

def _should_skip(path, name, cfg):
    if name.startswith('.'):
        return True
    if os.path.isdir(path) and name in cfg.get('skip_dirs', []):
        return True
    _, ext = os.path.splitext(name)
    if ext.lower() in cfg.get('skip_extensions', []):
        return True
    if os.path.isfile(path):
        try:
            if os.path.getsize(path) > cfg.get('max_file_bytes', 500000):
                return True
        except OSError:
            return True
    return False

def _is_binary(path):
    try:
        with open(path, 'rb') as f:
            chunk = f.read(1024)
        return b'\x00' in chunk
    except (OSError, PermissionError):
        return True

def _extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.pdf':
        try:
            result = subprocess.run(
                ['pdftotext', '-layout', path, '-'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None
    if ext == '.docx':
        try:
            result = subprocess.run(
                ['pandoc', '-t', 'plain', path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None
    if ext == '.csv':
        try:
            with open(path, 'r', errors='replace') as f:
                return f.read()
        except OSError:
            return None
    if _is_binary(path):
        return None
    try:
        with open(path, 'r', errors='replace') as f:
            return f.read()
    except OSError:
        return None

def ingest(paths, cfg):
    documents = []
    for base_path in paths:
        if base_path.startswith('github:'):
            repo = base_path[7:]
            clone_dir = f"/tmp/roadmap_git_{repo.replace('/', '_')}"
            if not os.path.exists(clone_dir):
                subprocess.run(
                    ['git', 'clone', '--depth', '1',
                     f'https://github.com/{repo}.git', clone_dir],
                    capture_output=True, timeout=120
                )
            base_path = clone_dir
        if not os.path.exists(base_path):
            print(f'  [skip] path not found: {base_path}')
            continue
        if os.path.isfile(base_path):
            text = _extract_text(base_path)
            if text and text.strip():
                documents.append({'path': base_path, 'text': text.strip()})
            continue
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if not _should_skip(os.path.join(root, d), d, cfg)]
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                if _should_skip(fpath, fname, cfg):
                    continue
                text = _extract_text(fpath)
                if text and text.strip():
                    documents.append({'path': fpath, 'text': text.strip()})
    print(f'  Ingested {len(documents)} files')
    return documents
