# Auto-generated code snippet by Emily Self-Modify
# Based on: Transformer, Agent, Llm
# Generated: 2026-07-15T09:47:06.495407

```python
async def fetch_arxiv_papers(query="transformer agent llm", max_results=5):
    import aiohttp, xml.etree.ElementTree as ET
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            root = ET.fromstring(await resp.text())
            papers = []
            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
                summary = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()[:200]
                papers.append({"title": title, "summary": summary})
            return papers
```