--!strict
-- Upgrade definitions (docs/GAME_DESIGN.md → Upgrades).
-- To add an upgrade: add its id to Types.UpgradeId, an entry to `defs` and to `order`,
-- then read its value with UpgradeService.GetValue where it should take effect.
-- Tier upgrades (ShooterTier, ProjectileTier) take their names, colours and max level from their tier lists.

local Gameplay = require(script.Parent.Gameplay)
local Projectiles = require(script.Parent.Projectiles)
local Shop = require(script.Parent.Shop)
local Types = require(script.Parent.Parent.Types)

export type ValueFormat = "Plain" | "Name"

export type UpgradeDef = {
	Id: Types.UpgradeId,
	DisplayName: string,
	Description: string,
	BaseCost: number,
	Growth: number,
	MaxLevel: number,
	-- Value at level n: BaseValue + Step * n.
	BaseValue: number,
	Step: number,
	Format: ValueFormat,
	-- Format "Name": level n is shown as ValueNames[n + 1], in ValueColors[n + 1].
	ValueNames: { string }?,
	ValueColors: { Color3 }?,
	-- Menu accent colour.
	Color: Color3,
}

local shooterTierNames: { string } = {}
local shooterTierColors: { Color3 } = {}
for _, tier in Gameplay.Shooters.Tiers do
	table.insert(shooterTierNames, tier.Name)
	table.insert(shooterTierColors, tier.Color)
end
local projectileTierNames: { string } = {}
local projectileTierColors: { Color3 } = {}
for _, id in Projectiles.Tiers do
	table.insert(projectileTierNames, Projectiles.Defs[id].DisplayName)
	table.insert(projectileTierColors, Projectiles.Defs[id].Color)
end

local defs: { [string]: UpgradeDef } = {
	MoveSpeed = {
		Id = "MoveSpeed",
		DisplayName = "Move Speed",
		Description = "Run faster to reach every stick in time.",
		BaseCost = 100,
		Growth = 2.6,
		MaxLevel = 10,
		BaseValue = 16,
		Step = 3,
		Format = "Plain",
		Color = Color3.fromRGB(80, 200, 255),
	},
	Shooters = {
		Id = "Shooters",
		DisplayName = "More Shibas",
		Description = "Another Shiba joins the ring around your island.",
		BaseCost = 500,
		Growth = 4,
		MaxLevel = 7,
		BaseValue = 1,
		Step = 1,
		Format = "Plain",
		Color = Color3.fromRGB(255, 140, 60),
	},
	ShooterTier = {
		Id = "ShooterTier",
		DisplayName = "Shiba Tier",
		Description = "Evolve all your Shibas: they throw faster and every bonk pays more.",
		BaseCost = 2000,
		-- Same price for the top tier as with 8 tiers (2,000 × 7^6): 4.3 = 7^(6/8).
		Growth = 4.3,
		MaxLevel = #shooterTierNames - 1,
		BaseValue = 0,
		Step = 1,
		Format = "Name",
		ValueNames = shooterTierNames,
		ValueColors = shooterTierColors,
		Color = Color3.fromRGB(190, 110, 255),
	},
	ProjectileTier = {
		Id = "ProjectileTier",
		DisplayName = "Projectile Tier",
		Description = "Better projectiles: new look, more points per bonk.",
		BaseCost = 1500,
		-- Same price for the top tier as with 4 tiers (1,500 × 10^2): 1.78 = 10^(2/8).
		Growth = 1.78,
		MaxLevel = #projectileTierNames - 1,
		BaseValue = 0,
		Step = 1,
		Format = "Name",
		ValueNames = projectileTierNames,
		ValueColors = projectileTierColors,
		Color = Color3.fromRGB(255, 200, 40),
	},
}

local order: { Types.UpgradeId } = { "ShooterTier", "ProjectileTier", "Shooters", "MoveSpeed" }

local Upgrades = {
	Defs = defs,
	-- Display order in the upgrade menu.
	Order = order,
}

-- Cost of buying the next level when the upgrade is currently at `level`: floor(BaseCost × Growth^level).
function Upgrades.GetCost(id: string, level: number): number
	local def = defs[id]
	-- The epsilon stops float error (e.g. 284.9999999) from rounding a cost down by one.
	return math.floor(def.BaseCost * def.Growth ^ level + 1e-6)
end

function Upgrades.GetValue(id: string, level: number): number
	local def = defs[id]
	return def.BaseValue + def.Step * level
end

-- Highest level this player can reach: the +2 Shiba Slots pass lifts More Shibas past its MaxLevel.
function Upgrades.GetMaxLevel(id: string, passes: { [string]: boolean }): number
	local max = defs[id].MaxLevel
	if id == "Shooters" and passes.ExtraShibas then
		max += Shop.Pass.ExtraShibas
	end
	return max
end

-- The text shown for a level's value ("Galaxy Shiba", "19", …).
function Upgrades.FormatValue(id: string, level: number): string
	local def = defs[id]
	if def.Format == "Name" and def.ValueNames then
		return def.ValueNames[level + 1] or "?"
	end
	return tostring(math.floor(Upgrades.GetValue(id, level) + 0.5))
end

return Upgrades
