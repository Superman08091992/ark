#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Memory Consolidation Pipelines

Pipeline functions for memory consolidation:
- summarize: Condense reasoning traces
- compress: Further reduce text size
- dedupe_hash: Generate SHA256 hash for deduplication
- embed: Generate vector embeddings for semantic search

These functions are called by MemoryEngine.consolidate() and MemoryEngine.embed()
"""

import hashlib
import logging
import re
from typing import List

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("NumPy not available - embeddings disabled")

logger = logging.getLogger(__name__)


def summarize(text: str, max_length: int = 500) -> str:
    """
    Summarize reasoning trace text
    
    Strategy:
    1. Extract key sentences (those with agent names, actions, decisions)
    2. Preserve structure and context
    3. Remove redundant explanations
    
    Args:
        text: Original reasoning trace text
        max_length: Maximum summary length in characters
        
    Returns:
        Summarized text
    """
    if not text or len(text) <= max_length:
        return text
    
    # Split into lines
    lines = text.split('\n')
    important_lines = []
    
    # Keywords that indicate important content
    important_keywords = [
        'agent:', 'input:', 'output:', 'decision:', 'action:',
        'result:', 'error:', 'warning:', 'critical:', 'success:',
        'failed:', 'completed:', 'reasoning:', 'conclusion:',
        'recommendation:', 'next step:'
    ]
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Keep lines with important keywords
        if any(keyword in line_lower for keyword in important_keywords):
            important_lines.append(line.strip())
        # Keep lines that are questions
        elif '?' in line:
            important_lines.append(line.strip())
        # Keep lines that start with bullet points or numbers
        elif re.match(r'^\s*[-*•\d]+[\.)]\s+', line):
            important_lines.append(line.strip())
    
    # If no important lines found, take first few sentences
    if not important_lines:
        sentences = re.split(r'[.!?]+', text)
        important_lines = [s.strip() for s in sentences[:5] if s.strip()]
    
    # Join and truncate if needed
    summary = '\n'.join(important_lines)
    
    if len(summary) > max_length:
        summary = summary[:max_length] + '...'
    
    return summary


def compress(text: str, aggressive: bool = False) -> str:
    """
    Compress text by removing redundancy
    
    Strategy:
    1. Remove extra whitespace
    2. Remove repeated phrases
    3. Abbreviate common terms
    4. Preserve semantic meaning
    
    Args:
        text: Text to compress
        aggressive: If True, use more aggressive compression
        
    Returns:
        Compressed text
    """
    if not text:
        return text
    
    compressed = text
    
    # Remove extra whitespace
    compressed = re.sub(r'\s+', ' ', compressed)
    compressed = re.sub(r'\n\s*\n', '\n', compressed)
    
    # Remove repeated phrases (same sentence appearing multiple times)
    lines = compressed.split('\n')
    seen = set()
    unique_lines = []
    for line in lines:
        normalized = line.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_lines.append(line)
    compressed = '\n'.join(unique_lines)
    
    if aggressive:
        # Abbreviate common terms
        abbreviations = {
            'reasoning': 'rsn',
            'decision': 'dec',
            'information': 'info',
            'configuration': 'config',
            'implementation': 'impl',
            'application': 'app',
            'generation': 'gen',
            'operation': 'op',
            'function': 'fn',
            'parameter': 'param',
            'response': 'resp',
            'request': 'req',
        }
        
        for full, abbr in abbreviations.items():
            # Only abbreviate if it appears multiple times
            if compressed.lower().count(full) > 2:
                compressed = re.sub(
                    f'\\b{full}\\b',
                    abbr,
                    compressed,
                    flags=re.IGNORECASE
                )
    
    return compressed.strip()


def dedupe_hash(text: str) -> str:
    """
    Generate SHA256 hash for deduplication
    
    Args:
        text: Text to hash
        
    Returns:
        SHA256 hash (hex string)
    """
    if not text:
        return hashlib.sha256(b'').hexdigest()
    
    # Normalize text before hashing
    normalized = text.strip().lower()
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def embed(text: str, dimensions: int = 384) -> 'np.ndarray':
    """
    Generate vector embedding for semantic search
    
    Simple TF-IDF-like embedding strategy:
    1. Tokenize text
    2. Compute term frequencies
    3. Generate fixed-size vector
    
    Note: This is a simple implementation. For production, consider:
    - sentence-transformers (all-MiniLM-L6-v2)
    - OpenAI embeddings API
    - Local LLM embeddings (llama.cpp)
    
    Args:
        text: Text to embed
        dimensions: Embedding dimensions (default: 384)
        
    Returns:
        Embedding vector as numpy array
    """
    if not NUMPY_AVAILABLE:
        raise RuntimeError("NumPy required for embeddings")
    
    if not text:
        return np.zeros(dimensions, dtype=np.float32)
    
    # Tokenize (simple word-based)
    tokens = re.findall(r'\b\w+\b', text.lower())
    
    if not tokens:
        return np.zeros(dimensions, dtype=np.float32)
    
    # Compute term frequencies
    token_counts = {}
    for token in tokens:
        token_counts[token] = token_counts.get(token, 0) + 1
    
    # Generate embedding vector using hash-based projection
    # Each token contributes to multiple dimensions based on its hash
    embedding = np.zeros(dimensions, dtype=np.float32)
    
    for token, count in token_counts.items():
        # Use multiple hash functions for better distribution
        for seed in range(3):  # 3 hash functions
            hash_val = int(hashlib.sha256(f"{token}:{seed}".encode()).hexdigest(), 16)
            dim = hash_val % dimensions
            
            # Add contribution (weighted by term frequency)
            weight = count / len(tokens)
            embedding[dim] += weight
    
    # Normalize to unit vector
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding


def embed_batch(texts: List[str], dimensions: int = 384) -> List['np.ndarray']:
    """
    Generate embeddings for multiple texts
    
    Args:
        texts: List of texts to embed
        dimensions: Embedding dimensions
        
    Returns:
        List of embedding vectors
    """
    return [embed(text, dimensions) for text in texts]


# Advanced pipeline functions (for future enhancement)

def lsh_signature(embedding: 'np.ndarray', num_planes: int = 128) -> str:
    """
    Generate LSH (Locality-Sensitive Hashing) signature for near-duplicate detection
    
    Uses random hyperplanes to create binary signature.
    
    Args:
        embedding: Embedding vector
        num_planes: Number of random hyperplanes (signature bits)
        
    Returns:
        Binary signature as hex string
    """
    if not NUMPY_AVAILABLE:
        raise RuntimeError("NumPy required for LSH")
    
    # Initialize random seed for reproducibility
    np.random.seed(42)
    
    # Generate random hyperplanes
    dimensions = len(embedding)
    planes = np.random.randn(num_planes, dimensions).astype(np.float32)
    
    # Compute dot products and convert to binary
    signature_bits = (np.dot(planes, embedding) >= 0).astype(np.uint8)
    
    # Convert to hex string
    # Pack bits into bytes
    signature_bytes = np.packbits(signature_bits)
    signature_hex = signature_bytes.tobytes().hex()
    
    return signature_hex


def hamming_distance(sig1: str, sig2: str) -> int:
    """
    Compute Hamming distance between two LSH signatures
    
    Args:
        sig1: First signature (hex string)
        sig2: Second signature (hex string)
        
    Returns:
        Hamming distance (number of differing bits)
    """
    if len(sig1) != len(sig2):
        raise ValueError("Signatures must have same length")
    
    # Convert hex to bytes
    bytes1 = bytes.fromhex(sig1)
    bytes2 = bytes.fromhex(sig2)
    
    # Count differing bits
    distance = 0
    for b1, b2 in zip(bytes1, bytes2):
        xor = b1 ^ b2
        distance += bin(xor).count('1')
    
    return distance


if __name__ == '__main__':
    # Test pipeline functions
    print("=" * 60)
    print("ARK Memory Consolidation Pipelines - Test Suite")
    print("=" * 60)
    
    # Test text
    test_text = """
    Agent: Aletheia
    Input: Analyze the reasoning trace from Corpus for decision quality
    Output: The reasoning trace shows good structure with clear decision points.
    However, there are some areas where confidence scores could be improved.
    The agent demonstrated logical thinking and appropriate caution.
    Reasoning: I analyzed the trace by examining decision points, confidence scores,
    and the logical flow of reasoning. The agent showed appropriate caution when
    dealing with uncertain information. This is a positive indicator of reasoning quality.
    Conclusion: Overall assessment is GOOD with minor recommendations for improvement.
    Recommendation: Continue current approach with slight adjustments to confidence calibration.
    """
    
    print("\n1. Summarization:")
    print("-" * 60)
    summary = summarize(test_text, max_length=300)
    print(f"Original length: {len(test_text)} chars")
    print(f"Summary length: {len(summary)} chars")
    print(f"Compression ratio: {len(summary)/len(test_text)*100:.1f}%")
    print(f"\nSummary:\n{summary}")
    
    print("\n2. Compression:")
    print("-" * 60)
    compressed = compress(summary)
    print(f"Summary length: {len(summary)} chars")
    print(f"Compressed length: {len(compressed)} chars")
    print(f"Compression ratio: {len(compressed)/len(summary)*100:.1f}%")
    print(f"\nCompressed:\n{compressed}")
    
    print("\n3. Deduplication Hash:")
    print("-" * 60)
    hash1 = dedupe_hash(compressed)
    hash2 = dedupe_hash(compressed)
    hash3 = dedupe_hash(compressed + " ")  # Slight variation
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3 (with space): {hash3}")
    print(f"Hash 1 == Hash 2: {hash1 == hash2}")
    print(f"Hash 1 == Hash 3: {hash1 == hash3} (should be True due to normalization)")
    
    if NUMPY_AVAILABLE:
        print("\n4. Embedding Generation:")
        print("-" * 60)
        emb1 = embed(compressed, dimensions=128)
        emb2 = embed(compressed, dimensions=128)
        emb3 = embed("Completely different text about cooking recipes", dimensions=128)
        
        print(f"Embedding shape: {emb1.shape}")
        print(f"Embedding dtype: {emb1.dtype}")
        print(f"Embedding norm: {np.linalg.norm(emb1):.4f} (should be ~1.0)")
        print(f"First 10 values: {emb1[:10]}")
        
        # Cosine similarity
        cos_sim_same = np.dot(emb1, emb2)
        cos_sim_diff = np.dot(emb1, emb3)
        print(f"\nCosine similarity (same text): {cos_sim_same:.4f}")
        print(f"Cosine similarity (different text): {cos_sim_diff:.4f}")
        
        print("\n5. LSH Signatures:")
        print("-" * 60)
        sig1 = lsh_signature(emb1, num_planes=128)
        sig2 = lsh_signature(emb2, num_planes=128)
        sig3 = lsh_signature(emb3, num_planes=128)
        
        print(f"Signature 1: {sig1[:32]}... (length: {len(sig1)})")
        print(f"Signature 2: {sig2[:32]}... (length: {len(sig2)})")
        print(f"Signature 3: {sig3[:32]}... (length: {len(sig3)})")
        
        dist_same = hamming_distance(sig1, sig2)
        dist_diff = hamming_distance(sig1, sig3)
        
        print(f"\nHamming distance (same text): {dist_same}")
        print(f"Hamming distance (different text): {dist_diff}")
        print(f"Similarity threshold: ~{128 * 0.2:.0f} bits for near-duplicates")
    else:
        print("\n4. Embedding Generation:")
        print("-" * 60)
        print("NumPy not available - embeddings disabled")
    
    print("\n" + "=" * 60)
    print("Pipeline tests complete!")
    print("=" * 60)
