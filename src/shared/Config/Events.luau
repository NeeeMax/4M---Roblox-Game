--!strict
-- Server events (docs/GAME_DESIGN.md → Server events): every `Interval` seconds (± `IntervalJitter`) one random
-- event runs for everyone in the server. EventService runs them, EventController shows the banner.

export type EventId = "GoldenMinute" | "MegaStick" | "DoublePoints" | "StickStorm"

export type EventDef = {
	Id: EventId,
	-- Banner title.
	DisplayName: string,
	-- One line under the title.
	Description: string,
	-- Seconds the event runs.
	Duration: number,
	-- Relative chance to be picked.
	Weight: number,
	Color: Color3,
}

local defs: { [string]: EventDef } = {
	GoldenMinute = {
		Id = "GoldenMinute",
		DisplayName = "GOLDEN MINUTE",
		Description = "Every stick is golden!",
		Duration = 60,
		Weight = 1,
		Color = Color3.fromRGB(255, 200, 40),
	},
	MegaStick = {
		Id = "MegaStick",
		DisplayName = "MEGA STICK",
		Description = "Your Shibas throw one GIANT stick: catch it for x50!",
		Duration = 90,
		Weight = 1,
		Color = Color3.fromRGB(170, 90, 255),
	},
	DoublePoints = {
		Id = "DoublePoints",
		DisplayName = "DOUBLE POINTS",
		Description = "All Bonk Points x2!",
		Duration = 120,
		Weight = 1,
		Color = Color3.fromRGB(70, 200, 100),
	},
	StickStorm = {
		Id = "StickStorm",
		DisplayName = "STICK STORM",
		Description = "Shibas throw twice as fast!",
		Duration = 90,
		Weight = 1,
		Color = Color3.fromRGB(80, 160, 255),
	},
}

return {
	Defs = defs,
	-- Pick order for the weighted roll (and the admin menu).
	Order = { "GoldenMinute", "MegaStick", "DoublePoints", "StickStorm" } :: { EventId },
	-- Seconds from one event's start to the next one's start.
	Interval = 15 * 60,
	-- The next start is moved by up to this many seconds either way, so events don't feel like a clock.
	IntervalJitter = 60,
	-- Seconds after the server starts until the first event.
	FirstDelay = 5 * 60,

	MegaStick = {
		-- Diameter (hit sphere and model) of the giant stick compared with a normal one.
		DiameterScale = 3,
		RewardMultiplier = 50,
		-- Marker attribute (boolean) on the giant stick, for client effects.
		Attribute = "Mega",
	},
	DoublePoints = {
		RewardMultiplier = 2,
	},
	StickStorm = {
		-- The Shibas' fire interval is multiplied by this.
		FireIntervalMultiplier = 0.5,
	},
}
