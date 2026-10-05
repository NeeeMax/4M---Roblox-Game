# Traps that cost days

Read before working in Studio. Add a line whenever something costs you more than an hour. Newest at the bottom of each section.

## Script Sync / Studio

- **`.client.luau` becomes a `Script` with RunContext `Client`, not a LocalScript.** It also runs from the
  `StarterPlayerScripts` template, so `Main.client.luau` returns early there. Studio warns about it — ignore the
  warning. Never set RunContext to `Legacy`: that turns it into a server script and the whole client stops.
- **"Sync to…" must point at `src`** for all three folders; Studio appends the folder name itself.
- **No attributes or tags on synced scripts** — Script Sync drops them. Values go into `src/shared/Config/`.
- **Code edited in Studio is lost or conflicts.** Edit the files in `src/`; Studio only mirrors them.
- **FBX models are imported by hand per place** (Home → Import). Dragging/cut-paste in Explorer is flaky; reparent
  with the command bar instead.
- **Robux products, passes and Max Players** live only on the Creator Hub (create.roblox.com), not in Studio.

## Gameplay / engine

- **Server physics for projectiles hangs at bounces.** Clients draw projectiles from the planned path (ADR 0004);
  the server validates hits against the analytic path (ADR 0003).
- **`Players.PlayerAdded` misses players who joined before the connection** — also loop over `Players:GetPlayers()`.

## Git

- **CI squash-merges into `main`.** Merging `origin/main` back can conflict with your own older commits: check with
  `git diff <squash> <your commit>` and keep yours.

## Asset pipeline

- **Open Cloud uploads images as-is** (`assets/upload.py`): a white background stays white. Cut it out before uploading UI icons.
- **Open Cloud model uploads (.fbx/.rbxm) become packages.**
- **Cloudflare flux-1-schnell** rejects a `seed` field and some requests when 6 run in parallel (HTTP 400) — send them one after another.
