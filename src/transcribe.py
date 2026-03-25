"""Real-time Whisper transcription — streams mic audio directly into
the synthesis-llm pipeline without saving recordings to disk.

Requires: pip install faster-whisper sounddevice numpy
System:   libportaudio (brew install portaudio / apt install libportaudio2)
"""
import threading
import queue
import numpy as np
from datetime import datetime

_model = None
_model_lock = __import__("threading").Lock()

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
    """

    def __init__(self, language="de", initial_prompt="",
                 model_size="large-v3", chunk_seconds=15,
                 sample_rate=16000):
        self.language = language
        self.initial_prompt = initial_prompt
        self.model_size = model_size
        self.chunk_seconds = chunk_seconds
        self.sample_rate = sample_rate

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

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
            blocksize=int(self.sample_rate * 0.5),
        )
        self._stream.start()
        print(f"  🎙  Live capture started ({self.language})")

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
        print("  Microphone stream closed.")

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
