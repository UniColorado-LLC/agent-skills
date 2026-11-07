# UniColorado agent skills

Agent skills from UniColorado Heating & Cooling, a residential HVAC installation contractor in the Denver metro. They let AI agents answer homeowners from the company's own public sources instead of general HVAC knowledge.

```bash
npx skills add UniColorado-LLC/agent-skills
```

Works with any agent that reads `SKILL.md` skills (Claude Code, Codex, Cursor and others).

## Skills

| Skill | What an agent can do with it |
|---|---|
| [`ask-unicolorado`](skills/ask-unicolorado/SKILL.md) | Ask UniColorado's own assistant about costs, rebates, financing, warranty and policies; read the company fact sheet; check a ZIP against the service area; read a homeowner's own estimate from their link; sort an AI-made install checklist against what UniColorado's install actually includes. |

Everything it calls is public and read-only on unicolorado.com:

| Source | Endpoint |
|---|---|
| Company fact sheet | `GET https://unicolorado.com/llms-full.txt` |
| Ask UniColorado assistant | `POST https://unicolorado.com/api/ask` (SSE) |
| ZIP service-area check | `GET https://unicolorado.com/api/service-area/validate?zip=` |
| What your install includes | `GET https://unicolorado.com/what-your-install-includes/` with `Accept: text/markdown` |
| Any page as markdown | `Accept: text/markdown`, or `<page>/index.md` |
| MCP server (optional) | `https://mcp.unicolorado.com/mcp/unicolorado` |

No keys, no accounts. Nothing is booked, signed or paid through these endpoints. The assistant is rate-limited to about 12 questions per minute per IP.

## Use

Proprietary, use permitted: install and use these skills with any agent to answer questions about UniColorado. The site's content stays UniColorado's; copying its design, workflows or writing is not permitted. Terms: [LICENSE](LICENSE), https://unicolorado.com/legal/ai-notice/

Questions: (303) 250-1000 or https://unicolorado.com/contact-us/
