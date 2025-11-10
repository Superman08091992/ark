"""
Production Configuration Validator and Setup
Ensures all required environment variables and settings are correct before go-live
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class ProductionConfigValidator:
    """Validate production configuration before deployment"""
    
    REQUIRED_ENV_VARS = [
        'ARK_ENV',
        'ARK_LOG_LEVEL',
        'ARK_STATE_DB',
        'REDIS_URL',
        'SESSION_SECRET',
        'JWT_SECRET',
    ]
    
    REQUIRED_FILES = [
        '/var/lib/ark',  # State directory
        '/var/backups/ark',  # Backup directory
    ]
    
    SECURITY_CHECKS = {
        'SESSION_SECRET': 32,  # Minimum length
        'JWT_SECRET': 32,
    }
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_env_vars(self) -> bool:
        """Validate required environment variables"""
        for var in self.REQUIRED_ENV_VARS:
            if not os.getenv(var):
                self.errors.append(f"Missing required environment variable: {var}")
        
        # Check ARK_ENV is 'prod'
        if os.getenv('ARK_ENV') != 'prod':
            self.errors.append(f"ARK_ENV must be 'prod', got: {os.getenv('ARK_ENV')}")
        
        return len(self.errors) == 0
    
    def validate_security(self) -> bool:
        """Validate security settings"""
        for key, min_length in self.SECURITY_CHECKS.items():
            value = os.getenv(key, '')
            
            if 'REPLACE' in value:
                self.errors.append(f"{key} still contains placeholder value")
            elif len(value) < min_length:
                self.errors.append(f"{key} must be at least {min_length} characters")
        
        # Check CORS origins
        cors_origins = os.getenv('CORS_ORIGINS', '')
        if '*' in cors_origins:
            self.errors.append("CORS_ORIGINS must not contain wildcard (*) in production")
        
        return len(self.errors) == 0
    
    def validate_directories(self) -> bool:
        """Validate required directories exist"""
        for dir_path in self.REQUIRED_FILES:
            path = Path(dir_path)
            if not path.exists():
                self.warnings.append(f"Directory does not exist (will be created): {dir_path}")
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {dir_path}")
                except PermissionError:
                    self.errors.append(f"Cannot create directory (permission denied): {dir_path}")
        
        return len(self.errors) == 0
    
    def validate_sqlite_wal(self) -> bool:
        """Validate SQLite WAL mode configuration"""
        db_path = os.getenv('ARK_STATE_DB')
        if not db_path:
            return False
        
        db_file = Path(db_path)
        db_dir = db_file.parent
        
        if not db_dir.exists():
            self.warnings.append(f"Database directory will be created: {db_dir}")
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                self.errors.append(f"Cannot create database directory: {db_dir}")
                return False
        
        # Check write permissions
        if not os.access(db_dir, os.W_OK):
            self.errors.append(f"No write permission for database directory: {db_dir}")
            return False
        
        return True
    
    def validate_redis(self) -> bool:
        """Validate Redis connectivity"""
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            self.errors.append("REDIS_URL not set")
            return False
        
        # Try to connect
        try:
            import redis
            r = redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            logger.info("✅ Redis connection successful")
            return True
        except ImportError:
            self.warnings.append("Redis library not available (will be needed in production)")
            return True
        except Exception as e:
            self.errors.append(f"Cannot connect to Redis: {e}")
            return False
    
    def validate_rate_limits(self) -> bool:
        """Validate rate limiting configuration"""
        kenny_rate = os.getenv('KENNY_MAX_ACTIONS_PER_MINUTE', '60')
        
        try:
            rate = int(kenny_rate)
            if rate > 100:
                self.warnings.append(f"Kenny rate limit very high: {rate}/min")
            elif rate < 10:
                self.warnings.append(f"Kenny rate limit very low: {rate}/min")
        except ValueError:
            self.errors.append(f"Invalid KENNY_MAX_ACTIONS_PER_MINUTE: {kenny_rate}")
            return False
        
        return True
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validations"""
        checks = [
            ('Environment Variables', self.validate_env_vars),
            ('Security Settings', self.validate_security),
            ('Directories', self.validate_directories),
            ('SQLite WAL', self.validate_sqlite_wal),
            ('Redis Connection', self.validate_redis),
            ('Rate Limits', self.validate_rate_limits),
        ]
        
        all_passed = True
        
        for name, check_func in checks:
            try:
                passed = check_func()
                status = "✅" if passed else "❌"
                print(f"{status} {name}")
                
                if not passed:
                    all_passed = False
            except Exception as e:
                print(f"❌ {name}: {e}")
                self.errors.append(f"{name} check failed: {e}")
                all_passed = False
        
        return all_passed, self.errors, self.warnings
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("PRODUCTION CONFIGURATION VALIDATION")
        print("=" * 60)
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All validations passed!")
        elif not self.errors:
            print("\n⚠️  Validation passed with warnings")
        else:
            print("\n❌ Validation FAILED - Cannot proceed to production")
        
        print("=" * 60)


def setup_sqlite_wal(db_path: str) -> bool:
    """Enable SQLite WAL mode"""
    import sqlite3
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")  # Better performance with WAL
        conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
        conn.execute("PRAGMA temp_store=MEMORY")
        result = conn.execute("PRAGMA journal_mode").fetchone()
        conn.close()
        
        if result[0] == 'wal':
            logger.info(f"✅ SQLite WAL mode enabled for {db_path}")
            return True
        else:
            logger.error(f"❌ Failed to enable WAL mode, got: {result[0]}")
            return False
    except Exception as e:
        logger.error(f"❌ Error enabling WAL mode: {e}")
        return False


def create_backup(db_path: str, backup_dir: str) -> bool:
    """Create database backup before deployment"""
    import shutil
    from datetime import datetime
    
    try:
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_path / f"ark_state_pre_deploy_{timestamp}.db"
        
        if Path(db_path).exists():
            shutil.copy2(db_path, backup_file)
            logger.info(f"✅ Backup created: {backup_file}")
            return True
        else:
            logger.warning(f"⚠️  No existing database to backup: {db_path}")
            return True  # Not an error for first deployment
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return False


if __name__ == "__main__":
    # Load environment from .env.production if it exists
    env_file = Path(__file__).parent.parent / '.env.production'
    if env_file.exists():
        print(f"Loading environment from: {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Skip shell expansions
                    if not value.startswith('$('):
                        os.environ[key] = value
    
    # Run validation
    validator = ProductionConfigValidator()
    passed, errors, warnings = validator.validate_all()
    validator.print_summary()
    
    if passed and not errors:
        print("\n🚀 Proceeding with production setup...")
        
        # Setup SQLite WAL
        db_path = os.getenv('ARK_STATE_DB', '/var/lib/ark/ark_state.db')
        if os.getenv('ARK_DB_WAL_ENABLED', 'true').lower() == 'true':
            setup_sqlite_wal(db_path)
        
        # Create backup
        backup_dir = os.getenv('BACKUP_DIR', '/var/backups/ark')
        create_backup(db_path, backup_dir)
        
        print("\n✅ Production configuration complete!")
        sys.exit(0)
    else:
        print("\n❌ Configuration validation failed")
        sys.exit(1)
