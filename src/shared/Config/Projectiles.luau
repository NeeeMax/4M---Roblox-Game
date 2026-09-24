--!strict
-- Projectile definitions (docs/GAME_DESIGN.md → Projectiles).
-- To add a projectile later: add an entry to `defs`. MVP only ever fires `DefaultId`.

export type ProjectileDef = {
	Id: string,
	DisplayName: string,
	-- Studs at ProjectileSize level 0.
	Diameter: number,
	-- Launch speed in studs/s at ProjectileSize level 0.
	BaseSpeed: number,
	-- Bonk Points for a Normal hit with no upgrades.
	BaseReward: number,
	Color: Color3,
	Material: Enum.Material,
}

local defs: { [string]: ProjectileDef } = {
	Ball = {
		Id = "Ball",
		DisplayName = "Ball",
		Diameter = 2,
		BaseSpeed = 36,
		BaseReward = 10,
		Color = Color3.fromRGB(255, 120, 30),
		Material = Enum.Material.SmoothPlastic,
	},
}

return {
	DefaultId = "Ball",
	Defs = defs,
}
