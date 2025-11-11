"""
ARK Federation Cryptographic Module

Provides key management, message signing, and signature verification
for inter-node KnowledgePacket authentication.

Uses PyNaCl (libsodium) for Ed25519 keypairs and digital signing.
No network code — just the cryptographic contract used by federation
and backend to ensure every message is verifiable and immutable.

Security Design:
- Algorithm: Ed25519 via libsodium (modern, fast, no nonce reuse risk)
- Keys: 64-byte private, 32-byte public, hex-encoded for portability
- Trust tier enforcement: Only CORE peers may share verified keys
- No dependencies on external PKI — fully sovereign key exchange
"""

from nacl import signing, exceptions
from nacl.encoding import HexEncoder
import json
import os
import time
import logging

logger = logging.getLogger(__name__)

KEY_DIR = os.getenv("ARK_KEY_DIR", "keys")
os.makedirs(KEY_DIR, exist_ok=True)


# =====================================================
# 1. Key Generation / Storage
# =====================================================

def generate_keypair(node_id: str):
    """
    Create a persistent Ed25519 keypair for this node.
    
    Args:
        node_id: Unique identifier for this node
        
    Returns:
        Tuple of (private_key, public_key)
        
    Note:
        Keys are stored in KEY_DIR as hex-encoded files.
        If keypair already exists, it will be loaded instead.
    """
    priv_path = os.path.join(KEY_DIR, f"{node_id}_private.key")
    pub_path = os.path.join(KEY_DIR, f"{node_id}_public.key")

    if os.path.exists(priv_path) and os.path.exists(pub_path):
        logger.info(f"Loading existing keypair for node: {node_id}")
        return load_keypair(node_id)

    logger.info(f"Generating new Ed25519 keypair for node: {node_id}")
    private_key = signing.SigningKey.generate()
    public_key = private_key.verify_key

    # Write private key (secure permissions)
    with open(priv_path, "wb") as f:
        f.write(private_key.encode(encoder=HexEncoder))
    os.chmod(priv_path, 0o600)  # Read/write for owner only

    # Write public key (can be shared)
    with open(pub_path, "wb") as f:
        f.write(public_key.encode(encoder=HexEncoder))
    os.chmod(pub_path, 0o644)  # Readable by all

    logger.info(f"✅ Keypair generated and saved for node: {node_id}")
    return private_key, public_key


def load_keypair(node_id: str):
    """
    Load existing keypair from disk.
    
    Args:
        node_id: Node identifier
        
    Returns:
        Tuple of (private_key, public_key)
        
    Raises:
        FileNotFoundError: If keypair files don't exist
    """
    priv_path = os.path.join(KEY_DIR, f"{node_id}_private.key")
    pub_path = os.path.join(KEY_DIR, f"{node_id}_public.key")

    if not os.path.exists(priv_path):
        raise FileNotFoundError(f"Private key not found for node: {node_id}")
    if not os.path.exists(pub_path):
        raise FileNotFoundError(f"Public key not found for node: {node_id}")

    with open(priv_path, "rb") as f:
        private_key = signing.SigningKey(f.read(), encoder=HexEncoder)
    
    with open(pub_path, "rb") as f:
        public_key = signing.VerifyKey(f.read(), encoder=HexEncoder)
    
    return private_key, public_key


def keypair_exists(node_id: str) -> bool:
    """Check if keypair exists for node"""
    priv_path = os.path.join(KEY_DIR, f"{node_id}_private.key")
    pub_path = os.path.join(KEY_DIR, f"{node_id}_public.key")
    return os.path.exists(priv_path) and os.path.exists(pub_path)


# =====================================================
# 2. Signing & Verification
# =====================================================

def sign_packet(private_key: signing.SigningKey, packet: dict) -> dict:
    """
    Sign a federation KnowledgePacket (dict) and return envelope.
    
    Args:
        private_key: Ed25519 signing key
        packet: KnowledgePacket as dictionary
        
    Returns:
        Signed envelope containing packet, signature, timestamp, node_id
        
    Example:
        >>> packet = {"origin_id": "node-alpha", "type": "KnowledgeUpdate", "data": {...}}
        >>> envelope = sign_packet(private_key, packet)
    """
    # Serialize packet deterministically (sorted keys)
    body = json.dumps(packet, sort_keys=True).encode()
    
    # Sign the body
    signed = private_key.sign(body)
    signature = signed.signature.hex()
    
    # Create envelope with signature
    envelope = {
        "packet": packet,
        "signature": signature,
        "timestamp": int(time.time() * 1000),  # Milliseconds since epoch
        "node_id": packet.get("origin_id", "unknown")
    }
    
    logger.debug(f"Signed packet from {envelope['node_id']}: sig={signature[:16]}...")
    return envelope


def verify_packet(envelope: dict, public_key: signing.VerifyKey) -> bool:
    """
    Verify a received signed KnowledgePacket.
    
    Args:
        envelope: Signed packet envelope (from sign_packet)
        public_key: Ed25519 verify key of the sender
        
    Returns:
        True if signature is valid, False otherwise
        
    Example:
        >>> peer_pub = load_peer_key("node-alpha")
        >>> verified = verify_packet(signed_envelope, peer_pub)
        >>> if not verified:
        ...     raise SecurityError("Invalid signature!")
    """
    try:
        # Re-serialize packet exactly as it was signed
        packet_bytes = json.dumps(envelope["packet"], sort_keys=True).encode()
        
        # Decode hex signature
        signature = bytes.fromhex(envelope["signature"])
        
        # Verify signature
        public_key.verify(packet_bytes, signature)
        
        logger.debug(f"✅ Verified packet from {envelope['node_id']}")
        return True
        
    except exceptions.BadSignatureError:
        logger.warning(f"❌ Invalid signature from {envelope.get('node_id', 'unknown')}")
        return False
    except (KeyError, ValueError) as e:
        logger.error(f"❌ Malformed envelope: {e}")
        return False


# =====================================================
# 3. Utilities
# =====================================================

def export_public_key(node_id: str) -> str:
    """
    Return public key string for peer registration.
    
    Args:
        node_id: Node identifier
        
    Returns:
        Hex-encoded public key string
        
    Example:
        >>> pub_hex = export_public_key("node-alpha")
        >>> print(f"Share this with peers: {pub_hex}")
    """
    _, pub = load_keypair(node_id)
    return pub.encode(encoder=HexEncoder).decode()


def import_peer_key(node_id: str, public_hex: str):
    """
    Save a trusted peer's public key locally.
    
    Args:
        node_id: Peer's node identifier
        public_hex: Hex-encoded public key from peer
        
    Note:
        Only import keys from CORE-tier peers you fully trust.
        This enables signature verification for their packets.
    """
    path = os.path.join(KEY_DIR, f"{node_id}_peer.key")
    
    # Validate format before saving
    try:
        signing.VerifyKey(public_hex.strip().encode(), encoder=HexEncoder)
    except Exception as e:
        raise ValueError(f"Invalid public key format: {e}")
    
    with open(path, "w") as f:
        f.write(public_hex.strip())
    
    os.chmod(path, 0o644)
    logger.info(f"✅ Imported public key for peer: {node_id}")


def load_peer_key(node_id: str) -> signing.VerifyKey:
    """
    Load a trusted peer's verify key.
    
    Args:
        node_id: Peer's node identifier
        
    Returns:
        Ed25519 verify key
        
    Raises:
        FileNotFoundError: If peer key not found
    """
    path = os.path.join(KEY_DIR, f"{node_id}_peer.key")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Peer key not found for: {node_id}")
    
    with open(path, "r") as f:
        public_hex = f.read().strip()
    
    return signing.VerifyKey(public_hex.encode(), encoder=HexEncoder)


def peer_key_exists(node_id: str) -> bool:
    """Check if peer key exists"""
    path = os.path.join(KEY_DIR, f"{node_id}_peer.key")
    return os.path.exists(path)


def list_keys() -> dict:
    """
    List all keys in KEY_DIR.
    
    Returns:
        Dictionary with 'local' and 'peers' key lists
    """
    files = os.listdir(KEY_DIR)
    
    local_nodes = set()
    peer_nodes = set()
    
    for f in files:
        if f.endswith("_private.key"):
            node_id = f.replace("_private.key", "")
            local_nodes.add(node_id)
        elif f.endswith("_peer.key"):
            node_id = f.replace("_peer.key", "")
            peer_nodes.add(node_id)
    
    return {
        "local": sorted(local_nodes),
        "peers": sorted(peer_nodes)
    }


def get_key_fingerprint(node_id: str, is_peer: bool = False) -> str:
    """
    Get short fingerprint of a public key for display.
    
    Args:
        node_id: Node identifier
        is_peer: True if this is a peer key, False if local
        
    Returns:
        First 16 chars of hex public key
    """
    try:
        if is_peer:
            pub_key = load_peer_key(node_id)
        else:
            _, pub_key = load_keypair(node_id)
        
        pub_hex = pub_key.encode(encoder=HexEncoder).decode()
        return pub_hex[:16] + "..."
    except Exception:
        return "unknown"


def delete_keypair(node_id: str):
    """
    Delete local keypair (use with caution!)
    
    Args:
        node_id: Node identifier
    """
    priv_path = os.path.join(KEY_DIR, f"{node_id}_private.key")
    pub_path = os.path.join(KEY_DIR, f"{node_id}_public.key")
    
    if os.path.exists(priv_path):
        os.remove(priv_path)
        logger.warning(f"Deleted private key for: {node_id}")
    
    if os.path.exists(pub_path):
        os.remove(pub_path)
        logger.warning(f"Deleted public key for: {node_id}")


def delete_peer_key(node_id: str):
    """
    Remove trust for a peer by deleting their public key.
    
    Args:
        node_id: Peer's node identifier
    """
    path = os.path.join(KEY_DIR, f"{node_id}_peer.key")
    
    if os.path.exists(path):
        os.remove(path)
        logger.info(f"Removed peer key for: {node_id}")


# =====================================================
# 4. Testing & Validation
# =====================================================

def test_sign_verify():
    """
    Self-test of signing and verification.
    
    Returns:
        True if test passes
    """
    logger.info("Running crypto self-test...")
    
    # Generate test keypair
    test_node = "test-node-crypto"
    priv, pub = generate_keypair(test_node)
    
    # Create test packet
    test_packet = {
        "origin_id": test_node,
        "type": "TestPacket",
        "data": {"message": "Hello, ARK!"}
    }
    
    # Sign packet
    envelope = sign_packet(priv, test_packet)
    
    # Verify with correct key
    valid = verify_packet(envelope, pub)
    if not valid:
        logger.error("❌ Self-test failed: valid signature rejected")
        return False
    
    # Verify with wrong key (should fail)
    wrong_priv, wrong_pub = generate_keypair("wrong-node")
    invalid = verify_packet(envelope, wrong_pub)
    if invalid:
        logger.error("❌ Self-test failed: invalid signature accepted")
        return False
    
    # Cleanup test keys
    delete_keypair(test_node)
    delete_keypair("wrong-node")
    
    logger.info("✅ Crypto self-test passed")
    return True


if __name__ == "__main__":
    # Run self-test when executed directly
    logging.basicConfig(level=logging.INFO)
    test_sign_verify()
