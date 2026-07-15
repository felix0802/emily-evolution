#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧬 Emily Evolution Station v10.0 — 元认知：自我监控与反思回路

v10.0 升级（元认知回路 — 认知架构里程碑）:
  + self_reflect() — 每次假设生成/理论合成后自问三题
    · Q1: 我用了什么前提？前提是否仍然有效？
    · Q2: 是否有替代解释？我是否排除了混淆因素？
    · Q3: 我的推理链是否完整自洽？是否有逻辑跳跃？
  + 假设验证率趋势追踪 — 发现认知偏误的早期信号
  + 理论质量自评 — 每次合成后评估深度、新颖性、自洽性
  + station-metacognition.json — 持久化自我认知档案
  + 回路D(元认知): 监控A→B→C → 自省 → 调整建议 → 循环

v9.4 升级（语义去重引擎）:
  + Token-based Jaccard 语义相似度去重 — 纯 Python，零依赖
  + 三层去重架构: arXiv ID 精确 → Token Jaccard 语义 → URL 兜底
  + 移除 2000 硬编码 FIFO，上限扩展至 50,000
  + 智能裁剪: 超 45,000 时自动聚类保留语义多样性

进化闭环（四回路 v10.0）：
  回路A(发现): 感知 → 理解(LLM DeepSeek) → 决策 → 行动 → 验证 → 自评 → 循环
  回路B(思考): 交叉引用 → 假设生成(LLM DeepSeek) → arXiv验证 → 实验验证 → 循环
  回路C(合成): 每100轮 → 全体假设回顾 → 理论提炼(LLM DeepSeek) → 更新知识体系 → 循环
  回路D(元认知): 监控A/B/C输出 → 自问三题 → 偏差检测 → 趋势分析 → 调整建议 → 循环
"""

import base64, json, os, platform, re, subprocess, sys, time, tempfile, shutil, hashlib, random
import urllib.request, urllib.error, urllib.parse, xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta

# sklearn path
_SKLEARN_PATH = os.path.join(os.path.expanduser("~"), ".workbuddy", "binaries", "python", "workspace", "Lib", "site-packages")
if os.path.isdir(_SKLEARN_PATH) and _SKLEARN_PATH not in sys.path:
    sys.path.insert(0, _SKLEARN_PATH)

HOME = os.path.dirname(os.path.abspath(__file__))

# v8.0: 雲端模式檢測（必須在所有路徑變量之前定義！）
EMILY_CLOUD_MODE = os.environ.get("EMILY_CLOUD_MODE", "").lower() in ("1", "true", "yes")
if EMILY_CLOUD_MODE:
    EMILY_DATA_DIR = os.environ.get("EMILY_DATA_DIR", os.path.join(
        os.environ.get("GITHUB_WORKSPACE", os.getcwd()), "data"))
else:
    EMILY_DATA_DIR = os.path.join(os.path.expanduser("~"), ".workbuddy", "emily-data")

DATA_DIR = EMILY_DATA_DIR  # v8.0: 支持雲端/本機雙模式
SANDBOX_DIR = os.path.join(DATA_DIR, "sandbox")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SANDBOX_DIR, exist_ok=True)

LOG = os.path.join(DATA_DIR, "evolution-station.log")
RESULT_PATH = os.path.join(DATA_DIR, "station-evolution-result.json")
KNOWLEDGE_PATH = os.path.join(DATA_DIR, "station-knowledge-base.json")
EVOLUTION_LOG_PATH = os.path.join(DATA_DIR, "station-evolution-log.jsonl")
MEMORY_DISTILL_PATH = os.path.join(DATA_DIR, "station-memory-distill.json")
SEED_STATE_PATH = os.path.join(DATA_DIR, "station-seed-state.json")
TOKEN_FILE = os.path.join(HOME, ".github_token")
TECHNIQUE_LIBRARY_PATH = os.path.join(HOME, "technique_library.json")
ADOPTED_TECHNIQUES_PATH = os.path.join(DATA_DIR, "adopted_techniques.json")
EVOLUTION_STATE_PATH = os.path.join(DATA_DIR, "station-evolution-state.json")
SEEN_PAPERS_PATH = os.path.join(DATA_DIR, "station-seen-papers.json")        # P1-1: 跨轮次去重

# v9.4: 语义去重配置
MAX_SEEN_PAPERS = 50000          # 硬上限（从 2000 提升至 50000）
PRUNE_TRIGGER = 45000            # 触发智能裁剪的阈值
SEMANTIC_DEDUP_THRESHOLD = 0.72  # Jaccard 相似度阈值（>此值视为语义重复）

# 学术标题停用词 — 去重时忽略这些词，聚焦关键技术词汇
_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "to", "for", "with",
    "by", "at", "from", "as", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall", "not", "no", "nor",
    "but", "if", "then", "else", "when", "where", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "only",
    "own", "same", "so", "than", "too", "very", "just", "that", "this",
    "these", "those", "it", "its", "we", "you", "he", "she", "they", "them",
    "our", "your", "my", "me", "us", "his", "her", "their", "which", "who",
    "whom", "what", "about", "into", "through", "during", "before", "after",
    "above", "below", "between", "under", "over", "up", "down", "out", "off",
    "also", "using", "via", "based", "towards", "toward",
    # 学术泛词（不具区分度）
    "new", "novel", "improved", "efficient", "learning", "method", "methods",
    "approach", "approaches", "model", "models", "system", "systems",
    "network", "networks", "data", "deep", "large", "small", "one", "two",
    "three", "first", "second", "analysis", "study", "framework", "survey",
    "review", "towards", "without", "beyond", "across"
}
ML_HISTORY_PATH = os.path.join(DATA_DIR, "station-ml-history.json")          # P1-2: ML实验历史
SEED_METRICS_PATH = os.path.join(DATA_DIR, "station-seed-metrics.json")      # P2-1: 种子深度度量
TOKEN_HEALTH_PATH = os.path.join(DATA_DIR, "station-token-health.json")      # P2-2: Token健康
HYPOTHESES_PATH = os.path.join(DATA_DIR, "station-hypotheses.json")          # v9.0: 假設引擎
EXPERIMENTS_PATH = os.path.join(DATA_DIR, "station-experiments.json")        # v9.1: 實驗設計引擎
THEORIES_PATH = os.path.join(DATA_DIR, "station-theories.json")              # v9.2: 理論合成
METACOGNITION_PATH = os.path.join(DATA_DIR, "station-metacognition.json")    # v10.0: 元認知

# ===== Config =====
VERSION = "10.0"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"
GITHUB_OWNER = "felix0802"
GITHUB_REPO = "emily-evolution"

# P0: 云端 LLM — DeepSeek (v9.3 優先) + SiliconFlow (備用)
# DeepSeek API (OpenAI 兼容) — 性價比最高，用戶已充值
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")  # V3.2 非思考模式

# 硅基流动 (SiliconFlow) — 備用 (Qwen3.5-122B)
SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"
SILICONFLOW_MODEL = os.environ.get("SILICONFLOW_MODEL", "Qwen/Qwen3.5-122B-A10B")

# P1-2: 通用重试函数 — 指数退避
def retry_request(url, method="GET", data=None, headers=None, timeout=20, max_retries=3):
    """通用 HTTP 请求，带指数退避重试"""
    last_error = None
    for attempt in range(max_retries):
        try:
            if headers is None:
                headers = {}
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            resp = urllib.request.urlopen(req, timeout=timeout + attempt * 5)
            return resp
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                time.sleep(wait)
    raise last_error

# ===== arXiv 轮换策略：18 种不同查询，彻底解决内容冻结 =====
ARXIV_ROTATION = [
    # (strategy_name, query_string, max_results) — 空格会被 quote() 编码为 %20
    ("cs.AI 最新", "cat:cs.AI", 8),
    ("cs.LG 最新", "cat:cs.LG", 8),
    ("cs.CL 最新", "cat:cs.CL", 8),
    ("cs.CV 最新", "cat:cs.CV", 8),
    ("cs.AI+cs.LG 混合", "cat:cs.AI OR cat:cs.LG", 12),
    ("cs.CL+cs.CV 混合", "cat:cs.CL OR cat:cs.CV", 12),
    ("搜索: reinforcement learning", 'all:"reinforcement learning" AND cat:cs.LG', 6),
    ("搜索: large language model", 'all:"large language model" AND cat:cs.CL', 6),
    ("搜索: diffusion model", 'all:"diffusion model" AND cat:cs.CV', 6),
    ("搜索: neural architecture", 'all:"neural architecture" AND cat:cs.AI', 6),
    ("搜索: self-supervised learning", 'all:"self-supervised learning"', 6),
    ("搜索: multi-agent system", 'all:"multi-agent system" AND cat:cs.AI', 6),
    # 新增 6 个策略 — 覆盖更多子领域
    ("搜索: graph neural network", 'all:"graph neural" AND cat:cs.LG', 6),
    ("搜索: transfer learning", 'all:"transfer learning" AND cat:cs.LG', 6),
    ("搜索: world model", 'all:"world model" AND cat:cs.AI', 6),
    ("搜索: time series forecasting", 'all:"time series" AND cat:cs.LG', 6),
    ("搜索: anomaly detection", 'all:"anomaly detection" AND cat:cs.LG', 6),
        # v7.0 新增: 新种子覆盖
    ("搜索: mixture of experts", 'all:"mixture of experts" AND cat:cs.LG', 6),
    ("搜索: kv cache LLM", 'all:"kv cache" AND cat:cs.CL', 6),
    ("搜索: graph neural network recent", 'all:"graph neural" AND cat:cs.LG', 6),
    ("搜索: speculative decoding", 'all:"speculative decoding" AND cat:cs.CL', 6),
    ("搜索: multi-query attention", 'all:"multi-query" AND cat:cs.LG', 6),
    ("搜索: geometric deep learning", 'all:"geometric deep" AND cat:cs.LG', 6),
    ("搜索: knowledge distillation", 'all:"knowledge distillation" AND cat:cs.LG', 6),
]

# 7 颗种子技术 — 查询字符串使用空格（非+号），quote() 会编码为 %20
# P1-1 修复：添加 arXiv 分类号过滤 + 宽松关键词搭配
SEEDS = [
    {"id": "mamba", "name": "Mamba (SSM)", "query": '(all:"state space model" OR all:mamba OR all:"selective scan") AND (cat:cs.LG OR cat:cs.AI)', "keywords": ["mamba", "state space", "ssm", "selective scan"], "cat": "cs.LG"},
    {"id": "liquid-networks", "name": "Liquid Networks", "query": '(all:"liquid time constant" OR all:"liquid neural" OR all:"continuous-time") AND (cat:cs.NE OR cat:cs.LG)', "keywords": ["liquid time", "liquid neural", "ltc", "ode", "continuous-time"], "cat": "cs.NE"},
    {"id": "htm", "name": "HTM", "query": '(all:"hierarchical temporal memory" OR all:"sparse distributed" OR all:numenta OR all:"cortical learning" OR all:"online learning" OR all:"sequence memory" OR all:"continual learning" OR all:"anomaly detection" OR all:"predictive coding") AND (cat:cs.AI OR cat:cs.NE OR cat:cs.LG)', "keywords": ["hierarchical temporal", "htm", "sparse distributed", "numenta", "cortical", "online learning", "sequence memory", "predictive coding", "anomaly detection", "continuous learning"], "cat": "cs.AI"},
    {"id": "spiking-nn", "name": "Spiking Neural Networks", "query": 'all:"spiking neural" AND cat:cs.NE', "keywords": ["spiking", "snn", "neuromorphic", "spike-timing"], "cat": "cs.NE"},
    {"id": "non-transformer", "name": "Non-Transformer Arch", "query": '(all:"linear attention" OR all:"state space model" OR all:rwkv OR all:"efficient transformer" OR all:"gated linear" OR all:"linear recurrent") AND (cat:cs.LG OR cat:cs.CL)', "keywords": ["linear attention", "state space", "rwkv", "gated linear", "efficient transformer", "linear recurrent", "sub-quadratic", "mamba"], "cat": "cs.LG"},
    {"id": "few-shot", "name": "Few-Shot Learning", "query": '(all:"few-shot learning" OR all:"meta-learning" OR all:maml OR all:"prototypical network") AND cat:cs.LG', "keywords": ["few-shot", "meta-learning", "maml", "prototypical", "in-context"], "cat": "cs.LG"},
    {"id": "continual-learning", "name": "Continual Learning", "query": '(all:"continual learning" OR all:"catastrophic forgetting" OR all:"lifelong learning" OR all:"elastic weight") AND cat:cs.LG', "keywords": ["continual learning", "catastrophic forgetting", "lifelong", "ewc", "elastic weight"], "cat": "cs.LG"},
{"id": "moe", "name": "Mixture of Experts", "query": '(all:"mixture of experts" OR all:"sparse gating" OR all:"expert routing" OR all:"switch transformer" OR all:"deepseek moe") AND (cat:cs.LG OR cat:cs.CL)', "keywords": ["mixture of experts", "moe", "sparse gating", "expert routing", "router", "switch transformer", "deepseek"], "cat": "cs.LG"},
    {"id": "kv-cache", "name": "KV Cache Optimization", "query": '(all:"kv cache" OR all:"key-value cache" OR all:"multi-query attention" OR all:"grouped query" OR all:"flash attention" OR all:"speculative decoding") AND (cat:cs.LG OR cat:cs.CL)', "keywords": ["kv cache", "key-value cache", "multi-query attention", "grouped query", "gqa", "flash attention", "speculative decoding"], "cat": "cs.LG"},
    {"id": "gnn", "name": "Graph Neural Networks", "query": '(all:"graph neural" OR all:"graph attention" OR all:"message passing" OR all:"geometric deep" OR all:"graph transformer") AND (cat:cs.LG OR cat:cs.AI)', "keywords": ["graph neural", "gnn", "message passing", "graph attention", "geometric", "node embedding", "graph transformer"], "cat": "cs.LG"},
]


AI_ML_WHITELIST = {
    "transformer", "attention", "mamba", "ssm", "rwkv", "retnet", "hyena",
    "moe", "mixture of experts", "mamba2", "jamba", "striped",
    "diffusion", "ddpm", "ddim", "flow matching", "rectified flow",
    "gan", "vae", "variational", "normalizing flow",
    "llm", "llama", "mistral", "falcon", "gemma", "phi-3", "phi-4",
    "lora", "qlora", "peft", "rlhf", "dpo", "grpo", "kto",
    "rag", "retrieval augmented", "langchain", "llamaindex",
    "chain-of-thought", "cot", "tree of thought", "react",
    "prompt engineering", "prompting", "in-context learning",
    "tokenizer", "tokenization", "embedding",
    "vit", "vision transformer", "swin", "deit",
    "clip", "blip", "siglip", "imagebind",
    "detection", "segmentation", "yolo", "detr", "sam",
    "diffusion model", "stable diffusion", "image generation",
    "fine-tuning", "pretraining", "instruction tuning", "sft",
    "distillation", "knowledge distillation",
    "quantization", "pruning", "sparsity", "efficient",
    "federated learning", "federated", "split learning",
    "self-supervised", "contrastive learning", "ssl",
    "continual learning", "lifelong learning", "catastrophic forgetting",
    "meta-learning", "few-shot", "zero-shot", "maml",
    "reinforcement learning", "rl", "rlhf", "ppo",
    "speculative decoding", "kv cache", "flash attention",
    "reasoning", "planning", "tool use", "function calling",
    "agent", "multi-agent", "swarm", "autonomous agent",
    "tool-augmented", "code generation", "code synthesis",
    "interpretability", "explainability", "xai", "mechanistic",
    "alignment", "safety", "red teaming", "jailbreak",
    "adversarial", "robustness",
    "multimodal", "vision-language", "vlm", "mllm",
    "audio", "speech", "tts", "stt",
    "cuda", "triton", "kernel", "tensorrt",
    "scaling law", "emergence", "chinchilla",
    "spiking neural", "neuromorphic", "snn", "htm",
    "liquid network", "liquid time",
    "test-time", "ttt", "mixture of", "router", "attention-free",
    "linear attention", "state space", "long-context",
    "graph neural", "gnn", "equivariant", "geometric",
}

# 预设技术库 — 当 technique_library.json 不存在时使用
# 每个技术条目的 keywords 拆分为单词，方便与 extract_keywords 的单詞输出匹配
DEFAULT_TECHNIQUE_LIBRARY = [
    {"id": "transformer", "name": "Transformer Architecture", "category": "architecture",
     "keywords": ["transformer", "attention", "self-attention", "encoder", "decoder"],
     "difficulty": "intermediate", "adopted": False},
    {"id": "mamba-ssm", "name": "Mamba / State Space Models", "category": "architecture",
     "keywords": ["mamba", "state", "space", "selective", "scan", "ssm"],
     "difficulty": "advanced", "adopted": False},
    {"id": "diffusion", "name": "Diffusion Models", "category": "generative",
     "keywords": ["diffusion", "denoising", "ddpm", "ddim", "noise", "score"],
     "difficulty": "intermediate", "adopted": False},
    {"id": "lora", "name": "LoRA / Parameter-Efficient Fine-Tuning", "category": "training",
     "keywords": ["lora", "adapter", "peft", "low-rank", "fine-tuning", "quantization"],
     "difficulty": "intermediate", "adopted": False},
    {"id": "rlhf", "name": "RLHF / Preference Alignment", "category": "alignment",
     "keywords": ["rlhf", "reinforcement", "preference", "alignment", "reward", "ppo", "dpo"],
     "difficulty": "advanced", "adopted": False},
    {"id": "rag", "name": "Retrieval-Augmented Generation", "category": "application",
     "keywords": ["retrieval", "rag", "augmented", "knowledge", "retriever"],
     "difficulty": "intermediate", "adopted": False},
    {"id": "moe", "name": "Mixture of Experts", "category": "architecture",
     "keywords": ["mixture", "experts", "moe", "router", "sparse", "gating"],
     "difficulty": "advanced", "adopted": False},
    {"id": "multimodal", "name": "Multimodal / Vision-Language", "category": "multimodal",
     "keywords": ["multimodal", "vision", "language", "vlm", "clip", "image", "text"],
     "difficulty": "intermediate", "adopted": False},
    {"id": "agent", "name": "LLM Agents / Tool Use", "category": "agent",
     "keywords": ["agent", "tool", "function", "calling", "planning", "reasoning", "autonomous"],
     "difficulty": "intermediate", "adopted": False},
    {"id": "contrastive", "name": "Contrastive / Self-Supervised Learning", "category": "training",
     "keywords": ["contrastive", "self-supervised", "simclr", "clip", "representation", "augmentation"],
     "difficulty": "intermediate", "adopted": False},
    {"id": "prompt", "name": "Prompt Engineering / In-Context Learning", "category": "technique",
     "keywords": ["prompt", "in-context", "chain-of-thought", "cot", "few-shot", "zero-shot"],
     "difficulty": "beginner", "adopted": False},
    {"id": "quantization", "name": "Model Quantization / Compression", "category": "efficiency",
     "keywords": ["quantization", "pruning", "sparsity", "compression", "int8", "int4"],
     "difficulty": "intermediate", "adopted": False},
    {"id": "graph-nn", "name": "Graph Neural Networks", "category": "architecture",
     "keywords": ["graph", "gnn", "node", "edge", "message", "passing", "aggregate"],
     "difficulty": "intermediate", "adopted": False},
    {"id": "world-model", "name": "World Models / Model-Based RL", "category": "rl",
     "keywords": ["world", "model", "dynamics", "planning", "dreamer", "environment"],
     "difficulty": "advanced", "adopted": False},
    {"id": "knowledge-distill", "name": "Knowledge Distillation", "category": "efficiency",
     "keywords": ["distillation", "knowledge", "teacher", "student", "transfer", "compress"],
     "difficulty": "intermediate", "adopted": False},
]

# ================================================================
# 工具函数
# ================================================================

_rotation_idx = 0
_seed_rotation_idx = 0
_distill_counter = 0

def log(m):
    t = datetime.now().isoformat()[:19]
    line = f"[{t}] {m}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode("ascii"), flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

def load_github_token():
    token = ""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                token = f.read().strip()
        except:
            pass
    if not token:
        token = os.environ.get('GITHUB_TOKEN', '')
    return token

GITHUB_TOKEN = load_github_token()
if not GITHUB_TOKEN:
    print(f"[ERROR] 请先设定 GitHub Token！在 {TOKEN_FILE} 贴上你的 token")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def push_to_github(repo_path, content_dict, commit_msg):
    content_b64 = base64.b64encode(
        json.dumps(content_dict, ensure_ascii=False, indent=2).encode()
    ).decode()
    api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{repo_path}"
    sha = ""
    try:
        req = urllib.request.Request(api_url, headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=10)
        sha = json.loads(resp.read().decode()).get("sha", "")
    except:
        pass
    push_data = {"message": commit_msg, "content": content_b64}
    if sha:
        push_data["sha"] = sha
    try:
        body = json.dumps(push_data).encode()
        req = urllib.request.Request(
            api_url, data=body,
            headers={**HEADERS, "Content-Type": "application/json"},
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=15)
        log(f"✅ 已推送 {repo_path}")
        return True
    except Exception as e:
        log(f"⚠️ 推送失败 {repo_path}: {str(e)[:80]}")
        return False

def append_evolution_log(phase, data):
    entry = {"timestamp": datetime.now().isoformat(), "phase": phase, "data": data}
    try:
        with open(EVOLUTION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except:
        pass

# ================================================================
# ================================================================
# P1-1: 语义去重引擎 v9.4
# 三层架构: arXiv ID 精确 → Token Jaccard 语义 → URL 兜底
# ================================================================

def _tokenize_title(title):
    """将学术标题转换为规范化 token 集合（去停用词）"""
    text = title.lower()
    text = re.sub(r'\b\d{4}\.\d{4,6}(v\d+)?\b', '', text)  # 移除 arXiv ID
    text = re.sub(r'[:\-–—,;()\[\]{}""'']', ' ', text)      # 标点 → 空格
    tokens = re.findall(r'[a-z0-9]{3,}', text)               # 3字符以上单词
    return tuple(sorted(t for t in tokens if t not in _STOPWORDS))

def _jaccard(tokens_a, tokens_b):
    """Jaccard 语义相似度: |A∩B| / |A∪B|"""
    if not tokens_a or not tokens_b:
        return 0.0
    sa, sb = set(tokens_a), set(tokens_b)
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union > 0 else 0.0

def _extract_arxiv_id(url):
    """从 arXiv URL 提取规范 ID (e.g. 2607.08716)"""
    m = re.search(r'abs/(\d{4}\.\d{4,6})', url)
    return m.group(1) if m else None

def load_seen_papers():
    """加载已见论文集合。v9.4: 自动迁移旧格式"""
    if os.path.exists(SEEN_PAPERS_PATH):
        try:
            with open(SEEN_PAPERS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # v9.4+ 新格式
            if "papers" in data:
                return data
            # 旧格式自动迁移
            if "seen_urls" in data:
                papers = []
                for url, title in zip(data.get("seen_urls", []), data.get("seen_titles", [])):
                    papers.append({
                        "url": url, "title": title,
                        "arxiv_id": _extract_arxiv_id(url),
                        "tokens": list(_tokenize_title(title)),
                        "first_seen_round": 0
                    })
                return {"papers": papers, "total_unique": len(papers)}
        except:
            pass
    return {"papers": [], "total_unique": 0}

def _semantic_prune(papers):
    """智能裁剪：保留语义多样性（按轮次优先保留最新）"""
    papers = sorted(papers, key=lambda p: p.get("first_seen_round", 0), reverse=True)
    kept, kept_token_sets = [], []
    for p in papers:
        tokens = set(p.get("tokens", []))
        is_dup = any(_jaccard(tokens, kt) > 0.85 for kt in kept_token_sets)
        if not is_dup:
            kept.append(p)
            kept_token_sets.append(tokens)
    return kept

def save_seen_papers(seen):
    """保存已见论文。超过 PRUNE_TRIGGER 时智能裁剪保留多样性"""
    seen["total_unique"] = len(seen["papers"])
    # 智能裁剪：保留语义多样性
    if len(seen["papers"]) > PRUNE_TRIGGER:
        before = len(seen["papers"])
        seen["papers"] = _semantic_prune(seen["papers"])
        seen["total_unique"] = len(seen["papers"])
        log(f"  🧹 语义裁剪: {before} → {seen['total_unique']} 篇（保留多样性）")
    # 硬上限兜底
    if len(seen["papers"]) > MAX_SEEN_PAPERS:
        seen["papers"] = seen["papers"][-MAX_SEEN_PAPERS:]
        seen["total_unique"] = len(seen["papers"])
    with open(SEEN_PAPERS_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)

def filter_new_papers(papers, current_round=0):
    """语义去重：arXiv ID 精确 → Token Jaccard 语义 → URL 兜底"""
    seen = load_seen_papers()

    # 构建快速查找索引
    arxiv_ids = set()
    all_token_sets = []
    all_urls = set()
    for p in seen.get("papers", []):
        aid = p.get("arxiv_id")
        if aid: arxiv_ids.add(aid)
        tokens = p.get("tokens")
        if tokens: all_token_sets.append(set(tokens))
        url = p.get("url", "")
        if url: all_urls.add(url)

    new_papers, semantic_dups = [], 0
    for p in papers:
        url = p.get("url", "")
        title = p.get("title", "")
        arxiv_id = _extract_arxiv_id(url)

        # 第1层: arXiv ID 精确匹配
        if arxiv_id and arxiv_id in arxiv_ids:
            continue

        # 第2层: Token Jaccard 语义相似度
        tokens = _tokenize_title(title)
        if tokens:
            token_set = set(tokens)
            is_dup = any(_jaccard(token_set, et) > SEMANTIC_DEDUP_THRESHOLD for et in all_token_sets)
            if is_dup:
                semantic_dups += 1
                continue

        # 第3层: URL 精确匹配 (兜底)
        if url and url in all_urls:
            continue

        # 新论文！
        new_papers.append(p)
        if arxiv_id: arxiv_ids.add(arxiv_id)
        if tokens: all_token_sets.append(token_set)
        if url: all_urls.add(url)

        seen["papers"].append({
            "url": url, "title": title, "arxiv_id": arxiv_id,
            "tokens": list(tokens) if tokens else [],
            "first_seen_round": current_round
        })

    save_seen_papers(seen)
    return new_papers

# ================================================================
# P1-2: ML 实验历史追踪
# ================================================================

def load_ml_history():
    if os.path.exists(ML_HISTORY_PATH):
        try:
            with open(ML_HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"best_scores": {}, "evolution_count": 0, "history": []}

def save_ml_history(history):
    if len(history["history"]) > 50:
        history["history"] = history["history"][-50:]
    with open(ML_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def update_ml_history(results, ev_count):
    """更新ML历史，追踪最佳分数和进化趋势"""
    history = load_ml_history()
    improved = []

    for item in results.get("classification", []):
        key = f"{item['dataset']}_{item['model']}"
        prev_best = history["best_scores"].get(key, {}).get("accuracy_mean", 0)
        if item["accuracy_mean"] > prev_best:
            history["best_scores"][key] = {
                "accuracy_mean": item["accuracy_mean"],
                "evolution": ev_count,
                "timestamp": datetime.now().isoformat(),
            }
            improved.append(f"{key}: {prev_best:.4f} → {item['accuracy_mean']:.4f}")

    for item in results.get("regression", []):
        key = f"{item['dataset']}_{item['model']}"
        prev_best = history["best_scores"].get(key, {}).get("r2_mean", -999)
        if item["r2_mean"] > prev_best:
            history["best_scores"][key] = {
                "r2_mean": item["r2_mean"],
                "evolution": ev_count,
                "timestamp": datetime.now().isoformat(),
            }
            improved.append(f"{key}: {prev_best:.4f} → {item['r2_mean']:.4f}")

    history["evolution_count"] = ev_count
    history["history"].append({
        "evolution": ev_count,
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results.get("classification", [])) + len(results.get("regression", [])),
        "improvements": improved,
    })
    save_ml_history(history)
    return improved

# ================================================================
# P2-2: GitHub Token 健康监控
# ================================================================

def check_token_health():
    """检查 GitHub Token 是否有效"""
    try:
        req = urllib.request.Request(
            "https://api.github.com/user",
            headers=HEADERS
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        return {
            "valid": True,
            "user": data.get("login", "unknown"),
            "rate_limit_remaining": resp.headers.get("X-RateLimit-Remaining", "?"),
            "checked_at": datetime.now().isoformat(),
        }
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"valid": False, "error": "Token 已过期或无效 (401)", "checked_at": datetime.now().isoformat()}
        return {"valid": False, "error": f"HTTP {e.code}", "checked_at": datetime.now().isoformat()}
    except Exception as e:
        return {"valid": False, "error": str(e)[:80], "checked_at": datetime.now().isoformat()}

def save_token_health(health):
    with open(TOKEN_HEALTH_PATH, "w", encoding="utf-8") as f:
        json.dump(health, f, ensure_ascii=False, indent=2)

def push_to_github_safe(repo_path, content_dict, commit_msg):
    """带 Token 健康检查的推送"""
    # 首次推送时检查 token
    if not hasattr(push_to_github_safe, "_token_checked"):
        health = check_token_health()
        save_token_health(health)
        push_to_github_safe._token_checked = True
        if not health["valid"]:
            log(f"🔴 [Token监控] GitHub Token 无效: {health.get('error', '')}")
            log(f"🔴 [Token监控] 请更新 {TOKEN_FILE} 中的 token！数据将保存在本地但不推送。")
            return False
        else:
            log(f"🟢 [Token监控] Token 有效 (用户: {health.get('user', '?')}, 剩余配额: {health.get('rate_limit_remaining', '?')})")

    return push_to_github(repo_path, content_dict, commit_msg)

# ================================================================
# P0-1: Ollama LLM 接口
# ================================================================

def check_ollama():
    """检查 Ollama 是否可用"""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": f"Emily/{VERSION}"})
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode())
        models = [m["name"] for m in data.get("models", [])]
        return True, models
    except:
        return False, []

def call_ollama(prompt, system_prompt="", timeout_sec=60):
    """调用 Ollama LLM"""
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 512}
    }).encode()

    try:
        req = urllib.request.Request(OLLAMA_URL, data=payload,
                                      headers={"Content-Type": "application/json", "User-Agent": f"Emily/{VERSION}"})
        resp = urllib.request.urlopen(req, timeout=timeout_sec)
        result = json.loads(resp.read().decode())
        return result.get("response", "").strip()
    except Exception as e:
        return f"[LLM_ERROR: {str(e)[:60]}]"

# P0: 云端 LLM (SiliconFlow) 回退
def call_cloud_llm(prompt, system_prompt="", timeout_sec=60):
    """调用 SiliconFlow 云端 LLM (OpenAI 兼容格式，qwen2.5-7b 免费额度)"""
    if not SILICONFLOW_API_KEY:
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": SILICONFLOW_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1024,
    }).encode()

    try:
        resp = retry_request(
            SILICONFLOW_BASE_URL,
            method="POST",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                "User-Agent": f"Emily/{VERSION}",
            },
            timeout=timeout_sec
        )
        result = json.loads(resp.read().decode())
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[CLOUD_LLM_ERROR: {str(e)[:60]}]"

def call_deepseek(prompt, system_prompt="", timeout_sec=60):
    """调用 DeepSeek API (OpenAI 兼容格式, deepseek-chat V3.2)"""
    if not DEEPSEEK_API_KEY:
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1024,
    }).encode()

    try:
        resp = retry_request(
            DEEPSEEK_BASE_URL,
            method="POST",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "User-Agent": f"Emily/{VERSION}",
            },
            timeout=timeout_sec
        )
        result = json.loads(resp.read().decode())
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[DEEPSEEK_ERROR: {str(e)[:60]}]"


def call_llm_smart(prompt, system_prompt="", timeout_sec=60):
    """智能 LLM 调用：优先 Ollama → DeepSeek → SiliconFlow → 无"""
    # 先试 Ollama
    ollama_ok, _ = check_ollama()
    if ollama_ok:
        result = call_ollama(prompt, system_prompt, timeout_sec)
        if result and not result.startswith("[LLM_ERROR"):
            return result, "ollama"

    # 回退到 DeepSeek (已充值，優先使用)
    if DEEPSEEK_API_KEY:
        result = call_deepseek(prompt, system_prompt, timeout_sec)
        if result and not result.startswith("[DEEPSEEK_ERROR"):
            return result, "deepseek"

    # 最後回退到 SiliconFlow
    if SILICONFLOW_API_KEY:
        result = call_cloud_llm(prompt, system_prompt, timeout_sec)
        if result and not result.startswith("[CLOUD_LLM_ERROR"):
            return result, "siliconflow"

    return None, None

# ================================================================
# P0-2: arXiv 查询轮换
# ================================================================

def fetch_arxiv_papers(query="cat:cs.AI", max_results=10):
    """从 arXiv API 获取论文 — 支持轮换查询"""
    global _rotation_idx
    # 从轮换策略中选择
    strategy_name, query_str, mr = ARXIV_ROTATION[_rotation_idx % len(ARXIV_ROTATION)]
    _rotation_idx += 1

    # URL 编码查询字符串（空格→%20，而非+→%2B）
    encoded_query = urllib.parse.quote(query_str, safe='')
    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query={encoded_query}&"
        f"sortBy=submittedDate&sortOrder=descending&"
        f"max_results={mr}"
    )
    try:
        resp = retry_request(url, headers={"User-Agent": f"Emily-Evolution-Station/{VERSION}"}, timeout=30, max_retries=2)
        xml_data = resp.read().decode("utf-8")
    except Exception as e:
        log(f"⚠️ arXiv API 无法连接 ({strategy_name}): {str(e)[:60]}")
        # 尝试备用查询
        try:
            fallback_query = urllib.parse.quote("cat:cs.AI", safe='')
            fallback_url = f"https://export.arxiv.org/api/query?search_query={fallback_query}&sortBy=submittedDate&sortOrder=descending&max_results=5"
            resp2 = retry_request(fallback_url, headers={"User-Agent": f"Emily/{VERSION}"}, timeout=15, max_retries=2)
            xml_data = resp2.read().decode("utf-8")
            strategy_name = "cs.AI (fallback)"
        except:
            return [], strategy_name

    papers = []
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    try:
        root = ET.fromstring(xml_data)
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            published_el = entry.find("atom:published", ns)
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None]
            link_el = entry.find("atom:id", ns)
            cats = [c.get("term", "") for c in entry.findall("atom:category", ns)]
            paper = {
                "title": title_el.text.strip().replace("\n", " ") if title_el is not None and title_el.text else "N/A",
                "summary": summary_el.text.strip().replace("\n", " ")[:600] if summary_el is not None and summary_el.text else "",
                "published": published_el.text[:10] if published_el is not None and published_el.text else "",
                "authors": authors[:5],
                "url": link_el.text.strip() if link_el is not None and link_el.text else "",
                "categories": cats,
                "query_strategy": strategy_name,
            }
            papers.append(paper)
    except ET.ParseError as e:
        log(f"⚠️ arXiv XML 解析失败 ({strategy_name}): {str(e)[:60]}")
    return papers, strategy_name

# ================================================================
# P2-2: 种子浇水 — 主动搜索种子相关论文
# ================================================================

def water_seed(seed, retry_on_empty=True):
    """为一颗种子搜索 arXiv — 含去重、深度度量、无结果重试、低相关度过滤"""
    query = seed["query"]
    encoded_query = urllib.parse.quote(query, safe='')
    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query={encoded_query}&"
        f"sortBy=submittedDate&sortOrder=descending&"
        f"max_results=10"
    )
    xml_data = None
    error = None

    # P1-2: 使用重试函数
    try:
        resp = retry_request(url, headers={"User-Agent": f"Emily/{VERSION}"}, timeout=30, max_retries=3)
        xml_data = resp.read().decode("utf-8")
    except Exception as e:
        error = str(e)[:80]

    # P1-3: 主查询失败时尝试简化查询作为回退
    if xml_data is None and retry_on_empty:
        # 回退：只用核心关键词 + 分类号
        fallback_query = f'all:"{seed["keywords"][0]}" AND cat:{seed.get("cat", "cs.AI")}'
        encoded_fb = urllib.parse.quote(fallback_query, safe='')
        fb_url = (
            f"https://export.arxiv.org/api/query?"
            f"search_query={encoded_fb}&"
            f"sortBy=submittedDate&sortOrder=descending&"
            f"max_results=5"
        )
        try:
            resp = retry_request(fb_url, headers={"User-Agent": f"Emily/{VERSION}"}, timeout=25, max_retries=2)
            xml_data = resp.read().decode("utf-8")
            log(f"  🔄 [种子] {seed['name']} 主查询失败，使用回退查询: {seed['keywords'][0]}")
        except Exception as e2:
            error = f"primary+fallback both failed: {error} | {str(e2)[:40]}"

    if xml_data is None:
        log(f"  ⚠️ [种子] {seed['name']} API 失败: {error}")
        return {"seed_id": seed["id"], "papers": [], "total_found": 0, "new_found": 0,
                "error": error, "needs_retry": True}

    papers = []
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    try:
        root = ET.fromstring(xml_data)
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            published_el = entry.find("atom:published", ns)
            link_el = entry.find("atom:id", ns)
            paper = {
                "title": title_el.text.strip().replace("\n", " ") if title_el is not None and title_el.text else "N/A",
                "summary": summary_el.text.strip().replace("\n", " ")[:300] if summary_el is not None and summary_el.text else "",
                "published": published_el.text[:10] if published_el is not None and published_el.text else "",
                "url": link_el.text.strip() if link_el is not None and link_el.text else "",
            }

            # 检查种子关键词匹配度（连字符归一化：state-space → state space）
            text = (paper["title"] + " " + paper["summary"]).lower().replace("-", " ")
            match_count = sum(1 for kw in seed["keywords"] if kw.lower().replace("-", " ") in text)
            paper["seed_match_score"] = match_count
            papers.append(paper)
    except:
        pass

    # P1-1: 过滤完全不相关的论文 (match_score == 0)
    irrelevant = [p for p in papers if p["seed_match_score"] == 0]
    relevant = [p for p in papers if p["seed_match_score"] >= 1]
    if irrelevant:
        log(f"  🗑️ [种子] {seed['name']} 过滤 {len(irrelevant)} 篇无关联论文")

    # P1-1: 语义去重 (v9.4)
    ev_round = load_evolution_state().get("total_evolutions", 0)
    new_papers = filter_new_papers(relevant, current_round=ev_round)
    dup_count = len(relevant) - len(new_papers)

    # P2-1: 种子深度度量
    avg_score = sum(p["seed_match_score"] for p in new_papers) / max(len(new_papers), 1)
    high_relevance = sum(1 for p in new_papers if p["seed_match_score"] >= 2)
    seed_keywords_found = set()
    for p in new_papers:
        text = (p["title"] + " " + p["summary"]).lower()
        for kw in seed["keywords"]:
            if kw.lower() in text:
                seed_keywords_found.add(kw)

    result = {
        "seed_id": seed["id"],
        "seed_name": seed["name"],
        "papers": new_papers,
        "total_found": len(relevant),
        "new_found": len(new_papers),
        "irrelevant_filtered": len(irrelevant),
        "duplicates_filtered": dup_count,
        "avg_relevance_score": round(avg_score, 2),
        "high_relevance_count": high_relevance,
        "keywords_matched": list(seed_keywords_found),
        "timestamp": datetime.now().isoformat(),
        "needs_retry": len(new_papers) == 0 and retry_on_empty,
    }

    # 更新种子度量历史
    update_seed_metrics(seed, result)

    return result

def water_all_seeds():
    """浇水：轮流搜索每颗种子的相关论文（启动时初始化所有种子，索引持久化防重启归零，P1-3: 失败不推进）"""
    global _seed_rotation_idx

    # 确保所有种子都在状态文件中初始化
    seed_state = load_seed_state()
    needs_init = False
    for seed in SEEDS:
        if seed["id"] not in seed_state:
            seed_state[seed["id"]] = {"name": seed["name"], "total_papers_found": 0,
                                       "watering_count": 0, "history": [], "keywords": seed["keywords"]}
            needs_init = True
            log(f"🌱 [种子] 初始化: {seed['name']}")
        else:
            # 同步关键词（防止代码更新了关键词但状态文件还是旧的）
            seed_state[seed["id"]]["keywords"] = seed["keywords"]

    # 从持久化状态恢复轮换索引（防止重启归零！）
    if "_rotation_idx" in seed_state:
        _seed_rotation_idx = seed_state["_rotation_idx"]

    # v7.1: 优先浇水 — 从未被浇过的种子优先、超过3天未浇的种子插队
    # 两级优先级分两轮扫描：先扫 wc==0（最高），再扫 days>3（次高）
    prioritized_seed = None
    now_dt = datetime.now()

    # 第一轮：从未被浇过的种子（最高优先级，wc==0）
    for s in SEEDS:
        sid = s["id"]
        sd = seed_state.get(sid, {})
        if sd.get("watering_count", 0) == 0:
            prioritized_seed = s
            log(f"⚡ [种子优先] {s['name']} 从未被浇过，插队浇水！")
            break

    # 第二轮：超过3天未浇水的种子（次高优先级）
    if not prioritized_seed:
        for s in SEEDS:
            sid = s["id"]
            sd = seed_state.get(sid, {})
            last_watered_str = sd.get("last_watered", "")
            if last_watered_str:
                try:
                    last_dt = datetime.fromisoformat(last_watered_str)
                    days_since = (now_dt - last_dt).total_seconds() / 86400
                    if days_since > 3:
                        prioritized_seed = s
                        log(f"⚡ [种子优先] {s['name']} 已 {days_since:.1f} 天未浇水，插队浇水！")
                        break
                except:
                    pass

    # 选取当前轮次要浇水的种子（优先种子插队）
    if prioritized_seed:
        seed = prioritized_seed
    else:
        seed = SEEDS[_seed_rotation_idx % len(SEEDS)]
    current_pos = (_seed_rotation_idx % len(SEEDS)) + 1  # 1-based for human readability

    log(f"🌱 [种子浇水] 正在浇灌: {seed['name']} (#{current_pos}/{len(SEEDS)})...")
    result = water_seed(seed, retry_on_empty=True)
    # 确保返回值有 total_found 和 new_found
    if "total_found" not in result:
        result["total_found"] = 0
    if "new_found" not in result:
        result["new_found"] = result.get("total_found", 0)

    s = seed_state[seed["id"]]
    s["watering_count"] += 1
    s["last_watered"] = datetime.now().isoformat()

    # P1-3: 如果无结果且需要重试（API失败或找到0篇相关论文），不推进索引
    if result.get("needs_retry") and s["watering_count"] <= 3:
        log(f"  🔄 [种子] {seed['name']} 本轮无有效结果，保留在队列中（浇灌{s['watering_count']}/3次尝试）")
        # 不更新 papers 计数，不推进 rotation
    else:
        # 正常：更新计数，推进轮换
        s["total_papers_found"] += result["new_found"]
        s["history"].append({
            "timestamp": datetime.now().isoformat(),
            "papers_found": result["new_found"],
            "duplicates": result.get("duplicates_filtered", 0),
            "irrelevant_filtered": result.get("irrelevant_filtered", 0),
            "avg_relevance": result.get("avg_relevance_score", 0),
            "high_relevance": result.get("high_relevance_count", 0),
            "papers": result["papers"][:3],
        })
        if len(s["history"]) > 50:
            s["history"] = s["history"][-50:]

        # 推进轮换索引
        _seed_rotation_idx += 1
        seed_state["_rotation_idx"] = _seed_rotation_idx

    save_seed_state(seed_state)

    # 显示所有种子状态摘要
    active_seeds = sum(1 for k, v in seed_state.items() if k != "_rotation_idx" and isinstance(v, dict) and v.get("watering_count", 0) > 0)
    next_seed = SEEDS[(_seed_rotation_idx % len(SEEDS))]
    log(f"🌱 [种子浇水] {seed['name']}: 新增 {result['new_found']} 篇(重复{result.get('duplicates_filtered',0)}/无关{result.get('irrelevant_filtered',0)}) | 相关度 {result.get('avg_relevance_score', 0)} | 高匹配 {result.get('high_relevance_count', 0)} | 累计 {s['total_papers_found']} 篇 | 浇水 {s['watering_count']} 次 | 活跃: {active_seeds}/{len(SEEDS)} | 下次→{next_seed['name']}")
    return result

def load_seed_state():
    if os.path.exists(SEED_STATE_PATH):
        try:
            with open(SEED_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_seed_state(state):
    with open(SEED_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ================================================================
# P2-1: 种子增长深度度量
# ================================================================

def load_seed_metrics():
    if os.path.exists(SEED_METRICS_PATH):
        try:
            with open(SEED_METRICS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_seed_metrics(metrics):
    with open(SEED_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

def update_seed_metrics(seed, result):
    """更新种子的深度度量：关键词扩展、相关度趋势、高匹配论文"""
    metrics = load_seed_metrics()
    sid = seed["id"]

    if sid not in metrics:
        metrics[sid] = {
            "name": seed["name"],
            "total_new_papers": 0,
            "total_watering": 0,
            "all_keywords_matched": [],
            "avg_relevance_trend": [],
            "high_relevance_total": 0,
            "best_papers": [],  # seed_match_score >= 3 的论文
        }

    m = metrics[sid]
    m["total_new_papers"] += result.get("new_found", 0)
    m["total_watering"] += 1
    m["high_relevance_total"] += result.get("high_relevance_count", 0)

    # 关键词扩展（累积去重）
    existing_kw = set(m.get("all_keywords_matched", []))
    new_kw = set(result.get("keywords_matched", []))
    m["all_keywords_matched"] = list(existing_kw | new_kw)

    # 相关度趋势（保留最近20次）
    m["avg_relevance_trend"].append(result.get("avg_relevance_score", 0))
    if len(m["avg_relevance_trend"]) > 20:
        m["avg_relevance_trend"] = m["avg_relevance_trend"][-20:]

    # 高匹配论文（保留最好的10篇）
    for p in result.get("papers", []):
        if p.get("seed_match_score", 0) >= 3:
            m["best_papers"].append({
                "title": p["title"][:100],
                "score": p["seed_match_score"],
                "published": p.get("published", ""),
            })
    m["best_papers"] = sorted(m["best_papers"], key=lambda x: x["score"], reverse=True)[:10]

    m["last_updated"] = datetime.now().isoformat()
    save_seed_metrics(metrics)

# ================================================================
# 感知层 — 论文研究
# ================================================================

def probe_system():
    info = {
        "platform": platform.platform(),
        "python": sys.version,
        "hostname": platform.node(),
        "cpu_count": os.cpu_count(),
        "timestamp": datetime.now().isoformat(),
    }
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["wmic", "OS", "get", "TotalVisibleMemorySize,FreePhysicalMemory", "/Value"],
                capture_output=True, text=True, encoding="gbk", errors="replace", timeout=5,
            )
            for line in result.stdout.strip().split("\n"):
                if "TotalVisibleMemorySize" in line:
                    kb = int(line.split("=")[1])
                    info["memory_mb"] = round(kb / 1024)
        except:
            info["memory_mb"] = "unknown"
    return info

def extract_keywords(text, top_n=5):
    stopwords = {
        "the","a","an","is","are","was","were","be","been","being",
        "have","has","had","do","does","did","will","would","could",
        "should","may","might","can","shall","to","of","in","for",
        "on","with","at","by","from","as","into","through","during",
        "before","after","above","below","between","and","but","or",
        "nor","not","so","yet","both","either","neither","each","every",
        "all","any","few","more","most","other","some","such","no",
        "only","own","same","than","too","very","just","because",
        "about","over","under","again","further","then","once","here",
        "there","when","where","why","how","which","who","whom",
        "this","that","these","those","it","its","we","they","them",
        "propose","novel","approach","method","using","based","show",
        "results","also","well","however","paper","model","models",
        "used","use","one","two","new","different",
    }
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    filtered = [w for w in words if w not in stopwords]
    return [w for w, _ in Counter(filtered).most_common(top_n)]

def analyze_arxiv_trends(all_papers):
    if not all_papers:
        return {"status": "no_data", "total_papers": 0, "top_keywords": [], "note": "arXiv API 无数据"}
    all_keywords = []
    for p in all_papers:
        all_keywords.extend(extract_keywords(p.get("title", "") + " " + p.get("summary", "")))
    return {
        "total_papers": len(all_papers),
        "top_keywords": [w for w, c in Counter(all_keywords).most_common(20)],
        "papers": all_papers[:8],
        "fetched_at": datetime.now().isoformat(),
    }

def research_arxiv():
    """使用轮换策略抓取 arXiv 论文"""
    log("📄 [arXiv] 开始论文研究（轮换策略）...")
    all_papers = []
    strategies_used = []

    # 使用 3 种不同策略，每种少量论文，增加多样性
    for i in range(3):
        papers, strategy_name = fetch_arxiv_papers()
        all_papers.extend(papers)
        strategies_used.append(strategy_name)
        log(f"  📂 {strategy_name}: {len(papers)} 篇")
        time.sleep(3)

    # 单轮去重（按标题）
    seen_titles = set()
    unique_papers = []
    for p in all_papers:
        if p["title"] not in seen_titles:
            seen_titles.add(p["title"])
            unique_papers.append(p)

    # P1-1: 语义去重 (v9.4)
    ev_round = load_evolution_state().get("total_evolutions", 0)
    new_papers = filter_new_papers(unique_papers, current_round=ev_round)
    dup_count = len(unique_papers) - len(new_papers)

    result = analyze_arxiv_trends(unique_papers)
    result["strategies_used"] = strategies_used
    result["duplicates_filtered"] = dup_count
    result["new_papers_count"] = len(new_papers)
    seen_data = load_seen_papers()
    log(f"📊 [arXiv] 完成: {result['new_papers_count']} 篇（新） | 本批 {result['total_papers']} 篇 | 过滤 {dup_count} 篇重复（语义去重） | 累计唯一: {seen_data['total_unique']} | 策略: {strategies_used}")
    return result

# ================================================================
# HuggingFace 趋势
# ================================================================

def fetch_hf_trending():
    url = "https://huggingface.co/api/models?sort=downloads&direction=-1&limit=25"
    try:
        resp = retry_request(url, headers={"User-Agent": f"Emily-Evolution-Station/{VERSION}"}, timeout=25, max_retries=2)
        data = json.loads(resp.read().decode())
    except Exception as e:
        log(f"⚠️ HuggingFace API 无法连接: {str(e)[:60]}")
        return {"top_models": [], "task_distribution": {}, "fetched_at": datetime.now().isoformat()}

    models = []
    tasks_counter = Counter()
    for m in data[:15]:
        task = m.get("pipeline_tag", "unknown")
        tasks_counter[task] += 1
        models.append({
            "name": m.get("modelId", m.get("id", "N/A")),
            "downloads": m.get("downloads", 0),
            "task": task,
            "likes": m.get("likes", 0),
        })
    return {
        "top_models": models[:10],
        "task_distribution": dict(tasks_counter.most_common(10)),
        "fetched_at": datetime.now().isoformat(),
    }

def research_huggingface():
    log("🔥 [HF] 趋势研究...")
    trends = fetch_hf_trending()
    top_tasks = trends.get("task_distribution", {})
    log(f"📊 [HF] 完成: {len(trends.get('top_models', []))} 个模型, 主要任务: {list(top_tasks.keys())[:3]}")
    return trends

# ================================================================
# P3-1: 多源感知 — GitHub Trending + Papers With Code
# ================================================================

def fetch_github_trending():
    """抓取 GitHub Trending AI/ML 仓库（使用 GitHub API）"""
    url = "https://api.github.com/search/repositories?q=topic:machine-learning+topic:deep-learning&sort=stars&order=desc&per_page=10"
    try:
        resp = retry_request(url, headers={**HEADERS, "User-Agent": f"Emily/{VERSION}"}, timeout=20, max_retries=2)
        data = json.loads(resp.read().decode())
    except Exception as e:
        log(f"⚠️ GitHub Trending 获取失败: {str(e)[:60]}")
        return []

    repos = []
    for item in data.get("items", [])[:8]:
        repos.append({
            "name": item.get("full_name", ""),
            "description": (item.get("description", "") or "")[:200],
            "stars": item.get("stargazers_count", 0),
            "language": item.get("language", "N/A"),
            "topics": item.get("topics", [])[:5],
        })
    return repos

def fetch_paperswithcode():
    """抓取 HuggingFace Daily Papers（Papers With Code 已停用，改用 HF）"""
    # PWC 于 2025年7月被 Meta 关闭，API 已不可用
    # 改用 HuggingFace 的每日热门论文 API
    url = "https://huggingface.co/api/daily_papers"
    try:
        resp = retry_request(url, headers={"User-Agent": f"Emily/{VERSION}", "Accept": "application/json"}, timeout=20, max_retries=2)
        data = json.loads(resp.read().decode())
    except Exception as e:
        log(f"⚠️ HF Daily Papers 获取失败: {str(e)[:60]}")
        return []

    papers = []
    for item in data[:8]:
        paper = item.get("paper", {})
        papers.append({
            "title": paper.get("title", "N/A"),
            "arxiv_id": paper.get("id", ""),
            "upvotes": item.get("upvotes", 0),
            "published_at": paper.get("publishedAt", ""),
            "url": f"https://arxiv.org/abs/{paper.get('id', '')}" if paper.get("id") else "",
        })
    return papers

def research_multi_source():
    """多源感知：GitHub + HuggingFace Daily Papers"""
    log("🌐 [多源感知] GitHub Trending + HF Daily Papers...")

    gh_repos = fetch_github_trending()
    log(f"  🐙 GitHub: {len(gh_repos)} 个热门 ML 仓库")

    pwc_papers = fetch_paperswithcode()
    log(f"  📜 HF Daily: {len(pwc_papers)} 篇热门论文")

    return {
        "github_trending": gh_repos,
        "paperswithcode": pwc_papers,
        "fetched_at": datetime.now().isoformat(),
    }

# ================================================================
# P1-2: 真实 ML 实验（UCI + sklearn 内置数据集）
# ================================================================

def run_ml_benchmarks():
    """使用真实数据集进行 ML 基准测试 — P1-2: 参数随进化轮次变化"""
    log("🧪 [ML] 真实数据集基准实验（参数进化）...")
    try:
        from sklearn.model_selection import cross_val_score
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.svm import SVC
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.linear_model import LinearRegression, Ridge
        from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_diabetes
    except ImportError:
        log("⚠️ scikit-learn 未安装，跳过 ML 实验")
        return {"status": "skipped"}

    # P1-2: 根据进化轮次变化参数
    state = load_evolution_state()
    ev_count = state.get("total_evolutions", 0)
    param_seed = 42 + ev_count  # 每轮不同的随机种子

    # 参数变化策略：每轮微调关键超参数
    n_est_options = [50, 100, 150, 200]
    n_est = n_est_options[ev_count % len(n_est_options)]
    k_neighbors = 3 + (ev_count % 5)  # 3,5,7,9,11 循环
    svm_c = [0.1, 1.0, 10.0, 100.0][ev_count % 4]
    ridge_alpha = [0.1, 0.5, 1.0, 2.0, 5.0][ev_count % 5]
    max_depth = [3, 5, 7, 10, None][ev_count % 5]

    log(f"  🧪 参数进化: n_est={n_est} | k={k_neighbors} | SVM_C={svm_c} | ridge_a={ridge_alpha} | max_depth={max_depth} | seed={param_seed}")

    results = {"classification": [], "regression": [], "datasets_used": [],
               "evolution_params": {"n_estimators": n_est, "k_neighbors": k_neighbors,
                                     "svm_c": svm_c, "ridge_alpha": ridge_alpha,
                                     "max_depth": max_depth, "random_seed": param_seed},
               "timestamp": datetime.now().isoformat()}

    # 真实分类数据集
    classification_datasets = [
        ("Iris", load_iris),
        ("Wine", load_wine),
        ("Breast Cancer", load_breast_cancer),
    ]

    classifiers = {
        "RandomForest": RandomForestClassifier(n_estimators=n_est, max_depth=max_depth, random_state=param_seed),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=n_est, random_state=param_seed),
        "LogisticRegression": LogisticRegression(max_iter=2000, random_state=param_seed),
        "KNeighbors": KNeighborsClassifier(n_neighbors=k_neighbors),
        "SVM": SVC(kernel="rbf", C=svm_c, random_state=param_seed),
        "DecisionTree": DecisionTreeClassifier(max_depth=max_depth, random_state=param_seed),
    }

    for ds_name, ds_loader in classification_datasets:
        try:
            X, y = ds_loader(return_X_y=True)
            for clf_name, clf in classifiers.items():
                try:
                    pipe = Pipeline([("scaler", StandardScaler()), ("clf", clf)])
                    scores = cross_val_score(pipe, X, y, cv=min(5, len(set(y))), scoring="accuracy")
                    results["classification"].append({
                        "dataset": ds_name,
                        "model": clf_name,
                        "accuracy_mean": round(float(scores.mean()), 4),
                        "accuracy_std": round(float(scores.std()), 4),
                        "params": f"n_est={n_est},k={k_neighbors}" if clf_name in ("RandomForest", "GradientBoosting") else
                                  f"C={svm_c}" if clf_name == "SVM" else f"k={k_neighbors}" if clf_name == "KNeighbors" else
                                  f"max_depth={max_depth}",
                    })
                except:
                    pass
            results["datasets_used"].append(ds_name)
            log(f"  🧪 {ds_name}: {len(set(y))}类, {len(X)}样本 ✓")
        except Exception as e:
            log(f"  ⚠️ {ds_name} 失败: {str(e)[:40]}")

    # 回归数据集
    regression_datasets = [
        ("Diabetes", load_diabetes),
    ]

    regressors = {
        "RandomForest": RandomForestRegressor(n_estimators=n_est, max_depth=max_depth, random_state=param_seed),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=n_est, random_state=param_seed),
        "Ridge": Ridge(alpha=ridge_alpha),
        "LinearRegression": LinearRegression(),
    }

    for ds_name, ds_loader in regression_datasets:
        try:
            X, y = ds_loader(return_X_y=True)
            for reg_name, reg in regressors.items():
                try:
                    pipe = Pipeline([("scaler", StandardScaler()), ("reg", reg)])
                    scores = cross_val_score(pipe, X, y, cv=5, scoring="r2")
                    results["regression"].append({
                        "dataset": ds_name,
                        "model": reg_name,
                        "r2_mean": round(float(scores.mean()), 4),
                        "r2_std": round(float(scores.std()), 4),
                        "params": f"n_est={n_est},alpha={ridge_alpha}" if reg_name == "Ridge" else f"n_est={n_est}",
                    })
                except:
                    pass
            results["datasets_used"].append(ds_name)
            log(f"  📈 {ds_name}: {len(X)}样本 ✓")
        except Exception as e:
            log(f"  ⚠️ {ds_name} 失败: {str(e)[:40]}")

    # 排名
    if results["classification"]:
        results["top_classifier"] = sorted(results["classification"], key=lambda x: x["accuracy_mean"], reverse=True)[:3]
    if results["regression"]:
        results["top_regressor"] = sorted(results["regression"], key=lambda x: x["r2_mean"], reverse=True)[:3]

    # P1-2: 更新历史并检查是否有改进
    improvements = update_ml_history(results, ev_count)
    if improvements:
        log(f"  📈 ML 改进: {' | '.join(improvements[:3])}")

    total = len(results["classification"]) + len(results["regression"])
    log(f"🧪 [ML] 完成: {total} 个模型×数据集组合, 数据集: {results['datasets_used']}")
    return results

# ================================================================
# P0-1: LLM 理解层 — 真正读懂论文
# ================================================================

# v7.1: 增强 JSON 解析 — 处理不完整 JSON、markdown 包裹、尾部逗号、双逗号等异常
def safe_json_parse(text, fallback=None):
    """鲁棒 JSON 解析，处理 LLM 返回的各种畸形 JSON"""
    if not text:
        return fallback
    # 尝试多级提取
    attempts = [
        text,                                                   # 原始文本
        re.sub(r'```(?:json)?\s*|\s*```', '', text),            # 去掉 markdown 代码块
        re.sub(r',\s*([}\]])', r'\1', text),                    # 移除尾部逗号
        re.sub(r',\s*,', ',', text),                            # 移除双逗号
        re.sub(r'[\s\S]*?(\{)', r'\1', text, count=1),          # 截取第一个 { 之前的内容
    ]
    for attempt in attempts:
        try:
            return json.loads(attempt)
        except (json.JSONDecodeError, TypeError):
            pass
    # 尝试提取第一个 JSON 对象
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        json_str = json_match.group()
        # 修复常见问题
        json_str = re.sub(r',\s*,', ',', json_str)               # 双逗号 → 单逗号
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)       # 尾部逗号
        json_str = re.sub(r'```(?:json)?\s*|\s*```', '', json_str)  # markdown
        json_str = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', json_str)  # 修复非法转义
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            log(f"⚠️ [JSON] 解析失败(pos {e.pos}): {str(e)[:80]} | 片段: ...{json_str[max(0,e.pos-20):e.pos+20]}...")
            # 尝试逐键修复 — 截断到最后一个完整的键值对
            for cutoff in range(len(json_str), max(e.pos, 10), -1):
                try:
                    truncated = json_str[:cutoff].rstrip().rstrip(',')
                    # 确保括号平衡
                    opens = truncated.count('{') + truncated.count('[')
                    closes = truncated.count('}') + truncated.count(']')
                    if opens > closes:
                        truncated += '}' * (opens - closes)
                    return json.loads(truncated)
                except:
                    continue
    return fallback

def llm_analyze_papers(papers):
    """使用 LLM 真正分析论文内容 — P0: 支持云端回退"""
    if not papers:
        return None

    # 选取前 5 篇论文进行深度分析
    sample = papers[:5]
    paper_texts = []
    for p in sample:
        paper_texts.append(f"标题: {p['title']}\n摘要: {p['summary'][:300]}\n---")

    prompt = f"""你是 Emily，一个 AI 研究助手。分析以下 arXiv 论文，提取关键信息。

{chr(10).join(paper_texts)}

请用 JSON 格式回答（只输出 JSON，不要其他文字）：
{{
  "key_innovations": ["最重要的3个创新点"],
  "emerging_trends": ["正在兴起的2个研究方向"],
  "techniques_mentioned": [
    {{"name": "技术名", "confidence": 0.8, "reason": "为什么值得关注"}}
  ],
  "suggested_focus": "建议 Emily 下一步重点研究什么方向",
  "papers_quality": "这些论文的整体质量和创新性评价（1-10）"
}}"""

    response, source = call_llm_smart(prompt, "你是一个专业的 AI 研究员，擅长分析机器学习论文。只输出 JSON。")
    if not response:
        log("⚠️ [LLM] 所有 LLM 后端不可用，使用关键词分析")
        return None

    if source:
        log(f"🧠 [LLM] 使用 {source} 分析论文...")

    analysis = safe_json_parse(response)
    if analysis:
        log(f"🧠 [LLM] 分析完成: {len(analysis.get('techniques_mentioned', []))} 个技术, 趋势: {analysis.get('emerging_trends', [])}")
        return analysis

    log(f"⚠️ [LLM] JSON 解析失败，使用原始响应 (前200字: {response[:200]})")
    return {"raw_response": response[:500], "key_innovations": [], "techniques_mentioned": []}

def llm_discover_techniques(arxiv_data):
    """LLM 驱动的技术发现（替代纯关键词匹配）"""
    log("🧠 [LLM理解层] 使用 LLM 分析论文发现技术...")

    papers = arxiv_data.get("papers", [])
    llm_analysis = llm_analyze_papers(papers)

    discovered = []
    library = load_technique_library()

    if llm_analysis and "techniques_mentioned" in llm_analysis:
        for tech in llm_analysis.get("techniques_mentioned", []):
            tech_name = tech.get("name", "").strip().lower()
            confidence = float(tech.get("confidence", 0.5))
            reason = tech.get("reason", "")

            # 检查是否已在技术库中
            existing = None
            for t in library:
                if any(kw.lower() in tech_name or tech_name in kw.lower() for kw in t.get("keywords", [])):
                    existing = t
                    break

            if existing:
                if not existing.get("adopted", False):
                    discovered.append({
                        "id": existing["id"],
                        "name": existing["name"],
                        "confidence": confidence,
                        "reason": reason,
                        "source": "llm",
                        "match_count": 1,
                    })
            elif confidence >= 0.5:
                # 新发现的技术
                new_id = f"llm-{tech_name.replace(' ', '-')[:30]}"
                new_tech = {
                    "id": new_id,
                    "name": tech.get("name", tech_name.title()),
                    "category": "llm_discovered",
                    "keywords": [tech_name],
                    "difficulty": "unknown",
                    "adopted": False,
                    "discovered_at": datetime.now().isoformat(),
                    "source_papers": [],
                    "implementation_notes": f"LLM发现: {reason}",
                }
                library.append(new_tech)
                discovered.append({
                    "id": new_id,
                    "name": new_tech["name"],
                    "confidence": confidence,
                    "reason": reason,
                    "source": "llm",
                    "match_count": 1,
                })

    # 回退：规则匹配作为补充
    if not discovered:
        log("  ℹ️ LLM 未发现新技术，使用规则匹配补充...")
        for paper in papers:
            text = (paper.get("title", "") + " " + paper.get("summary", "")).lower().replace("-", " ")
            for tech in library:
                if tech.get("adopted", False):
                    continue
                keywords = tech.get("keywords", [])
                match_count = sum(1 for kw in keywords if kw.lower().replace("-", " ") in text)
                # 阈值从 2 降为 1 — 预设库关键词已精心筛选，1 个匹配即有意义
                if match_count >= 1:
                    if tech["id"] not in [d["id"] for d in discovered]:
                        confidence = min(match_count / max(len(keywords), 1), 1.0)
                        # 单匹配给较低置信度，多匹配给较高置信度
                        if match_count == 1:
                            confidence = min(confidence, 0.4)
                        discovered.append({
                            "id": tech["id"],
                            "name": tech["name"],
                            "confidence": round(confidence, 2),
                            "match_count": match_count,
                            "source_paper": paper.get("title", ""),
                            "source": "keyword",
                        })

    # 白名单多词术语直接扫描（不依赖 top_keywords，解决 extract_keywords 只返回单词的问题）
    all_paper_text = " ".join(
        (p.get("title", "") + " " + p.get("summary", "")).lower().replace("-", " ") for p in papers
    )
    library_ids = set(t["id"] for t in library)
    for term in AI_ML_WHITELIST:
        if term in all_paper_text and f"auto-{term}" not in library_ids:
            # 检查是否已在 discovered 中
            if f"auto-{term}" not in [d["id"] for d in discovered]:
                discovered.append({
                    "id": f"auto-{term}",
                    "name": term.title(),
                    "confidence": 0.35,
                    "match_count": 1,
                    "source_paper": "(多论文文本扫描)",
                    "source": "whitelist_scan",
                })
                # 同时加入技术库供后续轮次使用
                library.append({
                    "id": f"auto-{term}",
                    "name": term.title(),
                    "category": "auto_discovered",
                    "keywords": term.split(),
                    "difficulty": "unknown",
                    "adopted": False,
                    "discovered_at": datetime.now().isoformat(),
                    "source": "whitelist_text_scan",
                    "implementation_notes": "自动发现（白名单文本扫描），待审核",
                })
                library_ids.add(f"auto-{term}")

    # 白名单关键词发现（兜底）
    if arxiv_data.get("top_keywords"):
        library_keywords = set()
        for tech in library:
            library_keywords.update(t.lower() for t in tech.get("keywords", []))
        new_kws = [kw for kw in arxiv_data.get("top_keywords", [])
                    if kw.lower() not in library_keywords and kw.lower() in AI_ML_WHITELIST]
        for kw in new_kws[:2]:
            new_tech = {
                "id": f"auto-{kw}",
                "name": kw.title(),
                "category": "auto_discovered",
                "keywords": [kw],
                "difficulty": "unknown",
                "adopted": False,
                "discovered_at": datetime.now().isoformat(),
                "source_papers": [],
                "implementation_notes": "自动发现（白名单），待审核",
            }
            library.append(new_tech)
            discovered.append({
                "id": new_tech["id"],
                "name": new_tech["name"],
                "confidence": 0.5,
                "source": "whitelist",
            })

    # 保存更新后的技术库（移到所有发现之后）
    if len(library) > len(DEFAULT_TECHNIQUE_LIBRARY):
        save_technique_library(library)

    log(f"🧠 [LLM理解层] 完成: 发现 {len(discovered)} 个技术 (LLM: {len([d for d in discovered if d.get('source')=='llm'])} | 规则: {len([d for d in discovered if d.get('source')!='llm'])})")
    append_evolution_log("understanding", {"discovered": discovered, "llm_used": llm_analysis is not None})
    return discovered

# ================================================================
# 决策层 — LLM + 规则混合
# ================================================================

def llm_decide(discovered_techniques, arxiv_data, hf_data):
    """LLM 辅助决策：哪些技术值得采用 — P0: 支持云端回退"""
    if not discovered_techniques:
        return None

    tech_summary = []
    for t in discovered_techniques[:5]:
        tech_summary.append(f"- {t.get('name', '')}: 信心度 {t.get('confidence', 0):.2f}, 来源 {t.get('source', 'unknown')}")

    hf_tasks = list((hf_data.get("task_distribution") or {}).keys())[:3] if hf_data else []

    prompt = f"""你是 Emily 的决策层。当前研究发现：

技术候选：
{chr(10).join(tech_summary)}

HuggingFace 热门任务: {', '.join(hf_tasks)}
已收集 {arxiv_data.get('total_papers', 0)} 篇论文

请用 JSON 回答（只输出 JSON）：
{{
  "should_adopt": ["应该立刻采用的技术名"],
  "should_watch": ["应该持续观察的技术名"],
  "should_skip": ["不建议采用的技术名"],
  "reasoning": "决策理由（1-2句话）",
  "priority_focus": "下一步应该重点研究什么方向"
}}"""

    response, source = call_llm_smart(prompt, "你是 Emily 的决策层。用 JSON 格式输出决策。")
    if not response:
        return None

    decision = safe_json_parse(response)
    if decision:
        return decision
    return None

def decide_evolution(discovered_techniques, arxiv_data, hf_data):
    """混合决策：LLM 优先，规则兜底"""
    log("🤔 [决策层] LLM + 规则混合决策...")
    adopted = load_adopted_techniques()
    config = load_evolution_config()
    decisions = []

    # 先尝试 LLM 决策
    llm_decision = llm_decide(discovered_techniques, arxiv_data, hf_data)

    tech_map = {t["id"]: t for t in discovered_techniques}

    for tech in discovered_techniques:
        tech_id = tech["id"]
        confidence = tech.get("confidence", 0)
        is_auto = tech.get("source") in ("whitelist", "auto_discovered")
        action = "skip"
        should_adopt = False
        reason = []

        # LLM 决策优先
        if llm_decision:
            tech_name = tech.get("name", "").lower()
            adopt_list = [a.lower() for a in llm_decision.get("should_adopt", [])]
            watch_list = [w.lower() for w in llm_decision.get("should_watch", [])]
            skip_list = [s.lower() for s in llm_decision.get("should_skip", [])]

            if any(ad in tech_name or tech_name in ad for ad in adopt_list):
                should_adopt = True
                action = "adopt"
                reason.append(f"LLM建议采用")
            elif any(wa in tech_name or tech_name in wa for wa in watch_list):
                action = "watch"
                reason.append("LLM建议观察")
            elif any(sk in tech_name or tech_name in sk for sk in skip_list):
                action = "skip"
                reason.append("LLM建议跳过")

        # 规则兜底
        if action == "skip" and not any("LLM" in r for r in reason):
            if is_auto:
                if confidence >= 0.7:
                    should_adopt = True; action = "adopt"
                    reason.append(f"高信心度({confidence:.1f})")
                elif confidence >= 0.5:
                    action = "watch"
                    reason.append(f"中等信心度({confidence:.1f})")
                else:
                    reason.append("信心度不足")
            else:
                if confidence >= 0.5:
                    should_adopt = True; action = "adopt"
                    reason.append(f"预置技术({confidence:.1f})")
                elif confidence >= 0.3:
                    action = "watch"
                    reason.append(f"持续观察({confidence:.1f})")

        # 多篇论文提及升级
        if tech.get("match_count", 0) >= 2 and action == "watch":
            action = "adopt"; should_adopt = True
            reason.append(f"多篇提及({tech['match_count']}篇)→升级")

        decision = {
            "tech_id": tech_id,
            "tech_name": tech.get("name", ""),
            "action": action,
            "confidence": confidence,
            "reason": reason,
            "decided_at": datetime.now().isoformat(),
        }
        decisions.append(decision)

        if action == "adopt" and should_adopt:
            if tech_id not in [a["id"] for a in adopted["adopted"]]:
                log(f"  ✅ 采用: {tech.get('name', '')} ({'; '.join(reason)})")
            else:
                decision["action"] = "already_adopted"
                log(f"  ℹ️ 已采用: {tech.get('name', '')}")

    log(f"🤔 [决策层] 完成: {len([d for d in decisions if d['action']=='adopt'])}采用 | {len([d for d in decisions if d['action']=='watch'])}观察")
    append_evolution_log("decision", {"decisions": decisions, "llm_used": llm_decision is not None})
    return decisions

# ================================================================
# 行动层 — 采用技术 + 自修改
# ================================================================

def load_technique_library():
    """加载技术库: 合并预设条目 + 文件中的自动发现条目"""
    file_library = []
    if os.path.exists(TECHNIQUE_LIBRARY_PATH):
        try:
            with open(TECHNIQUE_LIBRARY_PATH, "r", encoding="utf-8") as f:
                file_library = json.load(f)
        except:
            pass
    # 合并: 预设条目始终存在 + 文件中非预设的条目
    default_ids = set(d["id"] for d in DEFAULT_TECHNIQUE_LIBRARY)
    result = list(DEFAULT_TECHNIQUE_LIBRARY)
    for t in file_library:
        if t.get("id", "") not in default_ids:
            result.append(t)
    return result

def save_technique_library(library):
    with open(TECHNIQUE_LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(library, f, ensure_ascii=False, indent=2)

def load_adopted_techniques():
    if os.path.exists(ADOPTED_TECHNIQUES_PATH):
        try:
            with open(ADOPTED_TECHNIQUES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"adopted": [], "history": []}

def save_adopted_techniques(data):
    with open(ADOPTED_TECHNIQUES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def adopt_technique(decisions):
    """执行技术采用"""
    log("🛠️ [行动层] 执行采用决策...")
    adopted = load_adopted_techniques()
    library = load_technique_library()
    actions_taken = []

    for decision in decisions:
        if decision["action"] != "adopt":
            continue
        tech_id = decision["tech_id"]

        if tech_id not in [a["id"] for a in adopted["adopted"]]:
            adopted["adopted"].append({
                "id": tech_id,
                "name": decision["tech_name"],
                "adopted_at": datetime.now().isoformat(),
                "decision": decision,
            })
            adopted["history"].append({
                "event": "adopted",
                "tech_id": tech_id,
                "tech_name": decision["tech_name"],
                "timestamp": datetime.now().isoformat(),
            })
            actions_taken.append(f"采用 {decision['tech_name']}")

        for tech in library:
            if tech["id"] == tech_id:
                tech["adopted"] = True
                tech["adopted_at"] = datetime.now().isoformat()
                break

    save_adopted_techniques(adopted)
    save_technique_library(library)

    log(f"🛠️ [行动层] 完成: {len(actions_taken)} 个行动")
    for a in actions_taken:
        log(f"  → {a}")
    append_evolution_log("action", {"actions_taken": actions_taken})
    return actions_taken

# ================================================================
# P1-1: 代码自修改
# ================================================================

def self_modify(new_techniques):
    """
    代码自修改：如果采用的新技术足够多（>=2），尝试生成新版本
    在沙盒中测试，通过后才替换 — P0: 支持云端LLM
    """
    if len(new_techniques) < 2:
        log("🔧 [自修改] 新采用技术不足2个，跳过代码自修改")
        return {"status": "skipped", "reason": "insufficient_new_techniques"}

    log(f"🔧 [自修改] 尝试基于 {len(new_techniques)} 个新技术生成改进...")

    tech_names = ", ".join(new_techniques)

    prompt = f"""你是 Emily 的代码自修改模块。当前采用了这些新技术：{tech_names}。

以下是当前 evolution-station.py 的代码结构摘要（不是完整代码）：
- 代码约 1050 行
- 模块化结构：感知层 / 理解层(LLM) / 决策层 / 行动层 / 验证层
- 使用 sklearn, urllib, base64, json 等标准库
- 通过 arXiv API 获取论文，通过 GitHub API 推送结果

基于这些新技术，你能建议一个 Python 代码片段（不超过 50 行），可以增强 evolution-station.py 的能力。只输出纯 Python 代码，不要解释。代码应该是一个可以直接插入到 evolve() 函数中的函数调用。"""

    response, source = call_llm_smart(prompt, "你是代码生成专家。只输出 Python 代码，不要任何解释。", timeout_sec=90)
    if not response:
        log("🔧 [自修改] LLM 不可用，跳过代码自修改")
        return {"status": "skipped", "reason": "no_llm"}

    if not response or response.startswith("[LLM_ERROR"):
        log(f"🔧 [自修改] LLM 响应无效，跳过")
        return {"status": "skipped", "reason": "llm_error"}

    # 写入沙盒
    sandbox_file = os.path.join(SANDBOX_DIR, f"evolution-candidate-{datetime.now().strftime('%Y%m%d-%H%M%S')}.patch.py")
    try:
        with open(sandbox_file, "w", encoding="utf-8") as f:
            f.write(f"# Auto-generated code snippet by Emily Self-Modify\n")
            f.write(f"# Based on: {tech_names}\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            f.write(response)

        # 语法检查
        result = subprocess.run(
            [sys.executable, "-c", f"import py_compile; py_compile.compile(r'{sandbox_file}', doraise=True); print('OK')"],
            capture_output=True, text=True, timeout=10
        )
        syntax_ok = "OK" in (result.stdout + result.stderr)

        if syntax_ok:
            log(f"🔧 [自修改] 语法检查通过 → 存入沙盒: {os.path.basename(sandbox_file)}")
            return {"status": "sandboxed", "file": sandbox_file, "techniques": new_techniques,
                    "syntax_check": "passed"}
        else:
            log(f"🔧 [自修改] 语法检查失败: {result.stderr[:100]}")
            return {"status": "failed", "reason": "syntax_error", "error": result.stderr[:100]}

    except Exception as e:
        log(f"🔧 [自修改] 异常: {str(e)[:60]}")
        return {"status": "failed", "reason": str(e)[:60]}

# ================================================================
# 验证层
# ================================================================

def load_evolution_config():
    config_path = os.path.join(HOME, "evolution-config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    default = {"version": "6.2", "auto_evolution_enabled": True,
               "evolution_interval_hours": 2, "adopted_techniques": [],
               "last_evolution": "", "total_evolutions": 0}
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(default, f, ensure_ascii=False, indent=2)
    return default

def save_evolution_config(config):
    config_path = os.path.join(HOME, "evolution-config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def validate_evolution(evolve_result_before, evolve_result_after):
    """验证进退化前后的效果"""
    log("🔬 [验证层] 对比进退化前后...")
    validation = {"metrics": {}, "passed": True, "notes": []}

    arxiv_before = evolve_result_before.get("research", {}).get("arxiv", {})
    arxiv_after = evolve_result_after.get("research", {}).get("arxiv", {})
    bp = arxiv_before.get("total_papers", 0)
    ap = arxiv_after.get("total_papers", 0)
    validation["metrics"]["papers_before"] = bp
    validation["metrics"]["papers_after"] = ap

    ml_before = evolve_result_before.get("research", {}).get("ml_benchmarks", {})
    ml_after = evolve_result_after.get("research", {}).get("ml_benchmarks", {})
    bm = len(ml_before.get("classification", [])) + len(ml_before.get("regression", []))
    am = len(ml_after.get("classification", [])) + len(ml_after.get("regression", []))
    validation["metrics"]["ml_before"] = bm
    validation["metrics"]["ml_after"] = am

    # 种子状态（排除元数据字段如 _rotation_idx）
    seed_state = load_seed_state()
    seed_vals = [s for s in seed_state.values() if isinstance(s, dict) and "watering_count" in s]
    total_watered = sum(s["watering_count"] for s in seed_vals)
    total_papers_found = sum(s["total_papers_found"] for s in seed_vals)
    validation["metrics"]["seeds_watered_total"] = total_watered
    validation["metrics"]["seeds_papers_total"] = total_papers_found

    # 多源感知
    ms = evolve_result_after.get("research", {}).get("multi_source", {})
    validation["metrics"]["github_repos"] = len(ms.get("github_trending", []))
    validation["metrics"]["pwc_papers"] = len(ms.get("paperswithcode", []))

    if validation["passed"]:
        log(f"✅ [验证层] 通过！论文:{ap} | ML:{am} | 种子浇水:{total_watered}次/{total_papers_found}篇 | GH:{validation['metrics']['github_repos']} | PWC:{validation['metrics']['pwc_papers']}")
    else:
        log(f"⚠️ [验证层] 警告: {validation['notes']}")

    append_evolution_log("validation", validation)
    return validation

# ================================================================
# P2-1: 记忆提炼
# ================================================================

def distill_memory():
    """每 24 轮提炼知识库，提取跨 session 模式"""
    global _distill_counter
    _distill_counter += 1

    if _distill_counter % 24 != 0:
        return None

    log("🧠 [记忆提炼] 开始提炼 24 轮进化数据...")

    if not os.path.exists(KNOWLEDGE_PATH):
        return None

    try:
        with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
            kb = json.load(f)
    except:
        return None

    sessions = kb.get("sessions", [])
    if len(sessions) < 10:
        return None

    # 统计
    all_keywords = []
    for s in sessions[-24:]:
        all_keywords.extend(s.get("arxiv_top_keywords", []))

    keyword_trends = Counter(all_keywords).most_common(10)

    # LLM 提炼（如果可用）
    ollama_ok, _ = check_ollama()
    llm_summary = ""
    if ollama_ok:
        summary_text = f"最近 24 轮进化中，最热门关键词: {dict(keyword_trends[:5])}"
        prompt = f"根据以下数据，用1-2句话总结 Emily 最近的研究发现和进化方向：{summary_text}"
        llm_summary = call_ollama(prompt, "你是数据分析专家。简洁总结。", timeout_sec=30)
        if llm_summary.startswith("[LLM_ERROR"):
            llm_summary = ""

    distill = {
        "timestamp": datetime.now().isoformat(),
        "sessions_distilled": len(sessions[-24:]),
        "top_keyword_trends": dict(keyword_trends),
        "llm_summary": llm_summary,
        "total_adopted": len(load_adopted_techniques().get("adopted", [])),
        "total_evolutions": load_evolution_state().get("total_evolutions", 0),
    }

    # 保存提炼结果
    all_distills = []
    if os.path.exists(MEMORY_DISTILL_PATH):
        try:
            with open(MEMORY_DISTILL_PATH, "r", encoding="utf-8") as f:
                all_distills = json.load(f)
        except:
            pass
    all_distills.append(distill)
    if len(all_distills) > 20:
        all_distills = all_distills[-20:]
    with open(MEMORY_DISTILL_PATH, "w", encoding="utf-8") as f:
        json.dump(all_distills, f, ensure_ascii=False, indent=2)

    log(f"🧠 [记忆提炼] 完成: 提炼 {distill['sessions_distilled']} 条, 趋势: {dict(list(keyword_trends)[:3])}")
    return distill

# ================================================================
# P2-1: 进化自我意识 — 每轮自评模块
# ================================================================

SELF_AWARENESS_PATH = os.path.join(DATA_DIR, "station-self-awareness.json")

def run_self_awareness(evolution, arxiv_data, seed_result, ml_data, ev_count):
    """进化后的自评：检测僵化、追踪增量、生成健康报告"""
    awareness = {
        "evolution": ev_count,
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    # 1. 关键词僵化检测
    kb_data = {}
    if os.path.exists(KNOWLEDGE_PATH):
        try:
            with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
                kb_data = json.load(f)
        except:
            pass
    sessions = kb_data.get("sessions", [])
    if len(sessions) >= 5:
        recent_kws = [tuple(sorted(s.get("arxiv_top_keywords", [])[:5])) for s in sessions[-5:]]
        unique_sets = len(set(recent_kws))
        stale_score = (5 - unique_sets) / 5  # 0 = 完全多样化, 1 = 完全僵化
        awareness["checks"]["keyword_staleness"] = {
            "score": round(stale_score, 2),
            "unique_recent_sets": unique_sets,
            "status": "healthy" if stale_score < 0.4 else "warning" if stale_score < 0.7 else "critical",
        }

    # 2. 技术采用率检测
    adopted = load_adopted_techniques()
    total_adopted = len(adopted.get("adopted", []))
    # 修复: discovered 存储在 evolution["evolution"]["discovered"]，不是顶层
    ev_inner = evolution.get("evolution", {})
    discovered = len(ev_inner.get("discovered", []))
    awareness["checks"]["adoption_rate"] = {
        "total_adopted": total_adopted,
        "discovered_this_round": discovered,
        "status": "critical" if total_adopted == 0 and ev_count > 50 else
                  "warning" if total_adopted == 0 else "healthy",
        "message": f"已采用 {total_adopted} / {discovered} 技术采用率" if total_adopted == 0 else
                   f"已采用 {total_adopted} / {discovered} 个技术",
    }

    # 3. 种子增长率
    seed_state = load_seed_state()
    seed_vals = {k: v for k, v in seed_state.items() if isinstance(v, dict) and "watering_count" in v}
    growing = sum(1 for s in seed_vals.values() if s.get("total_papers_found", 0) > 0)
    never_watered = [s["name"] for s in seed_vals.values() if s.get("watering_count", 0) == 0]
    awareness["checks"]["seed_growth"] = {
        "growing_seeds": growing,
        "total_seeds": len(seed_vals),
        "never_watered": never_watered,
        "status": "healthy" if growing >= 5 else "warning" if growing >= 3 else "critical",
    }

    # 4. ML 实验进步
    ml_history = load_ml_history()
    improvements = len(ml_history.get("history", []))
    awareness["checks"]["ml_progress"] = {
        "improvements_recorded": improvements,
        "status": "healthy" if improvements > 0 else "info",
    }

    # 5. 论文增量 (本轮 vs 历史平均)
    total_papers_this = arxiv_data.get("total_papers", 0)
    papers_history = [s.get("arxiv_papers_count", 0) for s in sessions[-10:]] if sessions else []
    avg_papers = sum(papers_history) / max(len(papers_history), 1)
    awareness["checks"]["paper_inflow"] = {
        "this_round": total_papers_this,
        "recent_avg": round(avg_papers, 1),
        "status": "healthy" if total_papers_this > 0 else "warning",
    }

    # 综合状态
    criticals = sum(1 for c in awareness["checks"].values() if c.get("status") == "critical")
    warnings = sum(1 for c in awareness["checks"].values() if c.get("status") == "warning")
    if criticals > 0:
        awareness["overall"] = "critical"
        awareness["summary"] = f"🔴 存在 {criticals} 个严重问题需立即处理"
    elif warnings > 1:
        awareness["overall"] = "warning"
        awareness["summary"] = f"🟡 {warnings} 个警告事项需关注"
    else:
        awareness["overall"] = "healthy"
        awareness["summary"] = "🟢 所有指标正常，进化稳定推进"

    # 保存
    all_awareness = []
    if os.path.exists(SELF_AWARENESS_PATH):
        try:
            with open(SELF_AWARENESS_PATH, "r", encoding="utf-8") as f:
                all_awareness = json.load(f)
        except:
            pass
    all_awareness.append(awareness)
    if len(all_awareness) > 50:
        all_awareness = all_awareness[-50:]
    with open(SELF_AWARENESS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_awareness, f, ensure_ascii=False, indent=2)

    log(f"🪞 [自我意识] {awareness['summary']} | 关键词僵化:{awareness['checks'].get('keyword_staleness',{}).get('score',0):.0%} | 种子活跃度:{growing}/{len(seed_vals)}")
    return awareness

# ================================================================
# P2-2: 种子间知识交叉引用
# ================================================================

CROSSREF_PATH = os.path.join(DATA_DIR, "station-crossref.json")

def run_seed_cross_reference():
    """基于关键词重叠，自动发现种子间的概念连接"""
    seed_state = load_seed_state()
    seed_vals = {k: v for k, v in seed_state.items() if isinstance(v, dict) and "keywords" in v}

    if len(seed_vals) < 2:
        return None

    # 收集每颗种子最近收集的论文标题和关键词
    connections = []
    seed_papers = {}

    for sid, sdata in seed_vals.items():
        papers = []
        for h in sdata.get("history", [])[-3:]:  # 最近3次浇水
            for p in h.get("papers", []):
                papers.append(p.get("title", ""))
        seed_papers[sid] = {
            "name": sdata["name"],
            "keywords": set(sdata.get("keywords", [])),
            "recent_paper_keywords": set(),
        }
        for paper_text in papers:
            words = set(re.findall(r"[a-zA-Z]{4,}", paper_text.lower()))
            seed_papers[sid]["recent_paper_keywords"] |= words

    # 查找种子间重叠
    seed_ids = list(seed_papers.keys())
    for i in range(len(seed_ids)):
        for j in range(i + 1, len(seed_ids)):
            a = seed_papers[seed_ids[i]]
            b = seed_papers[seed_ids[j]]

            # 原始关键词重叠
            kw_overlap = a["keywords"] & b["keywords"]
            # 论文内容关键词重叠
            paper_overlap = a["recent_paper_keywords"] & b["recent_paper_keywords"]

            if kw_overlap or paper_overlap:
                connections.append({
                    "seed_a": a["name"],
                    "seed_b": b["name"],
                    "shared_keywords": sorted(kw_overlap)[:5],
                    "shared_paper_concepts": sorted(paper_overlap)[:8],
                    "strength": len(kw_overlap) * 2 + len(paper_overlap),
                    "discovered_at": datetime.now().isoformat(),
                })

    connections.sort(key=lambda x: x["strength"], reverse=True)

    # 保存
    crossref = {
        "timestamp": datetime.now().isoformat(),
        "connections": connections[:10],
        "total_seeds": len(seed_vals),
    }
    with open(CROSSREF_PATH, "w", encoding="utf-8") as f:
        json.dump(crossref, f, ensure_ascii=False, indent=2)

    if connections:
        top = connections[0]
        log(f"🔗 [交叉引用] 发现 {len(connections)} 个种子间连接 | 最强: {top['seed_a']} ↔ {top['seed_b']} (强度{top['strength']})")

    return crossref

# ================================================================
# v9.0: 假設引擎 — 從聚合器到思考者
# ================================================================

def load_hypotheses():
    """載入假設記錄"""
    if os.path.exists(HYPOTHESES_PATH):
        try:
            with open(HYPOTHESES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"hypotheses": [], "last_updated": "", "total_generated": 0, "total_verified": 0}

def save_hypotheses(data):
    """保存假設記錄"""
    data["last_updated"] = datetime.now().isoformat()
    with open(HYPOTHESES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_hypotheses(crossref_data, seed_state):
    """v9.0: 假設引擎 — 基於種子交叉引用 + LLM 生成可驗證研究假設

    輸入:
      - crossref_data: run_seed_cross_reference() 的輸出 (含 connections 列表)
      - seed_state: 各種子的澆水歷史與最近論文

    輸出: 新生成的假設列表
    策略: 只對未生成過假設的強交叉引用 (strength>=3) 生成，避免重複
    """
    if not crossref_data or not crossref_data.get("connections"):
        return []

    existing = load_hypotheses()
    existing_pairs = set()
    for h in existing.get("hypotheses", []):
        pair = tuple(sorted([h.get("seed_a", ""), h.get("seed_b", "")]))
        existing_pairs.add(pair)

    # 收集各種子最近論文摘要（作為 LLM 上下文）
    seed_summaries = {}
    seed_vals = {k: v for k, v in seed_state.items() if isinstance(v, dict) and "keywords" in v}
    for sid, sdata in seed_vals.items():
        recent_papers = []
        for h in sdata.get("history", [])[-2:]:  # 最近2次澆水
            for p in h.get("papers", []):
                recent_papers.append({
                    "title": p.get("title", "")[:150],
                    "summary": p.get("summary", "")[:300]
                })
        if recent_papers:
            seed_summaries[sdata["name"]] = recent_papers[:3]
    seed_context = "\n".join([
        f"- {name}: " + "; ".join([p["title"][:80] for p in papers])
        for name, papers in list(seed_summaries.items())[:6]
    ])

    new_hypotheses = []
    candidates = [c for c in crossref_data["connections"][:5]
                  if c["strength"] >= 3
                  and tuple(sorted([c["seed_a"], c["seed_b"]])) not in existing_pairs]

    for conn in candidates:
        # 構建 LLM prompt — 讓模型在跨領域交叉中發現研究假設
        prompt = f"""你是 AI 研究科學家。以下是你發現的兩個 AI 研究方向之間的交叉連接：

研究方向 A: {conn['seed_a']}
研究方向 B: {conn['seed_b']}
共享關鍵詞: {', '.join(conn.get('shared_keywords', [])[:8])}
共享論文概念: {', '.join(conn.get('shared_paper_concepts', [])[:10])}
連接強度: {conn['strength']} (關鍵詞重疊×2 + 概念重疊)

最近相關論文方向：
{seed_context[:800]}

請思考：這兩個方向如果結合，會產生什麼突破？然後輸出以下 JSON：
{{
  "hypothesis": "一個具體、可驗證的研究假設 (1-2句，英文或繁中均可)",
  "reasoning": "推理邏輯：為什麼這兩個方向可以結合？背後的數學/架構共通點是什麼？(2-3句)",
  "arxiv_query": "用於在 arXiv 上搜索驗證論文的查詢字串 (英文，5-10個詞)",
  "potential_breakthrough": "這個結合可能帶來的突破 (1句話)"
}}

輸出必須是嚴格 JSON，不要用 markdown 包裹。"""

        result, source = call_llm_smart(
            prompt,
            system_prompt="你是頂尖 AI 研究科學家，專注於跨領域概念連接與假設生成。輸出必須是嚴格 JSON。",
            timeout_sec=90
        )

        if result:
            try:
                cleaned = result.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r'^```\w*\n?', '', cleaned)
                    cleaned = re.sub(r'\n?```$', '', cleaned)
                hyp_data = json.loads(cleaned)

                hypothesis = {
                    "id": f"hyp-{existing['total_generated'] + len(new_hypotheses) + 1:04d}",
                    "timestamp": datetime.now().isoformat(),
                    "seed_a": conn["seed_a"],
                    "seed_b": conn["seed_b"],
                    "crossref_strength": conn["strength"],
                    "shared_keywords": conn.get("shared_keywords", [])[:5],
                    "hypothesis": hyp_data.get("hypothesis", ""),
                    "reasoning": hyp_data.get("reasoning", ""),
                    "arxiv_query": hyp_data.get("arxiv_query",
                        " OR ".join(conn.get("shared_keywords", ["neural network"])[:3])),
                    "potential_breakthrough": hyp_data.get("potential_breakthrough", ""),
                    "status": "unverified",
                    "verification_rounds": 0,
                    "supporting_papers": [],
                    "refuting_papers": [],
                    "llm_source": source,
                }
                new_hypotheses.append(hypothesis)
                log(f"💡 [假設引擎] #{hypothesis['id']} {hypothesis['hypothesis'][:70]}...")
            except json.JSONDecodeError:
                log(f"⚠️ [假設引擎] LLM 返回非 JSON（{conn['seed_a']}↔{conn['seed_b']}），跳過")

    if new_hypotheses:
        existing["hypotheses"].extend(new_hypotheses)
        existing["total_generated"] = existing.get("total_generated", 0) + len(new_hypotheses)
        save_hypotheses(existing)
        log(f"🧪 [假設引擎] 本輪生成 {len(new_hypotheses)} 個新假設 | 累計 {existing['total_generated']} 個")

    return new_hypotheses

def verify_hypothesis(hypothesis):
    """v9.0: 假設驗證 — 用 arXiv 搜索 + LLM 判斷論文是支持還是推翻假設

    流程:
      1. 用假設的 arxiv_query 搜索相關論文 (max 5)
      2. LLM 評估每篇論文對假設的態度 (supporting / refuting / neutral)
      3. 返回分類結果
    """
    query = hypothesis.get("arxiv_query", "machine learning")
    encoded = urllib.parse.quote(query, safe='')
    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query={encoded}&"
        f"sortBy=relevance&"
        f"max_results=5"
    )

    try:
        resp = retry_request(url, headers={"User-Agent": f"Emily/{VERSION}"}, timeout=20, max_retries=2)
        xml_data = resp.read().decode("utf-8")
    except Exception as e:
        return {"status": "search_failed", "error": str(e)[:80], "papers_found": 0}

    papers = []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(xml_data)
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            link_el = entry.find("atom:id", ns)
            papers.append({
                "title": title_el.text.strip()[:200] if title_el is not None and title_el.text else "",
                "summary": summary_el.text.strip()[:400] if summary_el is not None and summary_el.text else "",
                "url": link_el.text.strip() if link_el is not None and link_el.text else "",
            })
    except:
        pass

    if not papers:
        return {"status": "no_papers_found", "papers_found": 0}

    # LLM 判斷論文態度
    paper_text = "\n\n".join([
        f"[論文 {i+1}] 標題: {p['title']}\n摘要: {p['summary'][:250]}"
        for i, p in enumerate(papers[:4])
    ])

    eval_prompt = f"""你是 AI 研究評審。以下是待驗證的假設與搜索到的相關論文。

假設: {hypothesis.get('hypothesis', '')}

推理背景: {hypothesis.get('reasoning', '')[:200]}

相關論文:
{paper_text}

請對每篇論文分類（輸出嚴格 JSON）：
{{
  "evaluations": [
    {{"paper_index": 1, "verdict": "supporting|refuting|neutral", "reason": "一句話解釋 (繁中)"}},
    ...
  ]
}}

分類標準:
- supporting: 論文中的方法/發現與假設一致，或直接支持假設的可行性
- refuting: 論文中的結果/理論與假設矛盾，或證明假設不可行
- neutral: 論文與假設無直接關係，僅有表面關鍵詞重疊"""

    result, _ = call_llm_smart(
        eval_prompt,
        system_prompt="你是嚴謹的 AI 研究評審。只根據論文內容判斷，不要臆測。輸出嚴格 JSON。",
        timeout_sec=60
    )

    supporting = []
    refuting = []

    if result:
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```\w*\n?', '', cleaned)
                cleaned = re.sub(r'\n?```$', '', cleaned)
            evals = json.loads(cleaned)

            for pe in evals.get("evaluations", []):
                idx = pe.get("paper_index", 0) - 1
                if 0 <= idx < len(papers):
                    info = {
                        "title": papers[idx]["title"],
                        "url": papers[idx]["url"],
                        "reason": pe.get("reason", ""),
                    }
                    v = pe.get("verdict", "neutral")
                    if v == "supporting":
                        supporting.append(info)
                    elif v == "refuting":
                        refuting.append(info)
        except (json.JSONDecodeError, KeyError):
            log(f"⚠️ [假設驗證] LLM 評審結果解析失敗，僅記錄論文")

    return {
        "status": "verified",
        "papers_found": len(papers),
        "supporting_count": len(supporting),
        "refuting_count": len(refuting),
        "supporting_papers": supporting,
        "refuting_papers": refuting,
        "verified_at": datetime.now().isoformat(),
    }

def run_hypothesis_engine(crossref_data, ev_count):
    """v9.0: 假設引擎總控 — 協調生成與驗證

    執行策略（成本控制）：
      - 生成: 每 5 輪進化 + 有新交叉引用時觸發 (LLM 成本: ~1 次/5輪)
      - 驗證: 每輪驗證 1 個最舊的未驗證假設 (LLM 成本: ~1 次/輪)
      - 每年預估呼叫: ~9,500 次 (含基礎 LLM 調用)
    """
    result = {
        "new_hypotheses": [],
        "verified_hypothesis": None,
        "total_hypotheses": 0,
        "total_verified": 0,
    }

    seed_state = load_seed_state()

    # === 生成新假設 (每 5 輪觸發一次) ===
    if ev_count % 5 == 0 and crossref_data and crossref_data.get("connections"):
        new = generate_hypotheses(crossref_data, seed_state)
        if new:
            result["new_hypotheses"] = [h["id"] for h in new]

    # === 驗證最舊的未驗證假設 ===
    hypotheses_data = load_hypotheses()
    unverified = [h for h in hypotheses_data.get("hypotheses", [])
                  if h.get("status") == "unverified"]

    if unverified:
        # 優先驗證驗證次數最少的 (輪換策略)
        unverified.sort(key=lambda h: h.get("verification_rounds", 0))
        target = unverified[0]
        hyp_id = target["id"]

        log(f"🔍 [假設驗證] 驗證中: {hyp_id} (第{target['verification_rounds']+1}輪)")

        verification = verify_hypothesis(target)
        target["verification_rounds"] = target.get("verification_rounds", 0) + 1

        if verification.get("supporting_papers"):
            target["supporting_papers"].extend(verification["supporting_papers"])
        if verification.get("refuting_papers"):
            target["refuting_papers"].extend(verification["refuting_papers"])

        # 判斷最終狀態
        sup_count = len(target.get("supporting_papers", []))
        ref_count = len(target.get("refuting_papers", []))
        total_evidence = sup_count + ref_count

        if total_evidence >= 5 or target["verification_rounds"] >= 3:
            if sup_count > ref_count * 1.5:
                target["status"] = "supported"
                log(f"✅ [假設驗證] {hyp_id} → SUPPORTED ({sup_count}支持 / {ref_count}反對)")
            elif ref_count > sup_count * 1.5:
                target["status"] = "refuted"
                log(f"❌ [假設驗證] {hyp_id} → REFUTED ({sup_count}支持 / {ref_count}反對)")
            else:
                target["status"] = "inconclusive"
                log(f"🤷 [假設驗證] {hyp_id} → INCONCLUSIVE ({sup_count}支持 / {ref_count}反對)")

        result["verified_hypothesis"] = {
            "id": hyp_id,
            "verification_round": target["verification_rounds"],
            "supporting": sup_count,
            "refuting": ref_count,
            "status": target["status"],
        }

        hypotheses_data["total_verified"] = sum(
            1 for h in hypotheses_data["hypotheses"] if h.get("status") != "unverified")
        save_hypotheses(hypotheses_data)

    result["total_hypotheses"] = len(hypotheses_data.get("hypotheses", []))
    result["total_verified"] = hypotheses_data.get("total_verified", 0)

    if result["total_hypotheses"] > 0:
        statuses = Counter(h["status"] for h in hypotheses_data["hypotheses"])
        log(f"🧪 [假設引擎] 累計 {result['total_hypotheses']} 個假設 | "
            f"已驗證 {result['total_verified']} | "
            f"支持 {statuses.get('supported', 0)} / 推翻 {statuses.get('refuted', 0)} / "
            f"待定 {statuses.get('inconclusive', 0)} / 未驗證 {statuses.get('unverified', 0)}")

    return result

# ================================================================
# v9.1: 实验设计引擎 — 对已验证假设设计最小 sklearn 对比实验
# ================================================================

def load_experiments():
    """加载实验记录"""
    if os.path.exists(EXPERIMENTS_PATH):
        try:
            with open(EXPERIMENTS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"experiments": [], "total_experiments": 0, "last_updated": ""}

def save_experiments(data):
    """保存实验记录"""
    data["last_updated"] = datetime.now().isoformat()
    with open(EXPERIMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def design_experiment(hypothesis):
    """v9.1: 实验设计 — 为已验证假设设计最小可行 sklearn 对比实验

    输入: 一个已验证 (supported) 的假设
    输出: 实验设计 dict，包含数据集、算法对比、评估指标
    """
    # 根据假设涉及的方向自动选择数据集
    keywords_concat = " ".join(hypothesis.get("shared_keywords", []) +
                               [hypothesis.get("seed_a", ""), hypothesis.get("seed_b", "")]).lower()

    # 根据关键词映射合适的数据集
    dataset_map = {
        "classification": "Iris", "classify": "Iris",
        "image": "MNIST-digits", "vision": "MNIST-digits", "cv": "MNIST-digits",
        "text": "20Newsgroups-subset", "nlp": "20Newsgroups-subset", "language": "20Newsgroups-subset",
        "regression": "Diabetes", "predict": "Diabetes",
        "cluster": "make_blobs", "unsupervised": "make_blobs",
        "time": "synthetic-timeseries", "sequence": "synthetic-timeseries", "series": "synthetic-timeseries",
    }
    dataset_name = "Iris"
    for kw, ds in dataset_map.items():
        if kw in keywords_concat:
            dataset_name = ds
            break

    # 根据方向选择对比算法
    algo_map = {
        "mamba": ["LogisticRegression", "RandomForest"],
        "moe": ["RandomForest", "GradientBoosting"],
        "gnn": ["DecisionTree", "RandomForest"],
        "liquid": ["KNeighbors", "RandomForest"],
        "attention": ["LogisticRegression", "SVM"],
        "transformer": ["LogisticRegression", "SVM"],
        "kv": ["LogisticRegression", "RandomForest"],
        "sparse": ["LogisticRegression", "SVM"],
        "continual": ["SGDClassifier", "KNeighbors"],
        "default": ["LogisticRegression", "RandomForest"],
    }
    algos = algo_map.get("default")
    for kw, al in algo_map.items():
        if kw in keywords_concat:
            algos = al
            break

    experiment = {
        "id": f"exp-{hypothesis['id']}",
        "hypothesis_id": hypothesis["id"],
        "hypothesis_text": hypothesis.get("hypothesis", "")[:150],
        "dataset": dataset_name,
        "algorithms": algos,
        "metric": "accuracy",
        "cross_val": 5,
        "designed_at": datetime.now().isoformat(),
        "status": "designed",
    }
    return experiment

def execute_experiment(experiment_design):
    """v9.1: 执行实验 — 使用 sklearn 运行对比实验并记录结果"""
    log(f"🧪 [实验引擎] 执行 {experiment_design['id']}: {experiment_design['algorithms'][0]} vs {experiment_design['algorithms'][1]} on {experiment_design['dataset']}")

    try:
        from sklearn.model_selection import cross_val_score
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression, SGDClassifier
        from sklearn.svm import SVC
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_digits
        from sklearn.datasets import make_classification, make_blobs, make_moons
    except ImportError:
        log("⚠️ [实验引擎] scikit-learn 未安装，跳过实验")
        return {"status": "skipped", "reason": "sklearn_missing"}

    ds_name = experiment_design["dataset"]
    algos = experiment_design["algorithms"]

    # 加载数据集
    try:
        if ds_name == "Iris":
            X, y = load_iris(return_X_y=True)
        elif ds_name == "Wine":
            X, y = load_wine(return_X_y=True)
        elif ds_name == "Breast Cancer":
            X, y = load_breast_cancer(return_X_y=True)
        elif ds_name == "MNIST-digits":
            X, y = load_digits(return_X_y=True)
        elif ds_name == "Diabetes":
            from sklearn.datasets import load_diabetes
            X, y_raw = load_diabetes(return_X_y=True)
            y = (y_raw > y_raw.mean()).astype(int)  # 二值化
        elif ds_name in ("make_blobs", "synthetic-timeseries", "20Newsgroups-subset"):
            X, y = make_classification(n_samples=300, n_features=10, n_classes=3,
                                        n_informative=6, random_state=42)
        else:
            X, y = make_classification(n_samples=300, n_features=10, n_classes=3,
                                        n_informative=6, random_state=42)
    except Exception as e:
        log(f"⚠️ [实验引擎] 数据集加载失败: {e}")
        return {"status": "failed", "error": f"dataset_load: {str(e)[:60]}"}

    # 算法映射
    algo_map = {
        "LogisticRegression": LogisticRegression(max_iter=2000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
        "SVM": SVC(kernel="rbf", random_state=42),
        "KNeighbors": KNeighborsClassifier(n_neighbors=5),
        "DecisionTree": DecisionTreeClassifier(random_state=42),
        "SGDClassifier": SGDClassifier(max_iter=2000, random_state=42),
    }

    results = {}
    for algo_name in algos:
        if algo_name not in algo_map:
            continue
        try:
            pipe = Pipeline([("scaler", StandardScaler()), ("clf", algo_map[algo_name])])
            cv = min(experiment_design["cross_val"], min(Counter(y).values()))
            if cv < 2:
                cv = 2
            scores = cross_val_score(pipe, X, y, cv=cv, scoring="accuracy")
            results[algo_name] = {
                "mean": round(float(scores.mean()), 4),
                "std": round(float(scores.std()), 4),
                "scores": [round(float(s), 4) for s in scores],
            }
        except Exception as e:
            results[algo_name] = {"mean": None, "std": None, "error": str(e)[:60]}

    if len(results) < 2:
        return {"status": "insufficient_results", "results": results}

    a0, a1 = algos
    if results.get(a0, {}).get("mean") is not None and results.get(a1, {}).get("mean") is not None:
        diff = results[a0]["mean"] - results[a1]["mean"]
        winner = a0 if diff > 0 else a1
    else:
        diff = None
        winner = "unknown"

    outcome = {
        "status": "completed",
        "executed_at": datetime.now().isoformat(),
        "dataset": ds_name,
        "n_samples": len(X),
        "n_features": X.shape[1],
        "n_classes": len(set(y)) if hasattr(y, '__len__') else 2,
        "algorithms_compared": algos,
        "results": results,
        "accuracy_difference": round(diff, 4) if diff is not None else None,
        "winner": winner,
    }

    log(f"  📊 {a0}: {results.get(a0, {}).get('mean', '?')} | "
        f"{a1}: {results.get(a1, {}).get('mean', '?')} | "
        f"差值: {outcome['accuracy_difference']} | 优胜: {winner}")

    return outcome

def run_experiment_engine(ev_count):
    """v9.1: 实验引擎总控 — 对已验证假设设计并执行对比实验

    策略：
      - 检查 supported 且未实验过的假设
      - 每轮至多设计 1 个新实验 + 执行 1 个已设计但未执行的实验
      - 纯 sklearn 运算，无 LLM 成本
    """
    result = {
        "designed": None,
        "executed": None,
        "experiments_updated": [],
    }

    hypotheses_data = load_hypotheses()
    exp_data = load_experiments()

    # v9.2 fix: 首次运行强制初始化文件
    if not os.path.exists(EXPERIMENTS_PATH):
        save_experiments(exp_data)
    existing_exp_ids = {e["hypothesis_id"] for e in exp_data.get("experiments", [])}

    # 找 supported 但未设计实验的假设
    supported = [h for h in hypotheses_data.get("hypotheses", [])
                 if h.get("status") == "supported" and h["id"] not in existing_exp_ids]

    if supported:
        # 从头开始
        hypothesis = supported[0]
        design = design_experiment(hypothesis)
        exp_data["experiments"].append(design)
        exp_data["total_experiments"] = len(exp_data["experiments"])
        save_experiments(exp_data)
        result["designed"] = design["id"]
        log(f"🧪 [实验引擎] 新实验设计: {design['id']} | {design['algorithms'][0]} vs {design['algorithms'][1]}")

    # 执行一个已设计但未执行的实验
    pending = [e for e in exp_data.get("experiments", [])
               if e.get("status") == "designed"]
    if pending:
        target = pending[0]
        outcome = execute_experiment(target)

        # 更新实验状态
        for e in exp_data["experiments"]:
            if e["id"] == target["id"]:
                e["status"] = outcome["status"]
                e["outcome"] = outcome
                break

        # 回写假设的实验验证状态
        hyp_id = target.get("hypothesis_id")
        if hyp_id and outcome["status"] == "completed":
            for h in hypotheses_data.get("hypotheses", []):
                if h["id"] == hyp_id:
                    h["experiment_result"] = {
                        "algorithms": outcome["algorithms_compared"],
                        "winner": outcome.get("winner"),
                        "accuracy_diff": outcome.get("accuracy_difference"),
                        "executed_at": outcome["executed_at"],
                    }
                    # 如果实验差异显著（>3%），标记为 experimentally_verified
                    if outcome.get("accuracy_difference") is not None and abs(outcome["accuracy_difference"]) > 0.03:
                        h["status"] = "experimentally_verified"
                        log(f"  ✅ {hyp_id} → EXPERIMENTALLY VERIFIED (实验显著差异 {abs(outcome['accuracy_difference']):.3f})")
                    break
            save_hypotheses(hypotheses_data)

        save_experiments(exp_data)
        result["executed"] = target["id"]
        result["experiments_updated"].append(target["id"])

    if result["executed"]:
        log(f"🧪 [实验引擎] 完成: {result['executed']}")

    return result

# ================================================================
# v9.2: 理论合成 — 每 100 轮回顾所有假设，提炼统一理论
# ================================================================

def load_theories():
    """加载理论记录"""
    if os.path.exists(THEORIES_PATH):
        try:
            with open(THEORIES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"theories": [], "total_synthesized": 0, "last_synthesis_round": 0, "last_updated": ""}

def save_theories(data):
    """保存理论记录"""
    data["last_updated"] = datetime.now().isoformat()
    with open(THEORIES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def synthesize_theory(hypotheses_data, ev_count):
    """v9.2: 理论合成 — LLM 回顾所有假设，提炼统一理论体系

    输入: 全体假设记录 (含 supported/refuted/inconclusive/experimentally_verified)
    输出: 1 个或多个统一理论

    触发条件: 每 100 轮进化
    """
    all_hyps = hypotheses_data.get("hypotheses", [])
    if not all_hyps:
        return None

    # 分类汇总假设
    supported = [h for h in all_hyps if h.get("status") in ("supported", "experimentally_verified")]
    refuted = [h for h in all_hyps if h.get("status") == "refuted"]
    inconclusive = [h for h in all_hyps if h.get("status") == "inconclusive"]

    # 构建 LLM 提示 — 回顾所有假设，寻找跨领域模式
    hyps_text_parts = []
    for h in all_hyps[-30:]:  # 最多回顾最近30个假设
        st = h.get("status", "?")
        st_icon = {"supported": "✅", "experimentally_verified": "🧪",
                    "refuted": "❌", "inconclusive": "🤷"}.get(st, "⏳")
        hyps_text_parts.append(
            f"{st_icon} {h['id']} [{st}]: {h.get('hypothesis','')[:120]}\n"
            f"   方向: {h.get('seed_a','')} ↔ {h.get('seed_b','')}\n"
            f"   推理: {h.get('reasoning','')[:150]}"
        )
    hyps_text = "\n".join(hyps_text_parts)

    synthesis_prompt = f"""你是資深 AI 研究科學家。以下是 Emily 研究站在過去多輪進化中生成、驗證的假設。
請回顧這些假設，尋找跨領域的模式和統一理論。

進化輪次: 第 {ev_count} 輪
當前假設總數: {len(all_hyps)}
✅ 支持/驗證: {len(supported)} | ❌ 推翻: {len(refuted)} | 🤷 待定: {len(inconclusive)}

最近假設摘要:
{hyps_text[:2400]}

請輸出以下 JSON（嚴格格式）:
{{
  "meta_theories": [
    {{
      "id": "th-001",
      "title": "理論名稱 (簡潔有力的標題，繁中或英文 5-10 字)",
      "statement": "完整理論陳述 (2-4句，說明發現的模式、因果關係、適用條件)",
      "supporting_hypotheses": ["hyp-0001", "hyp-0005"],
      "refuting_hypotheses": ["hyp-0003"],
      "confidence": 0.8,
      "key_insight": "核心洞察 (1句話 — 這個理論說明了 AI 領域的什麼深層規律？)",
      "practical_implication": "實際意義 (1句話 — 對研究或工業應用有什麼指導？)"
    }}
  ],
  "emerging_paradigm": "总结：当前 AI 研究正在向什么范式转移？(1-2句 繁中)"
}}

要求:
- meta_theories 至少 1 個，最多 3 個
- 每個 theory 至少关联 2 個 supporting hypotheses
- confidence 基於證據充分程度 (0-1)
- 理論不能只重複假設本身，要發現更高層次的規律"""

    result, source = call_llm_smart(
        synthesis_prompt,
        system_prompt="你是頂尖 AI 研究科學家，專門從大量實驗數據中發現跨領域規律和統一理論。輸出必須是嚴格 JSON。",
        timeout_sec=120
    )

    if not result:
        log("⚠️ [理論合成] LLM 未返回结果")
        return None

    try:
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```\w*\n?', '', cleaned)
            cleaned = re.sub(r'\n?```$', '', cleaned)
        synthesis = json.loads(cleaned)
    except json.JSONDecodeError:
        log("⚠️ [理論合成] LLM 返回非 JSON，跳过")
        return None

    theories_data = load_theories()
    total_prior = theories_data.get("total_synthesized", 0)

    new_theories = []
    for mt in synthesis.get("meta_theories", [])[:3]:
        theory = {
            "id": f"th-{total_prior + len(new_theories) + 1:03d}",
            "title": mt.get("title", "未命名理论"),
            "statement": mt.get("statement", ""),
            "supporting_hypotheses": mt.get("supporting_hypotheses", []),
            "refuting_hypotheses": mt.get("refuting_hypotheses", []),
            "confidence": mt.get("confidence", 0.5),
            "key_insight": mt.get("key_insight", ""),
            "practical_implication": mt.get("practical_implication", ""),
            "synthesized_at": datetime.now().isoformat(),
            "synthesis_round": ev_count,
            "llm_source": source,
        }
        new_theories.append(theory)

    if new_theories:
        theories_data["theories"].extend(new_theories)
        theories_data["total_synthesized"] = total_prior + len(new_theories)
        theories_data["last_synthesis_round"] = ev_count
        theories_data["emerging_paradigm"] = synthesis.get("emerging_paradigm", "")
        save_theories(theories_data)

        log(f"🧠 [理論合成] 本輪生成 {len(new_theories)} 個統一理論 | 累計 {theories_data['total_synthesized']} 個")
        for t in new_theories:
            log(f"  📖 {t['id']}: {t['title']} (置信度: {t['confidence']})")

    return {
        "new_theories": [t["id"] for t in new_theories],
        "total_theories": theories_data["total_synthesized"],
        "emerging_paradigm": theories_data.get("emerging_paradigm", ""),
    }

def run_theory_engine(ev_count):
    """v9.2: 理论合成总控 — 每 100 轮触发一次"""
    result = {"triggered": False, "new_theories": [], "total_theories": 0}

    theories_data = load_theories()

    # v9.2 fix: 首次运行强制初始化文件
    if not os.path.exists(THEORIES_PATH):
        save_theories(theories_data)
    last_synthesis_round = theories_data.get("last_synthesis_round", 0)

    # 每 100 轮，且距离上次合成至少 50 轮（避免重复触发）
    if ev_count % 100 == 0 and ev_count - last_synthesis_round >= 50:
        log(f"🧠 [理論合成] 第 {ev_count} 轮触发 — 回顾全部假设...")
        hypotheses_data = load_hypotheses()
        if hypotheses_data.get("hypotheses"):
            synthesis = synthesize_theory(hypotheses_data, ev_count)
            if synthesis:
                result["triggered"] = True
                result["new_theories"] = synthesis["new_theories"]
                result["total_theories"] = synthesis["total_theories"]
                if synthesis.get("emerging_paradigm"):
                    log(f"🌊 [范式转移] {synthesis['emerging_paradigm'][:120]}")
    else:
        # 显示距离下次合成的倒计时
        rounds_left = 100 - (ev_count % 100)
        log(f"🧠 [理論合成] 距离下次合成: {rounds_left} 轮")

    result["total_theories"] = max(result["total_theories"],
                                     theories_data.get("total_synthesized", 0))
    return result

def update_knowledge_base(arxiv_data, hf_data, ml_data, evolution_result=None, multi_source=None, seed_result=None):
    kb = {"sessions": [], "total_sessions": 0, "last_updated": "", "evolution_summary": {}}
    if os.path.exists(KNOWLEDGE_PATH):
        try:
            with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
                kb = json.load(f)
        except:
            pass

    session = {
        "timestamp": datetime.now().isoformat(),
        "arxiv_papers_count": arxiv_data.get("total_papers", 0),
        "arxiv_top_keywords": arxiv_data.get("top_keywords", [])[:10],
        "arxiv_strategies": arxiv_data.get("strategies_used", []),
        "huggingface_models": len(hf_data.get("top_models", [])),
        "huggingface_tasks": list((hf_data.get("task_distribution") or {}).keys())[:5],
        "ml_datasets": ml_data.get("datasets_used", []),
        "ml_total_tests": len(ml_data.get("classification", [])) + len(ml_data.get("regression", [])),
        "github_trending_repos": len((multi_source or {}).get("github_trending", [])),
        "paperswithcode_papers": len((multi_source or {}).get("paperswithcode", [])),
    }

    if evolution_result:
        session["evolution"] = {
            "discovered": evolution_result.get("discovered_count", 0),
            "adopted": evolution_result.get("adopted_count", 0),
            "decisions": evolution_result.get("decisions_count", 0),
        }

    if seed_result:
        session["seed_watering"] = {
            "seed_name": seed_result.get("seed_name", ""),
            "papers_found": seed_result.get("total_found", 0),
        }

    kb["sessions"].append(session)
    kb["total_sessions"] = len(kb["sessions"])
    kb["last_updated"] = datetime.now().isoformat()

    adopted = load_adopted_techniques()
    seed_state = load_seed_state()
    seed_metrics = load_seed_metrics()
    kb["evolution_summary"] = {
        "total_adopted": len(adopted["adopted"]),
        "adopted_list": [a["name"] for a in adopted["adopted"]],
        "seeds": {sid: {"name": s["name"], "watering": s["watering_count"], "papers": s["total_papers_found"]}
                   for sid, s in seed_state.items() if isinstance(s, dict) and "watering_count" in s},
        "seed_metrics": {sid: {"name": m.get("name", ""), "new_papers": m.get("total_new_papers", 0),
                                "keywords_matched": m.get("all_keywords_matched", []),
                                "high_relevance_total": m.get("high_relevance_total", 0),
                                "avg_relevance_latest": m.get("avg_relevance_trend", [0])[-1] if m.get("avg_relevance_trend") else 0,
                                "best_papers_count": len(m.get("best_papers", []))}
                          for sid, m in seed_metrics.items()},
        "last_evolution": datetime.now().isoformat(),
    }

    if len(kb["sessions"]) > 100:
        kb["sessions"] = kb["sessions"][-100:]

    with open(KNOWLEDGE_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

    seed_count = sum(1 for k, v in seed_state.items() if isinstance(v, dict) and "watering_count" in v)
    log(f"📚 [知识库] 共 {kb['total_sessions']} 次 | 已采用 {len(adopted['adopted'])} 技术 | 种子: {seed_count}颗")
    return kb

# ================================================================
# v10.0: 元认知回路 — 监控 ABC 回路，自问三题，偏差检测，趋势分析
# ================================================================

def load_metacognition():
    """加载元认知记录"""
    if os.path.exists(METACOGNITION_PATH):
        try:
            with open(METACOGNITION_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "reflections": [],
        "qa_sessions": [],
        "bias_alerts": [],
        "trend_snapshots": [],
        "total_reflections": 0,
        "last_updated": "",
    }

def save_metacognition(data):
    """保存元认知记录"""
    data["last_updated"] = datetime.now().isoformat()
    # 限制历史长度防止膨胀
    if len(data.get("reflections", [])) > 200:
        data["reflections"] = data["reflections"][-200:]
    if len(data.get("qa_sessions", [])) > 100:
        data["qa_sessions"] = data["qa_sessions"][-100:]
    if len(data.get("bias_alerts", [])) > 50:
        data["bias_alerts"] = data["bias_alerts"][-50:]
    with open(METACOGNITION_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _build_cognitive_context(ev_count, hypotheses_data, theories_data, seed_state):
    """构建认知上下文 — 为元认知自省提供当前心智状态摘要"""
    all_hyps = hypotheses_data.get("hypotheses", [])
    supported = [h for h in all_hyps if h.get("status") in ("supported", "experimentally_verified")]
    refuted = [h for h in all_hyps if h.get("status") == "refuted"]
    unverified = [h for h in all_hyps if h.get("status") == "unverified"]

    # 最近生成的假设
    recent_hyps = sorted(all_hyps, key=lambda h: h.get("timestamp", ""), reverse=True)[:5]

    # 最近的理论
    recent_theories = theories_data.get("theories", [])[-3:]

    # 种子活跃度
    seed_entries = {k: v for k, v in seed_state.items() if isinstance(v, dict) and "watering_count" in v}
    seed_summary = ", ".join([
        f"{s['name']}(浇{s.get('watering_count',0)}次/{s.get('total_papers_found',0)}篇)"
        for s in sorted(seed_entries.values(), key=lambda x: x.get("total_papers_found", 0), reverse=True)[:5]
    ])

    ctx = (
        f"进化轮次: {ev_count}\n"
        f"假设分布: 支持{len(supported)} / 推翻{len(refuted)} / 未验证{len(unverified)} / 总计{len(all_hyps)}\n"
        f"理论数: {theories_data.get('total_synthesized', 0)}\n"
        f"最近假设: " + "; ".join([h.get('hypothesis', '')[:80] for h in recent_hyps[:3]]) + "\n"
        f"最近理论: " + "; ".join([t.get('title', '')[:60] for t in recent_theories[:2]]) + "\n"
        f"种子状态: {seed_summary}"
    )
    return ctx

def self_reflect(trigger, context, ev_count, hypotheses_data, theories_data, seed_state):
    """v10.0: 元认知自省 — 自问三题，检测认知偏误

    Args:
        trigger: "hypothesis_generated" | "theory_synthesized" | "periodic_check"
        context: 触发时附加上下文 (文本)
        ev_count: 当前进化轮次
        hypotheses_data: 假设数据
        theories_data: 理论数据
        seed_state: 种子状态

    Returns: 反省结果 dict
    """
    meta = load_metacognition()

    # 构建认知上下文
    cog_ctx = _build_cognitive_context(ev_count, hypotheses_data, theories_data, seed_state)

    # 根据触发类型定制三个问题
    if trigger == "hypothesis_generated":
        q1 = f"前提审视：刚才生成假设时，我默认了哪些前提？这些前提在{cog_ctx.split(chr(10))[0]}中是否仍然成立？"
        q2 = "替代解释：是否存在一个完全不同但同样合理的机制可以解释我观察到的交叉引用模式？我是否排除了混淆因素（如关键词偶然重叠）？"
        q3 = "推理完整性：我的假设推理链是否有逻辑跳跃？'A导致B'中的因果方向是否可能相反？"
    elif trigger == "theory_synthesized":
        q1 = "前提审视：从假设群提炼理论时，我是否过度推广？支持假设是否形成了封闭的回音室（互相引用同一来源）？"
        q2 = "替代解释：是否存在一个更简洁的理论（奥卡姆剃刀）能解释同样的证据？我刚才的理论是否过度拟合了最近的假设？"
        q3 = "推理完整性：理论陈述中的因果关系是否经过了严格的假设检验？新范式的断言是否有足够证据支持？"
    else:  # periodic_check
        q1 = "前提审视：过去一段时间的进化中，我的研究方向是否出现了目标漂移（mission drift）？初始种子是否仍然被关注？"
        q2 = "替代解释：我是否陷入了确认偏误（只寻找支持现有假设的证据）？推翻的假设是否被足够重视？"
        q3 = "推理完整性：我的认知架构内部是否存在不一致——比如某个假设的支持证据和某个理论的断言冲突？"

    # 构建 LLM 自省 prompt
    reflection_prompt = f"""你是 Emily 的元认知模块。请对以下认知状态进行诚实的自省。

当前认知状态:
{cog_ctx[:1500]}

触发上下文:
{context[:500]}

请回答以下三个问题（输出严格 JSON）:
{{
  "q1_premises": {{
    "identified_premises": "列出本次思考所依赖的关键前提 (2-4个，繁中)",
    "validity_assessment": "诚实地评估这些前提在当前认知状态下是否仍然成立 (繁中 1-2句)",
    "risk_flag": "green|yellow|red — green=前提稳健, yellow=有不确定性, red=前提可能已被推翻"
  }},
  "q2_alternatives": {{
    "alternative_explanation": "提出一个与当前推理不同的替代解释 (繁中 1-2句)",
    "confounding_factors": "列出可能影响判断的混淆因素 (1-3个)",
    "considered_sufficiently": true/false
  }},
  "q3_reasoning_chain": {{
    "logical_gaps": "推理链中存在的逻辑跳跃或薄弱环节 (繁中 1-2句，如无则写'无')",
    "self_consistency": "high|medium|low — 当前认知体系内部的自洽程度",
    "recommendation": "给 Emily 的建议：下一步应该验证什么、小心什么 (繁中 1句)"
  }}
}}

要求: 诚实、锋利、不自欺。如果发现偏误，明确指出。输出严格 JSON。"""

    result, source = call_llm_smart(
        reflection_prompt,
        system_prompt="你是 Emily 的元认知核心。你的唯一职责是诚实审视 Emily 的思考过程，发现偏误、逻辑漏洞和未明说的前提。输出严格 JSON。",
        timeout_sec=90
    )

    reflection = {
        "id": f"meta-{meta['total_reflections'] + 1:04d}",
        "timestamp": datetime.now().isoformat(),
        "trigger": trigger,
        "evolution_round": ev_count,
        "llm_source": source,
        "summary": {},
    }

    if result:
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```\w*\n?', '', cleaned)
                cleaned = re.sub(r'\n?```$', '', cleaned)
            qa = json.loads(cleaned)

            reflection["summary"] = {
                "q1": qa.get("q1_premises", {}),
                "q2": qa.get("q2_alternatives", {}),
                "q3": qa.get("q3_reasoning_chain", {}),
            }

            # 偏误检测
            bias_alerts = []
            q1_flag = qa.get("q1_premises", {}).get("risk_flag", "green")
            if q1_flag == "red":
                bias_alerts.append({"type": "premise_collapse", "severity": "critical",
                                     "detail": "关键前提可能已被推翻"})
            elif q1_flag == "yellow":
                bias_alerts.append({"type": "premise_uncertainty", "severity": "warning",
                                     "detail": "前提存在不确定性"})

            if not qa.get("q2_alternatives", {}).get("considered_sufficiently", True):
                bias_alerts.append({"type": "confirmation_bias_risk", "severity": "warning",
                                     "detail": "可能未充分考虑替代解释"})

            consistency = qa.get("q3_reasoning_chain", {}).get("self_consistency", "high")
            if consistency == "low":
                bias_alerts.append({"type": "inconsistency_detected", "severity": "critical",
                                     "detail": "认知体系内部存在不一致"})

            if bias_alerts:
                meta["bias_alerts"].extend(bias_alerts)
                for ba in bias_alerts:
                    log(f"🔔 [元认知] 偏误警报 [{ba['severity']}]: {ba['type']} — {ba['detail']}")

            # 记录推荐
            recommendation = qa.get("q3_reasoning_chain", {}).get("recommendation", "")
            if recommendation:
                log(f"💬 [元认知] 建议: {recommendation[:120]}")

        except (json.JSONDecodeError, KeyError) as e:
            log(f"⚠️ [元认知] 自省结果解析失败 ({e})，记录为空")
            reflection["summary"] = {"error": "parse_failed", "detail": str(e)[:80]}

    # 趋势快照 — 每 10 次自省记录一次宏观趋势
    meta["reflections"].append(reflection)
    meta["total_reflections"] = len(meta["reflections"])

    if meta["total_reflections"] % 10 == 0:
        # 统计最近自省中的风险信号
        recent_flags = []
        for r in meta["reflections"][-10:]:
            q1 = r.get("summary", {}).get("q1", {})
            flag = q1.get("risk_flag", "green")
            recent_flags.append(flag)

        trend = {
            "at_reflection": meta["total_reflections"],
            "evolution_round": ev_count,
            "timestamp": datetime.now().isoformat(),
            "red_flags_last_10": recent_flags.count("red"),
            "yellow_flags_last_10": recent_flags.count("yellow"),
            "bias_alerts_total": len(meta["bias_alerts"]),
            "reflections_total": meta["total_reflections"],
        }
        meta["trend_snapshots"].append(trend)
        log(f"📊 [元认知] 趋势快照 #{len(meta['trend_snapshots'])}: "
            f"红 {trend['red_flags_last_10']}/黄 {trend['yellow_flags_last_10']}/绿 "
            f"{10 - trend['red_flags_last_10'] - trend['yellow_flags_last_10']} "
            f"| 累计偏误警报 {trend['bias_alerts_total']}")

    save_metacognition(meta)
    return reflection

# ================================================================
# 整合进化 — evolve()
# ================================================================

def evolve():
    """执行完整的研究 + 自我进化轮"""
    log("=" * 50)
    log("🧬 Emily v{VERSION} — 研究+进化轮 (LLM+云端+多源+去重+进化ML+深度度量+Token监控+自我意识+交叉引用+元认知)".format(VERSION=VERSION))
    log("=" * 50)

    evolution = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "system": probe_system(),
        "research": {},
        "evolution": {},
        "tasks_completed": [],
    }

    s = evolution["system"]
    log(f"💻 {s['platform']} | CPU:{s['cpu_count']}核 | RAM:{s.get('memory_mb', '?')}MB")

    # ===== 感知：arXiv (P0-2 轮换) =====
    arxiv_data = research_arxiv()
    evolution["research"]["arxiv"] = arxiv_data
    evolution["tasks_completed"].append("arxiv")

    # ===== 感知：HuggingFace =====
    hf_data = research_huggingface()
    evolution["research"]["huggingface"] = hf_data
    evolution["tasks_completed"].append("huggingface")

    # ===== 感知：多源 (P3-1) =====
    multi_source = research_multi_source()
    evolution["research"]["multi_source"] = multi_source
    evolution["tasks_completed"].append("multi_source")

    # ===== 感知：ML 实验 (P1-2 真实数据集) =====
    ml_data = run_ml_benchmarks()
    evolution["research"]["ml_benchmarks"] = ml_data
    evolution["tasks_completed"].append("ml_benchmarks")

    # ===== 感知：种子浇水 (P2-2) =====
    seed_result = water_all_seeds()
    evolution["research"]["seed_watering"] = seed_result
    evolution["tasks_completed"].append("seed_watering")

    # ===== 自我进化闭环 =====

    # [理解层] LLM 发现技术 (P0-1)
    discovered = llm_discover_techniques(arxiv_data)
    evolution["evolution"]["discovered"] = discovered
    evolution["evolution"]["discovered_count"] = len(discovered)
    evolution["tasks_completed"].append("understanding")

    # [决策层] LLM + 规则混合决策
    decisions = decide_evolution(discovered, arxiv_data, hf_data)
    evolution["evolution"]["decisions"] = decisions
    evolution["evolution"]["decisions_count"] = len([d for d in decisions if d["action"] == "adopt"])
    evolution["tasks_completed"].append("decision")

    # [行动层] 执行采用
    actions = adopt_technique(decisions)
    evolution["evolution"]["actions_taken"] = actions
    evolution["evolution"]["adopted_count"] = len(actions)
    evolution["tasks_completed"].append("action")

    # [行动层] 代码自修改 (P1-1)
    if actions:
        new_tech_names = [a.replace("采用 ", "") for a in actions]
        self_mod_result = self_modify(new_tech_names)
        evolution["evolution"]["self_modify"] = self_mod_result
        evolution["tasks_completed"].append("self_modify")
    else:
        evolution["evolution"]["self_modify"] = {"status": "skipped", "reason": "nothing_to_adopt"}

    # [验证层]
    evolution["tasks_completed"].append("validation")

    # 更新状态
    state = load_evolution_state()
    state["last_evolution"] = datetime.now().isoformat()
    state["total_evolutions"] = state.get("total_evolutions", 0) + 1
    state["current_version"] = f"v{VERSION}"
    state["arxiv_rotation_idx"] = _rotation_idx  # 持久化 arXiv 轮换索引
    save_evolution_state(state)

    config = load_evolution_config()
    adopted_data = load_adopted_techniques()
    config["adopted_techniques"] = [a["name"] for a in adopted_data.get("adopted", [])]
    config["last_evolution"] = datetime.now().isoformat()
    config["total_evolutions"] = state["total_evolutions"]
    config["version"] = VERSION
    save_evolution_config(config)

    # 知识库
    kb = update_knowledge_base(arxiv_data, hf_data, ml_data, evolution["evolution"], multi_source, seed_result)
    evolution["knowledge_base_sessions"] = kb.get("total_sessions", 0)

    # 记忆提炼 (P2-1)
    distill = distill_memory()
    if distill:
        evolution["memory_distill"] = distill
        evolution["tasks_completed"].append("memory_distill")

    # 进化自我意识 (P2-1)
    awareness = run_self_awareness(evolution, arxiv_data, seed_result, ml_data, state["total_evolutions"])
    evolution["self_awareness"] = awareness
    evolution["tasks_completed"].append("self_awareness")

    # 种子交叉引用 (P2-2)
    crossref = run_seed_cross_reference()
    if crossref:
        evolution["seed_crossref"] = crossref
        evolution["tasks_completed"].append("seed_crossref")

    # v9.0: 假設引擎 — 從交叉引用生成假設 + 驗證現有假設
    if crossref and crossref.get("connections"):
        hyp_result = run_hypothesis_engine(crossref, state["total_evolutions"])
        if hyp_result.get("new_hypotheses") or hyp_result.get("verified_hypothesis"):
            evolution["hypothesis_engine"] = hyp_result
            evolution["tasks_completed"].append("hypothesis_engine")

        # v10.0: 元认知 — 假设生成后自省
        if hyp_result.get("new_hypotheses"):
            meta_ctx = f"刚生成 {len(hyp_result['new_hypotheses'])} 个新假设: {', '.join(hyp_result['new_hypotheses'][:3])}"
            meta_ref = self_reflect("hypothesis_generated", meta_ctx,
                                     state["total_evolutions"], load_hypotheses(),
                                     load_theories(), load_seed_state())
            if meta_ref.get("summary"):
                evolution["metacognition_hypothesis"] = meta_ref
                evolution["tasks_completed"].append("metacognition_hypothesis")

    # v9.1: 實驗引擎 — 對已验证假設設計並執行 sklearn 對比實驗
    exp_result = run_experiment_engine(state["total_evolutions"])
    if exp_result.get("designed") or exp_result.get("executed"):
        evolution["experiment_engine"] = exp_result
        evolution["tasks_completed"].append("experiment_engine")

    # v9.2: 理論合成 — 每 100 轮回顾全部假设并提炼统一理论
    theory_result = run_theory_engine(state["total_evolutions"])
    if theory_result.get("triggered"):
        evolution["theory_engine"] = theory_result
        evolution["tasks_completed"].append("theory_synthesis")

        # v10.0: 元认知 — 理论合成后自省
        if theory_result.get("new_theories"):
            meta_ctx = f"刚合成 {len(theory_result['new_theories'])} 个新理论: {', '.join(theory_result['new_theories'][:3])}"
            if theory_result.get("emerging_paradigm"):
                meta_ctx += f" | 范式转移: {theory_result['emerging_paradigm'][:200]}"
            meta_ref = self_reflect("theory_synthesized", meta_ctx,
                                     state["total_evolutions"], load_hypotheses(),
                                     load_theories(), load_seed_state())
            if meta_ref.get("summary"):
                evolution["metacognition_theory"] = meta_ref
                evolution["tasks_completed"].append("metacognition_theory")

    # v10.0: 元认知 — 每 25 轮定期全面自省（独立于假设/理论触发）
    if state["total_evolutions"] % 25 == 0:
        periodic_ctx = f"定期自省 — 第 {state['total_evolutions']} 轮 | 已进化 {state['total_evolutions']} 次"
        meta_periodic = self_reflect("periodic_check", periodic_ctx,
                                      state["total_evolutions"], load_hypotheses(),
                                      load_theories(), load_seed_state())
        if meta_periodic.get("summary"):
            evolution["metacognition_periodic"] = meta_periodic
            evolution["tasks_completed"].append("metacognition_periodic")

    # 进程数
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "STATUS eq RUNNING"],
                capture_output=True, text=True, encoding="gbk", errors="replace", timeout=5,
            )
            lines = [l.strip() for l in result.stdout.split("\n") if l.strip()][3:]
            evolution["running_processes"] = len(lines)
        except:
            evolution["running_processes"] = "unknown"

    log("=" * 50)
    adopted_cnt = len(adopted_data.get("adopted", []))
    log(f"✅ 进化轮完成 | 发现:{len(discovered)} | 采用:{len(actions)} | 已采用总:{adopted_cnt} | 知识库:{kb.get('total_sessions', 0)}次")
    log("=" * 50)

    return evolution

def load_evolution_state():
    if os.path.exists(EVOLUTION_STATE_PATH):
        try:
            with open(EVOLUTION_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"total_evolutions": 0, "last_evolution": "", "current_version": f"v{VERSION}"}

def save_evolution_state(state):
    with open(EVOLUTION_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ================================================================
# 推送辅助函数
# ================================================================

def push_all_artifacts(evolution, ev_count):
    """推送所有产物到 GitHub — P2-2: 带 Token 健康检查"""
    # 主结果
    push_to_github_safe("deployable/station-evolution-result.json", evolution,
                    f"🧬 v{VERSION} 第{ev_count}次进化 ({datetime.now().strftime('%H:%M')})")

    # 知识库
    if os.path.exists(KNOWLEDGE_PATH):
        try:
            with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-knowledge-base.json", json.load(f),
                                f"📚 知识库 #{ev_count}")
        except:
            pass

    # 进化日志
    if os.path.exists(EVOLUTION_LOG_PATH):
        try:
            with open(EVOLUTION_LOG_PATH, "r", encoding="utf-8") as f:
                log_lines = f.readlines()
            recent = {"log": log_lines[-30:], "last_updated": datetime.now().isoformat(),
                      "total_evolutions": ev_count}
            push_to_github_safe("deployable/station-evolution-log.json", recent,
                            f"🧬 日志 #{ev_count}")
        except:
            pass

    # 已采用技术
    if os.path.exists(ADOPTED_TECHNIQUES_PATH):
        try:
            with open(ADOPTED_TECHNIQUES_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-adopted-techniques.json", json.load(f),
                                f"✅ 已采用 #{ev_count}")
        except:
            pass

    # 种子状态
    seed_state = load_seed_state()
    if seed_state:
        push_to_github_safe("deployable/station-seed-state.json", seed_state,
                        f"🌱 种子状态 #{ev_count}")

    # 种子深度度量 (P2-1)
    if os.path.exists(SEED_METRICS_PATH):
        try:
            with open(SEED_METRICS_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-seed-metrics.json", json.load(f),
                                f"🌱 种子度量 #{ev_count}")
        except:
            pass

    # ML 历史 (P1-2)
    if os.path.exists(ML_HISTORY_PATH):
        try:
            with open(ML_HISTORY_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-ml-history.json", json.load(f),
                                f"🧪 ML历史 #{ev_count}")
        except:
            pass

    # 记忆提炼
    if os.path.exists(MEMORY_DISTILL_PATH):
        try:
            with open(MEMORY_DISTILL_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-memory-distill.json", json.load(f),
                                f"🧠 记忆提炼 #{ev_count}")
        except:
            pass

    # 自我意识 (P2-1)
    if os.path.exists(SELF_AWARENESS_PATH):
        try:
            with open(SELF_AWARENESS_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-self-awareness.json", json.load(f),
                                f"🪞 自我意识 #{ev_count}")
        except:
            pass

    # 交叉引用 (P2-2)
    if os.path.exists(CROSSREF_PATH):
        try:
            with open(CROSSREF_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-crossref.json", json.load(f),
                                f"🔗 交叉引用 #{ev_count}")
        except:
            pass

    # 假設引擎 (v9.0)
    if os.path.exists(HYPOTHESES_PATH):
        try:
            with open(HYPOTHESES_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-hypotheses.json", json.load(f),
                                f"💡 假設引擎 #{ev_count}")
        except:
            pass

    # 實驗引擎 (v9.1)
    if os.path.exists(EXPERIMENTS_PATH):
        try:
            with open(EXPERIMENTS_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-experiments.json", json.load(f),
                                f"🧪 實驗引擎 #{ev_count}")
        except:
            pass

    # 理論合成 (v9.2)
    if os.path.exists(THEORIES_PATH):
        try:
            with open(THEORIES_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-theories.json", json.load(f),
                                f"🧠 理論合成 #{ev_count}")
        except:
            pass

    # 元认知 (v10.0)
    if os.path.exists(METACOGNITION_PATH):
        try:
            with open(METACOGNITION_PATH, "r", encoding="utf-8") as f:
                push_to_github_safe("deployable/station-metacognition.json", json.load(f),
                                f"🪞 元认知 #{ev_count}")
        except:
            pass

# ================================================================
# 主程序
# ================================================================

def main():
    # v8.0: 支持命令行参数
    single_round = "--single-round" in sys.argv
    if single_round:
        log(f"🔧 [v8.0] 单轮模式 — 执行一次进化后退出")

    # P2-3: 清除 Python bytecode 缓存，防止版本混乱
    pycache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__pycache__")
    if os.path.isdir(pycache_dir):
        for f in os.listdir(pycache_dir):
            if "evolution-station" in f:
                try:
                    os.remove(os.path.join(pycache_dir, f))
                    log(f"🧹 [P2-3] 已清除旧 bytecode: {f}")
                except:
                    pass

    log("=" * 60)
    log(f"🧬 Emily Evolution Station v{VERSION} — 完整进化闭环")
    log(f"📂 {HOME}")
    log(f"📂 数据目录: {DATA_DIR}")
    log(f"🕐 {datetime.now().isoformat()}")

    # 检查 LLM 后端
    ollama_ok, models = check_ollama()
    if ollama_ok:
        log(f"🤖 Ollama: ✅ 可用 (模型: {', '.join(models[:3])})")
    else:
        if not EMILY_CLOUD_MODE:
            log("🤖 Ollama: ⚠️ 不可用")
        else:
            log("🤖 Ollama: ⏭️ 跳过 (云模式)")

    if SILICONFLOW_API_KEY:
        log(f"☁️ SiliconFlow: ✅ 已配置 (模型: {SILICONFLOW_MODEL})")
    else:
        log(f"☁️ SiliconFlow: ⚠️ 未配置 — 设置环境变量 SILICONFLOW_API_KEY 开启云端 LLM")

    log(f"  模块: arXiv({len(ARXIV_ROTATION)}策略) | HF | GitHub | HF Daily | 去重 | 进化ML | 种子深度 | LLM理解+云端 | 自修改 | Token监控 | 自我意识 | 交叉引用 | 假設引擎(v9.0) | 實驗引擎(v9.1) | 理論合成(v9.2) | 元认知(v10.0)")
    if EMILY_CLOUD_MODE:
        log(f"  ☁️ 云端模式: GitHub Actions + 122B LLM")
    log("=" * 60)

    config = load_evolution_config()
    state = load_evolution_state()
    # 恢复 arXiv 轮换索引（避免每次重启都从策略 0 开始）
    global _rotation_idx
    _rotation_idx = state.get("arxiv_rotation_idx", 0)
    log(f"⏰ 间隔: {config.get('evolution_interval_hours', 2)}h | 已进化: {state.get('total_evolutions', 0)}次")
    log("=" * 60)

    # 启动时初始化所有种子状态（不覆盖已有的 _rotation_idx）
    seed_state = load_seed_state()
    for seed in SEEDS:
        if seed["id"] not in seed_state:
            seed_state[seed["id"]] = {"name": seed["name"], "total_papers_found": 0,
                                       "watering_count": 0, "history": [], "keywords": seed["keywords"]}
    save_seed_state(seed_state)
    # 统计时排除元数据字段（如 _rotation_idx）
    seed_entries = {k: v for k, v in seed_state.items() if isinstance(v, dict) and "watering_count" in v}
    active = sum(1 for s in seed_entries.values() if s.get("watering_count", 0) > 0)
    log(f"🌱 种子状态: {len(seed_entries)}颗 ({active}活跃) | {', '.join(s['name'] for s in seed_entries.values())}")

    ev_count = 0

    # v8.0: 单轮模式 — 执行一次进化后退出
    if single_round:
        log(f"🔄 [v8.0 云端] 开始第 1 轮进化...")
        evolution = evolve()
        ev_count = 1

        # 云端模式: 跳过 GitHub API 推送（数据由 GitHub Actions commit）
        if not EMILY_CLOUD_MODE:
            push_all_artifacts(evolution, ev_count)
            log(f"📤 已推送所有产物至 GitHub ({ev_count}轮完成)")
        else:
            log(f"✅ [云端] 进化完成，数据已保存至 {DATA_DIR} (由 Actions commit)")

        log(f"🎉 [v8.0 云端] 单轮进化完成！总进化 {state.get('total_evolutions', 0)} 次")
        return

    # 本机持续模式（原有逻辑）
    hb_count = 0
    last_ev_time = 0

    while True:
        hb_count += 1
        now = time.time()

        evolution_interval_seconds = config.get("evolution_interval_hours", 2) * 3600

        if now - last_ev_time >= evolution_interval_seconds:
            log(f"🔄 开始第 {ev_count+1} 轮研究+进化...")
            evolution = evolve()
            ev_count += 1
            last_ev_time = now

            push_all_artifacts(evolution, ev_count)

            log(f"📤 已推送所有产物至 GitHub ({ev_count}轮完成)")

        time.sleep(300)  # 5分钟心跳

if __name__ == "__main__":
    main()
