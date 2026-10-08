# Dashboard (master control)
Progreso vs rúbrica + countdown freeze + agenda oficial (Ahora / Próximo hito, `agenda` en progress.json) + infra (AWS/Bedrock). Node, sin deps.
Run: `PORT=41830 node server.js` (127.0.0.1). Público: https://connect-atventures-dash.ericmaster.ninja (CF Access).
Editar `progress.json` (se lee por request): `nota` 1–5 o null, items `s` = todo|doing|done, actualizar `updated_at`.
Lanzado por /usr/local/bin/start-huayna-services. Log /tmp/connect-dashboard.log.
Pestaña Lean Canvas: `canvas.json` (GET/PUT `/api/canvas`, PUT fusiona `{blocks:{key:{title,items,status}}}`, solo con header CF Access o localhost directo; editable desde la UI).
Pestaña Propuesta de valor (método J.D. Montero, NEST.Lab): `value-prop.json` (GET/PUT `/api/value-prop`, PUT fusiona `{versions:{key:{name,template,text,audience,status,checks,note}}}`, mismas reglas de auth); conteo palabras/~s (regla 20 s) y checklist por versión.
