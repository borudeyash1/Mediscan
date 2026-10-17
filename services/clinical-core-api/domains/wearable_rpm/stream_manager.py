"""
Server-Sent Events (SSE) Live Telemetry Stream Manager.
Broadcasts real-time vitals, waveforms, and 3-Tier Escalation Alerts
to connected clinician workstation monitors via GET /api/v2/telemetry/stream/{clinical_subject_id}.
"""

import asyncio
import json
from typing import Any, AsyncGenerator
from datetime import datetime, timezone
import structlog

from .models import EscalationAlert, VitalReading, AnomalyEvent

logger = structlog.get_logger(__name__)


class TelemetryStreamBroadcaster:
    """Manages active SSE client subscriber queues per patient."""

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, clinical_subject_id: str) -> asyncio.Queue:
        """Register a new SSE stream listener queue for a subject."""
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        if clinical_subject_id not in self._subscribers:
            self._subscribers[clinical_subject_id] = []
        self._subscribers[clinical_subject_id].append(q)
        logger.info("telemetry_stream.subscriber_connected", subject_id=clinical_subject_id)
        return q

    def unsubscribe(self, clinical_subject_id: str, q: asyncio.Queue) -> None:
        """Remove listener queue upon disconnect."""
        if clinical_subject_id in self._subscribers:
            try:
                self._subscribers[clinical_subject_id].remove(q)
                if not self._subscribers[clinical_subject_id]:
                    del self._subscribers[clinical_subject_id]
            except ValueError:
                pass
        logger.info("telemetry_stream.subscriber_disconnected", subject_id=clinical_subject_id)

    async def broadcast_event(self, clinical_subject_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Send an SSE event packet to all active listeners for this patient."""
        queues = self._subscribers.get(clinical_subject_id, [])
        if not queues:
            return

        payload = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        for q in list(queues):
            try:
                if q.full():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await q.put(payload)
            except Exception as e:
                logger.warning("telemetry_stream.put_failed", error=str(e))

    async def broadcast_telemetry(
        self,
        clinical_subject_id: str,
        readings: list[VitalReading],
        news2_score: int,
        news2_category: str,
        anomalies: list[AnomalyEvent],
    ) -> None:
        """Broadcast live vitals update."""
        data = {
            "clinical_subject_id": clinical_subject_id,
            "readings": [r.model_dump(mode="json") for r in readings],
            "news2_score": news2_score,
            "news2_category": news2_category,
            "anomalies": [a.model_dump(mode="json") for a in anomalies],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.broadcast_event(clinical_subject_id, "telemetry_update", data)

    async def broadcast_escalation(self, alert: EscalationAlert) -> None:
        """Broadcast critical or moderate escalation alert."""
        data = alert.model_dump(mode="json")
        await self.broadcast_event(alert.clinical_subject_id, "escalation_alert", data)


# Global singleton instance
stream_broadcaster = TelemetryStreamBroadcaster()
