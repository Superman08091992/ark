"""
Code Indexer - Scans ARK codebase and builds searchable index

This module analyzes the ARK codebase to understand its structure:
- Extracts functions, classes, imports
- Calculates complexity metrics
- Stores metadata in code_index table
- Enables semantic code search

Created: 2025-11-12
"""

import ast
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


class CodeIndexer:
    """Indexes Python files in the ARK codebase"""
    
    def __init__(self, db_path: str = "data/ark.db", root_path: str = "."):
        self.db_path = db_path
        self.root_path = Path(root_path)
        self.conn = None
        
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
        
    def scan_codebase(self, 
                     directories: Optional[List[str]] = None,
                     exclude_patterns: Optional[List[str]] = None) -> Dict:
        """
        Scan specified directories and index all Python files
        
        Args:
            directories: List of directories to scan (default: key ARK modules)
            exclude_patterns: Patterns to exclude (default: venv, node_modules, etc.)
            
        Returns:
            Dict with scan statistics
        """
        if directories is None:
            directories = [
                "agents", "memory", "reflection", "id", "federation",
                "reasoning", "backend", "codegen", "shared"
            ]
            
        if exclude_patterns is None:
            exclude_patterns = [
                "venv", "node_modules", "__pycache__", ".git",
                "dist", "build", "*.egg-info", "sklearn_test_env"
            ]
            
        stats = {
            "files_scanned": 0,
            "files_indexed": 0,
            "files_skipped": 0,
            "errors": 0,
            "start_time": time.time()
        }
        
        for directory in directories:
            dir_path = self.root_path / directory
            if not dir_path.exists():
                print(f"⚠️  Directory not found: {directory}")
                continue
                
            print(f"📂 Scanning {directory}/...")
            
            for py_file in dir_path.rglob("*.py"):
                # Skip excluded patterns
                if any(pattern in str(py_file) for pattern in exclude_patterns):
                    stats["files_skipped"] += 1
                    continue
                    
                stats["files_scanned"] += 1
                
                try:
                    if self.index_file(py_file):
                        stats["files_indexed"] += 1
                    else:
                        stats["files_skipped"] += 1
                except Exception as e:
                    print(f"   ❌ Error indexing {py_file}: {e}")
                    stats["errors"] += 1
                    
        stats["duration"] = time.time() - stats["start_time"]
        return stats
        
    def index_file(self, file_path: Path) -> bool:
        """
        Index a single Python file
        
        Returns:
            True if indexed successfully, False if skipped
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Skip empty files
            if not content.strip():
                return False
                
            # Parse AST
            tree = ast.parse(content, filename=str(file_path))
            
            # Extract metadata
            metadata = self.extract_metadata(tree, content, file_path)
            
            # Store in database
            self.store_metadata(file_path, metadata)
            
            return True
            
        except SyntaxError as e:
            print(f"   ⚠️  Syntax error in {file_path}: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")
            raise
            
    def extract_metadata(self, tree: ast.AST, content: str, file_path: Path) -> Dict:
        """Extract metadata from AST"""
        metadata = {
            "functions": [],
            "classes": [],
            "imports": [],
            "dependencies": [],
            "complexity": 0,
            "lines_of_code": len(content.splitlines())
        }
        
        # Extract functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "signature": self.get_function_signature(node),
                    "docstring": ast.get_docstring(node) or "",
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                }
                metadata["functions"].append(func_info)
                metadata["complexity"] += self.calculate_complexity(node)
                
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    "docstring": ast.get_docstring(node) or "",
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "bases": [self.get_name(b) for b in node.bases]
                }
                metadata["classes"].append(class_info)
                
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        metadata["imports"].append(alias.name)
                else:  # ImportFrom
                    if node.module:
                        metadata["imports"].append(node.module)
                        
        # Deduplicate imports
        metadata["imports"] = list(set(metadata["imports"]))
        
        return metadata
        
    def get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature as string"""
        args = []
        
        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self.get_name(arg.annotation)}"
            args.append(arg_str)
            
        # Return annotation
        returns = ""
        if node.returns:
            returns = f" -> {self.get_name(node.returns)}"
            
        return f"{node.name}({', '.join(args)}){returns}"
        
    def get_name(self, node: ast.AST) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return ast.unparse(node) if hasattr(ast, 'unparse') else ""
            
    def calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
                
        return complexity
        
    def store_metadata(self, file_path: Path, metadata: Dict):
        """Store extracted metadata in database"""
        relative_path = str(file_path.relative_to(self.root_path))
        file_id = hashlib.sha256(relative_path.encode()).hexdigest()[:16]
        
        # Determine module name
        module_name = relative_path.replace("/", ".").replace(".py", "")
        
        # Determine trust tier based on location
        trust_tier = self.determine_trust_tier(relative_path)
        
        # Get file modification time
        last_modified = int(file_path.stat().st_mtime)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO code_index (
                file_id, file_path, module_name,
                functions, classes, imports, dependencies,
                complexity_score, lines_of_code,
                last_modified, indexed_at, trust_tier
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id,
            relative_path,
            module_name,
            json.dumps(metadata["functions"]),
            json.dumps(metadata["classes"]),
            json.dumps(metadata["imports"]),
            json.dumps(metadata["dependencies"]),
            metadata["complexity"],
            metadata["lines_of_code"],
            last_modified,
            int(time.time()),
            trust_tier
        ))
        self.conn.commit()
        
    def determine_trust_tier(self, file_path: str) -> str:
        """Determine trust tier based on file location"""
        if any(core in file_path for core in ["memory/", "reflection/", "id/", "federation/"]):
            return "core"
        elif any(trusted in file_path for trusted in ["agents/", "reasoning/", "backend/"]):
            return "trusted"
        elif "codegen/" in file_path:
            return "sandbox"
        else:
            return "testing"
            
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """Get indexed information for a file"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM code_index WHERE file_path = ?
        """, (file_path,))
        
        row = cursor.fetchone()
        if not row:
            return None
            
        return {
            "file_id": row["file_id"],
            "file_path": row["file_path"],
            "module_name": row["module_name"],
            "functions": json.loads(row["functions"]) if row["functions"] else [],
            "classes": json.loads(row["classes"]) if row["classes"] else [],
            "imports": json.loads(row["imports"]) if row["imports"] else [],
            "complexity_score": row["complexity_score"],
            "lines_of_code": row["lines_of_code"],
            "trust_tier": row["trust_tier"],
            "last_modified": row["last_modified"],
            "indexed_at": row["indexed_at"]
        }
        
    def search_functions(self, name_pattern: str) -> List[Dict]:
        """Search for functions by name pattern"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT file_path, functions FROM code_index
            WHERE functions LIKE ?
        """, (f"%{name_pattern}%",))
        
        results = []
        for row in cursor.fetchall():
            functions = json.loads(row["functions"]) if row["functions"] else []
            for func in functions:
                if name_pattern.lower() in func["name"].lower():
                    results.append({
                        "file_path": row["file_path"],
                        "function": func
                    })
                    
        return results
        
    def get_stats(self) -> Dict:
        """Get indexing statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM code_index")
        total_files = cursor.fetchone()["total"]
        
        cursor.execute("SELECT SUM(lines_of_code) as total_loc FROM code_index")
        total_loc = cursor.fetchone()["total_loc"] or 0
        
        cursor.execute("SELECT AVG(complexity_score) as avg_complexity FROM code_index")
        avg_complexity = cursor.fetchone()["avg_complexity"] or 0
        
        cursor.execute("SELECT trust_tier, COUNT(*) as count FROM code_index GROUP BY trust_tier")
        trust_distribution = {row["trust_tier"]: row["count"] for row in cursor.fetchall()}
        
        return {
            "total_files": total_files,
            "total_lines_of_code": total_loc,
            "avg_complexity": round(avg_complexity, 2),
            "trust_distribution": trust_distribution
        }


def main():
    """Demo: Index the ARK codebase"""
    print("🔍 ARK Code Indexer - Phase 7")
    print("=" * 60)
    
    indexer = CodeIndexer()
    
    with indexer:
        print("\n📊 Starting codebase scan...")
        stats = indexer.scan_codebase()
        
        print(f"\n✅ Scan complete!")
        print(f"   Files scanned: {stats['files_scanned']}")
        print(f"   Files indexed: {stats['files_indexed']}")
        print(f"   Files skipped: {stats['files_skipped']}")
        print(f"   Errors: {stats['errors']}")
        print(f"   Duration: {stats['duration']:.2f}s")
        
        print(f"\n📈 Index statistics:")
        index_stats = indexer.get_stats()
        print(f"   Total files: {index_stats['total_files']}")
        print(f"   Total LOC: {index_stats['total_lines_of_code']}")
        print(f"   Avg complexity: {index_stats['avg_complexity']}")
        print(f"   Trust distribution: {index_stats['trust_distribution']}")
        
        # Example: Search for functions
        print(f"\n🔎 Sample search: functions containing 'generate'")
        results = indexer.search_functions("generate")
        for i, result in enumerate(results[:5], 1):
            print(f"   {i}. {result['file_path']}: {result['function']['name']}()")
            
    print("\n✨ Code indexing demonstration complete!")


if __name__ == "__main__":
    main()
