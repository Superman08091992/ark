"""
Code Validator - Validates code safety before execution

This module performs static analysis to detect:
- Dangerous function calls (eval, exec, os.system)
- Forbidden imports
- Syntax errors
- Security vulnerabilities

Created: 2025-11-12
"""

import ast
import hashlib
import re
import sqlite3
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ValidationResult:
    """Result of code validation"""
    passed: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    code_hash: str
    validated_at: int
    
    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "code_hash": self.code_hash,
            "validated_at": self.validated_at
        }


class CodeValidator:
    """Validates generated code for safety and correctness"""
    
    def __init__(self, db_path: str = "data/ark.db"):
        self.db_path = db_path
        self.conn = None
        self.validation_rules = {}
        
    def connect(self):
        """Establish database connection and load rules"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.load_validation_rules()
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        
    def load_validation_rules(self):
        """Load validation rules from database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT rule_id, rule_name, rule_type, rule_pattern, severity, enabled
            FROM validation_rules
            WHERE enabled = 1
        """)
        
        for row in cursor.fetchall():
            self.validation_rules[row["rule_id"]] = {
                "name": row["rule_name"],
                "type": row["rule_type"],
                "pattern": row["rule_pattern"],
                "severity": row["severity"]
            }
            
        print(f"📋 Loaded {len(self.validation_rules)} validation rules")
        
    def validate(self, code: str, trust_tier: str = "sandbox") -> ValidationResult:
        """
        Validate code for safety and correctness
        
        Args:
            code: Python code to validate
            trust_tier: Trust level ('core', 'trusted', 'sandbox')
            
        Returns:
            ValidationResult with pass/fail and issues found
        """
        errors = []
        warnings = []
        info = []
        
        # Calculate code hash
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        
        # 1. Check syntax
        try:
            ast.parse(code)
            info.append("✓ Syntax valid")
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return ValidationResult(
                passed=False,
                errors=errors,
                warnings=warnings,
                info=info,
                code_hash=code_hash,
                validated_at=int(time.time())
            )
            
        # 2. Apply validation rules
        for rule_id, rule in self.validation_rules.items():
            if rule["type"] == "forbidden_call":
                violations = self.check_forbidden_pattern(code, rule["pattern"])
                if violations:
                    msg = f"{rule['name']}: Found {len(violations)} violation(s)"
                    if rule["severity"] == "error":
                        errors.append(msg)
                    elif rule["severity"] == "warning":
                        warnings.append(msg)
                        
            elif rule["type"] == "regex_pattern":
                violations = self.check_regex_pattern(code, rule["pattern"])
                if violations:
                    msg = f"{rule['name']}: Found {len(violations)} match(es)"
                    if rule["severity"] == "error":
                        errors.append(msg)
                    elif rule["severity"] == "warning":
                        warnings.append(msg)
                        
        # 3. Check imports
        forbidden_imports, risky_imports = self.check_imports(code, trust_tier)
        if forbidden_imports:
            errors.append(f"Forbidden imports: {', '.join(forbidden_imports)}")
        if risky_imports:
            warnings.append(f"Risky imports (review needed): {', '.join(risky_imports)}")
            
        # 4. Check AST for suspicious patterns
        suspicious = self.check_ast_patterns(code)
        if suspicious:
            for pattern, count in suspicious.items():
                warnings.append(f"Suspicious pattern '{pattern}': {count} occurrence(s)")
                
        # 5. Add trust tier info
        info.append(f"Trust tier: {trust_tier}")
        
        # Determine pass/fail
        passed = len(errors) == 0
        
        return ValidationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            info=info,
            code_hash=code_hash,
            validated_at=int(time.time())
        )
        
    def check_forbidden_pattern(self, code: str, pattern: str) -> List[Tuple[int, str]]:
        """Check for forbidden patterns in code"""
        violations = []
        for i, line in enumerate(code.splitlines(), 1):
            if re.search(pattern, line):
                violations.append((i, line.strip()))
        return violations
        
    def check_regex_pattern(self, code: str, pattern: str) -> List[Tuple[int, str]]:
        """Check for regex patterns in code"""
        matches = []
        for i, line in enumerate(code.splitlines(), 1):
            if re.search(pattern, line):
                matches.append((i, line.strip()))
        return matches
        
    def check_imports(self, code: str, trust_tier: str) -> Tuple[Set[str], Set[str]]:
        """
        Check imports for forbidden or risky modules
        
        Returns:
            Tuple of (forbidden_imports, risky_imports)
        """
        # Parse AST
        try:
            tree = ast.parse(code)
        except:
            return set(), set()
            
        imported = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module)
                    
        # Define forbidden and risky imports based on trust tier
        if trust_tier == "sandbox":
            forbidden = {
                "subprocess", "os", "sys", "socket", "urllib", "requests",
                "pickle", "marshal", "shelve", "dbm"
            }
            risky = {"shutil", "tempfile", "glob", "pathlib"}
        elif trust_tier == "testing":
            forbidden = {"subprocess", "os.system"}
            risky = {"socket", "urllib", "requests", "pickle"}
        else:
            forbidden = set()
            risky = set()
            
        forbidden_found = imported & forbidden
        risky_found = imported & risky
        
        return forbidden_found, risky_found
        
    def check_ast_patterns(self, code: str) -> Dict[str, int]:
        """Check AST for suspicious patterns"""
        try:
            tree = ast.parse(code)
        except:
            return {}
            
        suspicious = {}
        
        for node in ast.walk(tree):
            # Check for global/nonlocal usage
            if isinstance(node, ast.Global):
                suspicious["global"] = suspicious.get("global", 0) + 1
            elif isinstance(node, ast.Nonlocal):
                suspicious["nonlocal"] = suspicious.get("nonlocal", 0) + 1
                
            # Check for setattr/getattr/delattr
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("setattr", "getattr", "delattr"):
                        suspicious[node.func.id] = suspicious.get(node.func.id, 0) + 1
                        
            # Check for wild imports
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        suspicious["import_star"] = suspicious.get("import_star", 0) + 1
                        
        return suspicious
        
    def add_validation_rule(self, 
                           rule_name: str,
                           rule_type: str,
                           rule_pattern: str,
                           severity: str = "error",
                           description: str = "") -> str:
        """
        Add a new validation rule
        
        Returns:
            rule_id of the created rule
        """
        rule_id = f"rule_{rule_name.lower().replace(' ', '_')}"
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO validation_rules (
                rule_id, rule_name, rule_type, rule_pattern,
                severity, description, enabled, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            rule_id, rule_name, rule_type, rule_pattern,
            severity, description, int(time.time())
        ))
        self.conn.commit()
        
        # Reload rules
        self.load_validation_rules()
        
        return rule_id
        
    def disable_rule(self, rule_id: str):
        """Disable a validation rule"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE validation_rules SET enabled = 0 WHERE rule_id = ?
        """, (rule_id,))
        self.conn.commit()
        self.load_validation_rules()
        
    def enable_rule(self, rule_id: str):
        """Enable a validation rule"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE validation_rules SET enabled = 1 WHERE rule_id = ?
        """, (rule_id,))
        self.conn.commit()
        self.load_validation_rules()


def main():
    """Demo: Validate various code samples"""
    print("🛡️ ARK Code Validator - Phase 7")
    print("=" * 60)
    
    validator = CodeValidator()
    
    with validator:
        # Test 1: Safe code
        print("\n✅ Test 1: Safe code")
        safe_code = """
def add_numbers(a: int, b: int) -> int:
    \"\"\"Add two numbers\"\"\"
    return a + b

def greet(name: str) -> str:
    return f"Hello, {name}!"
"""
        result = validator.validate(safe_code, trust_tier="sandbox")
        print(f"   Passed: {result.passed}")
        print(f"   Errors: {len(result.errors)}")
        print(f"   Warnings: {len(result.warnings)}")
        
        # Test 2: Dangerous code
        print("\n❌ Test 2: Dangerous code (eval)")
        dangerous_code = """
def execute_user_input(user_code: str):
    result = eval(user_code)  # Dangerous!
    return result
"""
        result = validator.validate(dangerous_code, trust_tier="sandbox")
        print(f"   Passed: {result.passed}")
        print(f"   Errors: {result.errors}")
        
        # Test 3: Risky imports
        print("\n⚠️  Test 3: Risky imports")
        risky_code = """
import os
import sys

def list_files():
    return os.listdir('.')
"""
        result = validator.validate(risky_code, trust_tier="sandbox")
        print(f"   Passed: {result.passed}")
        print(f"   Errors: {result.errors}")
        print(f"   Warnings: {result.warnings}")
        
        # Test 4: Suspicious patterns
        print("\n🔍 Test 4: Suspicious patterns")
        suspicious_code = """
import json

data = {}

def update_data(key, value):
    global data  # Modifying global state
    setattr(data, key, value)  # Dynamic attribute setting
"""
        result = validator.validate(suspicious_code, trust_tier="testing")
        print(f"   Passed: {result.passed}")
        print(f"   Errors: {len(result.errors)}")
        print(f"   Warnings: {result.warnings}")
        
        # Test 5: Syntax error
        print("\n🔴 Test 5: Syntax error")
        invalid_code = """
def broken_function(
    print("Missing closing parenthesis"
"""
        result = validator.validate(invalid_code)
        print(f"   Passed: {result.passed}")
        print(f"   Errors: {result.errors}")
        
    print("\n✨ Code validation demonstration complete!")


if __name__ == "__main__":
    main()
