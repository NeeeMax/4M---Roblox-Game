--!strict
-- Upgrade definitions (docs/GAME_DESIGN.md → Upgrades).
-- To add an upgrade: add its id to Types.UpgradeId, an entry to `defs` and to `order`,
-- then read its value with UpgradeService.GetValue where it should take effect.

local Gameplay = require(script.Parent.Gameplay)
local Projectiles = require(script.Parent.Projectiles)
local Types = require(script.Parent.Parent.Types)

export type ValueFormat = "Plain" | "Multiplier" | "Seconds" | "Name"

export type UpgradeDef = {
	Id: Types.UpgradeId,
	DisplayName: string,
	Description: string,
	BaseCost: number,
	Growth: number,
	MaxLevel: number,
	-- Value at level n: BaseValue + Step * n ("Add") or BaseValue * Step ^ n ("Multiply").
	BaseValue: number,
	Step: number,
	StepKind: "Add" | "Multiply",
	Format: ValueFormat,
	-- Format "Name": the value v is shown as ValueNames[v + 1].
	ValueNames: { string }?,
}

local DEFAULT_BASE_COST = 100
local DEFAULT_GROWTH = 2.85

local shooterTierNames: { string } = {}
for _, tier in Gameplay.Shooters.Tiers do
	table.insert(shooterTierNames, tier.Name)
end
local projectileTierNames: { string } = {}
for _, id in Projectiles.Tiers do
	table.insert(projectileTierNames, Projectiles.Defs[id].DisplayName)
end

local defs: { [string]: UpgradeDef } = {
	MoveSpeed = {
		Id = "MoveSpeed",
		DisplayName = "Move Speed",
		Description = "Run faster to reach impact points in time.",
		BaseCost = DEFAULT_BASE_COST,
		Growth = DEFAULT_GROWTH,
		MaxLevel = 10,
		BaseValue = 16,
		Step = 3,
		StepKind = "Add",
		Format = "Plain",
	},
	ProjectileSize = {
		Id = "ProjectileSize",
		DisplayName = "Projectile Size",
		Description = "Bigger projectiles: easier to hit, more points, but slower.",
		BaseCost = DEFAULT_BASE_COST,
		Growth = DEFAULT_GROWTH,
		MaxLevel = 10,
		BaseValue = 1,
		Step = 1.2,
		StepKind = "Multiply",
		Format = "Multiplier",
	},
	FireRate = {
		Id = "FireRate",
		DisplayName = "Fire Rate",
		Description = "Shooters fire more often.",
		BaseCost = DEFAULT_BASE_COST,
		Growth = DEFAULT_GROWTH,
		MaxLevel = 12,
		BaseValue = 5,
		Step = 0.85,
		StepKind = "Multiply",
		Format = "Seconds",
	},
	Shooters = {
		Id = "Shooters",
		DisplayName = "Shooters",
		Description = "Adds another NPC shooter around your island.",
		BaseCost = 500,
		Growth = 4,
		MaxLevel = 7,
		BaseValue = 1,
		Step = 1,
		StepKind = "Add",
		Format = "Plain",
	},
	ShooterTier = {
		Id = "ShooterTier",
		DisplayName = "Shiba Tier",
		Description = "Evolve all your Shibas: new look, more points per bonk.",
		BaseCost = 5000,
		Growth = 12,
		MaxLevel = #shooterTierNames - 1,
		BaseValue = 0,
		Step = 1,
		StepKind = "Add",
		Format = "Name",
		ValueNames = shooterTierNames,
	},
	ProjectileTier = {
		Id = "ProjectileTier",
		DisplayName = "Projectile Tier",
		Description = "Better projectiles: new look, more points per bonk.",
		BaseCost = 1500,
		Growth = 10,
		MaxLevel = #projectileTierNames - 1,
		BaseValue = 0,
		Step = 1,
		StepKind = "Add",
		Format = "Name",
		ValueNames = projectileTierNames,
	},
}

local order: { Types.UpgradeId } =
	{ "MoveSpeed", "ProjectileSize", "FireRate", "Shooters", "ProjectileTier", "ShooterTier" }

local Upgrades = {
	Defs = defs,
	-- Display order in the upgrade menu.
	Order = order,
}

-- Cost of buying the next level when the upgrade is currently at `level`: floor(BaseCost × Growth^level).
function Upgrades.GetCost(id: Types.UpgradeId, level: number): number
	local def = defs[id]
	-- The epsilon stops float error (e.g. 284.9999999) from rounding a cost down by one.
	return math.floor(def.BaseCost * def.Growth ^ level + 1e-6)
end

function Upgrades.GetValue(id: Types.UpgradeId, level: number): number
	local def = defs[id]
	if def.StepKind == "Add" then
		return def.BaseValue + def.Step * level
	end
	return def.BaseValue * def.Step ^ level
end

return Upgrades
