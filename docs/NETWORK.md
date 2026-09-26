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
| `BonkHit` | RemoteEvent | S→C | `reward: number, quality: HitQuality, knockbackDirection: Vector3, onHead: boolean, combo: number, comboWindow: number, golden: boolean, firstBonk: boolean` (quality: `"Normal"` = BONK, after it touched the ground · `"Good"` = AIR BONK · `"Perfect"` = PERFECT BONK, see decisions/0005; `firstBonk` = this was the player's first paid hit, reward already × `EconomyConfig.Bonk.FirstBonkMultiplier`) | — (server → client) | Max |
| `AutomationCatch` | RemoteEvent | S→C | `source: AutomationSource ("Basket" \| "Intern"), projectileId: number, reward: number` — the basket or the intern caught one of the player's sticks (already paid by the server, `AutomationService`); sent only to the owner, **right before** the projectile's `Paid` attribute is set, so `AutomationController` takes the drawn stick over (basket: flies into `Prop_Basket`; intern: bounces off `BonkIntern`'s head) before other controllers react to `Paid`; drives the catch visuals and the "+B$ reward" popup | — (server → client) | Marco |
| `StateChanged` | RemoteEvent | S→C | `state: PlayerState` (a copy of the whole saved state, `Types.PlayerState`) | — | Marco |
| `Notify` | RemoteEvent | S→C | `message: string, kind: "Info" \| "Good" \| "Bad"` | — (server → client). Amounts are written with `Format.Money` ("B$ 1,234"); the HUD draws "B$" as the Bonk Dollars symbol | both |
| `RequestSpin` | RemoteEvent | C→S | — | spins left today (1, VIP 2), ≤ 2/s | Max |
| `SpinResult` | RemoteEvent | S→C | `segmentIndex: number, text: string` | — | Max |
| `CoinFlip` | RemoteEvent | C→S | `betFraction: number, side: "Heads" \| "Tails"` | fraction is one of `Hub.CoinFlip.BetFractions`, side valid, bet ≥ MinBet, ≤ 2/s | Max |
| `CoinFlipResult` | RemoteEvent | S→C | `won: boolean, side: "Heads" \| "Tails", amount: number` | — | Max |
| `DuelChallenge` | RemoteEvent | C→S | `targetUserId: number, amount: number` | target in server and not self, amount one of `Hub.Duel.Stakes`, challenger can afford it, no open duel on either side, ≤ 2/s | Max |
| `DuelInvite` | RemoteEvent | S→C | `duelId: number, challengerName: string, amount: number` | — | Max |
| `DuelRespond` | RemoteEvent | C→S | `duelId: number, accept: boolean` | duel exists, sender is its target, not expired, both can still afford it, ≤ 2/s | Max |
| `DuelResult` | RemoteEvent | S→C | `won: boolean, opponentName: string, amount: number, side: "Heads" \| "Tails"` | — | Max |
| `ClaimQuest` | RemoteEvent | C→S | `questIndex: number` | quest exists today, finished, not claimed, ≤ 5/s | Max |
| `ShopBuy` | RemoteEvent | C→S | `itemId: string` | known pass / product / `Trophy_<id>`, not owned yet, product-specific checks (top tier, instant upgrade not maxed, Double Offline only with pending offline earnings, starter pack once), points trophies: enough Bonk Points; Robux items only open Roblox's prompt, granting happens in ProcessReceipt / PromptGamePassPurchaseFinished; ≤ 3/s | Max |
| `UseBonkRain` | RemoteEvent | C→S | — | has a Bonk Rain, none running, on own island, ≤ 2/s | Max |
| `BonkRainStarted` | RemoteEvent | S→C | `seconds: number` | — | Max |
| `ClaimStreak` | RemoteEvent | C→S | — | today's streak reward not claimed yet, ≤ 5/s | Max |
| `ClaimPlaytime` | RemoteEvent | C→S | `giftIndex: number` | gift exists, enough play time today, not claimed, ≤ 5/s | Max |
| `ServerEvent` | RemoteEvent | S→C | `eventId: string, time: number` — `eventId` = the running server event (`Config/Events`) and `time` = when it ends; `eventId ""` = no event, `time` = when the next one starts (server clock, `Workspace:GetServerTimeNow()`). Sent to everyone on start / end and to each player on join | — (server → client) | Max |
| `ClaimIndex` | RemoteEvent | C→S | `entryId: string` | string, known `Config/Index` entry that the player has seen and not claimed yet (or `Index.CompleteId` "Complete": every entry seen, bonus not claimed), ≤ 5/s; reward computed on the server (`RewardService.Hits`) | Max |
| `OfflineEarnings` | RemoteEvent | S→C | `amount: number, seconds: number` (pending offline earnings, time away they cover) | — (server → client; sent on join when `Bank.Pending` > 0) | Marco |
| `ClaimOffline` | RemoteEvent | C→S | `double: boolean` | boolean, data loaded, `Bank.Pending` > 0, ≤ 2/s; `false` pays Pending and clears it; `true` only opens the Roblox prompt for the "DoubleOffline" product (Studio with id 0: test grant), 2× Pending is paid in ProcessReceipt (`ShopService.Grant`) | Marco |
| `ObbyStarted` | RemoteEvent | S→C | — | — (server → client). Sent when the server sees the character's root leave the start pad (position check 10×/s, alive character) | Max |
| `ObbyFinished` | RemoteEvent | S→C | `time: number, reward: number, bestTime: number, nextRewardAt: number` | — (server → client). Sent only when the server-side run is valid: started from the start pad, root inside the finish zone, ≥ `Obby.MinTime` (8 s), ≥ half of the platforms passed (`Obby.MinStageShare`, invisible zones, no checkpoints), never landed back on the plaza after climbing (`Obby.FallHeight`), ≤ `MaxRunTime`, never left `LeaveRadius`; time measured on the server; reward only if `RewardCooldown` passed since `state.Obby.LastRewardAt` | Max |

Remotes live in `ReplicatedStorage/Remotes`, created by `Net.CreateRemotes()` from `Main.server.luau`. Get one with `Net.Get(Net.BonkHit)`.
`StateChanged` is sent after the player's data loads and after every change to points, levels or active shooters.
Projectiles are invisible, anchored marker parts in `Workspace/Islands/Island_<UserId>/Projectiles`. They carry the
attribute `ProjectileId` (number) so the client can report hits, plus their planned path (`LaunchTime` on the server
clock, `Gravity`, `SettleTime`, `EndTime`, `FadeTime`, `Diameter`, `SegmentCount`, `S<n>Time/Position/Velocity`), written and read only by
`src/shared/Util/ProjectilePath.luau`, and `Paid` (true once it paid out), `Golden`, `Mega` (the MegaStick event's giant stick; its bigger size is already in `Diameter`) and `ValueMultiplier` (number, only when > 1: the stick density cap made it worth that many throws; clients show "×N"). Clients draw the model along that path
(`docs/decisions/0004`): small settling hops from `SettleTime`, lying still from `EndTime`, fully faded at `EndTime + FadeTime`.
Shooter models (the imported Shiba inside `Workspace/Islands/Island_<UserId>/…/Shooter`) carry two attributes, both
server → client only and purely visual (`Controllers/ShibaController`):
- `AimYaw` (number, radians): the yaw the model should face (pivot rotation `CFrame.Angles(0, AimYaw, 0)`,
  `YawOffsetDegrees` included). Set when the model is built and whenever the Shiba picks a target; the server never
  turns the model itself, clients turn it there smoothly. The model's invisible `ShibaPivot` part (its PrimaryPart)
  marks the rest pose they turn from.
- `ThrowAt` (number, server clock `Workspace:GetServerTimeNow()`): when the projectile leaves the paw. The server sets
  it when the Shiba starts aiming and clears it when the throw is cancelled; clients swing the `ThrowArm` toward that
  moment, and hide what is in the paw from then on for `Shooters.HandStickHideTime` (the server never changes it).
Island stalls (`StationService`, names in `Config/Stations`): the invisible anchor parts
`Workspace/Islands/Island_<UserId>/Stations/Station_<UpgradeId>` and `…/Stations/Station_Rebirth` carry three
attributes, server → client only, read by `Controllers/StationController` for the billboards:
- `Kind` (string): `"Upgrade"` or `"Rebirth"`.
- `Locked` (boolean): upgrade stall: the owner's Shiba Tier is below `UnlockAt` (grey shutter, prompts disabled);
  rebirth shrine: `RebirthService.CanRebirth` is false (hold prompt disabled). Updated on every `StateChanged`.
- `UnlockAt` (number): the ShooterTier level that unlocks it (`EconomyConfig.UnlockAtShibaTier[id]` or 0; the shrine:
  `EconomyConfig.Rebirth.MinShibaTier`). Never changes.
The shrine's hold prompt is named `UpgradeStand_Rebirth` (shares the stand prefix, so other players' clients hide it);
triggering it calls `RebirthService.TryRebirth` on the server (owner only, one trigger per 2 s).
`BonkHit` drives the client-only effects: popup, sound, knockback (the owning client moves its own character), head-hit
bonus text and the combo counter (`combo` hits in a row; it ends if no hit follows within `comboWindow` seconds).

Direction: `C→S` client to server, `S→C` server to client, `S→All` broadcast.
