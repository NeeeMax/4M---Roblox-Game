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
	-- Tiers 2-10: BaseReward spread geometrically over the same range as before (10 -> 80).
	Newspaper = {
		Id = "Newspaper",
		DisplayName = "Newspaper",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 13,
		AssetName = "Newspaper",
		Color = Color3.fromRGB(235, 232, 220),
		Material = Enum.Material.SmoothPlastic,
		Trail = true,
	},
	Baguette = {
		Id = "Baguette",
		DisplayName = "Baguette",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 16,
		AssetName = "Baguette",
		Color = Color3.fromRGB(220, 160, 80),
		Material = Enum.Material.SmoothPlastic,
		Trail = true,
	},
	RollingPin = {
		Id = "RollingPin",
		DisplayName = "Rolling Pin",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 20,
		AssetName = "RollingPin",
		Color = Color3.fromRGB(205, 150, 90),
		Material = Enum.Material.Wood,
		Trail = true,
	},
	BaseballBat = {
		Id = "BaseballBat",
		DisplayName = "Baseball Bat",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 25,
		AssetName = "BaseballBat",
		Color = Color3.fromRGB(255, 60, 40),
		Material = Enum.Material.Wood,
		Trail = true,
	},
	GiantBone = {
		Id = "GiantBone",
		DisplayName = "Giant Bone",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 32,
		AssetName = "GiantBone",
		Color = Color3.fromRGB(245, 240, 225),
		Material = Enum.Material.SmoothPlastic,
		Trail = true,
	},
	SqueakyHammer = {
		Id = "SqueakyHammer",
		DisplayName = "Squeaky Hammer",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 40,
		AssetName = "SqueakyHammer",
		Color = Color3.fromRGB(230, 40, 40),
		Material = Enum.Material.SmoothPlastic,
		Trail = true,
	},
	BonkSign = {
		Id = "BonkSign",
		DisplayName = "BONK Sign",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 50,
		AssetName = "BonkSign",
		Color = Color3.fromRGB(255, 210, 0),
		Material = Enum.Material.Metal,
		Trail = true,
	},
	NeonStick = {
		Id = "NeonStick",
		DisplayName = "Neon Stick",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 63,
		AssetName = "NeonStick",
		Color = Color3.fromRGB(255, 60, 220),
		Material = Enum.Material.Neon,
		Trail = true,
	},
	LegendaryStick = {
		Id = "LegendaryStick",
		DisplayName = "Legendary Stick",
		Diameter = 3,
		BaseSpeed = 36,
		BaseReward = 80,
		AssetName = "LegendaryStick",
		Color = Color3.fromRGB(255, 200, 40),
		Material = Enum.Material.Foil,
		Trail = true,
	},
}

-- Tier order: ProjectileTier level 0 fires the first one.
local tiers = {
	"Stick",
	"Newspaper",
	"Baguette",
	"RollingPin",
	"BaseballBat",
	"GiantBone",
	"SqueakyHammer",
	"BonkSign",
	"NeonStick",
	"LegendaryStick",
}

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
