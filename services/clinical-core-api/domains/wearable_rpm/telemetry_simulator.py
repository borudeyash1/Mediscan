"""
Live Telemetry & Waveform Simulator Worker.
Synthesizes realistic 12-lead ECG waveforms, PPG pulses, and continuous vitals for active ICU/RPM monitoring.
Supports simulated clinical crisis scenarios:
  - Normal Sinus Rhythm (stable baseline)
  - Acute Septic Shock Decompensation
  - Acute ST-Elevation Myocardial Infarction (STEMI)
"""

import math
import numpy as np
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    LOINC_HEART_RATE,
    LOINC_SPO2,
    LOINC_SYSTOLIC_BP,
    LOINC_DIASTOLIC_BP,
    LOINC_GLUCOSE,
    LOINC_RESPIRATORY_RATE,
    LOINC_TEMPERATURE,
    UCUM_BPM,
    UCUM_MS,
    UCUM_PERCENT,
    UCUM_MMHG,
    UCUM_MGDL,
    UCUM_CELSIUS,
    TelemetrySourceDevice,
    VitalReading,
)


def generate_ecg_lead_waveform(
    num_samples: int = 250,
    heart_rate_bpm: float = 75.0,
    st_elevation_mm: float = 0.0,
    lead_name: str = "II",
) -> list[float]:
    """
    Synthesize single-lead continuous ECG segment at 250Hz.
    Models physiological P wave, Q wave, R peak, S wave, ST segment, and T wave.
    """
    sampling_rate = 250.0  # Hz
    duration_sec = num_samples / sampling_rate
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)

    rr_interval = 60.0 / max(40.0, min(200.0, heart_rate_bpm))
    signal = np.zeros(num_samples, dtype=np.float32)

    # Base lead amplitude scale
    lead_scale = 1.0
    if lead_name in {"V2", "V3", "V4"}:
        lead_scale = 1.4
    elif lead_name in {"aVR"}:
        lead_scale = -0.8
    elif lead_name in {"III", "aVL"}:
        lead_scale = 0.7

    # Repeat cardiac cycles across duration
    num_cycles = int(math.ceil(duration_sec / rr_interval)) + 1
    for c in range(num_cycles):
        cycle_start = c * rr_interval
        # Relative phase inside cardiac cycle
        phase = t - cycle_start

        # 1. P wave (atrial depolarization)
        p_center = 0.12 * (rr_interval / 0.8)
        signal += lead_scale * 0.15 * np.exp(-((phase - p_center) ** 2) / (2 * (0.02 ** 2)))

        # 2. Q wave
        q_center = 0.18 * (rr_interval / 0.8)
        signal -= lead_scale * 0.12 * np.exp(-((phase - q_center) ** 2) / (2 * (0.008 ** 2)))

        # 3. R peak (ventricular depolarization)
        r_center = 0.20 * (rr_interval / 0.8)
        signal += lead_scale * 1.20 * np.exp(-((phase - r_center) ** 2) / (2 * (0.012 ** 2)))

        # 4. S wave
        s_center = 0.22 * (rr_interval / 0.8)
        signal -= lead_scale * 0.25 * np.exp(-((phase - s_center) ** 2) / (2 * (0.010 ** 2)))

        # 5. ST segment & T wave
        st_center = 0.28 * (rr_interval / 0.8)
        t_center = 0.38 * (rr_interval / 0.8)

        # ST elevation shift
        if st_elevation_mm > 0.0:
            st_boost = (st_elevation_mm / 10.0) * lead_scale
            signal += st_boost * np.exp(-((phase - st_center) ** 2) / (2 * (0.05 ** 2)))

        # T wave (ventricular repolarization)
        t_amp = 0.30 * lead_scale
        signal += t_amp * np.exp(-((phase - t_center) ** 2) / (2 * (0.04 ** 2)))

    # Normalize baseline to mV
    return [round(float(v), 4) for v in signal]


def generate_ppg_waveform(num_samples: int = 100, heart_rate_bpm: float = 75.0) -> list[float]:
    """
    Synthesize finger photoplethysmogram (PPG) pulse waveform.
    Features steep systolic anacrotic upstroke, dicrotic notch, and diastolic runoff.
    """
    t = np.linspace(0, 1.0, num_samples, endpoint=False)
    signal = np.zeros(num_samples, dtype=np.float32)

    # Primary systolic peak
    signal += 0.85 * np.exp(-((t - 0.20) ** 2) / (2 * (0.08 ** 2)))
    # Dicrotic notch reflection peak
    signal += 0.35 * np.exp(-((t - 0.50) ** 2) / (2 * (0.09 ** 2)))

    return [round(float(v), 4) for v in signal]


class TelemetrySimulatorWorker:
    """Worker engine generating continuous waveforms and synthetic patient telemetry."""

    LEAD_NAMES = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

    def generate_patient_snapshot(
        self,
        scenario: str = "NORMAL",
        clinical_subject_id: str = "sim_patient_001",
    ) -> dict[str, Any]:
        """
        Produce a synchronized physiological snapshot:
        scenario options: 'NORMAL', 'SEPTIC_SHOCK', 'STEMI'
        """
        now = datetime.now(timezone.utc)

        if scenario == "SEPTIC_SHOCK":
            hr = 154.0
            spo2 = 85.0
            sbp = 82.0
            dbp = 48.0
            rr = 28.0
            temp = 39.4
            glucose = 46.0
            st_elev = 0.5
        elif scenario == "STEMI":
            hr = 112.0
            spo2 = 93.0
            sbp = 164.0
            dbp = 98.0
            rr = 24.0
            temp = 36.8
            glucose = 125.0
            st_elev = 3.8
        else:
            # Normal Stable ICU/RPM
            hr = 72.0
            spo2 = 98.0
            sbp = 118.0
            dbp = 76.0
            rr = 15.0
            temp = 36.9
            glucose = 98.0
            st_elev = 0.0

        readings = [
            VitalReading(
                loinc_code=LOINC_HEART_RATE,
                metric_value=hr,
                ucum_unit=UCUM_BPM,
                recorded_at=now,
                device_source=TelemetrySourceDevice.BEDSIDE_ICU_MONITOR,
            ),
            VitalReading(
                loinc_code=LOINC_SPO2,
                metric_value=spo2,
                ucum_unit=UCUM_PERCENT,
                recorded_at=now,
                device_source=TelemetrySourceDevice.BLE_PULSE_OXIMETER,
            ),
            VitalReading(
                loinc_code=LOINC_SYSTOLIC_BP,
                metric_value=sbp,
                ucum_unit=UCUM_MMHG,
                recorded_at=now,
                device_source=TelemetrySourceDevice.BEDSIDE_ICU_MONITOR,
            ),
            VitalReading(
                loinc_code=LOINC_DIASTOLIC_BP,
                metric_value=dbp,
                ucum_unit=UCUM_MMHG,
                recorded_at=now,
                device_source=TelemetrySourceDevice.BEDSIDE_ICU_MONITOR,
            ),
            VitalReading(
                loinc_code=LOINC_RESPIRATORY_RATE,
                metric_value=rr,
                ucum_unit=UCUM_BPM,
                recorded_at=now,
                device_source=TelemetrySourceDevice.BEDSIDE_ICU_MONITOR,
            ),
            VitalReading(
                loinc_code=LOINC_TEMPERATURE,
                metric_value=temp,
                ucum_unit=UCUM_CELSIUS,
                recorded_at=now,
                device_source=TelemetrySourceDevice.BEDSIDE_ICU_MONITOR,
            ),
            VitalReading(
                loinc_code=LOINC_GLUCOSE,
                metric_value=glucose,
                ucum_unit=UCUM_MGDL,
                recorded_at=now,
                device_source=TelemetrySourceDevice.DEXCOM_CGM,
            ),
        ]

        # Synthesize 12-lead ECG waveforms
        ecg_leads: dict[str, list[float]] = {}
        for lead in self.LEAD_NAMES:
            lead_elev = st_elev if lead in {"V2", "V3", "V4"} else 0.0
            ecg_leads[lead] = generate_ecg_lead_waveform(
                num_samples=250, heart_rate_bpm=hr, st_elevation_mm=lead_elev, lead_name=lead
            )

        # Synthesize PPG
        ppg_samples = generate_ppg_waveform(num_samples=100, heart_rate_bpm=hr)

        return {
            "clinical_subject_id": clinical_subject_id,
            "scenario": scenario,
            "timestamp": now.isoformat(),
            "readings": [r.model_dump(mode="json") for r in readings],
            "raw_readings": readings,
            "waveforms": {
                "ecg_12_lead": ecg_leads,
                "ppg": ppg_samples,
                "sampling_rate_hz": 250,
            },
        }
