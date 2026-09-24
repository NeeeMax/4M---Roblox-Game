--!strict
-- Glow and particles on the higher Shiba tiers (from the Gold Shiba on, stronger with every tier), keyed by the
-- tier's AssetName (Config/Gameplay → Shooters.Tiers). NPCShooterService adds them to the shooter model.
-- Sizes are in studs for a 6-stud Shiba and scale with the tier's Height. Textures are Roblox's built-in particle
-- textures, so nothing has to be uploaded.

export type ParticleTexture = "Sparkles" | "Smoke" | "Fire"

export type Particles = {
	Texture: ParticleTexture,
	-- Colour over the particle's life (one colour = constant).
	Colors: { Color3 },
	-- Particles per second.
	Rate: number,
	Size: number,
	Lifetime: number,
	Speed: number,
	-- Upward acceleration (studs/s²); negative falls.
	Rise: number,
	-- 0 = normal, 1 = glows (additive).
	LightEmission: number,
	-- 0 = opaque … 1 = invisible.
	Transparency: number,
	-- "Body": from the whole model (slightly larger than it), "Feet": from a flat area at the bottom.
	Area: "Body" | "Feet",
}

export type Effect = {
	Light: { Color: Color3, Brightness: number, Range: number }?,
	Particles: { Particles },
}

local TEXTURES: { [ParticleTexture]: string } = {
	Sparkles = "rbxasset://textures/particles/sparkles_main.dds",
	Smoke = "rbxasset://textures/particles/smoke_main.dds",
	Fire = "rbxasset://textures/particles/fire_main.dds",
}

local effects: { [string]: Effect } = {
	GoldShiba = {
		Light = { Color = Color3.fromRGB(255, 200, 70), Brightness = 1, Range = 10 },
		Particles = {
			{
				Texture = "Sparkles",
				Colors = { Color3.fromRGB(255, 230, 120), Color3.fromRGB(255, 255, 255) },
				Rate = 6,
				Size = 0.5,
				Lifetime = 1.2,
				Speed = 0.4,
				Rise = 0.8,
				LightEmission = 0.8,
				Transparency = 0.1,
				Area = "Body",
			},
		},
	},
	GalaxyShiba = {
		Light = { Color = Color3.fromRGB(170, 90, 255), Brightness = 1.6, Range = 14 },
		Particles = {
			{
				Texture = "Sparkles",
				Colors = { Color3.fromRGB(255, 120, 220), Color3.fromRGB(120, 220, 255), Color3.fromRGB(255, 255, 255) },
				Rate = 20,
				Size = 0.4,
				Lifetime = 2,
				Speed = 0.3,
				Rise = 1.2,
				LightEmission = 1,
				Transparency = 0,
				Area = "Body",
			},
			{
				Texture = "Smoke",
				Colors = { Color3.fromRGB(120, 60, 220), Color3.fromRGB(40, 120, 255) },
				Rate = 3,
				Size = 3,
				Lifetime = 2.5,
				Speed = 0.3,
				Rise = 0.4,
				LightEmission = 1,
				Transparency = 0.75,
				Area = "Feet",
			},
		},
	},
	GiantShiba = {
		Light = { Color = Color3.fromRGB(255, 140, 50), Brightness = 2, Range = 20 },
		Particles = {
			{
				Texture = "Smoke",
				Colors = { Color3.fromRGB(190, 165, 130) },
				Rate = 6,
				Size = 3.5,
				Lifetime = 2.5,
				Speed = 1,
				Rise = 0.3,
				LightEmission = 0,
				Transparency = 0.55,
				Area = "Feet",
			},
			{
				Texture = "Sparkles",
				Colors = { Color3.fromRGB(255, 160, 40), Color3.fromRGB(255, 80, 20) },
				Rate = 12,
				Size = 0.5,
				Lifetime = 1.6,
				Speed = 0.5,
				Rise = 2.5,
				LightEmission = 1,
				Transparency = 0,
				Area = "Body",
			},
		},
	},
	CheemsGod = {
		Light = { Color = Color3.fromRGB(255, 235, 160), Brightness = 3, Range = 26 },
		Particles = {
			{
				Texture = "Sparkles",
				Colors = { Color3.fromRGB(255, 225, 110), Color3.fromRGB(255, 255, 255) },
				Rate = 32,
				Size = 0.6,
				Lifetime = 1.8,
				Speed = 0.5,
				Rise = 1,
				LightEmission = 1,
				Transparency = 0,
				Area = "Body",
			},
			{
				Texture = "Sparkles",
				Colors = { Color3.fromRGB(255, 250, 220) },
				Rate = 8,
				Size = 1.4,
				Lifetime = 3,
				Speed = 0.2,
				Rise = 1.8,
				LightEmission = 1,
				Transparency = 0.35,
				Area = "Body",
			},
			{
				Texture = "Smoke",
				Colors = { Color3.fromRGB(255, 245, 210) },
				Rate = 4,
				Size = 4,
				Lifetime = 3,
				Speed = 0.3,
				Rise = 0.3,
				LightEmission = 1,
				Transparency = 0.7,
				Area = "Feet",
			},
		},
	},
}

return {
	Effects = effects,
	Textures = TEXTURES,
}
