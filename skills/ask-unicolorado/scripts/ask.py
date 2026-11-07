#!/usr/bin/env python3
"""Ask UniColorado one question and print the answer.

Calls the public assistant at https://unicolorado.com/api/ask (the same one
behind the chat on unicolorado.com) and reads its server-sent-event stream.
Standard library only.

  python3 ask.py "Do you install Mitsubishi heat pumps in Lakewood?"
  python3 ask.py "And the rebates for that?" --conversation <id from last run>
  python3 ask.py "Explain my options" --estimate-link "<the homeowner's own estimate link>"

Exit codes: 0 answered, 1 request or network error, 2 rate limited or
assistant off (wait, or give the homeowner the phone number).
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://unicolorado.com/api/ask"
SITE = "https://unicolorado.com"
DISTINCT_ID = "agent-skill-ask-unicolorado"
USER_AGENT = "ask-unicolorado-skill/1.0"
MAX_MESSAGE_CHARS = 4000


def estimate_token(link: str) -> str:
    """Accept a full estimate link (…?t=TOKEN) or a bare token."""
    link = link.strip()
    if "://" in link or link.startswith("/"):
        query = urllib.parse.urlparse(link).query
        values = urllib.parse.parse_qs(query).get("t")
        if not values:
            raise ValueError("estimate link has no t= parameter")
        return values[0]
    return link


def absolute(href: str) -> str:
    return href if not href.startswith("/") else SITE + href


def read_stream(resp):
    """Yield (event, data) pairs from an SSE response."""
    event, data = None, []
    for raw in resp:
        line = raw.decode("utf-8").rstrip("\r\n")
        if line == "":
            if event is not None:
                try:
                    yield event, json.loads("\n".join(data)) if data else {}
                except json.JSONDecodeError:
                    pass
            event, data = None, []
        elif line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("message", help="the homeowner's question, in their words")
    parser.add_argument("--conversation", help="conversationId from the previous turn")
    parser.add_argument(
        "--estimate-link",
        help="the homeowner's own UniColorado estimate link or token (first turn only)",
    )
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    args = parser.parse_args()

    body = {"message": args.message[:MAX_MESSAGE_CHARS], "distinctId": DISTINCT_ID}
    if args.conversation:
        body["conversationId"] = args.conversation
    if args.estimate_link:
        try:
            body["t"] = estimate_token(args.estimate_link)
        except ValueError as err:
            print(f"error: {err}", file=sys.stderr)
            return 1

    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": USER_AGENT,
        },
    )

    try:
        resp = urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as err:
        text = err.read().decode("utf-8", "replace").strip()
        retry = err.headers.get("Retry-After")
        detail = f" (retry after {retry}s)" if retry else ""
        print(f"error {err.code}{detail}: {text}", file=sys.stderr)
        return 2 if err.code in (429, 503) else 1
    except (urllib.error.URLError, TimeoutError) as err:
        print(f"error: could not reach {ENDPOINT}: {err}", file=sys.stderr)
        return 1

    answer, done, error, conversation = "", None, None, args.conversation
    with resp:
        for event, data in read_stream(resp):
            if event == "status":
                conversation = data.get("conversationId", conversation)
            elif event == "delta":
                answer += data.get("t", "")
            elif event == "reset":
                # The model began, then called a tool: drop the fragment.
                answer = ""
            elif event == "done":
                done = data
                conversation = data.get("conversationId", conversation)
            elif event == "error":
                error = data.get("message", "unknown error")

    actions = [
        {"label": a.get("label"), "url": absolute(a.get("href", ""))}
        for a in (done or {}).get("actions", [])
    ]
    result = {
        "answer": answer.strip(),
        "conversationId": conversation,
        "estimateLinkState": (done or {}).get("estimateLinkState"),
        "toolsUsed": (done or {}).get("tools", []),
        "actions": actions,
        "followups": (done or {}).get("followups", []),
        "error": error,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["answer"]:
            print(result["answer"])
        if error:
            print(f"\n[assistant error] {error}", file=sys.stderr)
        print(f"\nconversationId: {conversation}")
        if result["estimateLinkState"] not in (None, "absent"):
            print(f"estimate link: {result['estimateLinkState']}")
        for a in actions:
            print(f"action: {a['label']} -> {a['url']}")
        for f in result["followups"]:
            print(f"suggested follow-up: {f}")

    if error and not result["answer"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
