# Island layout v2 (Workstream E)

Source of truth: `src/shared/Config/Stations.luau` (Zones, Stalls, NewPlayerSpawn, ZoneSign, PathRing, Grove).
Built by `StationService` (stalls, per player) and `IslandService` (zone signs, path, trees; once per plot at startup).
Every number below is printed and checked by `lune run docs/economy/layout_check` (exit code 1 if a rule breaks);
re-run it after changing any layout value.

Coordinates: **Angle** = degrees clockwise (seen from above) from the direction toward the bridge (`island.HubAngle`),
**Radius** = studs from the island centre, `direction(a) = (sin a, 0, −cos a)`. The x/z columns are island-local with
the bridge toward −Z and 90° toward +X (for a real island rotate by its HubAngle).

## Stall positions

Stalls stand on the outer ring behind the path and face the island centre (front = look vector), so their billboards
read from the field. The old stands (v1) stood on both sides of the bridge path, 8.5 studs off its centre line.

| Stall | Zone | Old Along / Side | Old x / z | Angle | Radius | x | z |
|-------|------|------------------|-----------|-------|--------|---|---|
| Move Speed (`MoveSpeed`) | Speed Gym | 47 / +8.5 | 8.5 / −47.0 | 30° | 74 | 37.0 | −64.1 |
| Shiba Tier (`ShooterTier`) | Shiba Shop | 38 / −8.5 | −8.5 / −38.0 | 62° | 74 | 65.3 | −34.7 |
| More Shibas (`Shooters`) | Shiba Shop | 47 / −8.5 | −8.5 / −47.0 | 118° | 74 | 65.3 | 34.7 |
| Projectile Tier (`ProjectileTier`) | Throwables | 38 / +8.5 | 8.5 / −38.0 | 150° | 74 | 37.0 | 64.1 |
| Bonk Basket (`Basket`) | Automation | new | — | 185° | 74 | −6.4 | 73.7 |
| Bonk Intern (`Intern`) | Automation | new | — | 220° | 74 | −47.6 | 56.7 |
| Rebirth shrine | Rebirth | new | — | 270° | 74 | −74.0 | 0.0 |

Other fixed points:

| Thing | Angle | Radius | Note |
|-------|-------|--------|------|
| New-player spawn (`NewPlayerSpawn`) | 90° | 72 | faces the centre; the NEW SHIBA pad (2nd Shiba) is at 90° r 56, 16 studs ahead |
| Zone signs | 30° / 90° / 150° / 202.5° / 270° | 78 | board 16 × 3.4 at 12.3–15.7 studs height, above the stall billboards (≤ 11.5) |
| Path ring | −3° … 270° | 70 (68–72) | 46 segments of ~6° + 1 link (r 72–79 at 0°, 7 wide) = 47 parts per island |
| Tree grove | 290° … 342° | 73.5 / 77 | 7 trees, 7 flower patches (3.5 studs in, 4° further) |
| Owner name sign | ≈ 7° | 72.6 | unchanged, right of the bridge, just beside the path edge |
| Trophies | 180° | 42 | unchanged, behind the field |
| Shiba ring | all round | 56 | Giant Shiba barrier (21 + 2 × 0.5 wide) reaches r 67 |

The unlock tier of each upgrade stall comes from `EconomyConfig.UnlockAtShibaTier` (currently: Shiba Tier and More
Shibas open from the start, Move Speed and Projectile Tier at the Shades Shiba (level 1), Basket at level 9, Intern at
level 10); the rebirth shrine needs `EconomyConfig.Rebirth.MinShibaTier` (level 20).

## Minimum distances (from `layout_check`)

| Rule | Result |
|------|--------|
| Stall ↔ stall ≥ `MinStallDistance` (30) | closest: Shiba Tier ↔ Move Speed 40.8 |
| Stall ↔ spawn ≥ 30 | closest: Shiba Tier 35.4 |
| Stall fronts outside the Shiba barrier (r 67) | fronts at r 71.2 |
| Path inner edge outside the Shiba barrier | 68.0 ≥ 67.0 |
| Stall backs inside the island (r 80) | r 76.9 |
| Zone signs inside the island | r 79.4 (post corners) |
| Zone sign behind its stall | 1.9 studs behind the stall backs, posts at ±6.5 beside the stall (stall is 7.6 wide) |
| Trees/flowers ↔ stall ≥ 10 | closest: tree 1 ↔ rebirth shrine 26.7 (minus footprint) |
| Trees/flowers ↔ sign ≥ 10 | closest: tree 1 ↔ REBIRTH sign 23.4 (minus half board) |
| Trees/flowers ↔ spawn ≥ 10 | 114.7 |
| Trees/flowers ↔ path ≥ 10 | 17.8 |
| Tree trunks / flowers outside the Shiba barrier | ≥ 2.3 |
| Sightlines between zones | no tree between 0° and 270° (grove starts 20° after the shrine) |

## Top-down sketch

```
                   top = toward the bridge (0°), angles clockwise

                                   bridge (0°)
                                       ║
         tree grove ♣ ♣ ♣              ║  owner name sign
         (290°–342°, no path)   .------╨------.      SPEED GYM: Move Speed stall + sign (30°)
                           .-'   path ring r70   '-.
                         /      Shibas on r56        \    SHIBA SHOP: Shiba Tier stall (62°)
                        /         .---------.         \
     REBIRTH ──►       |         /           \         |  ◄── SPAWN (90°, r72), SHIBA SHOP sign behind (r78)
     shrine + sign     |        |    FIELD    |        |      NEW SHIBA pad in front (90°, r56)
     (270°, path end)  |         \    r30    /         |
                        \         '---------'         /   SHIBA SHOP: More Shibas stall (118°)
                         \     trophies (180°, r42)  /
                           '-.                    .-'  ◄── THROWABLES: Projectile Tier stall + sign (150°)
                              '-.______________.-'
                Intern (220°)   AUTOMATION sign (202.5°)   Basket (185°)
```

Walking clockwise from the spawn follows the progression: Shiba Shop → Throwables → Automation → Rebirth. The Speed
Gym sits between the bridge and the spawn (cheap early upgrade on the way in).

## Studio test checklist

1. Play Solo with a fresh save. You spawn at 90° facing the field; the NEW SHIBA pad glows in front of you. Output
   shows no errors from StationService / IslandService (placeholder notes from PropService are expected).
2. Walk the whole path ring from the bridge clockwise to the rebirth shrine: nothing floats or sinks, the path never
   flickers (segments alternate 0.2 / 0.26 studs above the grass), you never get stuck (the path does not collide).
3. Every stall faces the field; from the field centre every billboard and zone sign is readable, signs are above the
   billboards, no sign or tree hides a stall.
4. Buy Shibas until 8–10 stand on the ring (admin commands): no Shiba barrier overlaps a stall or blocks its prompt;
   a Giant Shiba (any edition) platform does not reach the path (it may touch its inner edge).
5. Prompts: E on Shiba Tier / More Shibas works at once; Move Speed and Projectile Tier show the grey shutter and
   padlock (no prompt) until the Shades Shiba, then open. Basket / Intern stay locked until tier 9 / 10.
6. F "Buy with R$" appears on stalls that have an `Instant<UpgradeId>` product and opens the purchase.
7. Rebirth shrine: prompt hidden and the orb dim before Shiba Tier level 20; with an admin tier set to 20+ the orb
   glows, the prompt needs a 3 s hold, and rebirth resets money and levels (stalls lock again).
8. A second player (Local Server, 2 players): they see no prompts on your island and cannot buy from your stalls.
9. Trees stand only in the grove between the rebirth shrine and the bridge; the owner name sign still stands right of
   where the bridge arrives.
10. Check `Locked`, `Kind`, `UnlockAt` attributes on `Workspace/Islands/Island_<UserId>/Stations/Station_*`.

## Known risks

- Imported stall models (`Prop_UpgradeStand_<Id>`, `Prop_RebirthShrine`) must keep the placeholder footprint
  (≈ 7.6 × 4.2 / 7.2 × 5.6 studs, front toward −Z) or they can reach the path or the sign posts; the lock shutter is
  sized for the part-built stand.
- The spawn (r 72) is on the outer edge of the path, and the stall fronts touch it: intended ("market street"), but
  crowded if many Shibas stand at exactly 62° / 118°.
- Fixed numbers from other configs are copied into `layout_check.luau` (island radius, ring radius, Giant platform,
  trophy radius, tree count); update them there if those change.
