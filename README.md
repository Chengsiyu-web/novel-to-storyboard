# novel-to-storyboard

**Text → Structured Storyboard via 3-Call LLM Pipeline**

A Python CLI tool that converts novel/script text into a production-ready storyboard JSON, ready for downstream AI video generation. It implements a three-stage LLM chain that mirrors professional animation pre-production workflow.

---

## What It Does

Given a passage of novel text and optional character/scene/prop asset lists, the pipeline outputs a structured storyboard where every shot has:

- Scene group boundaries with narrative arc labels
- Individual shot durations (4–15 seconds, enforced)
- Camera language per sub-shot: `[景别·构图·机位·运镜·时长s] 画面描述`
- Dialogue lines, narration, background sound as typed `content_lines`
- Asset IDs bound to each shot (character, scene, prop)
- Spatial blocking snapshot (top-down view) per shot

---

## Pipeline Design

```
Input Text + Assets
       │
       ▼
┌─────────────┐
│   Call 1    │  Scene group splitting + screenplay rewrite
│             │  → Identify act/emotional boundaries
│             │  → Reformat raw prose into screenplay lines
└──────┬──────┘
       │ scene_list (with screenplay)
       ▼
┌─────────────┐
│   Call 2    │  Shot splitting — "能合就合" (merge-first)
│             │  → One shot per behavior event
│             │  → Estimate duration; enforce 4–15 s bounds
│             │  → Cross-shot closure for events > 15 s
└──────┬──────┘
       │ scene_list (with shot_list)
       ▼
┌─────────────┐
│   Call 3    │  Visual detail + camera language
│             │  → 2–5 sub-shots per shot
│             │  → Bind asset IDs
│             │  → scene_blocking spatial snapshot
└──────┬──────┘
       │
       ▼
storyboard_final.json
```

### Why three separate calls?

Each stage has a distinct cognitive task that benefits from a clean context window:

| Call | Task | Risk if merged |
|------|------|----------------|
| 1 | Story segmentation + prose-to-screenplay rewrite | Conflating narrative structure with shot logic |
| 2 | Shot splitting with strict timing rules | Over-cutting when visual detail distracts |
| 3 | Camera language + asset binding | Ignoring shot boundaries already established |

Separating them produces more consistent, rule-following output — especially on the hard constraints (4–15 s duration, merge-first tendency, cross-shot closure).

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/novel-to-storyboard.git
cd novel-to-storyboard
pip install -r requirements.txt
```

Set your API key:

```bash
export OPENAI_API_KEY=sk-...
# or for a compatible provider:
export OPENAI_BASE_URL=https://your-provider.com/v1
```

---

## Usage

```bash
# Minimal — just text, no assets
python main.py --text examples/sample_text.txt

# With assets (characters, scenes, props)
python main.py \
  --text examples/sample_text.txt \
  --assets examples/sample_assets.json \
  --output output/

# Also save intermediate call1/call2 results for debugging
python main.py \
  --text examples/sample_text.txt \
  --assets examples/sample_assets.json \
  --save-intermediates

# Use a different model
python main.py \
  --text examples/sample_text.txt \
  --model gpt-4-turbo \
  --base-url https://api.openai.com/v1
```

### Asset file format

```json
{
  "characters": [
    {
      "asset_id": "c_001",
      "name": "苏晚",
      "gender": "女",
      "age": 22,
      "appearance": "身形清瘦，长发及肩，面容清丽..."
    }
  ],
  "scene_assets": [
    {
      "asset_id": "s_001",
      "name": "顾家客厅",
      "description": "现代简约风格，落地窗朝南..."
    }
  ],
  "prop_assets": [
    {
      "asset_id": "p_001",
      "name": "体检报告",
      "description": "A4白纸，医院抬头..."
    }
  ]
}
```

---

## Output Format

`storyboard_final.json` — abridged example:

```json
{
  "scene_list": [
    {
      "llm_scene_code": "G-01",
      "scene_desc": "苏晚进门，呈上体检报告",
      "narrative_arc": "触发",
      "shot_list": [
        {
          "llm_shot_code": "V-01",
          "emotion": "压抑",
          "estimated_duration": 6,
          "content_lines": [
            { "type": "background_sound", "content": "室内安静，远处隐约车声" }
          ],
          "scene_blocking": "苏晚站于客厅门口左侧，顾深坐于沙发中央，茶几居中",
          "visual_description": [
            "[全景·水平·正面·固定·3s] 苏晚推门而入，夹着体检报告，停在门口打量客厅",
            "[中景·黄金分割·侧面·缓推·3s] 顾深坐于沙发，侧脸被百叶窗光影切割，未抬头"
          ],
          "persona_asset_ids": ["c_001", "c_002"],
          "scene_asset_ids": ["s_001"],
          "prop_asset_ids": ["p_001"]
        }
      ]
    }
  ]
}
```

---

## Project Structure

```
novel-to-storyboard/
├── main.py                   # CLI entry point
├── requirements.txt
├── src/
│   └── pipeline.py           # Core 3-call pipeline
├── prompts/
│   ├── call1_scene_split.txt  # Call 1 prompt template
│   ├── call2_shot_split.txt   # Call 2 prompt template
│   └── call3_visual_detail.txt# Call 3 prompt template
└── examples/
    ├── sample_text.txt        # Sample novel excerpt
    └── sample_assets.json     # Sample character/scene/prop assets
```

---

## Background & Motivation

This project operationalizes the **文本→分镜→AI视频** production pipeline used in short-drama content industrialization. The core insight is that professional storyboarding is a structured, rule-governed process — and those rules can be encoded precisely enough for LLMs to follow reliably when broken into discrete, single-responsibility prompting stages.

The three prompt templates in `prompts/` encode:
- Narrative segmentation theory (act structure, emotional arc labeling)
- Film grammar (shot types, camera movement vocabulary)
- Timing constraints derived from AI video generation model limits (4–15 s per clip)
- Asset binding conventions for downstream production pipelines

This tool is designed as a **PM-level integration layer**: it connects story structure thinking with the technical interface that video generation models consume, without requiring manual shot-by-shot annotation.

---

## Compatibility

Works with any OpenAI-compatible API endpoint. Tested with `gpt-4o`. For best results on complex action/dialogue scenes, use a model with strong instruction-following and long-context reliability (≥ 128k context recommended for longer texts).

---

## License

MIT
