"""Simple runner script to test the MCP agent locally.

Usage:
    python scripts/run_mcp.py "your query here"

Ensure SERPAPI_KEY is set in env for real searches. If not set, the agent will raise.
"""
import argparse
from mcp.agent import run


def print_sources(sources, show_full: bool = False):
    if not sources:
        print("(no sources)")
        return
    for i, s in enumerate(sources, 1):
        print(f"[{i}] {s.get('title')}")
        print(f"    URL: {s.get('url')}")
        if s.get('fetch_error'):
            print(f"    fetch_error: {s.get('fetch_error')}")
        if s.get('summary'):
            print(f"    summary: {s.get('summary')[:1000]}")
        if show_full and s.get('full_text'):
            print("    --- full_text (truncated 2000 chars) ---")
            print(s.get('full_text')[:2000])
        print("")


def main():
    p = argparse.ArgumentParser(description="Run MCP agent and print retrieved context")
    p.add_argument("query", help="Search query / user question")
    p.add_argument("--no-system", dest="include_system", action="store_false", help="Do not include system context when calling model")
    p.add_argument("--num", type=int, default=3, help="Number of search results to fetch")
    p.add_argument("--show-full", action="store_true", help="Print fetched full text for each source (may be large)")
    p.add_argument("--model", default="ibm/granite-4-h-tiny", help="Model id to pass to call_model")
    args = p.parse_args()

    out = run(args.query, num_results=args.num, model=args.model, include_system_context=args.include_system)
    messages = out.get("messages") or []
    # show system message if present
    system_msgs = [m for m in messages if m.get("role") == "system"]
    if system_msgs:
        print("--- System message (context passed to model) ---")
        print(system_msgs[0].get("content"))
        print("--- End system message ---\n")

    print("--- User prompt sent to model (truncated) ---")
    print(out.get("prompt")[:4000])
    print("\n--- Sources (summary) ---")
    print_sources(out.get("sources", []), show_full=args.show_full)
    print("--- Model response ---")
    print(out.get("model_response"))


if __name__ == "__main__":
    main()
