"""
api-shape-explorer
==================
Analyze Python API surfaces via AST introspection.
Supports Python 3.8+ with enhanced features on 3.10+.
"""
import ast
import sys
import inspect
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict

__version__ = "0.1.0"
__all__ = ["ShapeExplorer", "ModuleShape", "FunctionShape", "ClassShape"]

PY_VER = sys.version_info[:2]

@dataclass
class FunctionShape:
    name: str
    signature: str
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_generator: bool = False
    returns: Optional[str] = None
    params: List[Dict[str, Any]] = field(default_factory=list)
    line_no: int = 0
    complexity: int = 0  # cyclomatic

@dataclass
class ClassShape:
    name: str
    bases: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    methods: List[FunctionShape] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    is_dataclass: bool = False
    is_abstract: bool = False
    line_no: int = 0

@dataclass
class ModuleShape:
    name: str
    path: Optional[Path] = None
    functions: List[FunctionShape] = field(default_factory=list)
    classes: List[ClassShape] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    docstring: Optional[str] = None

class ShapeExplorer:
    def __init__(self, target: Union[str, Path]):
        self.target = Path(target) if isinstance(target, str) else target
        self.shapes: Dict[str, ModuleShape] = {}
        self._cache: Dict[str, ast.AST] = {}

    def explore(self) -> Dict[str, ModuleShape]:
        if self.target.is_file() and self.target.suffix == ".py":
            self._explore_file(self.target)
        elif self.target.is_dir():
            for fp in self.target.rglob("*.py"):
                if "test" not in fp.name and "__pycache__" not in str(fp):
                    self._explore_file(fp)
        return self.shapes

    def _explore_file(self, fp: Path) -> None:
        try:
            src = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return
        self._cache[str(fp)] = tree
        mod = ModuleShape(name=fp.stem, path=fp)
        mod.docstring = ast.get_docstring(tree)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod.imports.append(f"{node.module}.{node.names[0].name}" if node.names else node.module)
            elif isinstance(node, ast.FunctionDef) or (PY_VER >= (3, 5) and isinstance(node, ast.AsyncFunctionDef)):
                mod.functions.append(self._shape_function(node))
            elif isinstance(node, ast.ClassDef):
                mod.classes.append(self._shape_class(node))
        self.shapes[mod.name] = mod

    def _shape_function(self, node: ast.FunctionDef) -> FunctionShape:
        sig = self._get_signature(node)
        doc = ast.get_docstring(node)
        decs = [self._unparse(d) for d in node.decorator_list]
        is_async = isinstance(node, ast.AsyncFunctionDef) if hasattr(ast, "AsyncFunctionDef") else False
        is_gen = any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(node))
        ret = self._unparse(node.returns) if node.returns else None
        params = []
        for arg in node.args.args:
            params.append({"name": arg.arg, "annotation": self._unparse(arg.annotation) if arg.annotation else None})
        # Cyclomatic complexity
        complexity = 1 + sum(1 for n in ast.walk(node) if isinstance(n, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert, ast.comprehension)))
        return FunctionShape(
            name=node.name,
            signature=sig,
            docstring=doc,
            decorators=decs,
            is_async=is_async,
            is_generator=is_gen,
            returns=ret,
            params=params,
            line_no=node.lineno,
            complexity=complexity,
        )

    def _shape_class(self, node: ast.ClassDef) -> ClassShape:
        doc = ast.get_docstring(node)
        bases = [self._unparse(b) for b in node.bases]
        methods = []
        attrs = []
        is_dc = any(self._unparse(d) == "dataclass" for d in node.decorator_list)
        is_abs = any(self._unparse(d) == "abstractmethod" for d in node.decorator_list)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._shape_function(child))
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                attrs.append(child.target.id)
        return ClassShape(
            name=node.name,
            bases=bases,
            docstring=doc,
            methods=methods,
            attributes=attrs,
            is_dataclass=is_dc,
            is_abstract=is_abs,
            line_no=node.lineno,
        )

    def _get_signature(self, node: ast.FunctionDef) -> str:
        args = []
        defaults_start = len(node.args.args) - len(node.args.defaults)
        for i, arg in enumerate(node.args.args):
            a = arg.arg
            if arg.annotation:
                a += f": {self._unparse(arg.annotation)}"
            if i >= defaults_start:
                a += f" = {self._unparse(node.args.defaults[i - defaults_start])}"
            args.append(a)
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
        ret = f" -> {self._unparse(node.returns)}" if node.returns else ""
        return f"def {node.name}({', '.join(args)}){ret}"

    def _unparse(self, node: Optional[ast.AST]) -> str:
        if node is None:
            return ""
        if PY_VER >= (3, 9):
            return ast.unparse(node)
        # Fallback for 3.8
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Attribute):
            return f"{self._unparse(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._unparse(node.value)}[{self._unparse(node.slice)}]"
        elif isinstance(node, ast.List):
            return f"[{', '.join(self._unparse(e) for e in node.elts)}]"
        elif isinstance(node, ast.Tuple):
            return f"({', '.join(self._unparse(e) for e in node.elts)})"
        elif isinstance(node, ast.Call):
            args = [self._unparse(a) for a in node.args]
            kwargs = [f"{k.arg}={self._unparse(k.value)}" for k in node.keywords]
            return f"{self._unparse(node.func)}({', '.join(args + kwargs)})"
        return "..."

    def report(self, fmt: str = "json") -> str:
        if fmt == "json":
            import json
            return json.dumps({k: self._shape_to_dict(v) for k, v in self.shapes.items()}, indent=2, default=str)
        elif fmt == "markdown":
            return self._markdown_report()
        return ""

    def _shape_to_dict(self, shape: ModuleShape) -> dict:
        return {
            "name": shape.name,
            "path": str(shape.path) if shape.path else None,
            "docstring": shape.docstring,
            "functions": [
                {"name": f.name, "signature": f.signature, "complexity": f.complexity, "line": f.line_no}
                for f in shape.functions
            ],
            "classes": [
                {"name": c.name, "bases": c.bases, "methods": len(c.methods), "attributes": c.attributes}
                for c in shape.classes
            ],
            "imports": shape.imports,
        }

    def _markdown_report(self) -> str:
        lines = ["# API Shape Report", ""]
        for name, mod in self.shapes.items():
            lines.append(f"## {name}")
            lines.append(f"- Path: `{mod.path}`")
            lines.append(f"- Functions: {len(mod.functions)}")
            lines.append(f"- Classes: {len(mod.classes)}")
            lines.append("")
            for fn in mod.functions:
                lines.append(f"### `{fn.signature}`")
                lines.append(f"- Complexity: {fn.complexity}")
                lines.append(f"- Line: {fn.line_no}")
                if fn.docstring:
                    lines.append(f"- Doc: {fn.docstring[:100]}...")
                lines.append("")
        return "\n".join(lines)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Explore Python API shapes")
    ap.add_argument("target", help="Python file or directory to analyze")
    ap.add_argument("-f", "--format", choices=["json", "markdown"], default="json")
    ap.add_argument("-o", "--output", help="Output file")
    args = ap.parse_args()
    explorer = ShapeExplorer(args.target)
    explorer.explore()
    report = explorer.report(args.format)
    if args.output:
        Path(args.output).write_text(report)
    else:
        print(report)

if __name__ == "__main__":
    main()
