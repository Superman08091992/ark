#!/usr/bin/env python3
"""
A.R.K. Federation Service
=========================
Synchronizes node manifests and code-lattice deltas among peers.

Endpoints
---------
GET  /discover        → list active peers from Redis
POST /manifest        → register/update local node manifest
POST /sync            → request or push lattice deltas
"""

import os, json, time, hashlib, base64
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import redis
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
NODE_ID       = os.getenv("ARK_NODE_ID", "ark-node-local")
FEDERATION_KEY = os.getenv("ARK_FED_PUBKEY", "")      # base64-encoded Ed25519 pubkey
REDIS_URL     = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATA_DIR      = os.getenv("LATTICE_PATH", "./lattice_data")

r = redis.from_url(REDIS_URL, decode_responses=True)
app = FastAPI(title="A.R.K. Federation Service")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_hash(path: str) -> str:
    """Return SHA256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def verify_signature(payload: bytes, signature: str, pubkey_b64: str) -> bool:
    try:
        verify_key = VerifyKey(base64.b64decode(pubkey_b64))
        verify_key.verify(payload, base64.b64decode(signature))
        return True
    except (BadSignatureError, Exception):
        return False

def load_manifest() -> dict:
    path = os.path.join(DATA_DIR, "manifest.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------

@app.get("/discover")
def discover():
    """List peers recently seen via Redis."""
    peers = []
    for key in r.scan_iter(match="peer:*"):
        peers.append(r.hgetall(key))
    return {"peers": peers, "count": len(peers)}

@app.post("/manifest")
async def register_manifest(request: Request):
    """Register or update this node's manifest."""
    data = await request.json()
    manifest = data.get("manifest")
    signature = data.get("signature")
    pubkey = data.get("pubkey")
    if not (manifest and signature and pubkey):
        raise HTTPException(status_code=400, detail="missing fields")

    payload = json.dumps(manifest, sort_keys=True).encode()
    if not verify_signature(payload, signature, pubkey):
        raise HTTPException(status_code=401, detail="invalid signature")

    # Store in Redis
    node_id = manifest.get("node_id", "unknown")
    manifest["last_seen"] = int(time.time())
    r.hset(f"peer:{node_id}", mapping=manifest)
    r.expire(f"peer:{node_id}", 120)  # 2-minute TTL
    return {"status": "registered", "node_id": node_id}

@app.post("/sync")
async def sync_nodes(request: Request):
    """
    Exchange node deltas.
    Caller sends {manifest_hash, nodes:[{id,hash,...}]}.
    Respond with nodes that differ.
    """
    body = await request.json()
    remote_nodes = {n["id"]: n["hash"] for n in body.get("nodes", [])}
    local_manifest = load_manifest()
    local_nodes = {n["id"]: n["hash"] for n in local_manifest.get("nodes", [])}

    delta = []
    for nid, h in local_nodes.items():
        if remote_nodes.get(nid) != h:
            node_path = os.path.join(DATA_DIR, f"{nid}.json")
            if os.path.exists(node_path):
                with open(node_path) as f:
                    delta.append(json.load(f))

    return JSONResponse({"delta_count": len(delta), "nodes": delta})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("FEDERATION_PORT", "9001")))
