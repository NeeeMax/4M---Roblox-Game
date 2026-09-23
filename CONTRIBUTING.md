# Contributing to 4M

## 1. One-time setup (each developer)

1. Clone the repo to a normal local folder — **not** inside Synology Drive, OneDrive, Dropbox or any other sync tool. Sync tools corrupt `.git`.
2. Set your git identity so commits link to your GitHub account:
   ```
   git config --global user.name  "Your Name"
   git config --global user.email "<id>+<username>@users.noreply.github.com"
   ```
   (Find the noreply address under GitHub → Settings → Emails.)
3. Install VS Code and the recommended extensions (VS Code will prompt you; list in `.vscode/extensions.json`).
4. Install the toolchain with [Rokit](https://github.com/rojo-rbx/rokit):
   ```
   rokit install
   ```
   > Until `rokit.toml` exists, see issue "Set up toolchain + CI" — the first person to do it runs
   > `rokit init`, then `rokit add rojo-rbx/rojo`, `rokit add JohnnyMorganz/StyLua`,
   > `rokit add Kampfkarren/selene`, `rokit add JohnnyMorganz/luau-lsp`, and commits `rokit.toml`.

## 2. Roblox places

| Place | Who | Purpose | Code comes from |
|-------|-----|---------|-----------------|
| **4M (main)** — Team Create | both | building the world, maps, UI layout, playtests together | `main` only |
| **4M Dev – Max** | Max | syncing + testing your branch | your local clone |
| **4M Dev – <friend>** | friend | syncing + testing your branch | your local clone |

Why separate dev places: Script Sync pushes whatever is on your disk into the place. If you switch git branches
while synced to the shared Team Create place, your branch's code lands in your teammate's session.

To refresh a dev place with the latest world: in the main place, save the world as a copy or re-publish to the dev place.

## 3. Connecting Studio (Script Sync)

In your **dev place**, create these folders if they don't exist, then right-click each → **Sync to…** → choose the local folder:

| Studio folder | Local folder |
|---------------|--------------|
| `ServerScriptService/Server` | `src/server` |
| `StarterPlayer/StarterPlayerScripts/Client` | `src/client` |
| `ReplicatedStorage/Shared` | `src/shared` |

Studio remembers the sync for that place. If Studio shows the conflict dialog on start, choose **Keep Disk** — git is the source of truth for code.

Do **not** leave Script Sync running in the shared main place. To update its code after merges:

1. `git checkout main && git pull` — make sure nothing uncommitted is lying around.
2. Open the main place, sync the three folders, choose **Keep Disk**.
3. Stop syncing the three folders again, then publish.

Only one person does this at a time; say so in chat first.

`default.project.json` describes the same mapping for Rojo. It is used for tooling (sourcemap for luau-lsp) and lets us switch to Rojo later without restructuring — see `docs/decisions/0001-script-sync-now-rojo-compatible.md`.

## 4. Git workflow

- `main` is protected and always playable. No direct pushes.
- One issue → one branch → one PR.
  - Branch names: `feat/<area>-<name>`, `fix/<area>-<name>`, `docs/<name>`, `chore/<name>`
- Keep branches short-lived (ideally merged within a few days). Rebase on `main` often:
  ```
  git fetch origin
  git rebase origin/main
  ```
- The **other developer** reviews every PR. Squash-merge.
- Contract changes (`src/shared/Net/`, `src/shared/Types/`, `docs/CONVENTIONS.md`) get their own small PR, merged first.
- Never commit place files (`.rbxl`, `.rbxlx`). Export single models as `.rbxm` into `assets/` only when really needed.

## 5. Working with Claude Code

- Each developer runs Claude Code only in their own clone, on their own branch.
- Work is split by **feature area**, not by server vs client. Ownership is listed in `docs/ARCHITECTURE.md`.
- `CLAUDE.md` holds the rules every instance must follow. Change it via PR like any other file.
- The PR description is the hand-off: the other developer's Claude reads it before building on your work.
- If one person runs two instances at once, use `git worktree add ../4M-<branch> <branch>` so they never share a working tree.
