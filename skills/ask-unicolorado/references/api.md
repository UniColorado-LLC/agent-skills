# Ask UniColorado API contract

`POST https://unicolorado.com/api/ask`. No auth. Same endpoint the chat on unicolorado.com uses.

## Request

JSON body, max 32 KB:

| Field | Required | Notes |
|---|---|---|
| `message` | yes | The new question. Cut at 4,000 characters. |
| `conversationId` | no | From the previous turn. Omit on the first turn. The server keeps the history; never send the transcript. Unknown or expired ids start a fresh conversation (24 h inactivity). |
| `t` | no | Estimate token from the homeowner's own estimate link (`?t=...`). First turn only; later values are ignored. |
| `retry` | no | `true` re-answers the last question if it never got a reply. |
| `distinctId` | no | Analytics id. Agents should send `agent-skill-ask-unicolorado`. Never send an email or phone number. |

## Response

`200` with `Content-Type: text/event-stream`. Frames, in order:

| Event | Data | Meaning |
|---|---|---|
| `status` | `{estimateLinkState, conversationId}` | Always first. Save `conversationId`. |
| `progress` | `{tool}` | The assistant is looking something up. Ignore. |
| `delta` | `{t}` | Append `t` to the answer. |
| `reset` | `{}` | Discard the answer text so far; the model is starting over after a lookup. |
| `done` | `{estimateLinkState, conversationId, tools, actions, followups}` | Turn finished. `actions[].href` is site-relative (prefix `https://unicolorado.com`) or a `tel:`/`sms:` URI. |
| `error` | `{message, aborted}` | Turn failed. `message` is safe to show. |

`estimateLinkState`: `absent` (no link sent), `valid`, `invalid` (expired or wrong link: ask the homeowner to request a fresh one), `unavailable` (lookup down: try later), `unknown`.

## Errors before the stream

| Status | Body | Do |
|---|---|---|
| 400 | `No message provided` / `Invalid request` | Fix the JSON. |
| 413 | `Request too large` | Shorten the message. |
| 429 | plain text, `Retry-After` header | Wait that many seconds. Limit is about 12 requests per minute per IP. |
| 503 | plain text | Assistant is off. Use the fact sheet and the phone number. |

## curl

```bash
curl -sN https://unicolorado.com/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"message":"Do you install heat pumps in Littleton?","distinctId":"agent-skill-ask-unicolorado"}'
```

Concatenate the `t` values of the `delta` frames after the last `reset` to get the answer.
