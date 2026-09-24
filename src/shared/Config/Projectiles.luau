--!strict
-- Projectile definitions (docs/GAME_DESIGN.md → Projectiles).
-- The ProjectileTier upgrade picks the def: level n fires `Tiers[n + 1]`. To add a tier: add an entry to `defs`
-- and its id to `tiers` (the upgrade's max level follows automatically).
-- Hits use an invisible sphere of `Diameter`; the visible model (ReplicatedStorage.Assets.<AssetName>) is scaled
-- so its longest side equals the diameter. A tier without its own model uses the next lower tier's model;
-- without any model a plain sphere in `Color` is shown. `Trail` adds a trail in `Color` behind it.

export type ProjectileDef = {
	Id: string,
	DisplayName: string,
	-- Studs at ProjectileSize level 0.
	Diameter: number,
	-- Launch speed in studs/s at ProjectileSize level 0.
	BaseSpeed: number,
	-- Bonk Points for a Normal hit with no upgrades.
	BaseReward: number,
	-- Name of the model in ReplicatedStorage.Assets, or nil for a plain sphere.
	AssetName: string?,
	Color: Color3,
	Material: Enum.Material,
	-- Coloured trail behind the projectile: tells the tiers apart while they share a model.
	Trail: boolean,
}

local defs: { [string]: ProjectileDef } = {
	Stick = {
		Id = "Stick",
		DisplayName = "Bonk Stick",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 10,
		AssetName = "Stick",
		Color = Color3.fromRGB(150, 100, 60),
		Material = Enum.Material.Wood,
		Trail = false,
	},
	Bone = {
		Id = "Bone",
		DisplayName = "Bone",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 20,
		AssetName = "Bone",
		Color = Color3.fromRGB(245, 240, 225),
		Material = Enum.Material.SmoothPlastic,
		Trail = true,
	},
	GoldenStick = {
		Id = "GoldenStick",
		DisplayName = "Golden Stick",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 40,
		AssetName = "GoldenStick",
		Color = Color3.fromRGB(255, 200, 40),
		Material = Enum.Material.Foil,
		Trail = true,
	},
	DiamondStick = {
		Id = "DiamondStick",
		DisplayName = "Diamond Stick",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 80,
		AssetName = "DiamondStick",
		Color = Color3.fromRGB(90, 220, 255),
		Material = Enum.Material.Glass,
		Trail = true,
	},
}

-- Tier order: ProjectileTier level 0 fires the first one.
local tiers = { "Stick", "Bone", "GoldenStick", "DiamondStick" }

local Projectiles = {
	DefaultId = "Stick",
	Defs = defs,
	Tiers = tiers,
}

-- The def fired at this ProjectileTier level.
function Projectiles.ForTier(level: number): ProjectileDef
	return defs[tiers[math.clamp(level + 1, 1, #tiers)]]
end

-- Model names to try for this def: its own, then the lower tiers' (best first).
function Projectiles.AssetCandidates(id: string): { string }
	local names: { string } = {}
	local index = table.find(tiers, id) or 1
	for tier = index, 1, -1 do
		local assetName = defs[tiers[tier]].AssetName
		if assetName then
			table.insert(names, assetName)
		end
	end
	return names
end

return Projectiles
