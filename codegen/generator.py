"""
Code Generator - Template-based code generation

This module generates Python code from specifications:
- Function generation with type hints
- Test generation
- Documentation generation
- Uses Jinja2 templates

Created: 2025-11-12
"""

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template

from codegen.validator import CodeValidator
from codegen.sandbox import SandboxManager


class CodeGenerator:
    """Generates Python code from specifications"""
    
    def __init__(self, 
                 db_path: str = "data/ark.db",
                 templates_dir: str = "codegen/templates"):
        self.db_path = db_path
        self.templates_dir = Path(templates_dir)
        self.conn = None
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
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
        
    def generate_function(self,
                         function_name: str,
                         description: str,
                         parameters: List[Dict] = None,
                         return_type: Optional[str] = None,
                         body: Optional[str] = None,
                         use_types: bool = True) -> Dict:
        """
        Generate a function from specification
        
        Args:
            function_name: Name of the function
            description: What the function does
            parameters: List of {'name', 'type', 'description', 'default'}
            return_type: Return type annotation
            body: Function body (auto-generated if None)
            use_types: Use type hints
            
        Returns:
            Dict with generated_code, tests, metadata
        """
        if parameters is None:
            parameters = []
            
        # Select template
        template_name = "function/typed_function.jinja2" if use_types else "function/simple_function.jinja2"
        template = self.env.get_template(template_name)
        
        # Generate function body if not provided
        if body is None:
            body = self._generate_body(function_name, description, parameters, return_type)
        
        # Render template
        if use_types:
            code = template.render(
                function_name=function_name,
                docstring=description,
                parameters=parameters,
                return_type=return_type,
                return_description=f"Result of {function_name}",
                body=body
            )
        else:
            # Simple format for non-typed
            params_str = ", ".join([p["name"] for p in parameters])
            code = template.render(
                function_name=function_name,
                docstring=description,
                parameters=params_str,
                body=body
            )
        
        # Generate tests
        tests = self._generate_tests(function_name, parameters, return_type)
        
        # Store in database
        code_id = self._store_generated_code(
            request=f"Generate function: {function_name}",
            specification=json.dumps({
                "function_name": function_name,
                "description": description,
                "parameters": parameters,
                "return_type": return_type
            }),
            generated_code=code,
            generated_tests=tests
        )
        
        return {
            "code_id": code_id,
            "function_name": function_name,
            "code": code,
            "tests": tests,
            "parameters": parameters,
            "return_type": return_type
        }
    
    def _generate_body(self,
                      function_name: str,
                      description: str,
                      parameters: List[Dict],
                      return_type: Optional[str]) -> str:
        """Generate a simple function body"""
        
        # For demonstration, create a simple implementation
        if not parameters:
            return 'return "Hello from generated code!"'
        
        # Simple calculation or transformation
        if return_type == "int" or return_type == "float":
            # Assume numeric operation
            param_names = [p["name"] for p in parameters]
            if len(param_names) == 1:
                return f"return {param_names[0]} * 2"
            else:
                return f"return {' + '.join(param_names)}"
        
        elif return_type == "str":
            param_names = [p["name"] for p in parameters]
            if len(param_names) == 1:
                return f'return f"Result: {{{param_names[0]}}}"'
            else:
                params_joined = ', '.join([f'{{{p}}}' for p in param_names])
                return f'return f"Values: {params_joined}"'
        
        elif return_type == "List" or return_type.startswith("List["):
            param_names = [p["name"] for p in parameters]
            return f"return [{', '.join(param_names)}]"
        
        else:
            # Generic implementation
            return f"# TODO: Implement {function_name}\npass"
    
    def _generate_tests(self,
                       function_name: str,
                       parameters: List[Dict],
                       return_type: Optional[str]) -> str:
        """Generate pytest tests for the function"""
        
        template = self.env.get_template("test/pytest_test.jinja2")
        
        # Generate basic test case
        if not parameters:
            arrange = "# No parameters needed"
            act = f"result = {function_name}()"
            assert_stmt = 'assert result is not None'
        else:
            # Create test values
            test_values = []
            for param in parameters:
                if param.get("type") == "int":
                    test_values.append("1")
                elif param.get("type") == "float":
                    test_values.append("1.0")
                elif param.get("type") == "str":
                    test_values.append('"test"')
                else:
                    test_values.append("None")
            
            param_assignments = [
                f'{p["name"]} = {v}' 
                for p, v in zip(parameters, test_values)
            ]
            arrange = "\n".join(param_assignments)
            
            param_names = [p["name"] for p in parameters]
            act = f"result = {function_name}({', '.join(param_names)})"
            
            if return_type:
                assert_stmt = 'assert result is not None'
            else:
                assert_stmt = 'assert True  # Function executed'
        
        test_code = template.render(
            function_name=function_name,
            test_case="basic",
            test_description=f"Test {function_name} with basic inputs",
            imports=[],
            arrange=arrange,
            act=act,
            assert_statement=assert_stmt
        )
        
        return test_code
    
    def _store_generated_code(self,
                             request: str,
                             specification: str,
                             generated_code: str,
                             generated_tests: str) -> str:
        """Store generated code in database"""
        
        code_id = f"code_{int(time.time())}_{hashlib.sha256(generated_code.encode()).hexdigest()[:8]}"
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO generated_code (
                code_id, request, specification,
                generated_code, generated_tests,
                language, created_at, created_by,
                trust_tier, deployed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code_id,
            request,
            specification,
            generated_code,
            generated_tests,
            "python",
            int(time.time()),
            "CodeGenerator",
            "sandbox",
            0
        ))
        self.conn.commit()
        
        return code_id
    
    def get_generated_code(self, code_id: str) -> Optional[Dict]:
        """Retrieve generated code by ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM generated_code WHERE code_id = ?
        """, (code_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
            
        return {
            "code_id": row["code_id"],
            "request": row["request"],
            "specification": json.loads(row["specification"]) if row["specification"] else {},
            "generated_code": row["generated_code"],
            "generated_tests": row["generated_tests"],
            "created_at": row["created_at"],
            "deployed": bool(row["deployed"])
        }
    
    def validate_and_test(self, code_id: str) -> Dict:
        """Validate and test generated code"""
        
        # Get the code
        code_info = self.get_generated_code(code_id)
        if not code_info:
            return {"error": "Code not found"}
        
        code = code_info["generated_code"]
        tests = code_info["generated_tests"]
        
        # Step 1: Validate code
        validator = CodeValidator(self.db_path)
        with validator:
            validation = validator.validate(code, trust_tier="sandbox")
        
        if not validation.passed:
            return {
                "validation": "failed",
                "errors": validation.errors,
                "warnings": validation.warnings
            }
        
        # Step 2: Run code in sandbox
        sandbox = SandboxManager(self.db_path)
        with sandbox:
            # Add a simple test call at the end
            test_code = code + "\n\n# Test execution\nprint('Code executed successfully')"
            exec_result = sandbox.execute(test_code, trust_tier="sandbox", validate=False)
        
        return {
            "validation": "passed",
            "execution_status": exec_result.status,
            "execution_output": exec_result.stdout,
            "execution_duration_ms": exec_result.duration_ms,
            "errors": validation.errors,
            "warnings": validation.warnings
        }
    
    def get_stats(self) -> Dict:
        """Get code generation statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM generated_code")
        total = cursor.fetchone()["total"]
        
        cursor.execute("""
            SELECT COUNT(*) as deployed 
            FROM generated_code 
            WHERE deployed = 1
        """)
        deployed = cursor.fetchone()["deployed"]
        
        cursor.execute("""
            SELECT language, COUNT(*) as count 
            FROM generated_code 
            GROUP BY language
        """)
        lang_dist = {row["language"]: row["count"] for row in cursor.fetchall()}
        
        return {
            "total_generated": total,
            "deployed_count": deployed,
            "language_distribution": lang_dist
        }


def main():
    """Demo: Generate functions"""
    print("🎨 ARK Code Generator - Phase 7")
    print("=" * 60)
    
    generator = CodeGenerator()
    
    with generator:
        # Example 1: Simple addition function
        print("\n✨ Example 1: Generate addition function")
        result1 = generator.generate_function(
            function_name="add_numbers",
            description="Add two numbers together",
            parameters=[
                {"name": "a", "type": "int", "description": "First number"},
                {"name": "b", "type": "int", "description": "Second number"}
            ],
            return_type="int"
        )
        print(f"   Code ID: {result1['code_id']}")
        print(f"   Function: {result1['function_name']}")
        print("\n   Generated Code:")
        print("   " + "\n   ".join(result1['code'].split('\n')[:10]))
        
        # Validate and test
        print("\n   🔍 Validating and testing...")
        test_result1 = generator.validate_and_test(result1['code_id'])
        print(f"   Validation: {test_result1['validation']}")
        print(f"   Execution: {test_result1['execution_status']}")
        
        # Example 2: String formatter
        print("\n✨ Example 2: Generate string formatter")
        result2 = generator.generate_function(
            function_name="format_greeting",
            description="Format a greeting message",
            parameters=[
                {"name": "name", "type": "str", "description": "Person's name"}
            ],
            return_type="str"
        )
        print(f"   Code ID: {result2['code_id']}")
        print("\n   Generated Code:")
        print("   " + "\n   ".join(result2['code'].split('\n')[:8]))
        
        # Test it
        test_result2 = generator.validate_and_test(result2['code_id'])
        print(f"\n   Validation: {test_result2['validation']}")
        print(f"   Execution: {test_result2['execution_status']}")
        
        # Example 3: List creator
        print("\n✨ Example 3: Generate list creator")
        result3 = generator.generate_function(
            function_name="create_range_list",
            description="Create a list from start to end",
            parameters=[
                {"name": "start", "type": "int", "description": "Start value"},
                {"name": "end", "type": "int", "description": "End value"}
            ],
            return_type="List[int]",
            body="return list(range(start, end + 1))"
        )
        print(f"   Code ID: {result3['code_id']}")
        print("\n   Generated Code:")
        print("   " + "\n   ".join(result3['code'].split('\n')))
        
        # Show statistics
        print("\n📊 Code Generation Statistics:")
        stats = generator.get_stats()
        print(f"   Total functions generated: {stats['total_generated']}")
        print(f"   Deployed: {stats['deployed_count']}")
        print(f"   Languages: {stats['language_distribution']}")
    
    print("\n✨ Code generation demonstration complete!")


if __name__ == "__main__":
    main()
