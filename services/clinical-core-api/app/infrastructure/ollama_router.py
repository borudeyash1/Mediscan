"""
MediScan Enterprise — Dual-Engine Local Ollama Clinical Router
==============================================================
Intelligent dispatching between:
  1. medgemma:4b        -> Multimodal imaging, clinical differential reasoning, SOAP scribe notes, patient dialogue
  2. qwen2.5-coder:7b   -> Strict JSON schema output, HL7 FHIR R4 bundles, LOINC/SNOMED coding
  3. nomic-embed-text   -> 768-dim vector embeddings for Qdrant Hybrid Clinical RAG
"""

import base64
import json
from typing import Any, TypeVar
import httpx
from pydantic import BaseModel
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class OllamaClinicalRouter:
    """Intelligent Dual-Engine Router between local medical, structured coder, and embedding models."""

    def __init__(self, host_url: str | None = None):
        self.host_url = host_url or settings.OLLAMA_HOST_URL
        self.medical_model = settings.OLLAMA_MEDICAL_MODEL          # medgemma:4b
        self.structured_model = settings.OLLAMA_STRUCTURED_MODEL    # qwen2.5-coder:7b
        self.embed_model = settings.OLLAMA_EMBED_MODEL              # nomic-embed-text
        self.temperature = settings.OLLAMA_TEMPERATURE              # 0.1
        self.num_ctx = settings.OLLAMA_NUM_CTX                      # 8192
        self._available_models: set[str] = set()

    async def initialize(self) -> None:
        """Query local Ollama to discover available models and verify connectivity."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.host_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    self._available_models = {m.get("name", "").split(":")[0] for m in data.get("models", [])}
                    # Also keep full tags
                    self._available_models.update(m.get("name", "") for m in data.get("models", []))
                    logger.info("ollama.discovered_models", models=list(self._available_models))
        except Exception as e:
            logger.warning("ollama.discovery_failed", error=str(e), fallback_assumed=True)

    def _resolve_model(self, preferred: str, fallback: str) -> str:
        """Resolve to preferred model if present locally, else fallback."""
        if not self._available_models:
            return preferred
        preferred_prefix = preferred.split(":")[0]
        if preferred in self._available_models or preferred_prefix in self._available_models:
            return preferred
        logger.info("ollama.routing_fallback", requested=preferred, fallback=fallback)
        return fallback

    async def generate_clinical_reasoning(
        self,
        prompt: str,
        system_prompt: str | None = None,
        image_bytes: bytes | None = None,
        stream: bool = False,
    ) -> str:
        """Route to medgemma:4b (Doctor) for clinical reasoning, triage, and multimodal interpretation."""
        model = self._resolve_model(self.medical_model, self.structured_model)
        system = system_prompt or (
            "You are an expert physician decision support and clinical informaticist engine. "
            "Provide evidence-based differential diagnosis, clinical safety checks, and actionable observations."
        )

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
            },
            "stream": stream,
        }

        if image_bytes:
            # Attach base64 image for multimodal inspection
            b64_img = base64.b64encode(image_bytes).decode("utf-8")
            payload["messages"][-1]["images"] = [b64_img]

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.host_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def generate_structured_json(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        """
        Route to qwen2.5-coder:7b (Informaticist) for strict schema compliance
        (FHIR R4 bundles, LOINC mappings, structured SOAP notes).
        Uses Ollama's native 'format' parameter with Pydantic JSON schema.
        """
        model = self._resolve_model(self.structured_model, self.medical_model)
        system = system_prompt or (
            "You are a clinical informaticist engine specializing in medical ontology mapping and strict FHIR R4 schemas. "
            "Output strictly valid JSON complying exactly with the provided schema without Markdown wrapping or preamble."
        )

        schema = response_model.model_json_schema()
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "format": schema,
            "options": {
                "temperature": 0.05,
                "num_ctx": self.num_ctx,
            },
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.host_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_content = data.get("message", {}).get("content", "").strip()
            # Clean markdown code blocks if present
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            parsed_json = json.loads(raw_content.strip())
            return response_model.model_validate(parsed_json)

    async def generate_embeddings(self, texts: list[str] | str) -> list[list[float]]:
        """
        Generate 768-dimensional vector embeddings via nomic-embed-text for Qdrant Hybrid RAG.
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings: list[list[float]] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for text in texts:
                resp = await client.post(
                    f"{self.host_url}/api/embeddings",
                    json={"model": self.embed_model, "prompt": text},
                )
                if resp.status_code == 200:
                    embeddings.append(resp.json().get("embedding", []))
                else:
                    # Alternative Ollama endpoint (/api/embed)
                    embed_resp = await client.post(
                        f"{self.host_url}/api/embed",
                        json={"model": self.embed_model, "input": text},
                    )
                    embed_resp.raise_for_status()
                    embeddings.append(embed_resp.json().get("embeddings", [[]])[0])
        return embeddings


# Global router singleton
clinical_router = OllamaClinicalRouter()
