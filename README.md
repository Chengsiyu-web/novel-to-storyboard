<div align="center">

<h1>📖 → 🎬 novel-to-storyboard</h1>
<p><strong>扔进去一段小说，吐出来一份分镜表</strong></p>
<p>做 AI 视频的前置流水线。把小说正文或剧本丢进去，自动拆成带镜头语言、资产绑定、时长的结构化分镜，直接拿去生产。</p>

<p>
  <a href="https://github.com/Chengsiyu-web/novel-to-storyboard/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/OpenAI-Compatible-green" alt="OpenAI Compatible">
</p>

<p>
  <a href="#快速上手">快速上手</a> •
  <a href="#怎么工作的">怎么工作的</a> •
  <a href="#输出长什么样">输出长什么样</a> •
  <a href="#路线图">路线图</a>
</p>

</div>

---

## 这玩意能干嘛

写小说的人和做 AI 视频的人之间，隔了一个「分镜」的鸿沟。这个项目就是填这个沟的：

- **三段式 LLM 流水线** —— 每次只干一件事，不贪多
- **第一步拆场景**：自动找幕边界、情绪转折点，把散文改成剧本格式
- **第二步拆镜头**：遵循「能合就合」原则，每个镜头 4–15 秒，超长的自动跨镜收尾
- **第三步补画面**：给每个子镜头标上 `[景别·构图·机位·运镜·时长s]`，还有空间走位和资产绑定
- **支持资产绑定**：角色、场景、道具可以预定义，输出里直接带 ID，下游直接认
- **兼容任意 OpenAI 风格 API**：OpenAI、Azure、Claude 代理、本地模型都能接
- **CLI + Web UI 双模式**：命令行适合批处理和自动化，Streamlit 界面适合随手试试

---

## 快速上手

### 装起来

```bash
git clone https://github.com/Chengsiyu-web/novel-to-storyboard.git
cd novel-to-storyboard
pip install -r requirements.txt
```

### 配 API 密钥

**方式一：环境变量（推荐 CLI 用）**

```bash
export OPENAI_API_KEY="sk-..."
# 如果用第三方代理，再加这个
export OPENAI_BASE_URL="https://your-provider.com/v1"
```

**方式二：`.env` 文件（推荐本地开发）**

```bash
cp .env.example .env
# 然后编辑 .env 填密钥
```

**方式三：Web UI 里直接贴**

Streamlit 界面侧边栏可以输密钥，只存在当前会话里，不会存任何地方。

### 跑起来

#### Web UI（新手友好）

```bash
streamlit run app.py
```

浏览器打开 http://localhost:8501 就行。

功能：直接粘贴文本、可视化预览镜头、一键下载 JSON、还有示例数据可以直接试。

**免费部署到 Streamlit Cloud**：

1. GitHub 上 Fork 这个仓库
2. 去 [share.streamlit.io](https://share.streamlit.io) 连上 GitHub
3. 选这个仓库点 Deploy
4. 拿到公开链接，谁都能用 —— 但每个人得自带 API 密钥

#### CLI（老手/自动化）

```bash
# 最简：只给文本
python main.py --text examples/sample_text.txt

# 带上角色/场景/道具资产
python main.py \
  --text examples/sample_text.txt \
  --assets examples/sample_assets.json \
  --output output/ \
  --save-intermediates

# 换模型
python main.py --text examples/sample_text.txt --model gpt-4-turbo
```

跑完你会看到类似这样的输出：

```
🎬 开始跑流水线
──────────────────────────────────────────────────
▶ 调用 1：拆场景 + 改剧本...
  → 3 个场景组
▶ 调用 2：拆镜头...
  → 7 个镜头
▶ 调用 3：补视觉细节...
  → 搞定
  → 已保存到 output/storyboard_final.json

✅ 完成：3 个场景，7 个镜头
   输出：output/storyboard_final.json
```

---

## 怎么工作的

```
输入文本 + 可选资产
       │
       ▼
┌─────────────────┐
│    调用 1       │  拆场景组 + 改剧本
│                 │  • 找幕边界和情绪转折点
│                 │  • 标叙事弧：触发/上升/高潮/下降/收束
│                 │  • 把散文改成剧本行
└────────┬────────┘
         │ scene_list（带剧本）
         ▼
┌─────────────────┐
│    调用 2       │  拆镜头 —— "能合就合"
│                 │  • 一个行为事件一个镜头
│                 │  • 估算时长，强制 4–15 秒
│                 │  • 超 15 秒的跨镜收尾
└────────┬────────┘
         │ scene_list（带 shot_list）
         ▼
┌─────────────────┐
│    调用 3       │  补画面细节 + 镜头语言
│                 │  • 每镜头拆 2–5 个子镜头，标镜头参数
│                 │  • 内容行：对白/旁白/音效
│                 │  • 场景走位：俯视空间快照
│                 │  • 资产 ID 绑定
└────────┬────────┘
         │
         ▼
  storyboard_final.json
```

### 为什么非要拆三次？

每次调用干一件 focused 的事，上下文干净，不容易跑偏：

| 调用 | 干什么 | 如果混在一起会出什么问题 |
|------|--------|------------------------|
| 1 | 叙事分段 + 散文改剧本 | 故事结构和镜头逻辑互相干扰 |
| 2 | 按规则拆镜头 | 视觉细节进来后容易过度切割 |
| 3 | 镜头语言 + 资产绑定 | 可能无视前面已经定好的镜头边界 |

拆开跑的好处是输出更稳定、更守规矩 —— 尤其那种硬约束（4–15 秒、优先合并、跨镜收尾）不容易被忽略。

---

## 资产格式

如果想让输出更精细，可以预定义角色、场景、道具：

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

资产是可选的，不给也能跑，但给了之后第三步的画面描述会更丰富，而且资产 ID 能正确绑到输出里，下游直接认。

---

## 输出长什么样

`storyboard_final.json` 的结构大概是：

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

### 字段速查

| 字段 | 什么意思 |
|------|----------|
| `llm_scene_code` | 场景组编号，G-01、G-02... |
| `narrative_arc` | 这场景在叙事里起什么作用：触发/上升/高潮/下降/收束 |
| `llm_shot_code` | 镜头编号，V-01、V-02...，全局连续 |
| `emotion` | 情绪关键词，比如压抑/紧张/平静/爆发/茫然 |
| `estimated_duration` | 预估秒数，4–15（第二步强制约束） |
| `content_lines` | 声音/对白行，分 `character`、`narration`、`background_sound`、`anonymous_voice` |
| `scene_blocking` | 俯视视角的空间安排，给美术和摄影看 |
| `visual_description` | 子镜头数组，格式：`[景别·构图·机位·运镜·时长s] 画面描述` |
| `*_asset_ids` | 绑定的资产 ID，下游渲染/生产直接引用 |

---

## CLI 参数

```
usage: main.py [-h] --text TEXT [--assets ASSETS] [--output OUTPUT]
               [--model MODEL] [--base-url BASE_URL] [--api-key API_KEY]
               [--save-intermediates]

通过三调用 LLM 流水线把小说文本转结构化分镜

options:
  -h, --help            显示帮助并退出
  --text TEXT           输入文本文件路径（.txt）
  --assets ASSETS       资产 JSON 文件路径
  --output OUTPUT       输出目录，默认 ./output/
  --model MODEL         LLM 模型，默认 gpt-4o
  --base-url BASE_URL   自定义 API base URL
  --api-key API_KEY     API 密钥，默认读 OPENAI_API_KEY 环境变量
  --save-intermediates  同时保存调用 1 和 2 的中间结果
```

---

## 开发

```bash
# 空跑验证（不耗 API）
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

## 路线图

- [ ] 支持多章节/长篇小说的批量处理
- [ ] 给中间输出加 JSON Schema 校验
- [ ] 原生支持 Claude、Gemini 等非 OpenAI 服务商
- [ ] 输出格式可选 JSON / CSV / FCPXML
- [x] 可视化 Web UI，支持交互式编辑生成结果
- [ ] 接入 ComfyUI / Stable Video Diffusion 工作流

---

## 想贡献？

欢迎。大改动请先开 Issue 聊聊。

1. Fork 仓库
2. 切分支：`git checkout -b feature/你想加的东西`
3. 提交：`git commit -m 'Add ...'`
4. 推送：`git push origin feature/你想加的东西`
5. 开 Pull Request

---

## 许可证

MIT —— 详见 [LICENSE](LICENSE)。

---

## 致谢

这个项目把 **文本→分镜→AI视频** 的工业化流程做成了工程工具。三段式提示策略是基于 AI 视频生成模型的实际限制（片段时长、资产一致性）和专业动画前期流程设计的。

Built with ❤️ for AI-native content creation.
