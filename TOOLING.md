# Tooling (box = Huayna's machine, Debian 13, no systemd)

## CLIs
- node v24 (nvm default) | system node v20 in /usr/bin
- pnpm 10, git, jq, gh (no login), vercel CLI (no login)
- opencode v2 (`opencode`) | openchamber 2.1 (`openchamber`, needs node>=22, opencode>=2.0.20)
- cursor-agent (CLI only, no desktop app) — login pending
- cloudflared, cloudflare-warp (`warp-cli`)

## Infra
- CF tunnel `huayna-box` (remote-managed, http2 + pinned edge IPs; box DNS is fake → don't change)
- `chamber-huayna.ericmaster.ninja` → localhost:3000 (OpenChamber). CF Access: eric@nimblersoft.com, eric7master@gmail.com, ericmaster@nimblersoft.com. UI pass: `~/.config/openchamber-ui-password`
- CF Mesh node: `100.96.0.8`. SSH: `ssh box@100.96.0.8` (keys only)
- New public hostname = add ingress rule to tunnel + proxied CNAME → `<tunnel-id>.cfargotunnel.com` (+ Access app if private)

## Services (no systemd)
- `start-huayna-services` (runs from ~/.bashrc): sshd, cloudflared, warp-svc, openchamber
- Logs: /var/log/cloudflared-huayna.log, /tmp/warp-svc.log, /tmp/openchamber-start.log

## Pending
- Logins: gh, vercel, cursor-agent, opencode providers
- AWS Workshop Studio (event code in docs/drive AWS guide, 1 setup per team)
