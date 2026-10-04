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
		DisplayName = "DOUBLE DOLLARS",
		Description = "All Bonk Dollars x2!",
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

local Events = {
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
		-- The stick density cap (Gameplay.Shooters.MaxThrowsPerSecond) is multiplied by this during the storm, so it
		-- still looks like a storm on islands that are already at the cap (a short spectacle; value per stick still
		-- keeps the income right).
		MaxThrowsMultiplier = 1.5,
	},

	-- ==== Weekend Bonk Party (feat/social-party, docs/GAME_DESIGN.md → Weekend Bonk Party) ====
	-- Every week from `Weekday` (1 = Sunday … 7 = Saturday, UTC) `StartHourUtc` for `DurationHours`. Every server
	-- computes it from the UTC clock (Events.PartyWindow), so all servers agree without messaging.
	Party = {
		Weekday = 7,
		StartHourUtc = 12,
		DurationHours = 24,
		-- Seconds from one server event's start to the next during the party (instead of `Interval`).
		PartyInterval = 7 * 60,
		-- Variant luck multiplier during the party (EventService.VariantLuckMultiplier).
		VariantLuck = 3,
		-- Sticks to catch with your hands during one party for the party quest (reward: EconomyConfig.Party).
		QuestCatches = 500,
		-- Admin "Start party": runs this long.
		AdminDurationMinutes = 10,
		DisplayName = "BONK PARTY",
		Color = Color3.fromRGB(255, 90, 200),
	},
	-- ==== end Weekend Bonk Party ====
}

local SECONDS_PER_DAY = 24 * 60 * 60
local SECONDS_PER_WEEK = 7 * SECONDS_PER_DAY
-- 1970-01-04 00:00 UTC, the first Sunday after the Unix epoch.
local FIRST_SUNDAY = 3 * SECONDS_PER_DAY

-- The scheduled Bonk Party window at Unix time `now`: the one running now, else the next one.
-- Returns startsAt, endsAt (Unix seconds); it runs while startsAt <= now < endsAt.
function Events.PartyWindow(now: number): (number, number)
	local party = Events.Party
	local offset = (party.Weekday - 1) * SECONDS_PER_DAY + party.StartHourUtc * 60 * 60
	local duration = party.DurationHours * 60 * 60
	local weekStart = FIRST_SUNDAY + (now - FIRST_SUNDAY - offset) // SECONDS_PER_WEEK * SECONDS_PER_WEEK
	local startsAt = weekStart + offset
	if now >= startsAt + duration then
		startsAt += SECONDS_PER_WEEK
	end
	return startsAt, startsAt + duration
end

return Events
