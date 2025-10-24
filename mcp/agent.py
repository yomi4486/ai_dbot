import os
from typing import List, Dict
from .search import serpapi_search, SerpApiError
from .fetcher import fetch_text_from_url
from .summarizer import simple_summary
import requests


def build_context(results: List[Dict]) -> List[Dict]:
    context = []
    for r in results:
        fetched = fetch_text_from_url(r.get("link"))
        full_text = fetched.get("text")
        summary = simple_summary(full_text)
        context.append({
            "title": r.get("title"),
            "url": r.get("link"),
            "snippet": r.get("snippet"),
            "summary": summary,
            "fetch_error": fetched.get("error"),
            "full_text": full_text,
        })
    return context


def build_prompt(query: str, context_items: List[Dict]) -> str:
    parts = ["参照データ:"]
    for i, it in enumerate(context_items, 1):
        parts.append(f"[{i}] {it.get('title') or 'No title'}\nURL: {it.get('url')}\n要約: {it.get('summary') or '(抽出失敗)'}\n")
    parts.append("これらを参考に、簡潔に回答してください。回答の末尾に参照元の番号とURLを列挙してください。")
    parts.append("質問: " + query)
    return "\n\n".join(parts)


def build_system_message(context_items: List[Dict], max_items: int = 5) -> str:
    """Build a system-role message that contains the MCP-sourced context.

    The message is intended to be passed as the `system` message to the LLM so the model
    treats the retrieved documents as authoritative context.
    """
    parts = ["参照データ（システムコンテキスト）:\n"]
    for i, it in enumerate(context_items[:max_items], 1):
        title = it.get("title") or "(No title)"
        url = it.get("url") or "(No url)"
        summary = it.get("summary") or "(抽出失敗)"
        parts.append(f"[{i}] {title}\nURL: {url}\n要約: {summary}\n")
    parts.append("---\n注意: この情報を参照してからユーザーの質問に答えてください。情報の出典を回答末尾に記載してください。")
    return "\n".join(parts)


def call_model(messages: List[Dict[str, str]], model: str = "ibm/granite-4-h-tiny") -> Dict:
    """Call LM Studio (or another LM endpoint) if configured.

    If environment variable LMSTUDIO_API_URL is set, send a POST with JSON body that
    includes a jinjaPromptTemplate with bosToken/eosToken/inputConfig to avoid the earlier schema error.
    Otherwise, return a dummy response (for offline testing).
    """
    api_url = os.getenv("LMSTUDIO_API_URL")
    api_key = os.getenv("LMSTUDIO_API_KEY")
    # honor global network-disable setting via env var
    if os.getenv("DISABLE_NETWORK", "").lower() in ("1", "true", "yes"):
        return {"text": "(network disabled)", "status_code": 200}
    # Use messages (list of {"role":..., "content":...}) so we can pass system prompt
    body = {
        "model": model,
        "messages": messages,
        # include jinjaPromptTemplate to satisfy LM Studio schema
        "llm": {
            "prediction": {
                "promptTemplate": {
                    "jinjaPromptTemplate": {
                        "bosToken": "<BOS>",
                        "eosToken": "<EOS>",
                        "inputConfig": {}
                    }
                }
            }
        }
    }
    if api_url:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            resp = requests.post(api_url, json=body, headers=headers, timeout=30)
            resp.raise_for_status()
            return {"text": resp.text, "status_code": resp.status_code}
        except Exception as e:
            return {"error": str(e)}
    # Fallback dummy response for offline use
    return {"text": "(デバッグ) モデル呼び出しは未設定です。", "status_code": 200}


def run(query: str, num_results: int = 3, model: str = "ibm/granite-4-h-tiny", include_system_context: bool = True) -> Dict:
    try:
        results = serpapi_search(query, num=num_results)
    except SerpApiError as e:
        return {"error": str(e)}
    context = build_context(results)
    prompt = build_prompt(query, context)
    messages = []
    if include_system_context:
        system_msg = build_system_message(context)
        messages.append({"role": "system", "content": system_msg})
    messages.append({"role": "user", "content": prompt})
    resp = call_model(messages, model=model)
    return {"prompt": prompt, "messages": messages, "model_response": resp, "sources": context}
