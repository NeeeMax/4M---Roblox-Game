--!strict
-- Upgrade definitions (docs/GAME_DESIGN.md → Upgrades).
-- To add an upgrade: add its id to Types.UpgradeId, an entry to `defs` and to `order`, a Route line in
-- Config/EconomyConfig (which prices it), then read its value with UpgradeService.GetValue where it should take effect.
-- Prices and max levels come from EconomyConfig (Costs, RouteSpecs); tier upgrades take names and colours from their
-- tier lists.

local EconomyConfig = require(script.Parent.EconomyConfig)
local Gameplay = require(script.Parent.Gameplay)
local Projectiles = require(script.Parent.Projectiles)
local Shop = require(script.Parent.Shop)
local Types = require(script.Parent.Parent.Types)

export type ValueFormat = "Plain" | "Name"

export type UpgradeDef = {
	Id: Types.UpgradeId,
	DisplayName: string,
	Description: string,
	-- Levels priced by EconomyConfig's Route (Upgrades.GetCost reads EconomyConfig.Costs).
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

local internNames: { string } = { "None" }
local internColors: { Color3 } = { Color3.fromRGB(160, 160, 160) }
for _, name in EconomyConfig.Automation.Intern.Names do
	table.insert(internNames, name)
	table.insert(internColors, Color3.fromRGB(90, 200, 160))
end

local defs: { [string]: UpgradeDef } = {
	MoveSpeed = {
		Id = "MoveSpeed",
		DisplayName = "Move Speed",
		Description = "Run faster to reach every stick in time.",
		MaxLevel = EconomyConfig.RouteCount("MoveSpeed"),
		BaseValue = 16,
		Step = 3,
		Format = "Plain",
		Color = Color3.fromRGB(80, 200, 255),
	},
	Shooters = {
		Id = "Shooters",
		DisplayName = "More Shibas",
		Description = "Another Shiba joins the ring around your island.",
		MaxLevel = EconomyConfig.RouteCount("Shooters"),
		BaseValue = 1,
		Step = 1,
		Format = "Plain",
		Color = Color3.fromRGB(255, 140, 60),
	},
	ShooterTier = {
		Id = "ShooterTier",
		DisplayName = "Shiba Tier",
		Description = "Evolve all your Shibas: they throw faster and every bonk pays more.",
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
		Description = "Better projectiles: new look, more Bonk Dollars per bonk.",
		MaxLevel = #projectileTierNames - 1,
		BaseValue = 0,
		Step = 1,
		Format = "Name",
		ValueNames = projectileTierNames,
		ValueColors = projectileTierColors,
		Color = Color3.fromRGB(255, 200, 40),
	},
	-- Automation (Config/EconomyConfig → Automation). Level 0 = none; level n uses the automation tables' entry n.
	Basket = {
		Id = "Basket",
		DisplayName = "Bonk Basket",
		Description = "Catches sticks you miss and pays for them, even while you are away.",
		MaxLevel = EconomyConfig.RouteCount("Basket"),
		BaseValue = 0,
		Step = 1,
		Format = "Plain",
		Color = Color3.fromRGB(200, 140, 70),
	},
	Intern = {
		Id = "Intern",
		DisplayName = "Bonk Intern",
		Description = "Hire a helper who runs to the sticks and gets bonked for you.",
		MaxLevel = EconomyConfig.RouteCount("Intern"),
		BaseValue = 0,
		Step = 1,
		Format = "Name",
		ValueNames = internNames,
		ValueColors = internColors,
		Color = Color3.fromRGB(90, 200, 160),
	},
}

local order: { Types.UpgradeId } = { "ShooterTier", "ProjectileTier", "Shooters", "MoveSpeed", "Basket", "Intern" }

local Upgrades = {
	Defs = defs,
	-- Display order in the upgrade menu.
	Order = order,
}

-- Cost of buying the next level when the upgrade is currently at `level` (EconomyConfig.Costs, derived from the
-- target pace; math.huge past the priced levels).
function Upgrades.GetCost(id: string, level: number): number
	return EconomyConfig.GetCost(id, level)
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
