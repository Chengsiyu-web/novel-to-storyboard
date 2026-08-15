<div align="center">

<h1>📖 → 🎬 novel-to-storyboard</h1>
<p><strong>Text → Structured Storyboard via 3-Call LLM Pipeline</strong></p>
<p>Automated pre-production pipeline for AI video generation. Convert novel prose or script text into production-ready shot lists with camera language, asset bindings, and timing constraints.</p>

<p>
  <a href="https://github.com/Chengsiyu-web/novel-to-storyboard/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/OpenAI-Compatible-green" alt="OpenAI Compatible">
</p>

<p>
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#output-format">Output Format</a> •
  <a href="#roadmap">Roadmap</a>
</p>

</div>

---

## 🌟 Features

- **Three-stage LLM pipeline** with single-responsibility prompting — each call handles one cognitive task
- **Scene group splitting** (Call 1): Detects act boundaries, emotional arcs, and reformats prose into screenplay format
- **Shot splitting** (Call 2): Merge-first heuristic (`能合就合`) with strict 4–15 second duration bounds per shot
- **Visual detail generation** (Call 3): Camera language per sub-shot `[景别·构图·机位·运镜·时长s]`, spatial blocking snapshots, asset ID binding
- **Asset-aware**: Binds character, scene, and prop assets to each shot for downstream production pipelines
- **OpenAI-compatible**: Works with any OpenAI-compatible API (OpenAI, Azure, Claude via proxy, local LLMs)
- **CLI-first**: Zero-config command line tool with intermediate result saving for debugging

---

## 📦 Quick Start

### Installation

```bash
git clone https://github.com/Chengsiyu-web/novel-to-storyboard.git
cd novel-to-storyboard
pip install -r requirements.txt
```

### Set API Key

```bash
export OPENAI_API_KEY="sk-..."
# Optional: custom base URL for compatible providers
export OPENAI_BASE_URL="https://your-provider.com/v1"
```

### Run

```bash
# Minimal — text only
python main.py --text examples/sample_text.txt

# With character/scene/prop assets
python main.py \
  --text examples/sample_text.txt \
  --assets examples/sample_assets.json \
  --output output/ \
  --save-intermediates

# Use a different model
python main.py \
  --text examples/sample_text.txt \
  --model gpt-4-turbo
```

### Output

```
🎬 Starting text → storyboard pipeline
──────────────────────────────────────────────────
▶ Call 1: Scene group splitting + screenplay rewrite...
  → 3 scene groups found
▶ Call 2: Shot splitting...
  → 7 shots total
▶ Call 3: Visual description + camera language...
  → Done
  → Saved to output/storyboard_final.json

✅ Pipeline complete: 3 scenes, 7 shots
   Output: output/storyboard_final.json
```

---

## 🏗️ Architecture

```
Input Text + Assets
       │
       ▼
┌─────────────────┐
│    Call 1       │  Scene Group Splitting + Screenplay Rewrite
│                 │  • Detect act/emotional boundaries
│                 │  • Label narrative arcs (触发/上升/高潮/下降/收束)
│                 │  • Reformat prose into screenplay lines
└────────┬────────┘
         │ scene_list (with screenplay)
         ▼
┌─────────────────┐
│    Call 2       │  Shot Splitting — "能合就合" (Merge-First)
│                 │  • One shot per behavior event
│                 │  • Estimate duration; enforce 4–15 s bounds
│                 │  • Cross-shot closure for events > 15 s
└────────┬────────┘
         │ scene_list (with shot_list)
         ▼
┌─────────────────┐
│    Call 3       │  Visual Detail + Camera Language
│                 │  • 2–5 sub-shots per shot with camera specs
│                 │  • Content lines (dialogue / narration / sound)
│                 │  • Scene blocking (top-down spatial snapshot)
│                 │  • Asset ID binding (character / scene / prop)
└────────┬────────┘
         │
         ▼
  storyboard_final.json
```

### Why three separate calls?

Each stage has a distinct cognitive task that benefits from a clean context window and focused system prompt:

| Call | Task | Risk if merged |
|------|------|----------------|
| 1 | Narrative segmentation + prose-to-screenplay rewrite | Conflating story structure with shot logic |
| 2 | Shot splitting with strict timing rules | Over-cutting when visual detail distracts |
| 3 | Camera language + asset binding | Ignoring shot boundaries already established |

Separating them produces more consistent, rule-following output — especially on hard constraints (4–15 s duration, merge-first tendency, cross-shot closure rules).

---

## 📄 Asset Format

Create a JSON file with character, scene, and prop definitions:

```json
{
  "characters": [
    {
      "asset_id": "c_001",
      "name": "苏晚",
      "gender": "女",
      "age": 22,
      "appearance": "身形清瘦，长发及肩，面容清丽，常穿浅色连衣裙"
    }
  ],
  "scene_assets": [
    {
      "asset_id": "s_001",
      "name": "顾家客厅",
      "description": "现代简约风格，落地窗朝南，傍晚光线从百叶窗斜入"
    }
  ],
  "prop_assets": [
    {
      "asset_id": "p_001",
      "name": "体检报告",
      "description": "A4白纸，医院抬头，密密麻麻的检查项目和盖章"
    }
  ]
}
```

Assets are optional — the pipeline works with raw text alone, but providing them enables richer visual descriptions and proper ID binding in Call 3.

---

## 📤 Output Format

`storyboard_final.json` contains a fully structured storyboard. Abridged example:

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
          "emotion_note": "苏晚独自推门而入，光线昏暗，顾深未抬头",
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

### Field Reference

| Field | Description |
|-------|-------------|
| `llm_scene_code` | Scene group ID (G-01, G-02...) |
| `narrative_arc` | Scene function: 触发 / 上升 / 高潮 / 下降 / 收束 |
| `llm_shot_code` | Shot ID (V-01, V-02...), globally continuous |
| `emotion` | Single keyword: 压抑 / 紧张 / 平静 / 爆发 / 茫然... |
| `estimated_duration` | Integer seconds, 4–15 (enforced by Call 2) |
| `content_lines` | Typed audio/dialogue lines: `character`, `narration`, `background_sound`, `anonymous_voice` |
| `scene_blocking` | Top-down spatial snapshot for set arrangement |
| `visual_description` | Array of sub-shots with camera language: `[景别·构图·机位·运镜·时长s] 画面描述` |
| `*_asset_ids` | References to bound assets for downstream rendering |

---

## 🔧 CLI Options

```
usage: main.py [-h] --text TEXT [--assets ASSETS] [--output OUTPUT]
               [--model MODEL] [--base-url BASE_URL] [--api-key API_KEY]
               [--save-intermediates]

Convert novel text to structured storyboard via 3-call LLM pipeline

options:
  -h, --help            show this help message and exit
  --text TEXT           Path to the input text file (.txt)
  --assets ASSETS       Path to assets JSON file
  --output OUTPUT       Output directory (default: ./output/)
  --model MODEL         LLM model to use (default: gpt-4o)
  --base-url BASE_URL   Custom API base URL
  --api-key API_KEY     API key (defaults to OPENAI_API_KEY env var)
  --save-intermediates  Also save call1 and call2 intermediate results
```

---

## 🧪 Development

```bash
# Run dry validation (no API calls)
python3 -c "
import sys; sys.path.insert(0, 'src')
from pipeline import load_prompt, extract_json
import json

for name in ['call1_scene_split.txt', 'call2_shot_split.txt', 'call3_visual_detail.txt']:
    p = load_prompt(name)
    print(f'{name}: {len(p)} chars')

print('All prompt templates loaded successfully')
"
```

---

## 🗺️ Roadmap

- [ ] Support multi-chapter / long-form novel batch processing
- [ ] Add JSON Schema validation for intermediate outputs
- [ ] Support non-OpenAI providers (Claude, Gemini) natively
- [ ] Add `--format` option for output (JSON / CSV / FCPXML)
- [ ] Web UI for interactive editing of generated storyboards
- [ ] Integration with ComfyUI / Stable Video Diffusion workflows

---

## 🤝 Contributing

Contributions are welcome. Please open an issue first to discuss major changes.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

This project operationalizes the **文本→分镜→AI视频** production pipeline used in short-drama content industrialization. The three-stage prompting strategy is designed around the practical constraints of AI video generation models (clip duration limits, asset consistency requirements) and professional animation pre-production workflows.

Built with ❤️ for AI-native content creation.
