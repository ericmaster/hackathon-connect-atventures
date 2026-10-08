# AGENTS.md

## What
Hackathon Connect atVentures 2026. Thu Oct 8. Solo dev: Eric.
Sponsors: Farmaenlace (pharmacy group, EC) + BYD.
Retos: fidelización | servicio cliente/postventa | mejora operativa.
Idea: Generative UI omnichannel. Personalized exp per brand/customer type. Cross-brand via SmartClub.
- Web: hybrid = classic web + prompt that generates UI (ref: nimblersoft.com).
- Mobile: prompt input + chat + big audio-first button (people don't use tech).
- NO forms. NO complex classic UI. MVP = simplest possible.
- KPIs to pitch: SmartClub frequency, ticket, share of wallet. ~2% online = context only.

## Rules
- Build product TODAY in event. No pre-built product. Old projects = reference ok.
- Declare: own code vs libs vs AI vs 3rd-party data.
- Demo must say what real vs simulated.
- Synthetic data only. No real personal/health/payment data.
- Freeze 15:45. Deliver: repo + public deployed demo URL + short PPT (what/why). Finalist pitch 3 min.

## Score (100)
value/impact 30 | tech 25 | novelty 20 | viability 15 | demo 10

## Stack
- app/: SvelteKit 3 + Svelte 5 + Tailwind 4 PWA. Static (adapter-static, SPA fallback). Native SvelteKit SW.
- Host: AWS Amplify Hosting manual deploy (`app/deploy.sh`).
- AI: AWS Bedrock planned (max 1 RPS). Now all mocked: app/src/lib/mock.
- Keep small. Ship working demo > features.

## Context hygiene
- Read only what task needs.
- Event facts: docs/DRIVE-SUMMARY.md. Audio notes: docs/AUDIOS-SUMMARY.md (when ready).
- Progress tracker = services/dashboard/progress.json. Edit it, bump updated_at.
- Infra/tools: TOOLING.md. Don't touch infra unless asked.
- GenUI ref (read-only, not in repo): /workspace/reference/nimblersoft-web (SvelteKit+Hono on CF Workers, A2UI JSON → Svelte comps). Copy patterns ok, declare it.
- No secrets in repo. Env → .env (gitignored).
- Short commits. Small diffs.

## MCP
- gemini-notebook-mcp (NotebookLM, Eric personal acct). Read ok. Delete/share/public/save_auth → ASK Eric first.
