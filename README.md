# awesome-api-shape-explorer

> Analyze Python API surfaces via AST introspection. Zero runtime execution. Safe for untrusted code.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## What It Does

You inherit a 50K-line codebase. You need to know:
- What functions exist and what they take
- Class hierarchies and method counts
- Which files import what
- Cyclomatic complexity for refactoring targets

`api-shape-explorer` answers all of this in seconds without executing a single line.

## Install

```bash
pip install awesome-api-shape-explorer
```

## Quickstart

```python
from api_shape_explorer import ShapeExplorer

# Analyze a package
explorer = ShapeExplorer("./src")
explorer.explore()

# JSON report for tooling
json_report = explorer.report("json")

# Markdown report for docs
md_report = explorer.report("markdown")
```

## CLI

```bash
# JSON output for CI pipelines
api-shape-explorer src/ -f json -o api-report.json

# Markdown for documentation
api-shape-explorer src/ -f markdown -o API.md

# Single file analysis
api-shape-explorer my_module.py
```

## Features

| Feature | Description | 3.8 | 3.9 | 3.10+ | 3.12 |
|---------|-------------|-----|-----|-------|------|
| AST parsing | Full syntax tree traversal | ✅ | ✅ | ✅ | ✅ |
| Signature extraction | Function signatures with types | ✅ | ✅ | ✅ | ✅ |
| Cyclomatic complexity | McCabe complexity per function | ✅ | ✅ | ✅ | ✅ |
| `ast.unparse` | Reconstruct source from AST | — | ✅ | ✅ | ✅ |
| Async detection | Identify coroutines | ✅ | ✅ | ✅ | ✅ |
| Dataclass detection | Spot `@dataclass` decorators | ✅ | ✅ | ✅ | ✅ |
| Abstract detection | Spot `@abstractmethod` | ✅ | ✅ | ✅ | ✅ |
| Type annotation parsing | Full annotation support | ✅ | ✅ | ✅ | ✅ |

## Output Examples

### JSON
```json
{
  "my_module": {
    "name": "my_module",
    "path": "/path/to/my_module.py",
    "docstring": "Module docs...",
    "functions": [
      {
        "name": "process_data",
        "signature": "def process_data(data: List[Dict]) -> Result",
        "complexity": 5,
        "line": 42,
        "docstring": "Process incoming data."
      }
    ],
    "classes": [
      {
        "name": "DataProcessor",
        "bases": ["BaseProcessor"],
        "methods": 8,
        "attributes": ["config", "cache"],
        "is_dataclass": false
      }
    ],
    "imports": ["typing.List", "typing.Dict"]
  }
}
```

### Markdown
```markdown
# API Shape Report

## my_module
- Path: `/path/to/my_module.py`
- Functions: 12 | Classes: 3

### `def process_data(data: List[Dict]) -> Result`
- Complexity: 5
- Line: 42
- Doc: Process incoming data.
```

## Why Pure AST?

- **Safe**: No runtime execution means no side effects
- **Fast**: Single-pass analysis, no imports needed
- **Complete**: Sees everything, including dead code
- **Version agnostic**: Works on 3.8+ with feature detection

## Testing

```bash
python3 -m pytest tests/ -v
```

## License

MIT
