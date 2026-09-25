--!strict
-- Glow, particles and motion on the higher Shiba tiers (from the Gold Shiba on, more special with every tier:
-- Gold < Galaxy < Giant < Cheems God), keyed by the tier's AssetName (Config/Gameplay → Shooters.Tiers).
-- NPCShooterService adds light and particles to the shooter model; Controllers/ShibaController plays the motion
-- (Float, Orbit) on every model with that name. Sizes are in studs for a 6-stud Shiba and scale with
-- the tier's Height. Lights and glowing particles are kept moderate so a ring of big Shibas doesn't blow out the
-- screen. Textures are Roblox's built-in particle textures, so nothing has to be uploaded.

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
	-- The model floats up and down by Height studs (above its platform) every Period seconds.
	Float: { Height: number, Period: number }?,
	-- The model's Orbit part (Gameplay → Shooters.Motion.OrbitName) spins around its OrbitCenter marker at
	-- DegreesPerSecond, about Axis (model space: relative to the model's pivot, front = −Z, up = +Y; default up).
	Orbit: { DegreesPerSecond: number, Axis: Vector3? }?,
}

local TEXTURES: { [ParticleTexture]: string } = {
	Sparkles = "rbxasset://textures/particles/sparkles_main.dds",
	Smoke = "rbxasset://textures/particles/smoke_main.dds",
	Fire = "rbxasset://textures/particles/fire_main.dds",
}

local effects: { [string]: Effect } = {
	GoldShiba = {
		Light = { Color = Color3.fromRGB(255, 200, 70), Brightness = 0.8, Range = 9 },
		Particles = {
			{
				Texture = "Sparkles",
				Colors = { Color3.fromRGB(255, 230, 120), Color3.fromRGB(255, 255, 255) },
				Rate = 6,
				Size = 0.5,
				Lifetime = 1.2,
				Speed = 0.4,
				Rise = 0.8,
				LightEmission = 0.6,
				Transparency = 0.1,
				Area = "Body",
			},
		},
	},
	GalaxyShiba = {
		Light = { Color = Color3.fromRGB(170, 90, 255), Brightness = 1, Range = 11 },
		Particles = {
			{
				Texture = "Sparkles",
				Colors = { Color3.fromRGB(255, 120, 220), Color3.fromRGB(120, 220, 255), Color3.fromRGB(255, 255, 255) },
				Rate = 16,
				Size = 0.4,
				Lifetime = 2,
				Speed = 0.3,
				Rise = 1.2,
				LightEmission = 0.7,
				Transparency = 0.1,
				Area = "Body",
			},
			{
				Texture = "Smoke",
				Colors = { Color3.fromRGB(120, 60, 220), Color3.fromRGB(40, 120, 255) },
				Rate = 3,
				Size = 2.5,
				Lifetime = 2.5,
				Speed = 0.3,
				Rise = 0.4,
				LightEmission = 0.4,
				Transparency = 0.8,
				Area = "Feet",
			},
		},
		Float = { Height = 0.6, Period = 2.6 },
		-- The planet ring is tilted: spin it about its own axis so it doesn't wobble. Must match the ring tilt in
		-- assets/models/build_shiba_tiers.py (ORBIT_AXIS, Blender (x, y, z) → model (−x, z, y)).
		Orbit = { DegreesPerSecond = 45, Axis = Vector3.new(0.265, 0.946, 0.189) },
	},
	GiantShiba = {
		-- The range grows with the model (16 studs tall): about 32 studs.
		Light = { Color = Color3.fromRGB(255, 140, 50), Brightness = 1.15, Range = 12 },
		Particles = {
			{
				Texture = "Smoke",
				Colors = { Color3.fromRGB(190, 165, 130) },
				Rate = 5,
				Size = 2.6,
				Lifetime = 2.5,
				Speed = 1,
				Rise = 0.3,
				LightEmission = 0,
				Transparency = 0.65,
				Area = "Feet",
			},
			{
				Texture = "Sparkles",
				Colors = { Color3.fromRGB(255, 160, 40), Color3.fromRGB(255, 80, 20) },
				Rate = 10,
				Size = 0.35,
				Lifetime = 1.6,
				Speed = 0.5,
				Rise = 2.5,
				LightEmission = 0.5,
				Transparency = 0.1,
				Area = "Body",
			},
		},
	},
	CheemsGod = {
		-- The range grows with the model (12 studs tall): about 34 studs.
		Light = { Color = Color3.fromRGB(255, 235, 160), Brightness = 1.3, Range = 17 },
		Particles = {
			{
				Texture = "Sparkles",
				Colors = { Color3.fromRGB(255, 225, 110), Color3.fromRGB(255, 255, 255) },
				Rate = 20,
				Size = 0.4,
				Lifetime = 1.8,
				Speed = 0.5,
				Rise = 1,
				LightEmission = 0.55,
				Transparency = 0.1,
				Area = "Body",
			},
			{
				Texture = "Sparkles",
				Colors = { Color3.fromRGB(255, 250, 220) },
				Rate = 6,
				Size = 0.9,
				Lifetime = 3,
				Speed = 0.2,
				Rise = 1.8,
				LightEmission = 0.4,
				Transparency = 0.5,
				Area = "Body",
			},
			{
				Texture = "Smoke",
				Colors = { Color3.fromRGB(255, 245, 210) },
				Rate = 3,
				Size = 3,
				Lifetime = 3,
				Speed = 0.3,
				Rise = 0.3,
				LightEmission = 0.15,
				Transparency = 0.8,
				Area = "Feet",
			},
		},
	},
}

-- Shiny / Mythic editions (EconomyConfig.Shibas[i].Edition): they reuse a base model (and its entry above, platform
-- and motion) and add an outline plus a light aura in the tier's Color (NPCShooterService). Outline = a Highlight
-- (FillTransparency 1 = outline only; Occluded, so it doesn't show through walls). Particles with empty Colors use
-- the tier's Color fading toward white; the Light takes the tier's Color. Kept moderate: Mythic is stronger than
-- Shiny, but a ring of them must not blow out the screen.
export type EditionLook = {
	FillTransparency: number,
	OutlineTransparency: number,
	Light: { Brightness: number, Range: number }?,
	Particles: { Particles },
}

local editions: { [string]: EditionLook } = {
	Shiny = {
		FillTransparency = 0.85,
		OutlineTransparency = 0,
		Light = { Brightness = 0.5, Range = 8 },
		Particles = {
			{
				Texture = "Sparkles",
				Colors = {},
				Rate = 5,
				Size = 0.45,
				Lifetime = 1.4,
				Speed = 0.4,
				Rise = 0.8,
				LightEmission = 0.6,
				Transparency = 0.15,
				Area = "Body",
			},
		},
	},
	Mythic = {
		FillTransparency = 0.7,
		OutlineTransparency = 0,
		Light = { Brightness = 0.9, Range = 12 },
		Particles = {
			{
				Texture = "Sparkles",
				Colors = {},
				Rate = 10,
				Size = 0.55,
				Lifetime = 1.6,
				Speed = 0.6,
				Rise = 1.2,
				LightEmission = 0.75,
				Transparency = 0.1,
				Area = "Body",
			},
			{
				-- A soft glowing haze rising from the feet: the "aura".
				Texture = "Smoke",
				Colors = {},
				Rate = 4,
				Size = 1.6,
				Lifetime = 2.2,
				Speed = 0.3,
				Rise = 0.8,
				LightEmission = 0.35,
				Transparency = 0.75,
				Area = "Feet",
			},
		},
	},
}

return {
	Effects = effects,
	Editions = editions,
	-- Name of the edition outline (Highlight). Roblox draws at most 31 Highlights at once (golden sticks use some too),
	-- so each client keeps only the MaxEditionOutlines nearest to its camera enabled (Controllers/ShibaController).
	EditionOutlineName = "EditionOutline",
	MaxEditionOutlines = 16,
	Textures = TEXTURES,
}
