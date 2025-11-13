#!/usr/bin/env python3
"""
ARK Input Validation Layer (REQ_SEC_02)

Validates and sanitizes all external inputs from:
- Telegram messages
- HTTP/API requests
- WebSocket messages
- Command-line arguments
- Configuration files

Prevents injection attacks, path traversal, and malformed data.
"""

import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


class ValidationError(Exception):
    """Exception raised when input validation fails"""
    pass


class InputValidator:
    """
    Comprehensive input validation for ARK system.
    
    Features:
    - String sanitization
    - Path traversal prevention
    - SQL injection detection
    - Command injection prevention
    - JSON schema validation
    - Symbol/ticker validation
    """
    
    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        r'[;&|`$]',  # Command injection
        r'\.\./+',    # Path traversal
        r'<script',   # XSS
        r'javascript:',  # JavaScript injection
        r'DROP\s+TABLE',  # SQL injection
        r'UNION\s+SELECT',  # SQL injection
        r'--\s*$',    # SQL comment
        r"'\s*OR\s*'1'\s*=\s*'1",  # SQL tautology
    ]
    
    # Valid symbol pattern (alphanumeric + hyphen/underscore)
    SYMBOL_PATTERN = re.compile(r'^[A-Z0-9_-]{1,20}$')
    
    # Valid agent names
    VALID_AGENTS = {'kyle', 'joey', 'kenny', 'hrm', 'aletheia', 'id'}
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize input validator.
        
        Args:
            strict_mode: Reject any suspicious input (recommended for production)
        """
        self.strict_mode = strict_mode
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
    
    def validate_string(self, value: str, max_length: int = 10000, allow_special: bool = False) -> str:
        """
        Validate and sanitize a string input.
        
        Args:
            value: Input string to validate
            max_length: Maximum allowed length
            allow_special: Allow special characters (default: False)
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If input is malicious or invalid
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value).__name__}")
        
        # Check length
        if len(value) > max_length:
            raise ValidationError(f"Input exceeds maximum length of {max_length}")
        
        # Check for dangerous patterns
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                if self.strict_mode:
                    raise ValidationError(f"Dangerous pattern detected in input")
                else:
                    # Sanitize by removing dangerous characters
                    value = pattern.sub('', value)
        
        # Strip leading/trailing whitespace
        value = value.strip()
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        return value
    
    def validate_path(self, path: str, base_dir: Optional[Path] = None, must_exist: bool = False) -> Path:
        """
        Validate file path and prevent directory traversal.
        
        Args:
            path: File path to validate
            base_dir: Base directory to restrict access (optional)
            must_exist: Require path to exist
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If path is invalid or dangerous
        """
        if not isinstance(path, (str, Path)):
            raise ValidationError(f"Expected string or Path, got {type(path).__name__}")
        
        path = Path(path)
        
        # Prevent absolute paths if base_dir specified
        if base_dir and path.is_absolute():
            raise ValidationError("Absolute paths not allowed")
        
        # Resolve to absolute path
        if base_dir:
            resolved = (base_dir / path).resolve()
            
            # Ensure resolved path is within base_dir
            try:
                resolved.relative_to(base_dir.resolve())
            except ValueError:
                raise ValidationError("Path traversal detected")
        else:
            resolved = path.resolve()
        
        # Check if path contains dangerous patterns
        path_str = str(resolved)
        if '..' in path_str:
            raise ValidationError("Path contains '..' which could be directory traversal")
        
        # Check existence if required
        if must_exist and not resolved.exists():
            raise ValidationError(f"Path does not exist: {resolved}")
        
        return resolved
    
    def validate_symbol(self, symbol: str) -> str:
        """
        Validate trading symbol/ticker.
        
        Args:
            symbol: Symbol to validate (e.g., 'BTC-USD', 'AAPL')
            
        Returns:
            Uppercase symbol string
            
        Raises:
            ValidationError: If symbol is invalid
        """
        if not isinstance(symbol, str):
            raise ValidationError(f"Symbol must be string, got {type(symbol).__name__}")
        
        symbol = symbol.upper().strip()
        
        if not self.SYMBOL_PATTERN.match(symbol):
            raise ValidationError(
                f"Invalid symbol format. Must be 1-20 alphanumeric characters, "
                f"hyphens, or underscores: {symbol}"
            )
        
        return symbol
    
    def validate_agent_name(self, agent_name: str) -> str:
        """
        Validate agent name.
        
        Args:
            agent_name: Name of agent to validate
            
        Returns:
            Lowercase agent name
            
        Raises:
            ValidationError: If agent name is invalid
        """
        if not isinstance(agent_name, str):
            raise ValidationError(f"Agent name must be string, got {type(agent_name).__name__}")
        
        agent_name = agent_name.lower().strip()
        
        if agent_name not in self.VALID_AGENTS:
            raise ValidationError(
                f"Invalid agent name: {agent_name}. "
                f"Valid agents: {', '.join(sorted(self.VALID_AGENTS))}"
            )
        
        return agent_name
    
    def validate_number(self, value: Union[int, float, str], 
                       min_value: Optional[float] = None,
                       max_value: Optional[float] = None,
                       allow_negative: bool = True) -> float:
        """
        Validate numeric input.
        
        Args:
            value: Numeric value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_negative: Allow negative numbers
            
        Returns:
            Float value
            
        Raises:
            ValidationError: If value is invalid
        """
        try:
            if isinstance(value, str):
                value = float(value)
            elif not isinstance(value, (int, float)):
                raise ValueError(f"Expected number, got {type(value).__name__}")
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid numeric value: {e}")
        
        # Check bounds
        if not allow_negative and value < 0:
            raise ValidationError("Negative values not allowed")
        
        if min_value is not None and value < min_value:
            raise ValidationError(f"Value {value} below minimum {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValidationError(f"Value {value} exceeds maximum {max_value}")
        
        return float(value)
    
    def validate_json(self, data: Union[str, Dict], schema: Optional[Dict] = None) -> Dict:
        """
        Validate JSON data.
        
        Args:
            data: JSON string or dict to validate
            schema: Optional JSON schema for validation
            
        Returns:
            Parsed dict
            
        Raises:
            ValidationError: If JSON is invalid
        """
        # Parse if string
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON: {e}")
        
        if not isinstance(data, dict):
            raise ValidationError(f"Expected JSON object, got {type(data).__name__}")
        
        # TODO: Add jsonschema validation if schema provided
        # For now, basic structure validation
        if schema:
            for required_key in schema.get('required', []):
                if required_key not in data:
                    raise ValidationError(f"Missing required field: {required_key}")
        
        return data
    
    def validate_url(self, url: str, allowed_schemes: Optional[List[str]] = None) -> str:
        """
        Validate URL.
        
        Args:
            url: URL to validate
            allowed_schemes: List of allowed schemes (default: ['http', 'https'])
            
        Returns:
            Validated URL string
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not isinstance(url, str):
            raise ValidationError(f"URL must be string, got {type(url).__name__}")
        
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                raise ValidationError("URL missing scheme (http/https)")
            
            if parsed.scheme not in allowed_schemes:
                raise ValidationError(
                    f"Invalid URL scheme: {parsed.scheme}. "
                    f"Allowed: {', '.join(allowed_schemes)}"
                )
            
            if not parsed.netloc:
                raise ValidationError("URL missing domain")
            
        except Exception as e:
            raise ValidationError(f"Invalid URL: {e}")
        
        return url
    
    def sanitize_for_logging(self, data: Any, mask_sensitive: bool = True) -> str:
        """
        Sanitize data for safe logging.
        
        Args:
            data: Data to sanitize
            mask_sensitive: Mask sensitive fields (passwords, tokens, etc.)
            
        Returns:
            Safe string for logging
        """
        # Convert to string
        if isinstance(data, dict):
            data = data.copy()
            
            if mask_sensitive:
                # Mask sensitive keys
                sensitive_keys = {'password', 'token', 'secret', 'api_key', 'private_key'}
                for key in data:
                    if any(s in key.lower() for s in sensitive_keys):
                        data[key] = '***REDACTED***'
            
            data_str = json.dumps(data, default=str)
        else:
            data_str = str(data)
        
        # Truncate if too long
        if len(data_str) > 500:
            data_str = data_str[:497] + '...'
        
        return data_str


# Global validator instance
validator = InputValidator(strict_mode=True)


def main():
    """Test input validator"""
    print("Testing ARK Input Validator\n")
    
    # Test string validation
    try:
        safe = validator.validate_string("SELECT * FROM users")
        print(f"✅ String validation: {safe}")
    except ValidationError as e:
        print(f"❌ String validation: {e}")
    
    # Test path validation
    try:
        safe = validator.validate_path("../../etc/passwd")
        print(f"✅ Path validation: {safe}")
    except ValidationError as e:
        print(f"❌ Path validation (expected): {e}")
    
    # Test symbol validation
    try:
        symbol = validator.validate_symbol("BTC-USD")
        print(f"✅ Symbol validation: {symbol}")
    except ValidationError as e:
        print(f"❌ Symbol validation: {e}")
    
    # Test agent validation
    try:
        agent = validator.validate_agent_name("Kyle")
        print(f"✅ Agent validation: {agent}")
    except ValidationError as e:
        print(f"❌ Agent validation: {e}")


if __name__ == "__main__":
    main()
