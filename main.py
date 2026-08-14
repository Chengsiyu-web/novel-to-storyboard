#!/usr/bin/env python3
"""
novel-to-storyboard CLI

Usage:
  python main.py --text examples/sample_text.txt --assets examples/sample_assets.json --output output/
  python main.py --text examples/sample_text.txt  # run with no assets
"""

import argparse
import json
import sys
from pathlib import Path

# Make sure src/ is importable when running from project root
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pipeline import run_pipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert novel text to structured storyboard via 3-call LLM pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --text examples/sample_text.txt
  python main.py --text examples/sample_text.txt --assets examples/sample_assets.json
  python main.py --text examples/sample_text.txt --output output/ --save-intermediates
  python main.py --text examples/sample_text.txt --model gpt-4o --base-url https://api.openai.com/v1
        """,
    )
    parser.add_argument(
        "--text",
        required=True,
        help="Path to the input text file (.txt)",
    )
    parser.add_argument(
        "--assets",
        default=None,
        help='Path to assets JSON file with keys: "characters", "scene_assets", "prop_assets"',
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: ./output/)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="LLM model to use (default: gpt-4o)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Custom API base URL (for OpenAI-compatible providers)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key (defaults to OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--save-intermediates",
        action="store_true",
        help="Also save call1 and call2 intermediate results",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # ── Load text ──────────────────────────────────────────────────────────
    text_path = Path(args.text)
    if not text_path.exists():
        print(f"[error] Text file not found: {text_path}", file=sys.stderr)
        sys.exit(1)
    text = text_path.read_text(encoding="utf-8").strip()
    if not text:
        print("[error] Text file is empty", file=sys.stderr)
        sys.exit(1)
    print(f"✔ Loaded text: {len(text)} chars from {text_path}")

    # ── Load assets ────────────────────────────────────────────────────────
    characters, scene_assets, prop_assets = [], [], []
    if args.assets:
        assets_path = Path(args.assets)
        if not assets_path.exists():
            print(f"[error] Assets file not found: {assets_path}", file=sys.stderr)
            sys.exit(1)
        assets = json.loads(assets_path.read_text(encoding="utf-8"))
        characters = assets.get("characters", [])
        scene_assets = assets.get("scene_assets", [])
        prop_assets = assets.get("prop_assets", [])
        print(
            f"✔ Assets: {len(characters)} characters, "
            f"{len(scene_assets)} scenes, {len(prop_assets)} props"
        )

    # ── Run pipeline ───────────────────────────────────────────────────────
    print("\n🎬 Starting text → storyboard pipeline\n" + "─" * 50)
    result = run_pipeline(
        text=text,
        characters=characters,
        scene_assets=scene_assets,
        prop_assets=prop_assets,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        save_intermediates=args.save_intermediates,
        output_dir=args.output,
    )

    # ── Print summary ──────────────────────────────────────────────────────
    scene_count = len(result.get("scene_list", []))
    shot_count = sum(
        len(s.get("shot_list", [])) for s in result.get("scene_list", [])
    )
    print("\n" + "─" * 50)
    print(f"✅ Pipeline complete: {scene_count} scenes, {shot_count} shots")
    print(f"   Output: {Path(args.output) / 'storyboard_final.json'}")


if __name__ == "__main__":
    main()
