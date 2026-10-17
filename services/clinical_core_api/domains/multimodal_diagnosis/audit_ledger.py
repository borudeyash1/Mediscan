"""
MediScan Enterprise — Immutable Cryptographic Audit Ledger
==========================================================
Maintains SHA-256 hash-chained records of AI diagnostic inferences
and clinical actions for FDA SaMD / HIPAA traceability.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class ImmutableAuditLedger:
    """Manages cryptographic SHA-256 hash-chained audit logging."""

    GENESIS_HASH = "0" * 64
    _in_memory_ledger: List[Dict[str, Any]] = []
    _in_memory_inferences: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_latest_hash(cls) -> str:
        """Returns the current_row_hash of the most recent log entry or genesis hash."""
        if not cls._in_memory_ledger:
            return cls.GENESIS_HASH
        return cls._in_memory_ledger[-1]["current_row_hash"]

    @classmethod
    def append_audit_entry(
        cls,
        tenant_id: UUID,
        actor_id: UUID,
        actor_role: str,
        action_type: str,
        resource_type: str,
        resource_id: UUID,
        access_reason: str,
        client_ip: str = "127.0.0.1",
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Calculates SHA-256 hash-chain and appends an entry to the immutable ledger.
        current_row_hash = SHA256(prev_hash || tenant_id || actor_id || actor_role || action_type || resource_type || resource_id || access_reason || client_ip || logged_at)
        """
        prev_hash = cls.get_latest_hash()
        now = timestamp or datetime.now(timezone.utc)
        iso_time = now.isoformat()

        # Construct deterministic payload for SHA-256 hashing
        payload_str = (
            f"{prev_hash}"
            f"{str(tenant_id)}"
            f"{str(actor_id)}"
            f"{actor_role}"
            f"{action_type}"
            f"{resource_type}"
            f"{str(resource_id)}"
            f"{access_reason}"
            f"{client_ip}"
            f"{iso_time}"
        )

        curr_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        log_entry = {
            "log_id": len(cls._in_memory_ledger) + 1,
            "tenant_id": str(tenant_id),
            "actor_id": str(actor_id),
            "actor_role": actor_role,
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "access_reason": access_reason,
            "client_ip": client_ip,
            "previous_row_hash": prev_hash,
            "current_row_hash": curr_hash,
            "logged_at": iso_time,
        }

        cls._in_memory_ledger.append(log_entry)
        return log_entry

    @classmethod
    def record_diagnostic_inference(
        cls,
        inference_id: UUID,
        encounter_id: UUID,
        tenant_id: UUID,
        model_name: str,
        model_version: str,
        git_commit_sha: str,
        input_modalities: List[str],
        top_differential_json: List[Dict[str, Any]],
        execution_time_ms: int,
        saliency_artifact_uris: Optional[Dict[str, Any]] = None,
        guardrail_interventions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Stores full AI diagnostic inference record and appends to hash-chained audit log.
        """
        inference_record = {
            "inference_id": str(inference_id),
            "tenant_id": str(tenant_id),
            "encounter_id": str(encounter_id),
            "model_name": model_name,
            "model_version": model_version,
            "git_commit_sha": git_commit_sha,
            "input_modalities": input_modalities,
            "top_differential_json": top_differential_json,
            "saliency_artifact_uris": saliency_artifact_uris or {},
            "guardrail_interventions": guardrail_interventions or [],
            "clinician_disposition": "PENDING",
            "execution_time_ms": execution_time_ms,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        cls._in_memory_inferences[str(inference_id)] = inference_record

        # Append audit ledger entry
        audit_entry = cls.append_audit_entry(
            tenant_id=tenant_id,
            actor_id=inference_id,
            actor_role="AI_DIAGNOSTIC_ORCHESTRATOR",
            action_type="MULTIMODAL_INFERENCE_GENERATED",
            resource_type="ENCOUNTER",
            resource_id=encounter_id,
            access_reason="FDA_SAMD_AUDIT_LOG_CREATION",
        )

        return {
            "inference_record": inference_record,
            "audit_ledger_entry": audit_entry,
        }

    @classmethod
    def verify_chain_integrity(cls) -> bool:
        """Verifies cryptographic hash chain integrity of the ledger."""
        for i in range(len(cls._in_memory_ledger)):
            entry = cls._in_memory_ledger[i]
            expected_prev = cls.GENESIS_HASH if i == 0 else cls._in_memory_ledger[i - 1]["current_row_hash"]
            if entry["previous_row_hash"] != expected_prev:
                return False

            payload_str = (
                f"{entry['previous_row_hash']}"
                f"{entry['tenant_id']}"
                f"{entry['actor_id']}"
                f"{entry['actor_role']}"
                f"{entry['action_type']}"
                f"{entry['resource_type']}"
                f"{entry['resource_id']}"
                f"{entry['access_reason']}"
                f"{entry['client_ip']}"
                f"{entry['logged_at']}"
            )
            recalculated = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
            if recalculated != entry["current_row_hash"]:
                return False

        return True
