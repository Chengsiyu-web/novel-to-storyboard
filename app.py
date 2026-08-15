"""
novel-to-storyboard Web UI
Streamlit frontend for the 3-call LLM pipeline.

Run locally:
    streamlit run app.py

Deploy to Streamlit Cloud:
    https://streamlit.io/cloud — connect your GitHub repo
"""

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
from pipeline import run_pipeline

st.set_page_config(
    page_title="📖 → 🎬 Novel to Storyboard",
    page_icon="🎬",
    layout="wide",
)

st.title("📖 → 🎬 Novel to Storyboard")
st.caption("Text → Structured Storyboard via 3-Call LLM Pipeline")

# ── Sidebar: API Configuration ──────────────────────────────────────────
with st.sidebar:
    st.header("🔑 API Configuration")

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Your API key is used only for this session and is not stored.",
    )

    base_url = st.text_input(
        "Base URL (optional)",
        placeholder="https://api.openai.com/v1",
        help="Leave empty for default OpenAI endpoint. Set for compatible providers (Azure, proxy, etc.)",
    )

    model = st.selectbox(
        "Model",
        options=["gpt-4o", "gpt-4-turbo", "gpt-4o-mini", "claude-3-5-sonnet", "custom"],
        index=0,
        help="Select the LLM model. For best results, use a model with strong instruction-following and ≥128k context.",
    )

    if model == "custom":
        model = st.text_input("Custom model name", placeholder="e.g. gpt-4o-2024-08-06")

    st.divider()
    st.header("⚙️ Options")

    save_intermediates = st.checkbox(
        "Save intermediate results",
        value=False,
        help="Also save Call 1 and Call 2 outputs for debugging",
    )

    st.divider()
    st.info(
        "💡 **Why do I need an API key?**\n\n"
        "This tool calls LLM APIs to generate storyboards. "
        "API usage is billed to your own account. We do not store or proxy your key."
    )

    st.markdown(
        "[📖 GitHub Repo](https://github.com/Chengsiyu-web/novel-to-storyboard)"
    )

# ── Main: Input ─────────────────────────────────────────────────────────
st.header("1. Input Text")

text_input = st.text_area(
    "Paste your novel or script text here",
    height=250,
    placeholder="苏晚把体检报告夹在腋下，推开了顾家的门...",
    help="The text to convert into a storyboard. Chinese or English prose works best.",
)

# Example loader
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("📄 Load Example", help="Load a sample text for quick testing"):
        example_path = Path(__file__).parent / "examples" / "sample_text.txt"
        if example_path.exists():
            st.session_state["text_input"] = example_path.read_text(encoding="utf-8")
            st.rerun()

if "text_input" in st.session_state and not text_input:
    text_input = st.session_state["text_input"]

st.header("2. Assets (Optional)")

with st.expander("Define characters, scenes, and props"):
    assets_json = st.text_area(
        "Assets JSON",
        height=180,
        placeholder='{\n  "characters": [...],\n  "scene_assets": [...],\n  "prop_assets": [...]\n}',
        help="Optional asset definitions for richer visual descriptions and ID binding.",
    )

    col3, col4 = st.columns([1, 5])
    with col3:
        if st.button("📄 Load Example Assets"):
            example_assets_path = Path(__file__).parent / "examples" / "sample_assets.json"
            if example_assets_path.exists():
                st.session_state["assets_json"] = example_assets_path.read_text(
                    encoding="utf-8"
                )
                st.rerun()

    if "assets_json" in st.session_state and not assets_json:
        assets_json = st.session_state["assets_json"]

# ── Run Button ──────────────────────────────────────────────────────────
st.header("3. Generate")

run_disabled = not api_key or not text_input.strip()

if run_disabled:
    if not api_key:
        st.warning("⚠️ Please enter your API key in the sidebar to continue.")
    if not text_input.strip():
        st.warning("⚠️ Please enter some text to process.")

if st.button("🎬 Generate Storyboard", type="primary", disabled=run_disabled):
    # Parse assets
    characters, scene_assets, prop_assets = [], [], []
    if assets_json.strip():
        try:
            assets = json.loads(assets_json)
            characters = assets.get("characters", [])
            scene_assets = assets.get("scene_assets", [])
            prop_assets = assets.get("prop_assets", [])
        except json.JSONDecodeError as e:
            st.error(f"Invalid assets JSON: {e}")
            st.stop()

    progress_bar = st.progress(0, text="Starting pipeline...")
    status_text = st.empty()

    try:
        def progress_callback(stage: str, pct: float):
            progress_bar.progress(min(int(pct), 100), text=stage)
            status_text.info(stage)

        progress_callback("▶ Call 1: Scene group splitting...", 10)

        result = run_pipeline(
            text=text_input.strip(),
            characters=characters,
            scene_assets=scene_assets,
            prop_assets=prop_assets,
            model=model,
            api_key=api_key,
            base_url=base_url if base_url else None,
            save_intermediates=save_intermediates,
            output_dir="output",
        )

        progress_callback("✅ Pipeline complete!", 100)

        # ── Results ─────────────────────────────────────────────────────
        st.success("Storyboard generated successfully!")

        scene_count = len(result.get("scene_list", []))
        shot_count = sum(
            len(s.get("shot_list", [])) for s in result.get("scene_list", [])
        )

        st.metric(label="Scenes", value=scene_count)
        st.metric(label="Shots", value=shot_count)

        st.subheader("📋 Full Result (JSON)")
        st.json(result)

        # Download button
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        st.download_button(
            label="⬇️ Download storyboard_final.json",
            data=result_json,
            file_name="storyboard_final.json",
            mime="application/json",
        )

        # Visual preview of shots
        st.subheader("🎞️ Shot Preview")
        for scene in result.get("scene_list", []):
            with st.expander(
                f"🎬 {scene.get('llm_scene_code', '?')} — {scene.get('scene_desc', 'Untitled')} "
                f"({scene.get('narrative_arc', '')})"
            ):
                for shot in scene.get("shot_list", []):
                    st.markdown(
                        f"**{shot.get('llm_shot_code', '?')}** — "
                        f"*{shot.get('emotion', '')}* — "
                        f"⏱️ {shot.get('estimated_duration', '?')}s"
                    )

                    if shot.get("visual_description"):
                        for line in shot["visual_description"]:
                            st.markdown(f"- {line}")

                    if shot.get("content_lines"):
                        st.caption("💬 Content Lines")
                        for line in shot["content_lines"]:
                            st.markdown(
                                f"- `{line.get('type', '?')}`: {line.get('content', '')}"
                            )

                    st.divider()

    except Exception as e:
        st.error(f"Pipeline failed: {e}")
        st.exception(e)

# ── Footer ──────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Built with ❤️ for AI-native content creation. "
    "[GitHub](https://github.com/Chengsiyu-web/novel-to-storyboard)"
)
