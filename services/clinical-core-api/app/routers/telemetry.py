"""
Wearable Telemetry & Streaming RPM Router
==========================================
Handles:
  - Telemetry Ingestion (POST /api/v2/telemetry/ingest)
  - Stateful EWMA Z-Score Anomaly Detection
  - 3-Tier Automated Escalation Ladder
  - Live SSE Telemetry Stream (GET /api/v2/telemetry/stream/{clinical_subject_id})
  - Simulated Waveform Generator (12-lead ECG & PPG)
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from domains.wearable_rpm.models import (
    TelemetryIngestRequest,
    TelemetryIngestResponse,
)
from domains.wearable_rpm.ewma_detector import EWMAAnomalyDetector
from domains.wearable_rpm.escalation_ladder import EscalationLadderEngine
from domains.wearable_rpm.stream_manager import stream_broadcaster
from domains.wearable_rpm.telemetry_simulator import TelemetrySimulatorWorker

router = APIRouter()
_ewma_detector = EWMAAnomalyDetector()
_escalation_engine = EscalationLadderEngine()
_simulator_worker = TelemetrySimulatorWorker()


@router.post(
    "/ingest",
    response_model=TelemetryIngestResponse,
    summary="Ingest High-Frequency Wearable Telemetry Readings",
)
async def ingest_telemetry(payload: TelemetryIngestRequest) -> TelemetryIngestResponse:
    """
    Ingests vital telemetry readings from Apple HealthKit, Google Health Connect,
    Continuous Glucose Monitors, or BLE Pulse Oximeters.
    Executes stateful EWMA personal baseline tracking, calculates Z-scores,
    updates live NEWS2 score, and triggers the 3-Tier Escalation Ladder.
    """
    subject_id = payload.clinical_subject_id
    if not payload.readings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Readings array cannot be empty.",
        )

    # 1. Process readings through EWMA Anomaly Detector
    anomalies, current_vitals = _ewma_detector.process_readings(subject_id, payload.readings)

    # 2. Evaluate 3-Tier Escalation & Dynamic NEWS2
    news2_score, news2_cat, escalation_alert = _escalation_engine.evaluate_escalation(
        clinical_subject_id=subject_id,
        anomalies=anomalies,
        vitals=current_vitals,
        supplemental_oxygen=payload.supplemental_oxygen,
    )

    # 3. Broadcast to Live SSE Stream Subscribers
    await stream_broadcaster.broadcast_telemetry(
        clinical_subject_id=subject_id,
        readings=payload.readings,
        news2_score=news2_score,
        news2_category=news2_cat,
        anomalies=anomalies,
    )

    if escalation_alert:
        await stream_broadcaster.broadcast_escalation(escalation_alert)

    return TelemetryIngestResponse(
        clinical_subject_id=subject_id,
        readings_processed=len(payload.readings),
        anomalies_detected=anomalies,
        current_news2_score=news2_score,
        current_news2_category=news2_cat,
        escalation_triggered=escalation_alert,
    )


@router.get(
    "/stream/{clinical_subject_id}",
    summary="Live SSE Real-Time Telemetry Stream for Clinician Workstation",
)
async def live_telemetry_stream(clinical_subject_id: str):
    """
    Server-Sent Events (SSE) live connection emitting real-time vitals updates,
    12-lead ECG waveforms, and 3-Tier Escalation alerts.
    """
    queue = stream_broadcaster.subscribe(clinical_subject_id)

    async def event_generator():
        # Emit initial connection handshake
        yield f"event: stream_connected\ndata: {{\"subject_id\": \"{clinical_subject_id}\", \"status\": \"connected\"}}\n\n"
        try:
            while True:
                # Wait for next event with keepalive timeout
                try:
                    event_payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event_payload
                except asyncio.TimeoutError:
                    # Keepalive ping
                    yield "event: ping\ndata: {\"keepalive\": true}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            stream_broadcaster.unsubscribe(clinical_subject_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/simulator/snapshot",
    summary="Generate Synthetic Telemetry & 12-Lead ECG Waveforms",
)
async def generate_simulator_snapshot(
    scenario: str = Query("NORMAL", description="NORMAL | SEPTIC_SHOCK | STEMI"),
    clinical_subject_id: str = "sim_patient_001",
):
    """
    Worker endpoint returning simulated 12-lead ECG, PPG, and multi-vital snapshots
    for live demonstration and testing.
    """
    return _simulator_worker.generate_patient_snapshot(
        scenario=scenario, clinical_subject_id=clinical_subject_id
    )
