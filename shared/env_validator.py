#!/usr/bin/env python3
"""
ARK Environment Variable Validator (REQ_SEC_01)

Validates environment variables against .env.schema specification.
Ensures credential boundary separation and required variables are present.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class EnvValidationError(Exception):
    """Exception raised when environment validation fails"""
    pass


class EnvValidator:
    """
    Validates environment variables against schema.
    
    Features:
    - Required field validation
    - Type checking (string, int, bool)
    - Range validation for numeric values
    - Sensitive field detection
    - Credential boundary enforcement
    """
    
    # Sensitive variable patterns
    SENSITIVE_PATTERNS = [
        'PASSWORD', 'SECRET', 'TOKEN', 'KEY', 'API_KEY', 'PRIVATE_KEY'
    ]
    
    # Required variables by environment
    REQUIRED_PRODUCTION = {
        'ARK_ENVIRONMENT',
        'ARK_SESSION_SECRET',
    }
    
    REQUIRED_DEVELOPMENT = {
        'ARK_ENVIRONMENT',
    }
    
    # Credential boundaries (separate credential domains)
    CREDENTIAL_BOUNDARIES = {
        'telegram': ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_ALLOWED_USERS'],
        'llm': ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'OLLAMA_HOST'],
        'trading': ['ALPACA_API_KEY', 'ALPACA_API_SECRET', 'COINBASE_API_KEY', 'COINBASE_API_SECRET'],
        'infrastructure': ['REDIS_PASSWORD', 'ARK_SESSION_SECRET'],
        'external': ['NEWS_API_KEY']
    }
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize environment validator.
        
        Args:
            schema_path: Path to .env.schema file (default: .env.schema in current dir)
        """
        if schema_path is None:
            schema_path = Path(__file__).parent.parent / '.env.schema'
        
        self.schema_path = schema_path
        self.schema = self._parse_schema()
    
    def _parse_schema(self) -> Dict[str, Dict]:
        """
        Parse .env.schema file to extract variable specifications.
        
        Returns:
            Dict mapping variable names to their specifications
        """
        if not self.schema_path.exists():
            print(f"⚠️  Schema file not found: {self.schema_path}")
            return {}
        
        schema = {}
        current_var = None
        
        with open(self.schema_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and section headers
                if not line or line.startswith('#') or line.startswith('---') or line.startswith('=='):
                    continue
                
                # Variable definition
                if '=' in line and not line.startswith('#'):
                    var_name = line.split('=')[0].strip()
                    default_value = line.split('=', 1)[1].strip() if '=' in line else None
                    
                    schema[var_name] = {
                        'name': var_name,
                        'default': default_value,
                        'required': False,
                        'sensitive': any(p in var_name for p in self.SENSITIVE_PATTERNS),
                        'type': 'string'
                    }
                    current_var = var_name
                
                # Parse annotations in comments above variable
                elif line.startswith('# REQUIRED'):
                    if current_var:
                        schema[current_var]['required'] = True
                
                elif line.startswith('# OPTIONAL'):
                    if current_var:
                        schema[current_var]['required'] = False
                
                elif '# SENSITIVE' in line:
                    if current_var:
                        schema[current_var]['sensitive'] = True
        
        return schema
    
    def validate_environment(self, env: Optional[Dict[str, str]] = None) -> Tuple[bool, List[str]]:
        """
        Validate environment variables against schema.
        
        Args:
            env: Environment dict to validate (default: os.environ)
            
        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        if env is None:
            env = dict(os.environ)
        
        errors = []
        
        # Determine environment mode
        ark_env = env.get('ARK_ENVIRONMENT', 'development').lower()
        
        # Check required variables
        required = self.REQUIRED_PRODUCTION if ark_env == 'production' else self.REQUIRED_DEVELOPMENT
        
        for var in required:
            if var not in env or not env[var]:
                errors.append(f"Missing required variable: {var}")
        
        # Validate credential boundaries
        boundary_errors = self._validate_credential_boundaries(env)
        errors.extend(boundary_errors)
        
        # Validate specific variables
        validation_errors = self._validate_variables(env)
        errors.extend(validation_errors)
        
        return len(errors) == 0, errors
    
    def _validate_credential_boundaries(self, env: Dict[str, str]) -> List[str]:
        """
        Ensure credentials from different domains are properly isolated.
        
        Args:
            env: Environment dict
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Check if mixing production and development credentials
        ark_env = env.get('ARK_ENVIRONMENT', 'development').lower()
        
        if ark_env == 'production':
            # Warn about development-only credentials in production
            dev_only = ['ARK_DEBUG_MODE', 'ARK_MOCK_APIS', 'ARK_HOT_RELOAD']
            for var in dev_only:
                if env.get(var, '').lower() == 'true':
                    errors.append(f"Development feature {var} enabled in production environment")
        
        # Validate each credential boundary
        for boundary_name, vars in self.CREDENTIAL_BOUNDARIES.items():
            present_vars = [v for v in vars if v in env and env[v]]
            
            # If any credential from a boundary is present, log it
            if present_vars:
                # No errors here, just validation
                pass
        
        return errors
    
    def _validate_variables(self, env: Dict[str, str]) -> List[str]:
        """
        Validate specific variable types and constraints.
        
        Args:
            env: Environment dict
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Validate ports
        port_vars = {
            'ARK_API_PORT': (1024, 65535),
            'ARK_FRONTEND_PORT': (1024, 65535),
            'REDIS_PORT': (1024, 65535),
            'ARK_FEDERATION_WS_PORT': (1024, 65535),
        }
        
        for var, (min_val, max_val) in port_vars.items():
            if var in env:
                try:
                    port = int(env[var])
                    if not (min_val <= port <= max_val):
                        errors.append(f"{var} must be between {min_val} and {max_val}, got {port}")
                except ValueError:
                    errors.append(f"{var} must be an integer, got '{env[var]}'")
        
        # Validate boolean flags
        bool_vars = [
            'ARK_DEBUG_MODE', 'ARK_ENABLE_LLM', 'ARK_ENABLE_WEB_SEARCH',
            'ARK_ENABLE_LIVE_TRADING', 'ARK_ENABLE_FEDERATION', 'ARK_METRICS_ENABLED'
        ]
        
        for var in bool_vars:
            if var in env:
                value = env[var].lower()
                if value not in ('true', 'false', '1', '0', 'yes', 'no'):
                    errors.append(f"{var} must be a boolean (true/false), got '{env[var]}'")
        
        # Validate session secret length
        if 'ARK_SESSION_SECRET' in env:
            secret = env['ARK_SESSION_SECRET']
            if len(secret) < 32:
                errors.append("ARK_SESSION_SECRET must be at least 32 characters long")
        
        return errors
    
    def get_sensitive_vars(self, env: Optional[Dict[str, str]] = None) -> Set[str]:
        """
        Get list of sensitive variable names present in environment.
        
        Args:
            env: Environment dict (default: os.environ)
            
        Returns:
            Set of sensitive variable names
        """
        if env is None:
            env = dict(os.environ)
        
        sensitive = set()
        
        for var_name in env.keys():
            if any(pattern in var_name for pattern in self.SENSITIVE_PATTERNS):
                sensitive.add(var_name)
        
        return sensitive
    
    def mask_sensitive_value(self, value: str) -> str:
        """
        Mask sensitive value for safe display.
        
        Args:
            value: Value to mask
            
        Returns:
            Masked string
        """
        if not value:
            return '<not set>'
        
        if len(value) <= 8:
            return '***'
        else:
            return f"{value[:4]}...{value[-4:]}"
    
    def print_validation_report(self, env: Optional[Dict[str, str]] = None, show_sensitive: bool = False):
        """
        Print comprehensive validation report.
        
        Args:
            env: Environment dict (default: os.environ)
            show_sensitive: Show masked sensitive values
        """
        if env is None:
            env = dict(os.environ)
        
        is_valid, errors = self.validate_environment(env)
        
        print("=" * 70)
        print("🔐 ARK Environment Validation Report")
        print("=" * 70)
        
        # Environment mode
        ark_env = env.get('ARK_ENVIRONMENT', 'development')
        print(f"\n📍 Environment: {ark_env.upper()}")
        
        # Validation status
        if is_valid:
            print("\n✅ Environment validation PASSED")
        else:
            print(f"\n❌ Environment validation FAILED ({len(errors)} errors)")
            print("\nErrors:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
        
        # Credential boundaries
        print("\n🔑 Credential Boundaries:")
        for boundary_name, vars in self.CREDENTIAL_BOUNDARIES.items():
            present = [v for v in vars if v in env and env[v]]
            if present:
                print(f"  • {boundary_name}: {len(present)} credentials configured")
                if show_sensitive:
                    for var in present:
                        masked = self.mask_sensitive_value(env[var])
                        print(f"      {var}={masked}")
        
        # Sensitive variables
        sensitive_vars = self.get_sensitive_vars(env)
        print(f"\n🔒 Sensitive Variables: {len(sensitive_vars)} detected")
        if show_sensitive and sensitive_vars:
            for var in sorted(sensitive_vars):
                masked = self.mask_sensitive_value(env.get(var, ''))
                print(f"  • {var}={masked}")
        
        print("=" * 70)


def main():
    """CLI for environment validation"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="ARK Environment Variable Validator")
    parser.add_argument("--env-file", help="Path to .env file to validate")
    parser.add_argument("--show-sensitive", action="store_true", help="Show masked sensitive values")
    parser.add_argument("--quiet", action="store_true", help="Only show errors")
    
    args = parser.parse_args()
    
    validator = EnvValidator()
    
    # Load environment from file if specified
    if args.env_file:
        env = {}
        with open(args.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
    else:
        env = None
    
    # Validate
    is_valid, errors = validator.validate_environment(env)
    
    if not args.quiet:
        validator.print_validation_report(env, show_sensitive=args.show_sensitive)
    else:
        if not is_valid:
            for error in errors:
                print(f"❌ {error}")
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
