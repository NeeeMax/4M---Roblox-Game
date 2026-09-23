# Conventions — 4M

## Files and naming

| Thing | Style | Example |
|-------|-------|---------|
| ModuleScript file | PascalCase | `DataService.luau` |
| Server / client entry | fixed | `Main.server.luau`, `Main.client.luau` |
| Folders | PascalCase | `Services/`, `Controllers/` |
| Local variables, functions | camelCase | `local playerData`, `local function getCoins()` |
| Module tables, types | PascalCase | `local DataService = {}`, `type PlayerData = {...}` |
| Constants | UPPER_SNAKE_CASE | `MAX_PLAYERS` |
| Private module members | leading underscore | `DataService._cache` |
| Remote names | PascalCase verb phrase | `RequestPurchase`, `RoundStarted` |

File and folder names must be valid on Windows and macOS: no duplicates in one folder, no `: * ? " < > |`.

## Code

- First line of every file: `--!strict`.
- Services via `game:GetService("...")` at the top of the file, never `game.Players`.
- `task.*` instead of `wait`, `spawn`, `delay`.
- Every connection that outlives its owner is disconnected (store it, clean it up on `PlayerRemoving` / destroy).
- Errors from DataStores and other web calls are handled with `pcall` and retried with backoff.
- No magic numbers in logic — put them in `shared/Config`.
- Comments explain **why**, not what.

## Formatting and linting

- Formatter: StyLua (`stylua.toml`). Linter: selene (`selene.toml`). Type checking: luau-lsp.
- Formatting is not discussed in reviews — StyLua decides.

## Commits and branches

- Branch: `feat/<area>-<name>`, `fix/<area>-<name>`, `docs/<name>`, `chore/<name>`
- Commit: `<area>: <imperative summary>` — e.g. `rounds: add intermission timer`
