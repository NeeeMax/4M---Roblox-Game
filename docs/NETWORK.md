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
| `ReportHit` | RemoteEvent | C→S | `projectileId: number, onHead: boolean` | number (+ boolean, anything else = false), projectile exists and belongs to the player, not paid, player alive and not immune, report arrives within `ReportGracePeriod` (2 s) after the projectile stopped being collectable (`ProjectilePath.GetCollectEndTime`), path so far passed within radius + `PickupPadding` (2) + `HitTolerance` (6) studs of the server-side root, ≤ 10/s (see `docs/decisions/0003`); `onHead` only counts if the path also passed within radius + `PickupPadding` + `HeadTolerance` of the server-side head | Max |
| `AdminCommand` | RemoteEvent | C→S | `command: string, argument: string \| number \| nil` | sender is admin (`Config/Admin.IsAdmin`, checked on the server), known command, argument validated per command (point amounts only from `Admin.PointAmounts`, upgrade ids only from `Upgrades.Order`), ≤ 10/s | both |
| `BonkHit` | RemoteEvent | S→C | `reward: number, quality: HitQuality, knockbackDirection: Vector3, onHead: boolean, combo: number, comboWindow: number, golden: boolean` | — (server → client) | Max |
| `StateChanged` | RemoteEvent | S→C | `state: PlayerState` (a copy of the whole saved state, `Types.PlayerState`) | — | Marco |
| `Notify` | RemoteEvent | S→C | `message: string, kind: "Info" \| "Good" \| "Bad"` | — | both |
| `RequestSpin` | RemoteEvent | C→S | — | spins left today (1, VIP 2), ≤ 2/s | Max |
| `SpinResult` | RemoteEvent | S→C | `segmentIndex: number, text: string` | — | Max |
| `CoinFlip` | RemoteEvent | C→S | `betFraction: number, side: "Heads" \| "Tails"` | fraction is one of `Hub.CoinFlip.BetFractions`, side valid, bet ≥ MinBet, ≤ 2/s | Max |
| `CoinFlipResult` | RemoteEvent | S→C | `won: boolean, side: "Heads" \| "Tails", amount: number` | — | Max |
| `DuelChallenge` | RemoteEvent | C→S | `targetUserId: number, amount: number` | target in server and not self, amount one of `Hub.Duel.Stakes`, challenger can afford it, no open duel on either side, ≤ 2/s | Max |
| `DuelInvite` | RemoteEvent | S→C | `duelId: number, challengerName: string, amount: number` | — | Max |
| `DuelRespond` | RemoteEvent | C→S | `duelId: number, accept: boolean` | duel exists, sender is its target, not expired, both can still afford it, ≤ 2/s | Max |
| `DuelResult` | RemoteEvent | S→C | `won: boolean, opponentName: string, amount: number, side: "Heads" \| "Tails"` | — | Max |
| `ClaimQuest` | RemoteEvent | C→S | `questIndex: number` | quest exists today, finished, not claimed, ≤ 5/s | Max |
| `ShopBuy` | RemoteEvent | C→S | `itemId: string` | known pass / product / `Trophy_<id>`, not owned yet, product-specific checks (top tier, starter pack once), points trophies: enough Bonk Points; Robux items only open Roblox's prompt, granting happens in ProcessReceipt / PromptGamePassPurchaseFinished; ≤ 3/s | Max |
| `UseBonkRain` | RemoteEvent | C→S | — | has a Bonk Rain, none running, on own island, ≤ 2/s | Max |
| `BonkRainStarted` | RemoteEvent | S→C | `seconds: number` | — | Max |
| `ClaimStreak` | RemoteEvent | C→S | — | today's streak reward not claimed yet, ≤ 5/s | Max |
| `ClaimPlaytime` | RemoteEvent | C→S | `giftIndex: number` | gift exists, enough play time today, not claimed, ≤ 5/s | Max |
| `ServerEvent` | RemoteEvent | S→C | `eventId: string, time: number` — `eventId` = the running server event (`Config/Events`) and `time` = when it ends; `eventId ""` = no event, `time` = when the next one starts (server clock, `Workspace:GetServerTimeNow()`). Sent to everyone on start / end and to each player on join | — (server → client) | Max |
| `ClaimIndex` | RemoteEvent | C→S | `entryId: string` | string, known `Config/Index` entry that the player has seen and not claimed yet (or `Index.CompleteId` "Complete": every entry seen, bonus not claimed), ≤ 5/s; reward computed on the server (`RewardService.Hits`) | Max |

Remotes live in `ReplicatedStorage/Remotes`, created by `Net.CreateRemotes()` from `Main.server.luau`. Get one with `Net.Get(Net.BonkHit)`.
`StateChanged` is sent after the player's data loads and after every change to points, levels or active shooters.
Projectiles are invisible, anchored marker parts in `Workspace/Islands/Island_<UserId>/Projectiles`. They carry the
attribute `ProjectileId` (number) so the client can report hits, plus their planned path (`LaunchTime` on the server
clock, `Gravity`, `SettleTime`, `EndTime`, `FadeTime`, `Diameter`, `SegmentCount`, `S<n>Time/Position/Velocity`), written and read only by
`src/shared/Util/ProjectilePath.luau`, and `Paid` (true once it paid out), `Golden` and `Mega` (the MegaStick event's giant stick; its bigger size is already in `Diameter`). Clients draw the model along that path
(`docs/decisions/0004`): small settling hops from `SettleTime`, lying still from `EndTime`, fully faded at `EndTime + FadeTime`.
Shooter models (the imported Shiba inside `Workspace/Islands/Island_<UserId>/…/Shooter`) carry two attributes, both
server → client only and purely visual (`Controllers/ShibaController`):
- `AimYaw` (number, radians): the yaw the model should face (pivot rotation `CFrame.Angles(0, AimYaw, 0)`,
  `YawOffsetDegrees` included). Set when the model is built and whenever the Shiba picks a target; the server never
  turns the model itself, clients turn it there smoothly. The model's invisible `ShibaPivot` part (its PrimaryPart)
  marks the rest pose they turn from.
- `ThrowAt` (number, server clock `Workspace:GetServerTimeNow()`): when the projectile leaves the paw. The server sets
  it when the Shiba starts aiming and clears it when the throw is cancelled; clients swing the `ThrowArm` toward that
  moment.
`BonkHit` drives the client-only effects: popup, sound, knockback (the owning client moves its own character), head-hit
bonus text and the combo counter (`combo` hits in a row; it ends if no hit follows within `comboWindow` seconds).

Direction: `C→S` client to server, `S→C` server to client, `S→All` broadcast.
