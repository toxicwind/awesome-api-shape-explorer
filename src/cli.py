import argparse
from pathlib import Path
from .api_shape_explorer import ShapeExplorer

def main():
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
