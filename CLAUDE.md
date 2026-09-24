# CLAUDE.md — rules for every Claude Code instance working on 4M

Two developers each run their own Claude Code instance against their own clone of this repo.
Read this file fully before any task. It overrides your defaults.

## Staying in sync (merging is automatic)

Every push to any branch except `main` runs CI; when it is green, CI opens a pull request into `main` and merges it
(`.github/workflows/ci.yml`, job "Merge into main"). Nobody merges by hand. Consequences for you:

- **Before starting a task and before every push**, bring in the other developer's work:
  `git fetch origin` then `git merge --no-edit origin/main`. Resolve conflicts, re-run the checks.
- **Push after every finished change**: your human expects it, and the other developer only sees merged work.
- Only push what passes the checks and runs in Studio: it lands in `main` within minutes.
- Bump `Label` in `src/shared/Config/Build.luau` when a push changes something visible in a playtest; it is printed
  in Output, so both developers can see which version their Studio runs.
- Never push to `main` directly, never force-push.

## Before you start a task

1. Sync (see above). Work on your own branch; one long-lived branch per developer is fine
   (Max: `feat/bonk-core-loop`, Marco: `feat/economy-admin-marco`). For bigger features create `feat/<area>-<short-name>`.
2. Read `docs/ARCHITECTURE.md` (ownership + load order) and, if the task touches the network, `docs/NETWORK.md`.
3. Read the last few merged PRs (`git log --oneline -20 main`) to see what the other developer changed.
4. If the task touches an area owned by the other developer (see ownership table in `docs/ARCHITECTURE.md`), stop and ask your human first.

## Project layout (do not invent new top-level folders)

| Local path     | Studio location                                   | Runs on |
|----------------|---------------------------------------------------|---------|
| `src/server/`  | `ServerScriptService/Server`                      | server  |
| `src/client/`  | `StarterPlayer/StarterPlayerScripts/Client`       | client  |
| `src/shared/`  | `ReplicatedStorage/Shared`                        | both    |

File name → instance type (Script Sync / Rojo convention):
`Name.luau` = ModuleScript · `Name.server.luau` = Script · `Name.client.luau` = LocalScript · `Folder/init.luau` = ModuleScript with children.

## Hard rules

- **Exactly one Script per side.** `src/server/Main.server.luau` and `src/client/Main.client.luau` are the only entry points. Everything else is a ModuleScript loaded by them. Never add another `.server.luau` or `.client.luau` file.
- **`--!strict` at the top of every `.luau` file.** Fix type errors; do not silence them with `any` unless the reason is written in a comment.
- **The server is authoritative.** Never trust data from the client. Every remote handler validates type, range and rate before acting.
- **Remotes are defined only in `src/shared/Net/`** and documented in `docs/NETWORK.md` in the same PR. No `Instance.new("RemoteEvent")` anywhere else.
- **`src/shared/` has no side effects on require.** No connections, no loops, no instance creation at module load.
- **No attributes or tags on scripts.** Script Sync does not support synced scripts with attributes/tags. Put configuration in `src/shared/Config/`.
- **No deprecated APIs:** use `task.wait/spawn/defer/delay`, not `wait/spawn/delay`. When connecting `Players.PlayerAdded`, also handle players who joined before the connection.
- **Contract changes go in their own PR.** Changes to `src/shared/Net/`, `src/shared/Types/`, or `docs/CONVENTIONS.md` are split out, merged first, and features build on top.
- **Do not edit `main` directly, do not force-push shared branches, do not commit `.rbxl`/`.rbxlx` files.**

## Before you commit

- Run formatting and linting (once the toolchain is installed, see `CONTRIBUTING.md`):
  `stylua src` · `selene src`
- Update the docs your change affects (`ARCHITECTURE.md`, `NETWORK.md`, `GAME_DESIGN.md`) in the same PR.
- Commit messages: imperative, short, prefixed with the area: `rounds: add intermission timer`.

## PR description (this is how the two instances communicate)

The pull request is opened automatically. If `gh` is available, replace its body with the filled-in
`.github/pull_request_template.md` (`gh pr edit <branch> --body-file <file>`). The other developer's Claude reads
merged PRs later, so be explicit about changed remotes, changed types, and how to test in Studio. Commit messages
must be clear either way; they are the minimum record.

## When unsure

Ask your human. Do not guess at game design decisions; if `docs/GAME_DESIGN.md` does not answer it, it is not decided yet.
