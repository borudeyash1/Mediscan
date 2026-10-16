import urllib.request
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def probe(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("[1/3] Testing nomic-embed-text (768 dimensions)...")
emb = probe("http://localhost:11434/api/embeddings", {"model": "nomic-embed-text", "prompt": "cardiology AHA guideline"})
vec = emb.get("embedding", [])
print(f"  ✓ Embedding length: {len(vec)}")
assert len(vec) == 768, f"Expected 768 dimensions, got {len(vec)}"

print("[2/3] Testing qwen2.5-coder:7b (Structured JSON)...")
qwen = probe("http://localhost:11434/api/generate", {
    "model": "qwen2.5-coder:7b",
    "prompt": "Return a JSON object with keys status and phase set to ok and 1",
    "format": "json",
    "stream": False,
})
resp_str = qwen.get("response", "").strip()
print(f"  ✓ Qwen response: {resp_str}")
parsed = json.loads(resp_str)
assert "status" in parsed

print("[3/3] Testing medgemma:4b (Clinical Reasoning)...")
med = probe("http://localhost:11434/api/generate", {
    "model": "medgemma:4b",
    "prompt": "What is the first-line pharmacotherapy for essential hypertension? Answer in one sentence.",
    "stream": False,
})
med_str = med.get("response", "").strip()
print(f"  ✓ MedGemma response: {med_str}")

print("\nALL OLLAMA PROBES PASSED ✓")
