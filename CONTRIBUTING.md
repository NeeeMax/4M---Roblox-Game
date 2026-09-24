# Contributing to 4M

## 0. Team access (Max, once per new teammate)

1. **GitHub:** repo → Settings → Collaborators → *Add people* → the teammate's GitHub username. They accept the email invite.
2. **Roblox:** be Roblox friends, then open the main place → **Collaborate** (or File → Game Settings → Permissions)
   → add their Roblox username with **Edit**. The place then shows up in their Studio.

## 1. One-time setup (each developer)

1. Clone the repo to a normal local folder — **not** inside Synology Drive, OneDrive, Dropbox or any other sync tool. Sync tools corrupt `.git`.
2. Set your git identity so commits link to your GitHub account:
   ```
   git config --global user.name  "Your Name"
   git config --global user.email "<id>+<username>@users.noreply.github.com"
   ```
   (Find the noreply address under GitHub → Settings → Emails.)
3. Install VS Code and the recommended extensions (VS Code will prompt you; list in `.vscode/extensions.json`).
4. Install [Rokit](https://github.com/rojo-rbx/rokit) (Windows: download the `windows-x86_64` zip from the
   latest release, unzip, run `.\rokit.exe self-install`, then open a new terminal). In the repo folder run:
   ```
   rokit install
   ```
   This installs the tool versions pinned in `rokit.toml` (Rojo, StyLua, selene, luau-lsp). Answer **yes** when
   Rokit asks whether to trust each tool. To upgrade a tool, run `rokit update <tool>` and commit `rokit.toml` in its own PR.

## 1b. Checks (same as CI)

Every PR runs `.github/workflows/ci.yml`: StyLua, selene and luau-lsp must pass before merging. Run them locally first
(Git Bash, from the repo root):

```
stylua src                 # formats files (CI runs `stylua --check src`)
selene src                 # lint
rojo sourcemap default.project.json --output sourcemap.json
curl -sSfL -o globalTypes.d.luau https://raw.githubusercontent.com/JohnnyMorganz/luau-lsp/main/scripts/globalTypes.None.d.luau
luau-lsp analyze --definitions=globalTypes.d.luau --sourcemap=sourcemap.json src
```

`sourcemap.json` and `globalTypes.d.luau` are generated and git-ignored. `luau-lsp analyze` reports "no files provided"
while `src/` has no `.luau` files yet — CI skips the step in that case.

## 2. Roblox places

| Place | Who | Purpose | Code comes from |
|-------|-----|---------|-----------------|
| **4M (main)** — Team Create | both | building the world, maps, UI layout, playtests together | `main` only |
| **4M Dev – Max** | Max | syncing + testing your branch | your local clone |
| **4M Dev – Marco** | Marco | syncing + testing your branch | your local clone |

Why separate dev places: Script Sync pushes whatever is on your disk into the place. If you switch git branches
while synced to the shared Team Create place, your branch's code lands in your teammate's session.

To refresh a dev place with the latest world: in the main place, save the world as a copy or re-publish to the dev place.

### 3D models and other assets

- Models are built in the **main place** and kept in **`ReplicatedStorage/Assets`** with fixed names (e.g. `Ball`, `Shooter`, `Island`).
  Code uses them by exactly these names (falling back to plain parts if one is missing — wired up per asset as models arrive). Renaming an asset = code change in the same PR.
- To get them into a dev place: right-click the model → **Convert to Package**, then insert it in the dev place from
  Toolbox → Inventory → Packages (updates can flow automatically). Quick alternative: copy/paste into the same folder.
- Owner: Marco (see `docs/ARCHITECTURE.md`).

## 3. Connecting Studio (Script Sync)

In your **dev place**, create these three folders (hover over the parent in the Explorer → **⊕** → Folder), then right-click each → **Sync to…** → choose the repo's **`src`** folder for all three.
Studio adds the Studio folder's name itself, so `Server` ends up as `src/server` (Windows ignores the case). Choosing `src/server` directly creates an empty `src/server/Server` instead.

| Studio folder | Sync to… | Resulting local folder |
|---------------|----------|------------------------|
| `ServerScriptService/Server` | `src` | `src/server` |
| `StarterPlayer/StarterPlayerScripts/Client` | `src` | `src/client` |
| `ReplicatedStorage/Shared` | `src` | `src/shared` |

After syncing, `Server` must contain `Main` and `Services`. If a folder stays empty, the sync points to the wrong place.

Studio remembers the sync for that place. If Studio shows the conflict dialog on start, choose **Keep Disk** — git is the source of truth for code.

Do **not** leave Script Sync running in the shared main place. To update its code after merges:

1. `git checkout main && git pull` — make sure nothing uncommitted is lying around.
2. Open the main place, sync the three folders, choose **Keep Disk**.
3. Stop syncing the three folders again, then publish.

Only one person does this at a time; say so in chat first.

`default.project.json` describes the same mapping for Rojo. It is used for tooling (sourcemap for luau-lsp) and lets us switch to Rojo later without restructuring — see `docs/decisions/0001-script-sync-now-rojo-compatible.md`.

## 4. Git workflow

- `main` is protected and always playable. No direct pushes.
- **Merging is automatic:** every push to another branch opens a PR into `main` and merges it (merge commit) as soon as
  CI is green (`.github/workflows/auto-merge.yml`). A red check blocks the merge: fix it and push again.
- Each developer may keep one long-lived branch; bigger features get their own.
  - Branch names: `feat/<area>-<name>`, `fix/<area>-<name>`, `docs/<name>`, `chore/<name>`
- Bring in `main` before every task and every push (merge, not rebase: branches are shared with GitHub):
  ```
  git fetch origin
  git merge --no-edit origin/main
  ```
- Reviews are optional: look at merged PRs on GitHub to see what the other developer changed.
- Contract changes (`src/shared/Net/`, `src/shared/Types/`, `docs/CONVENTIONS.md`) get their own small PR, merged first.
- Never commit place files (`.rbxl`, `.rbxlx`). Export single models as `.rbxm` into `assets/` only when really needed.

## 5. Daily workflow

1. Pick a task in your area (ownership: `docs/ARCHITECTURE.md`). Bring in `main` (section 4).
2. Code (with Claude Code if you like) and test in **your own dev place**. Don't switch branches while you playtest — Studio loads whatever is on disk.
3. Run the checks (section 1b), commit, bring in `main` again, push. GitHub opens and merges the PR by itself.
4. The other developer brings in `main` before their next task; their Studio updates on its own (Stop → Play).

### Automatic merging: one-time GitHub setup (repo owner)

1. **Settings → General → Pull Requests:** tick **Allow merge commits** and **Allow auto-merge**.
2. **Settings → Actions → General → Workflow permissions:** choose **Read and write permissions** and tick
   **Allow GitHub Actions to create and approve pull requests** → Save.
3. **Settings → Branches → Add branch protection rule** (or Rules → Rulesets) for `main`: tick **Require status checks
   to pass** and add the check **StyLua, selene, luau-lsp**. Do **not** require approvals (that would block auto-merge).
5. From time to time, one person loads `main` into the main place (section 3) and publishes. Say so in chat first.

Playing together: in the main place, **Test → Team Test** starts a server you can both join. The published game gives everyone their own island.

## 6. Working with Claude Code

- Each developer runs Claude Code only in their own clone, on their own branch.
- Work is split by **feature area**, not by server vs client. Ownership is listed in `docs/ARCHITECTURE.md`.
- `CLAUDE.md` holds the rules every instance must follow. Change it via PR like any other file.
- The PR description is the hand-off: the other developer's Claude reads it before building on your work.
- If one person runs two instances at once, use `git worktree add ../4M-<branch> <branch>` so they never share a working tree.
