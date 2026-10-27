# Auto-generated code snippet by Emily Self-Modify
# Based on: 代码驱动视频生成, 一步动作生成
# Generated: 2026-10-27T23:18:19.472182

def enhance_with_code_video_generation(self, papers, repo_context):
    """Enhance evolution with code-driven video generation and one-step action generation."""
    import json, urllib.request, base64

    def _call_llm(prompt, max_tokens=800):
        payload = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]

    video_papers = [p for p in papers if any(
        k in (p.get("title", "") + p.get("summary", "")).lower()
        for k in ["video generation", "video synthesis", "text-to-video", "code-driven video"]
    )]
    action_papers = [p for p in papers if any(
        k in (p.get("title", "") + p.get("summary", "")).lower()
        for k in ["one-step", "one step", "single-step action", "action generation"]
    )]

    enhancements = []
    if video_papers:
        ctx = "\n".join(f"- {p['title']}: {p.get('summary','')[:300]}" for p in video_papers[:3])
        prompt = (
            "You are a code self-modification engine. Based on these code-driven video "
            "generation papers, propose a concrete Python function (<=25 lines) that can be "
            "inserted into an evolution pipeline to generate a short video summary of "
            "code changes. Return ONLY Python code, no markdown.\n\n" + ctx
        )
        try:
            code = _call_llm(prompt, 900)
            code = code.replace("