"""
novel-to-storyboard pipeline
Text → Scene Groups (Call1) → Shot List (Call2) → Visual Detail (Call3)
"""

import json
import os
from pathlib import Path
from typing import Optional
from openai import OpenAI


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

DEFAULT_ASSETS = {
    "characters": [],
    "scene_assets": [],
    "prop_assets": [],
}


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def call_llm(client: OpenAI, model: str, prompt: str) -> str:
    """Single LLM call, returns raw text."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def extract_json(text: str) -> dict:
    """Extract and parse JSON from LLM output."""
    # Strip markdown code fences if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return json.loads(text.strip())


def call1_scene_split(
    client: OpenAI,
    model: str,
    text: str,
    characters: list,
    scene_assets: list,
    prop_assets: list,
) -> dict:
    """Call 1: Split text into scene groups + screenplay rewrite."""
    prompt_template = load_prompt("call1_scene_split.txt")
    prompt = prompt_template.format(
        text=text,
        characters=json.dumps(characters, ensure_ascii=False),
        scene_assets=json.dumps(scene_assets, ensure_ascii=False),
        prop_assets=json.dumps(prop_assets, ensure_ascii=False),
    )
    raw = call_llm(client, model, prompt)
    return extract_json(raw)


def call2_shot_split(
    client: OpenAI,
    model: str,
    text: str,
    call1_result: dict,
    characters: list,
    scene_assets: list,
    prop_assets: list,
) -> dict:
    """Call 2: Split each scene group into individual Shots."""
    prompt_template = load_prompt("call2_shot_split.txt")
    prompt = prompt_template.format(
        text=text,
        scene_list=json.dumps(call1_result["scene_list"], ensure_ascii=False),
        characters=json.dumps(characters, ensure_ascii=False),
        scene_assets=json.dumps(scene_assets, ensure_ascii=False),
        prop_assets=json.dumps(prop_assets, ensure_ascii=False),
    )
    raw = call_llm(client, model, prompt)
    return extract_json(raw)


def call3_visual_detail(
    client: OpenAI,
    model: str,
    text: str,
    call2_result: dict,
    characters: list,
    scene_assets: list,
    prop_assets: list,
) -> dict:
    """Call 3: Add visual description, camera language, and asset IDs to each Shot."""
    prompt_template = load_prompt("call3_visual_detail.txt")
    prompt = prompt_template.format(
        text=text,
        scene_list=json.dumps(call2_result["scene_list"], ensure_ascii=False),
        characters=json.dumps(characters, ensure_ascii=False),
        scene_assets=json.dumps(scene_assets, ensure_ascii=False),
        prop_assets=json.dumps(prop_assets, ensure_ascii=False),
    )
    raw = call_llm(client, model, prompt)
    return extract_json(raw)


def run_pipeline(
    text: str,
    characters: Optional[list] = None,
    scene_assets: Optional[list] = None,
    prop_assets: Optional[list] = None,
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    save_intermediates: bool = False,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Run the full text-to-storyboard pipeline.

    Args:
        text: Novel/script text to process
        characters: List of character assets [{asset_id, name, gender, age, appearance}]
        scene_assets: List of scene assets [{asset_id, name, description}]
        prop_assets: List of prop assets [{asset_id, name, description}]
        model: LLM model name
        api_key: API key (defaults to OPENAI_API_KEY env var)
        base_url: Custom API base URL (for compatible providers)
        save_intermediates: Whether to save intermediate results
        output_dir: Directory to save results

    Returns:
        Final storyboard dict (Call 3 output)
    """
    characters = characters or []
    scene_assets = scene_assets or []
    prop_assets = prop_assets or []

    client = OpenAI(
        api_key=api_key or os.getenv("OPENAI_API_KEY"),
        base_url=base_url or os.getenv("OPENAI_BASE_URL"),
    )

    out_dir = Path(output_dir) if output_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    # ── Call 1: Scene groups + screenplay ─────────────────────────────────
    print("▶ Call 1: Scene group splitting + screenplay rewrite...")
    c1 = call1_scene_split(client, model, text, characters, scene_assets, prop_assets)
    print(f"  → {len(c1['scene_list'])} scene groups found")

    if save_intermediates and out_dir:
        (out_dir / "call1_result.json").write_text(
            json.dumps(c1, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ── Call 2: Shot splitting ─────────────────────────────────────────────
    print("▶ Call 2: Shot splitting...")
    c2 = call2_shot_split(client, model, text, c1, characters, scene_assets, prop_assets)
    total_shots = sum(len(s.get("shot_list", [])) for s in c2["scene_list"])
    print(f"  → {total_shots} shots total")

    if save_intermediates and out_dir:
        (out_dir / "call2_result.json").write_text(
            json.dumps(c2, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ── Call 3: Visual detail ──────────────────────────────────────────────
    print("▶ Call 3: Visual description + camera language...")
    c3 = call3_visual_detail(client, model, text, c2, characters, scene_assets, prop_assets)
    print("  → Done")

    if out_dir:
        (out_dir / "storyboard_final.json").write_text(
            json.dumps(c3, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  → Saved to {out_dir / 'storyboard_final.json'}")

    return c3
