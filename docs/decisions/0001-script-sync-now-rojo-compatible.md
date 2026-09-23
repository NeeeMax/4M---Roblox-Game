# 0001 — Use Studio Script Sync, keep the layout Rojo-compatible

- Status: accepted
- Date: 2026-09-23

## Context

We need code in git (for GitHub, reviews and Claude Code) while building the world in Roblox Studio.
Options: Roblox Studio Script Sync (built in, fully released) or Rojo (third-party, file system is the source of truth).

Script Sync syncs only Scripts, LocalScripts, ModuleScripts and Folders, both directions. It does not sync scripts that have attributes or tags,
and Roblox advises against multiple people syncing and editing the same scripts at the same time.
Roblox's own docs recommend Rojo when the file system should be the single source of truth.

## Decision

- Use **Script Sync** for now: no extra Studio plugin, works out of the box.
- Git is the source of truth for code. On sync conflicts: **Keep Disk**.
- Each developer syncs only into their **own dev place**. The shared Team Create place is not left synced (see `CONTRIBUTING.md`).
- Use the file naming that Script Sync and Rojo share (`.server.luau`, `.client.luau`, `init.luau`).
- Keep `default.project.json` with the same mapping. It generates a sourcemap for luau-lsp and makes a switch to Rojo a config change, not a restructure.

## Revisit when

- Syncing overwrites work more than once, or
- we need to version non-script instances (e.g. UI built from code, models), or
- keeping the main place in sync with `main` becomes a chore.

Then switch to Rojo.
