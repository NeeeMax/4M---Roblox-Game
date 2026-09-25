-- Checks the island layout (src/shared/Config/Stations.luau) outside Roblox: `lune run docs/economy/layout_check`.
-- Prints the stall positions and every minimum distance listed in docs/economy/LAYOUT.md, and fails (exit 1) if a
-- rule is broken. Island-local, top-down coordinates with the bridge toward −Z: x = r·sin(a), z = −r·cos(a),
-- a = degrees clockwise from the bridge (the direction() convention of StationService / IslandService).
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local process = require("@lune/process")
local roblox = require("@lune/roblox")

local function load(path: string): any
	local chunk = luau.load(fs.readFile(path), {
		debugName = path,
		environment = { Color3 = roblox.Color3, Vector3 = roblox.Vector3, Enum = roblox.Enum },
		injectGlobals = true,
	})
	return chunk()
end

local Stations = load("src/shared/Config/Stations.luau")

-- Fixed numbers from other configs / services (keep in sync if those change).
local ISLAND_RADIUS = 80 -- Config/Gameplay → Island.Radius
local FIELD_RADIUS = 30 -- Island.FieldRadius (+ border 2)
local RING_RADIUS = 56 -- Shooters.RingRadius
local RING_REACH = RING_RADIUS + (21 + 2 * 0.5) / 2 -- Giant Shiba platform 21 wide + barrier padding 0.5 → 67
local TROPHY_RADIUS = 42 -- TrophyService: FieldRadius + 12, behind the field (180°)
local NAME_SIGN = { x = 9, z = -72 } -- IslandService: (Radius − 8) toward the bridge, 9 to the right
-- Footprint half-size (tangential, radial) of a stall: the stand is 7.6 × 3.8 (+ awning), the shrine 7.2 × 5.6.
local STAND_HALF = { w = 3.8, d = 2.1 }
local SHRINE_HALF = { w = 3.6, d = 2.8 }
local TREE_CROWN = 0.6 * 15 / 2 -- widest placeholder crown radius (height 15)
local MIN_CLEAR = 10 -- trees/flowers keep this far from stalls, signs, spawn and path

-- Old layout (v1, removed): Along = toward the bridge, Side = right of the path.
local OLD = {
	ShooterTier = { Along = 38, Side = -8.5 },
	ProjectileTier = { Along = 38, Side = 8.5 },
	Shooters = { Along = 47, Side = -8.5 },
	MoveSpeed = { Along = 47, Side = 8.5 },
}

type Point = { x: number, z: number }

local function polar(angle: number, radius: number): Point
	local a = math.rad(angle)
	return { x = radius * math.sin(a), z = -radius * math.cos(a) }
end

local function dist(a: Point, b: Point): number
	return math.sqrt((a.x - b.x) ^ 2 + (a.z - b.z) ^ 2)
end

local function fmt(value: number): string
	return string.format("%.1f", value)
end

local failures = 0
local function check(ok: boolean, message: string)
	print(`  {if ok then "ok  " else "FAIL"} {message}`)
	if not ok then
		failures += 1
	end
end

-- Distance from a point to the path ring (arc band + link rectangle); 0 if on it.
local path = Stations.PathRing
local function angleOf(p: Point): number
	local a = math.deg(math.atan2(p.x, -p.z))
	return if a < path.FromAngle then a + 360 else a
end
local function toPath(p: Point): number
	local r = math.sqrt(p.x ^ 2 + p.z ^ 2)
	local a = angleOf(p)
	local best: number
	if a >= path.FromAngle and a <= path.ToAngle then
		best = math.max(0, math.abs(r - path.Radius) - path.Width / 2)
	else
		best = math.huge
		for _, endAngle in { path.FromAngle, path.ToAngle } do
			for step = -1, 1, 0.25 do
				best = math.min(best, dist(p, polar(endAngle, path.Radius + step * path.Width / 2)))
			end
		end
	end
	-- Link: along angle 0 (−Z), x within ±LinkWidth/2, radius LinkFrom … LinkTo.
	local dx = math.max(0, math.abs(p.x) - path.LinkWidth / 2)
	local along = -p.z
	local dz = math.max(0, path.LinkFrom - along, along - path.LinkTo)
	return math.min(best, math.sqrt(dx ^ 2 + dz ^ 2))
end

-- Stalls.
print("Stalls (island-local x/z; the bridge is −Z, +X is 90°):")
print("| Stall | Zone | Old Along/Side | Old x/z | Angle | Radius | x | z |")
local stalls: { { name: string, p: Point, half: { w: number, d: number }, stall: any } } = {}
for _, stall in Stations.Stalls do
	local name = if stall.Kind == "Rebirth" then "Rebirth shrine" else stall.Upgrade
	local p = polar(stall.Angle, stall.Radius)
	local old = OLD[name]
	local oldText = if old then `{old.Along} / {old.Side}` else "new"
	local oldXZ = if old then `{fmt(old.Side)} / {fmt(-old.Along)}` else "—"
	print(
		`| {name} | {stall.Zone} | {oldText} | {oldXZ} | {stall.Angle}° | {stall.Radius} | {fmt(p.x)} | {fmt(p.z)} |`
	)
	table.insert(stalls, {
		name = name,
		p = p,
		half = if stall.Kind == "Rebirth" then SHRINE_HALF else STAND_HALF,
		stall = stall,
	})
end

local spawn = polar(Stations.NewPlayerSpawn.Angle, Stations.NewPlayerSpawn.Radius)
print(
	`Spawn: {Stations.NewPlayerSpawn.Angle}° r{Stations.NewPlayerSpawn.Radius} → x {fmt(spawn.x)}, z {fmt(spawn.z)}`
)

print("\nStall spacing (MinStallDistance " .. Stations.MinStallDistance .. "):")
local minPair, minPairName = math.huge, ""
for i = 1, #stalls do
	for j = i + 1, #stalls do
		local d = dist(stalls[i].p, stalls[j].p)
		if d < minPair then
			minPair, minPairName = d, `{stalls[i].name} – {stalls[j].name}`
		end
	end
end
check(minPair >= Stations.MinStallDistance, `closest stalls: {minPairName} {fmt(minPair)} studs`)
local minSpawn, minSpawnName = math.huge, ""
for _, s in stalls do
	local d = dist(s.p, spawn)
	if d < minSpawn then
		minSpawn, minSpawnName = d, s.name
	end
end
check(minSpawn >= Stations.MinStallDistance, `closest stall to the spawn: {minSpawnName} {fmt(minSpawn)} studs`)

print("\nRings (radial clearances):")
local innerFront, outerBack = math.huge, 0
for _, s in stalls do
	innerFront = math.min(innerFront, s.stall.Radius - s.half.d)
	outerBack = math.max(outerBack, math.sqrt((s.stall.Radius + s.half.d) ^ 2 + s.half.w ^ 2))
end
check(innerFront > RING_REACH, `stall fronts at r {fmt(innerFront)} > Giant Shiba barrier r {fmt(RING_REACH)}`)
check(
	path.Radius - path.Width / 2 >= RING_REACH,
	`path inner edge r {fmt(path.Radius - path.Width / 2)} ≥ barrier r {fmt(RING_REACH)}`
)
check(outerBack < ISLAND_RADIUS, `stall backs reach r {fmt(outerBack)} < island edge {ISLAND_RADIUS}`)
check(innerFront > TROPHY_RADIUS + 3 and innerFront > FIELD_RADIUS + 2, "stalls far outside field and trophies")
local sign = Stations.ZoneSign
for _, zone in Stations.Zones do
	-- Board corners and the posts' outer corners (posts stand right behind the board).
	local boardReach = math.sqrt((zone.Radius + sign.BoardSize.Z / 2) ^ 2 + (sign.BoardSize.X / 2) ^ 2)
	local postReach = math.sqrt(
		(zone.Radius + sign.BoardSize.Z / 2 + sign.PostWidth) ^ 2 + (sign.PostOffset + sign.PostWidth / 2) ^ 2
	)
	local reach = math.max(boardReach, postReach)
	check(reach < ISLAND_RADIUS, `sign {zone.Id} reaches r {fmt(reach)} < {ISLAND_RADIUS}`)
end

-- Zone signs vs stalls: a sign stands behind its stalls (radially), its board above their billboards.
print("\nZone signs:")
for _, zone in Stations.Zones do
	local p = polar(zone.Angle, zone.Radius)
	local nearest, nearestName = math.huge, ""
	for _, s in stalls do
		local d = dist(p, s.p)
		if d < nearest then
			nearest, nearestName = d, s.name
		end
	end
	local behind = zone.Radius - (74 + STAND_HALF.d)
	check(
		behind > 1,
		`{zone.Id} at {zone.Angle}°: nearest stall {nearestName} {fmt(nearest)} studs, {fmt(behind)} behind its back`
	)
end
check(
	sign.BoardHeight - sign.BoardSize.Y / 2 > 11.5,
	`sign boards start at {fmt(sign.BoardHeight - sign.BoardSize.Y / 2)} studs, over the stall billboards (≤ 11.5)`
)

-- Trees and flowers.
print("\nGrove (trees and flowers ≥ " .. MIN_CLEAR .. " studs from stalls, signs, spawn and path):")
local grove = Stations.Grove
local treeCount = 7 -- Config/World → Decor.TreesPerIsland
local worst = { stall = math.huge, sign = math.huge, spawn = math.huge, path = math.huge, ring = math.huge }
local worstName = { stall = "", sign = "", spawn = "", path = "", ring = "" }
local function consider(key: string, value: number, name: string)
	if value < worst[key] then
		worst[key] = value
		worstName[key] = name
	end
end
for index = 1, treeCount do
	local angle = grove.FromAngle + (index - 0.5) / treeCount * (grove.ToAngle - grove.FromAngle)
	local radius = grove.Radii[(index - 1) % #grove.Radii + 1]
	local items = {
		{ name = `tree {index} ({fmt(angle)}°, r{radius})`, p = polar(angle, radius), size = TREE_CROWN },
		{
			name = `flowers {index}`,
			p = polar(angle + grove.FlowerAngle, radius - grove.FlowerInset),
			size = 1,
		},
	}
	for _, item in items do
		for _, s in stalls do
			consider("stall", dist(item.p, s.p) - math.max(s.half.w, s.half.d), `{item.name} – {s.name}`)
		end
		for _, zone in Stations.Zones do
			consider(
				"sign",
				dist(item.p, polar(zone.Angle, zone.Radius)) - sign.BoardSize.X / 2,
				`{item.name} – {zone.Id}`
			)
		end
		consider("sign", dist(item.p, NAME_SIGN), `{item.name} – name sign`)
		consider("spawn", dist(item.p, spawn), item.name)
		consider("path", toPath(item.p), item.name)
		-- Trunk (1.4 wide) vs the Shiba barrier; crowns hang higher than any platform.
		consider("ring", math.sqrt(item.p.x ^ 2 + item.p.z ^ 2) - 0.7 - RING_REACH, item.name)
	end
end
for _, key in { "stall", "sign", "spawn", "path" } do
	check(worst[key] >= MIN_CLEAR, `closest to a {key}: {worstName[key]} {fmt(worst[key])} studs`)
end
check(worst.ring > 0, `closest to the Shiba barrier: {worstName.ring} {fmt(worst.ring)} studs`)

-- Sightlines: no tree between two neighbouring zones (all trees sit in the grove sector, outside every stall arc).
local lastStall = 0
for _, s in stalls do
	lastStall = math.max(lastStall, s.stall.Angle)
end
check(grove.FromAngle > lastStall + 15, `grove starts at {grove.FromAngle}° after the last stall ({lastStall}°)`)

-- Name sign vs path.
check(
	toPath(NAME_SIGN) >= 0 and toPath(NAME_SIGN) < 1,
	`owner name sign stands beside the path ({fmt(toPath(NAME_SIGN))} studs off its edge)`
)

-- Part budget.
local segments = math.ceil((path.ToAngle - path.FromAngle) / path.SegmentDegrees)
check(segments + 1 <= 60, `path parts per island: {segments + 1}`)

print(if failures == 0 then "\nAll layout checks passed." else `\n{failures} layout check(s) failed.`)
if failures > 0 then
	process.exit(1)
end
