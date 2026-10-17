"""
Vocal Biomarker Analyzer for Ambient Clinical Voice Streams.
Computes real-time acoustic & prosodic biomarkers:
  - Speech rate / cadence (Words Per Minute)
  - Pause-to-speech ratio
  - Respiratory distress index & cadence regularity
"""

import base64
import math
from typing import Optional
import numpy as np

from .models import VocalBiomarkers, VocalCadenceCategory


class VocalBiomarkerAnalyzer:
    """Deterministic, signal-processing acoustic biomarker extraction engine."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def analyze_audio_frame(
        self,
        audio_bytes: bytes,
        known_word_count: Optional[int] = None,
    ) -> VocalBiomarkers:
        """
        Analyze raw PCM 16-bit 16kHz audio buffer.
        Extracts energy envelope, Voice Activity Detection (VAD) segments,
        silence pauses, and computes respiratory distress cadence.
        """
        if len(audio_bytes) < 320:
            # Minimal frame fallback
            return VocalBiomarkers(
                speech_rate_wpm=120.0,
                pause_ratio=0.20,
                respiratory_distress_index=0.10,
                respiratory_cadence_score=0.90,
                classification=VocalCadenceCategory.NORMAL,
                mean_pause_duration_ms=200.0,
                burst_count=1,
            )

        # Convert 16-bit PCM to float normalized [-1.0, 1.0]
        try:
            samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception:
            samples = np.zeros(1600, dtype=np.float32)

        total_samples = len(samples)
        total_duration_sec = max(0.1, total_samples / float(self.sample_rate))
        total_duration_ms = total_duration_sec * 1000.0

        # Frame-wise Root Mean Square (RMS) energy (25ms window, 10ms hop)
        window_size = int(self.sample_rate * 0.025)
        hop_size = int(self.sample_rate * 0.010)

        num_frames = max(1, (total_samples - window_size) // hop_size + 1)
        energies = []
        for i in range(num_frames):
            start = i * hop_size
            end = start + window_size
            frame = samples[start:end]
            rms = math.sqrt(float(np.mean(frame ** 2))) if len(frame) > 0 else 0.0
            energies.append(rms)

        # Adaptive energy threshold for speech vs silence
        mean_energy = float(np.mean(energies)) if energies else 0.01
        silence_threshold = max(0.012, mean_energy * 0.35)

        # Classify frames as speech (1) or silence (0)
        is_speech = [1 if e >= silence_threshold else 0 for e in energies]

        # Identify continuous speech bursts and silence pauses
        bursts: list[float] = []
        pauses: list[float] = []
        current_state = is_speech[0] if is_speech else 0
        state_count = 0

        for state in is_speech:
            if state == current_state:
                state_count += 1
            else:
                dur_ms = state_count * 10.0  # 10ms hop
                if current_state == 1:
                    bursts.append(dur_ms)
                else:
                    pauses.append(dur_ms)
                current_state = state
                state_count = 1

        # Append last state
        if state_count > 0:
            dur_ms = state_count * 10.0
            if current_state == 1:
                bursts.append(dur_ms)
            else:
                pauses.append(dur_ms)

        total_pause_ms = sum(pauses) if pauses else (total_duration_ms * 0.20)
        pause_ratio = min(1.0, max(0.0, total_pause_ms / total_duration_ms))
        mean_pause_ms = float(np.mean(pauses)) if pauses else 0.0

        # Speech rate (WPM)
        if known_word_count is not None and known_word_count > 0:
            speech_rate_wpm = (known_word_count / total_duration_sec) * 60.0
        else:
            # Estimate syllable/word count from energy peaks
            peaks = 0
            for i in range(1, len(energies) - 1):
                if energies[i] > silence_threshold and energies[i] > energies[i - 1] and energies[i] > energies[i + 1]:
                    peaks += 1
            estimated_words = max(1, int(peaks / 1.6))
            speech_rate_wpm = (estimated_words / total_duration_sec) * 60.0

        # Cap speech rate to physiological range [40, 320]
        speech_rate_wpm = max(40.0, min(320.0, speech_rate_wpm))

        # Respiratory distress indicators:
        # Patients in respiratory distress speak in short fragmented bursts (<1200ms) with elevated pause ratios
        short_burst_ratio = (
            sum(1 for b in bursts if b < 1200.0) / float(len(bursts)) if bursts else 0.0
        )
        # Respiratory distress index composite
        rdi = 0.5 * pause_ratio + 0.5 * short_burst_ratio
        if pause_ratio > 0.40 and bursts and max(bursts) < 2000.0:
            rdi = min(1.0, rdi + 0.25)
        rdi = round(min(1.0, max(0.0, rdi)), 3)

        # Regularity cadence score (1.0 = highly fluent, 0.0 = broken/gasping)
        cadence_score = round(max(0.05, 1.0 - rdi), 3)

        # Classification
        if rdi >= 0.55:
            classification = VocalCadenceCategory.DYSPNEIC_DISTRESS
        elif speech_rate_wpm > 180.0:
            classification = VocalCadenceCategory.TACHYPNEIC_SHORT_PHRASES
        elif speech_rate_wpm < 95.0 and pause_ratio > 0.40:
            classification = VocalCadenceCategory.BRADYPNEIC_HESITANT
        else:
            classification = VocalCadenceCategory.NORMAL

        return VocalBiomarkers(
            speech_rate_wpm=round(speech_rate_wpm, 1),
            pause_ratio=round(pause_ratio, 3),
            respiratory_distress_index=rdi,
            respiratory_cadence_score=cadence_score,
            classification=classification,
            mean_pause_duration_ms=round(mean_pause_ms, 1),
            burst_count=len(bursts) if bursts else 1,
        )

    def analyze_utterance_timing(
        self,
        text: str,
        duration_ms: int,
        pause_duration_ms: Optional[int] = None,
        is_short_burst: bool = False,
    ) -> VocalBiomarkers:
        """
        Synthesize vocal biomarkers from transcript segment metadata & timing.
        Used during streaming text or WebRTC data channel events.
        """
        duration_sec = max(0.5, duration_ms / 1000.0)
        words = [w for w in text.strip().split() if w]
        word_count = len(words)

        # Words per minute calculation
        wpm = (word_count / duration_sec) * 60.0
        wpm = max(40.0, min(300.0, wpm))

        if pause_duration_ms is None:
            # Empirical pause ratio estimation based on punctuation and commas
            comma_count = text.count(",") + text.count("...") + text.count("-")
            period_count = text.count(".") + text.count("?") + text.count("!")
            estimated_pause_ms = (comma_count * 250.0) + (period_count * 500.0)
            if is_short_burst:
                estimated_pause_ms += 400.0
            pause_duration_ms = int(min(duration_ms * 0.6, estimated_pause_ms))

        pause_ratio = round(min(0.85, max(0.08, float(pause_duration_ms) / float(duration_ms))), 3)

        # Respiratory distress evaluation:
        # Signs of dyspnea: short phrase (< 5 words) over high duration, or explicit breathlessness cues
        breathless_tokens = {"gasping", "breath", "pant", "cant breathe", "can't breathe", "short of breath"}
        has_breathless_token = any(bt in text.lower() for bt in breathless_tokens)

        if has_breathless_token or is_short_burst or (word_count <= 4 and duration_sec >= 2.5):
            rdi = min(0.95, 0.45 + (pause_ratio * 0.5))
        else:
            rdi = max(0.08, min(0.40, pause_ratio * 0.6))
        rdi = round(rdi, 3)

        cadence_score = round(max(0.10, 1.0 - rdi), 3)

        if rdi >= 0.55:
            classification = VocalCadenceCategory.DYSPNEIC_DISTRESS
        elif wpm > 185.0:
            classification = VocalCadenceCategory.TACHYPNEIC_SHORT_PHRASES
        elif wpm < 90.0 and pause_ratio > 0.40:
            classification = VocalCadenceCategory.BRADYPNEIC_HESITANT
        else:
            classification = VocalCadenceCategory.NORMAL

        return VocalBiomarkers(
            speech_rate_wpm=round(wpm, 1),
            pause_ratio=pause_ratio,
            respiratory_distress_index=rdi,
            respiratory_cadence_score=cadence_score,
            classification=classification,
            mean_pause_duration_ms=float(pause_duration_ms),
            burst_count=max(1, word_count // 5),
        )
