"""Real-time Whisper transcription — streams mic audio directly into
the synthesis-llm pipeline without saving recordings to disk.

Requires: pip install faster-whisper sounddevice numpy
System:   libportaudio (brew install portaudio / apt install libportaudio2)
"""
import subprocess
import threading
import queue
import numpy as np
from datetime import datetime

_model = None
_model_lock = __import__("threading").Lock()


def _find_loopback_device():
    """Auto-detect the system audio loopback device for the current OS.

    Returns (device_index, use_wasapi_loopback) on success, or None on failure.
    - Windows: uses WASAPI loopback on the default output device (no extra software needed)
    - Linux:   finds a PulseAudio/PipeWire monitor source automatically
    - Mac:     scans for BlackHole or similar virtual audio cable by name
    """
    import sys
    import sounddevice as sd

    platform = sys.platform

    if platform == "win32":
        # On Windows, WASAPI loopback captures the default output device directly.
        # We find the default output device index so we can re-open it as a loopback input.
        try:
            default_output = sd.default.device[1]  # (input_idx, output_idx)
            if default_output is None or default_output < 0:
                devices = sd.query_devices()
                for i, dev in enumerate(devices):
                    if dev["max_output_channels"] > 0:
                        default_output = i
                        break
            return (default_output, True)
        except Exception as e:
            print(f"  [loopback] Could not find WASAPI output device: {e}")
            return None

    devices = sd.query_devices()

    if platform == "darwin":
        # Look for BlackHole, Loopback, or similar virtual audio cables
        for i, dev in enumerate(devices):
            name = dev["name"].lower()
            if any(kw in name for kw in ("blackhole", "loopback", "virtual")):
                return (i, False)
        print(
            "  [loopback] No loopback device found on macOS.\n"
            "  Install BlackHole: brew install blackhole-2ch\n"
            "  Then create a Multi-Output Device in Audio MIDI Setup (speakers + BlackHole)\n"
            "  and set BlackHole as the system input."
        )
        return None

    if platform.startswith("linux"):
        # First try: scan sounddevice for "monitor" in device name (PulseAudio native)
        for i, dev in enumerate(devices):
            name = dev["name"].lower()
            if "monitor" in name:
                return (i, False)

        # Second try: use pactl to find monitor sources and set as default,
        # then use the pipewire/default sounddevice device
        try:
            result = subprocess.run(
                ["pactl", "list", "short", "sources"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                monitor_sources = [
                    line.split("\t")[1] for line in result.stdout.strip().split("\n")
                    if "monitor" in line.lower()
                ]
                if monitor_sources:
                    # Prefer a RUNNING source, otherwise take the first monitor
                    chosen = monitor_sources[0]
                    for line in result.stdout.strip().split("\n"):
                        if "monitor" in line.lower() and "RUNNING" in line:
                            chosen = line.split("\t")[1]
                            break

                    subprocess.run(
                        ["pactl", "set-default-source", chosen],
                        capture_output=True, timeout=5
                    )
                    print(f"  [loopback] Set PulseAudio default source to: {chosen}")

                    # Now find the pipewire or default device in sounddevice
                    for i, dev in enumerate(devices):
                        if dev["name"].lower() in ("pipewire", "default") and dev["max_input_channels"] > 0:
                            return (i, False)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        print(
            "  [loopback] No monitor source found on Linux.\n"
            "  Make sure PulseAudio or PipeWire is running.\n"
            "  You can create a loopback with: pactl load-module module-loopback"
        )
        return None

    print(f"  [loopback] Unsupported platform for automatic loopback detection: {platform}")
    return None

def _get_model(model_size="large-v3", device="auto", compute_type="int8"):
    global _model
    with _model_lock:
        if _model is None:
            print(f"  Loading Whisper model ({model_size})...")
            from faster_whisper import WhisperModel
            _model = WhisperModel(model_size, device=device, compute_type=compute_type)
    return _model


class LiveTranscriber:
    """Captures mic audio in a background thread, transcribes in chunks,
    and accumulates a running transcript in memory.

    Usage:
        t = LiveTranscriber(language="de", initial_prompt="Grüezi...")
        t.start()          # begins listening
        # ... lecture happens ...
        t.stop()            # stop capture
        docs = t.as_documents("Lecture Name")  # → list[dict] for extract()

    Pass loopback=True to capture system audio output (Teams/Zoom/Meet) instead
    of the microphone. The loopback device is detected automatically.
    """

    def __init__(self, language="de", initial_prompt="",
                 model_size="large-v3", chunk_seconds=15,
                 sample_rate=16000, loopback=False):
        self.language = language
        self.initial_prompt = initial_prompt
        self.model_size = model_size
        self.chunk_seconds = chunk_seconds
        self.sample_rate = sample_rate
        self.loopback = loopback

        self._audio_queue = queue.Queue()
        self._segments = []
        self._running = False
        self._stream = None
        self._worker = None
        self._prompt = initial_prompt
        self._audio_offset_seconds = 0.0

    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio block — just enqueues."""
        if status:
            print(f"  [audio] {status}")
        self._audio_queue.put(indata.copy())

    def _transcribe_loop(self):
        import sounddevice as sd

        model = _get_model(self.model_size)
        chunk_samples = self.chunk_seconds * self.sample_rate
        buffer = np.empty((0, 1), dtype="float32")

        if self.loopback:
            result = _find_loopback_device()
            if result is None:
                print("  Cannot start loopback capture — no loopback device found.")
                self._running = False
                return
            device_index, use_wasapi = result
            if use_wasapi:
                # Windows WASAPI loopback: re-open the output device as a loopback input
                extra = sd.WasapiSettings(exclusive=False, loopback=True)
                self._stream = sd.InputStream(
                    device=device_index,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32",
                    callback=self._audio_callback,
                    blocksize=int(self.sample_rate * 0.5),
                    extra_settings=extra,
                )
            else:
                self._stream = sd.InputStream(
                    device=device_index,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32",
                    callback=self._audio_callback,
                    blocksize=int(self.sample_rate * 0.5),
                )
            print(f"  🔊  Loopback capture started (device {device_index}, {self.language})")
        else:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                callback=self._audio_callback,
                blocksize=int(self.sample_rate * 0.5),
            )
            print(f"  🎙  Live capture started ({self.language})")

        self._stream.start()
        while self._running:
            # Drain queue into buffer
            try:
                while True:
                    block = self._audio_queue.get(timeout=0.2)
                    buffer = np.concatenate([buffer, block])
            except queue.Empty:
                pass

            # Once we have enough audio, transcribe the chunk
            if len(buffer) >= chunk_samples:
                audio_chunk = buffer[:chunk_samples].flatten()
                buffer = buffer[chunk_samples:]

                segments, _ = model.transcribe(
                    audio_chunk,
                    language=self.language,
                    initial_prompt=self._prompt,
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=500,
                        speech_pad_ms=300,
                    ),
                    beam_size=5,
                )

                for seg in segments:
                    abs_start = self._audio_offset_seconds + seg.start
                    mm, ss = divmod(int(abs_start), 60)
                    line = f"[{mm:02d}:{ss:02d}] {seg.text.strip()}"
                    self._segments.append(line)
                    print(f"    {line}")

                self._audio_offset_seconds += self.chunk_seconds

                # Feed last transcript as prompt context → improves
                # continuity and Swiss German consistency
                if self._segments:
                    self._prompt = " ".join(
                        s.split("] ", 1)[1] if "] " in s else s
                        for s in self._segments[-5:]
                    )

        # Flush remaining buffer after stop
        if len(buffer) > self.sample_rate:
            audio_chunk = buffer.flatten()
            segments, _ = model.transcribe(
                audio_chunk,
                language=self.language,
                initial_prompt=self._prompt,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=300,
                ),
                beam_size=5,
            )
            for seg in segments:
                abs_start = self._audio_offset_seconds + seg.start
                mm, ss = divmod(int(abs_start), 60)
                line = f"[{mm:02d}:{ss:02d}] {seg.text.strip()}"
                self._segments.append(line)
                print(f"    {line}")

        self._stream.stop()
        self._stream.close()
        print("  Audio stream closed.")

    def start(self):
        """Begin live capture + transcription in a background thread."""
        self._running = True
        self._worker = threading.Thread(target=self._transcribe_loop, daemon=True)
        self._worker.start()

    def stop(self):
        """Stop capture, flush remaining audio, close mic."""
        self._running = False
        if self._worker:
            self._worker.join()

    def as_documents(self, topic_name="Live Lecture"):
        """Return transcript in the same format as ingest() output:
        [{"path": "...", "text": "..."}]
        This plugs directly into extract() with zero changes.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        transcript = "\n".join(self._segments)
        return [{
            "path": f"live_transcript_{topic_name}_{ts}.md",
            "text": transcript.strip(),
        }]
