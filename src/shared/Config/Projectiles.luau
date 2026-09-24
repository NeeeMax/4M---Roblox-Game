--!strict
-- Projectile definitions (docs/GAME_DESIGN.md → Projectiles).
-- To add a projectile later: add an entry to `defs`. MVP only ever fires `DefaultId`.
-- Hits use an invisible sphere of `Diameter`; the visible model (ReplicatedStorage.Assets.<AssetName>) is scaled
-- so its longest side equals the diameter. Without that model a plain sphere in `Color` is shown.

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
	},
}

return {
	DefaultId = "Stick",
	Defs = defs,
}
