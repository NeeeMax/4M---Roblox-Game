# Network contract — 4M

Every RemoteEvent and RemoteFunction is listed here. A PR that adds or changes a remote updates this file in the same PR.

## Rules

- Remotes are created only in `src/shared/Net/`.
- The server validates **every** argument from the client: type, range, ownership (does this player own this item?), and rate (how often per second).
- Prefer RemoteEvents. Never use `RemoteFunction:InvokeClient` — a client can hang the server thread.
- Payloads are small and flat. Send IDs, not instances or whole tables of state.
- Use UnreliableRemoteEvent only for high-frequency cosmetic data that may be dropped.

## Remotes

| Name | Type | Direction | Payload | Server validation | Owner |
|------|------|-----------|---------|-------------------|-------|
| `RequestPurchase` | RemoteEvent | C→S | `upgradeId: string` | string, known upgrade id, below max level, enough Bonk Points, ≤ 5/s | Marco |
| `SetActiveShooters` | RemoteEvent | C→S | `count: number` | integer, 1 ≤ count ≤ owned shooters, ≤ 5/s | Marco |
| `ReportHit` | RemoteEvent | C→S | `projectileId: number` | number, projectile exists and belongs to the player, not paid, player alive and not immune, flight path passed within radius + 6 studs of the server-side root, ≤ 10/s (see `docs/decisions/0003`) | Max |
| `AdminAddPoints` | RemoteEvent | C→S | `amount: number` | sender is admin (`Config/Admin.IsAdmin`, checked on the server), amount is one of `Admin.PointAmounts`, ≤ 5/s | Marco |
| `BonkHit` | RemoteEvent | S→C | `reward: number, quality: HitQuality, knockbackDirection: Vector3` | — (server → client) | Max |
| `StateChanged` | RemoteEvent | S→C | `bonkPoints: number, upgradeLevels: { [UpgradeId]: number }, activeShooters: number` | — (server → client) | Marco |

Remotes live in `ReplicatedStorage/Remotes`, created by `Net.CreateRemotes()` from `Main.server.luau`. Get one with `Net.Get(Net.BonkHit)`.
`StateChanged` is sent after the player's data loads and after every change to points, levels or active shooters.
Projectiles are invisible, anchored marker parts in `Workspace/Islands/Island_<UserId>/Projectiles`. They carry the
attribute `ProjectileId` (number) so the client can report hits, plus their planned path (`LaunchTime` on the server
clock, `Gravity`, `EndTime`, `Diameter`, `SegmentCount`, `S<n>Time/Position/Velocity`), written and read only by
`src/shared/Util/ProjectilePath.luau`, and `Paid` (true once it paid out). Clients draw the model along that path
(`docs/decisions/0004`).
`BonkHit` drives the client-only effects: popup, sound and knockback (the owning client moves its own character).

Direction: `C→S` client to server, `S→C` server to client, `S→All` broadcast.
