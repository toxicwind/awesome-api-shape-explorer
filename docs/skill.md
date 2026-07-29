# Skill: api-shape-explorer

## Description

Analyze Python API surfaces via AST introspection. Supports Python 3.8+ with enhanced features on 3.10+.

## When to Use

- When you need to understand a codebase's public API quickly
- When auditing third-party dependencies for surface area
- When generating documentation from source
- When calculating cyclomatic complexity for refactoring decisions

## How to Use

```python
from api_shape_explorer import ShapeExplorer

explorer = ShapeExplorer("./src")
explorer.explore()
report = explorer.report("json")
```

## CLI

```bash
api-shape-explorer src/ -f markdown -o API.md
```

## Features

- Pure AST analysis (no runtime execution)
- Cyclomatic complexity calculation
- Signature extraction with type annotations
- Class hierarchy mapping
- Import graph analysis
- Markdown and JSON output

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)
