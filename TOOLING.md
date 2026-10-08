# Tooling (box = Huayna's machine, Debian 13, no systemd)

## CLIs
- node v24 (nvm default) | system node v20 in /usr/bin
- pnpm 10, git, jq, gh (no login), vercel CLI (no login)
- opencode v2 (`opencode`) | openchamber 2.1 (`openchamber`, needs node>=22, opencode>=2.0.20)
- cursor-agent (CLI only, no desktop app) — login pending
- cloudflared, cloudflare-warp (`warp-cli`)
- nlm 0.15.4 (`nlm` + `notebooklm-mcp`, uv tool) — NotebookLM MCP `gemini-notebook-mcp` wired: opencode (global + ./opencode.json), cursor (~/.cursor + ./.cursor/mcp.json). 53 tools = heavy ctx

- aws-cli v2 (/usr/local/bin/aws, no creds yet)
- opencode provider: Kilo Gateway (key stored in opencode auth, also env KILO_API_KEY; no balance → use `kilo/kilo-auto/free` or `:free` models)
- opencode provider: OpenAI via ChatGPT login (ericmaster@nimblersoft.com). Headless: `opencode run -m openai/gpt-5.5 "..." </dev/null` (no stdin or it hangs). NotebookLM MCP validated.
- opencode skills ~/.config/opencode/skills: archify 3.0.1 (symlink → ~/.agents/skills/archify; skills CLI put it there, metadata verified = v3.0.1), with-artifact (copy from artifacts-manager repo).
- agent-fabric (main @04df4c9, built from src; release 0.1.1 lacks 3 agents): 11 agents in ~/.config/opencode/agents, default openai/gpt-6.1-sol (also set as global `model` in ~/.config/opencode/opencode.json; else run fell back to exo-free). Primary: planner, plan-supervisor, bug-fixer, deploy-supervisor. CLI `agent-fabric`/`agf` ~/.local/bin. Src /workspace/reference/agent-fabric.
- GitHub SSH key ~/.ssh/id_ed25519_github (acct ericmaster), ~/.ssh/config host github.com

## Infra
- CF tunnel `huayna-box` (remote-managed, http2 + pinned edge IPs; box DNS is fake → don't change)
- `chamber-huayna.ericmaster.ninja` → localhost:3000 (OpenChamber). CF Access: eric@nimblersoft.com, eric7master@gmail.com, ericmaster@nimblersoft.com. UI pass: `~/.config/openchamber-ui-password`
- CF Mesh node: `100.96.0.8`. SSH: `ssh box@100.96.0.8` (keys only)
- `am-huayna.ericmaster.ninja` → localhost:41820 (artifacts-manager hub). CF Access app "Artifacts Manager Huayna", same 3 emails
- New public hostname = add ingress rule to tunnel + proxied CNAME → `<tunnel-id>.cfargotunnel.com` (+ Access app if private)

## Services
- app (PWA): AWS Amplify app `d2bloxc35rzfqy` (connect-atventures-app, us-east-1, branch main, manual deploy, SPA rewrite rule) → https://main.d2bloxc35rzfqy.amplifyapp.com. Deploy: `app/deploy.sh` (build + zip + create/start-deployment)
- warp watchdog: /usr/local/bin/huayna-warp-watchdog (loop 30s, restarts warp-svc). Log /tmp/warp-watchdog.log. warp-svc died 08:13 Oct 8 once. (no systemd)
- `start-huayna-services` (runs from ~/.bashrc): sshd, cloudflared, warp-svc, openchamber, artifacts-manager, dashboard
- artifacts-manager: /workspace/reference/artifacts-manager, prod build `node build/index.js` (HOST=127.0.0.1 PORT=41820 PROTOCOL_HEADER=x-forwarded-proto), started by start-huayna-services if :41820 free. After git pull → `npm run build` + restart. hackathon-connect registered (`bin/artman register`); `artman setup` NOT run (needs Eric ok)
- dashboard: services/dashboard (node server.js, no deps) 127.0.0.1:41830 → `connect-atventures-dash.ericmaster.ninja` (CF Access "Connect atVentures Dash", same 3 emails). Started by start-huayna-services (pgrep guard). Log /tmp/connect-dashboard.log
- Logs: /var/log/cloudflared-huayna.log, /tmp/warp-svc.log, /tmp/openchamber-start.log, /tmp/artifacts-manager.log

## Pending
- Logins: gh, vercel
- nlm login: `DISPLAY=:<desk> nlm login --storage file` → Chrome on box desktop, Eric sign in eric7master@gmail.com. Creds ~/.notebooklm-mcp-cli/ (never commit)
- AWS Workshop Studio: joined as eric7master@gmail.com. Event "Hackaton | Oct 8th" starts 10/08 00:00, 48h, us-east-1 (Bedrock, Amplify). Console/CLI creds appear on https://catalog.workshops.aws/event/dashboard once started. Bedrock max 1 RPS. Synthetic data only.
