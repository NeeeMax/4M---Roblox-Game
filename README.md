# 4M — GET BONKED

NPCs lob silly objects at your own floating island; run and jump into them to get bonked and earn Bonk Points.
A Roblox game built by two developers with Roblox Studio, GitHub, Claude Code and Studio Script Sync.

> Status: playable MVP prototype (one island per player, shooters, hits, upgrade shop, saving).

## Where things are

| What | Where |
|------|-------|
| What the game is | [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md) |
| How the code is organised, who owns what | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Every RemoteEvent / RemoteFunction | [`docs/NETWORK.md`](docs/NETWORK.md) |
| Code style and naming | [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) |
| Why we decided things | [`docs/decisions/`](docs/decisions/) |
| Setup, git workflow, Studio sync | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Rules for Claude Code | [`CLAUDE.md`](CLAUDE.md) |
| Tasks | GitHub Issues |

## Source layout

```
src/
├─ server/   → ServerScriptService/Server
├─ client/   → StarterPlayer/StarterPlayerScripts/Client
└─ shared/   → ReplicatedStorage/Shared
```

Code lives in git. The world (map, models, UI layout) lives in the Roblox place.
