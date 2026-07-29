import ast
import sys
from pathlib import Path
from api_shape_explorer import ShapeExplorer, ModuleShape, FunctionShape, ClassShape

def test_explore_file():
    code = """
from typing import List

class Base:
    pass

class MyClass(Base):
    """A test class."""
    def method(self, x: int) -> str:
        return str(x)

def func(a: int, b: str = "default") -> bool:
    """A test function."""
    if a > 0:
        return True
    return False
"""
    p = Path("/tmp/test_mod.py")
    p.write_text(code)
    exp = ShapeExplorer(p)
    shapes = exp.explore()
    assert "test_mod" in shapes
    mod = shapes["test_mod"]
    assert len(mod.classes) == 2
    assert len(mod.functions) == 1
    assert mod.functions[0].name == "func"
    assert mod.functions[0].complexity == 2
    p.unlink()

def test_unparse_fallback():
    exp = ShapeExplorer(".")
    node = ast.Name(id="test")
    assert exp._unparse(node) == "test"
