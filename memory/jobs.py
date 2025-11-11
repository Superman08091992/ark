#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Memory Consolidation Jobs

Scheduled and on-demand jobs for memory consolidation:
- Nightly consolidator: Runs consolidation pipeline on unconsolidated traces
- On-demand compactor: Manual trigger for immediate consolidation
- Embedding generator: Batch embedding generation for new chunks

Can be run as cron jobs or triggered via API.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.engine import MemoryEngine

logger = logging.getLogger(__name__)


# ============================================================================
# Job Configuration
# ============================================================================

DEFAULT_CONFIG = {
    'consolidation': {
        'batch_size': 100,
        'max_age_hours': 24,  # Only consolidate traces older than this
        'min_traces': 10,  # Minimum traces needed before consolidating
    },
    'embedding': {
        'batch_size': 50,
        'max_chunks_per_run': 500,
    },
    'cleanup': {
        'max_age_days': 90,  # Archive traces older than this
        'keep_consolidated': True,  # Keep consolidated chunks even if traces archived
    },
}


# ============================================================================
# Nightly Consolidator
# ============================================================================

async def run_consolidation(
    engine: Optional[MemoryEngine] = None,
    config: Optional[Dict] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Run consolidation pipeline on unconsolidated traces.
    
    This is the main nightly job that:
    1. Finds unconsolidated reasoning traces
    2. Runs summarization, compression, deduplication
    3. Creates memory chunks
    4. Marks traces as consolidated
    
    Args:
        engine: MemoryEngine instance (creates new if None)
        config: Job configuration (uses defaults if None)
        dry_run: If True, report what would be done without making changes
        
    Returns:
        Job result dictionary with statistics
        
    Example:
        >>> result = await run_consolidation(dry_run=True)
        >>> print(f"Would consolidate {result['traces_found']} traces")
    """
    start_time = time.time()
    config = config or DEFAULT_CONFIG['consolidation']
    
    # Create engine if not provided
    if engine is None:
        engine = MemoryEngine()
        created_engine = True
    else:
        created_engine = False
    
    try:
        logger.info("=" * 60)
        logger.info("Starting memory consolidation job")
        logger.info(f"Config: {json.dumps(config, indent=2)}")
        logger.info(f"Dry run: {dry_run}")
        logger.info("=" * 60)
        
        # Calculate cutoff timestamp (only consolidate old enough traces)
        cutoff_ts = int((datetime.now() - timedelta(hours=config['max_age_hours'])).timestamp() * 1000)
        
        # Get statistics before consolidation
        stats_before = engine.get_stats()
        logger.info(f"Stats before: {json.dumps(stats_before, indent=2)}")
        
        # Check if we have enough traces to consolidate
        unconsolidated = stats_before.get('traces_total', 0) - stats_before.get('chunks_total', 0)
        if unconsolidated < config['min_traces']:
            logger.info(f"Only {unconsolidated} unconsolidated traces (min: {config['min_traces']})")
            logger.info("Skipping consolidation - not enough traces")
            return {
                'status': 'skipped',
                'reason': 'insufficient_traces',
                'traces_found': unconsolidated,
                'min_required': config['min_traces'],
                'duration_seconds': time.time() - start_time,
            }
        
        if dry_run:
            logger.info(f"DRY RUN: Would consolidate up to {config['batch_size']} traces")
            return {
                'status': 'dry_run',
                'traces_found': unconsolidated,
                'batch_size': config['batch_size'],
                'cutoff_timestamp': cutoff_ts,
                'duration_seconds': time.time() - start_time,
            }
        
        # Run consolidation
        logger.info(f"Consolidating traces older than {cutoff_ts}...")
        consolidation_result = engine.consolidate(
            since_ts=cutoff_ts,
            batch_size=config['batch_size']
        )
        
        logger.info(f"Consolidation result: {json.dumps(consolidation_result, indent=2)}")
        
        # Get statistics after consolidation
        stats_after = engine.get_stats()
        logger.info(f"Stats after: {json.dumps(stats_after, indent=2)}")
        
        duration = time.time() - start_time
        
        result = {
            'status': 'success',
            'traces_processed': consolidation_result.get('traces_processed', 0),
            'chunks_created': consolidation_result.get('chunks_created', 0),
            'duplicates_found': consolidation_result.get('duplicates_skipped', 0),
            'quarantined': consolidation_result.get('quarantined', 0),
            'duration_seconds': duration,
            'stats_before': stats_before,
            'stats_after': stats_after,
        }
        
        logger.info("=" * 60)
        logger.info("Consolidation job completed successfully")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info("=" * 60)
        
        return result
    
    except Exception as e:
        logger.error(f"Consolidation job failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'duration_seconds': time.time() - start_time,
        }
    
    finally:
        if created_engine:
            engine.close()


# ============================================================================
# Embedding Generator
# ============================================================================

async def run_embedding_generation(
    engine: Optional[MemoryEngine] = None,
    config: Optional[Dict] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Generate embeddings for memory chunks that don't have them.
    
    This job:
    1. Finds chunks without embeddings
    2. Generates embeddings in batches
    3. Updates database
    
    Args:
        engine: MemoryEngine instance (creates new if None)
        config: Job configuration (uses defaults if None)
        dry_run: If True, report what would be done without making changes
        
    Returns:
        Job result dictionary with statistics
    """
    start_time = time.time()
    config = config or DEFAULT_CONFIG['embedding']
    
    # Create engine if not provided
    if engine is None:
        engine = MemoryEngine()
        created_engine = True
    else:
        created_engine = False
    
    try:
        logger.info("=" * 60)
        logger.info("Starting embedding generation job")
        logger.info(f"Config: {json.dumps(config, indent=2)}")
        logger.info(f"Dry run: {dry_run}")
        logger.info("=" * 60)
        
        # Get statistics
        stats = engine.get_stats()
        logger.info(f"Stats: {json.dumps(stats, indent=2)}")
        
        # Check how many chunks need embeddings
        chunks_without_embeddings = stats.get('chunks_without_embeddings', 0)
        if chunks_without_embeddings == 0:
            logger.info("No chunks need embeddings")
            return {
                'status': 'skipped',
                'reason': 'no_chunks_need_embeddings',
                'duration_seconds': time.time() - start_time,
            }
        
        logger.info(f"Found {chunks_without_embeddings} chunks without embeddings")
        
        # Calculate how many to process
        chunks_to_process = min(chunks_without_embeddings, config['max_chunks_per_run'])
        
        if dry_run:
            logger.info(f"DRY RUN: Would generate embeddings for {chunks_to_process} chunks")
            return {
                'status': 'dry_run',
                'chunks_found': chunks_without_embeddings,
                'chunks_would_process': chunks_to_process,
                'batch_size': config['batch_size'],
                'duration_seconds': time.time() - start_time,
            }
        
        # Generate embeddings
        logger.info(f"Generating embeddings for up to {chunks_to_process} chunks...")
        embedded_count = engine.embed(
            chunk_ids=None,  # Process all chunks without embeddings
            batch_size=config['batch_size']
        )
        
        logger.info(f"Generated {embedded_count} embeddings")
        
        duration = time.time() - start_time
        
        result = {
            'status': 'success',
            'chunks_embedded': embedded_count,
            'duration_seconds': duration,
        }
        
        logger.info("=" * 60)
        logger.info("Embedding generation job completed successfully")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info("=" * 60)
        
        return result
    
    except Exception as e:
        logger.error(f"Embedding generation job failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'duration_seconds': time.time() - start_time,
        }
    
    finally:
        if created_engine:
            engine.close()


# ============================================================================
# Full Pipeline (Consolidation + Embedding)
# ============================================================================

async def run_full_pipeline(
    engine: Optional[MemoryEngine] = None,
    config: Optional[Dict] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Run full consolidation pipeline: consolidate + generate embeddings.
    
    This is the recommended nightly job that runs both stages.
    
    Args:
        engine: MemoryEngine instance (creates new if None)
        config: Job configuration (uses defaults if None)
        dry_run: If True, report what would be done without making changes
        
    Returns:
        Job result dictionary with statistics from both stages
    """
    start_time = time.time()
    
    # Create engine if not provided (will be shared across jobs)
    if engine is None:
        engine = MemoryEngine()
        created_engine = True
    else:
        created_engine = False
    
    try:
        logger.info("=" * 70)
        logger.info("Starting FULL memory consolidation pipeline")
        logger.info("=" * 70)
        
        # Stage 1: Consolidation
        logger.info("\n>>> Stage 1: Consolidation")
        consolidation_result = await run_consolidation(
            engine=engine,
            config=config.get('consolidation') if config else None,
            dry_run=dry_run
        )
        
        # Stage 2: Embedding generation
        logger.info("\n>>> Stage 2: Embedding Generation")
        embedding_result = await run_embedding_generation(
            engine=engine,
            config=config.get('embedding') if config else None,
            dry_run=dry_run
        )
        
        duration = time.time() - start_time
        
        result = {
            'status': 'success',
            'consolidation': consolidation_result,
            'embedding': embedding_result,
            'total_duration_seconds': duration,
        }
        
        logger.info("=" * 70)
        logger.info("Full pipeline completed successfully")
        logger.info(f"Total duration: {duration:.2f}s")
        logger.info("=" * 70)
        
        return result
    
    except Exception as e:
        logger.error(f"Full pipeline failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'total_duration_seconds': time.time() - start_time,
        }
    
    finally:
        if created_engine:
            engine.close()


# ============================================================================
# CLI Entry Points
# ============================================================================

def main():
    """
    CLI entry point for running jobs manually.
    
    Usage:
        python memory/jobs.py consolidate [--dry-run]
        python memory/jobs.py embed [--dry-run]
        python memory/jobs.py full [--dry-run]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='ARK Memory Consolidation Jobs')
    parser.add_argument('job', choices=['consolidate', 'embed', 'full'],
                       help='Job to run')
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform dry run without making changes')
    parser.add_argument('--config', type=str,
                       help='Path to config JSON file')
    parser.add_argument('--db', type=str, default='data/ark_memory.db',
                       help='Path to SQLite database')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Load config if provided
    config = DEFAULT_CONFIG
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    
    # Create engine
    engine = MemoryEngine(db_path=args.db)
    
    # Run job
    if args.job == 'consolidate':
        result = asyncio.run(run_consolidation(
            engine=engine,
            config=config.get('consolidation'),
            dry_run=args.dry_run
        ))
    elif args.job == 'embed':
        result = asyncio.run(run_embedding_generation(
            engine=engine,
            config=config.get('embedding'),
            dry_run=args.dry_run
        ))
    elif args.job == 'full':
        result = asyncio.run(run_full_pipeline(
            engine=engine,
            config=config,
            dry_run=args.dry_run
        ))
    else:
        parser.print_help()
        return 1
    
    # Print result
    print("\n" + "=" * 70)
    print("JOB RESULT")
    print("=" * 70)
    print(json.dumps(result, indent=2))
    print("=" * 70)
    
    # Close engine
    engine.close()
    
    # Return exit code based on status
    return 0 if result.get('status') in ['success', 'skipped', 'dry_run'] else 1


if __name__ == '__main__':
    sys.exit(main())
