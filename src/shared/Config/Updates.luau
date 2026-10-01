--!strict
-- Update log board (Services/UpdateBoardService, docs/GAME_DESIGN.md → Update log board): the last updates and a
-- countdown to the next one. Edit `Entries` (newest first) with every update; the countdown needs no edit because
-- updates ship on a fixed weekday (docs/research/ROBLOX_PACING.md: Roblox suggests a regular cadence, and the Bonk
-- Party on Saturday then shows the new content).

export type Entry = {
	Date: string,
	Title: string,
	-- Short lines (the board is small): at most ~4 lines of ~32 characters.
	Lines: { string },
}

local SECONDS_PER_DAY = 24 * 60 * 60
local SECONDS_PER_WEEK = 7 * SECONDS_PER_DAY
-- 1970-01-04 00:00 UTC, the first Sunday after the Unix epoch.
local FIRST_SUNDAY = 3 * SECONDS_PER_DAY

local entries: { Entry } = {
	{
		Date = "2026-10-01",
		Title = "Update log + badges",
		Lines = {
			"New: this update board",
			"New: badges for first milestones",
		},
	},
	{
		Date = "2026-09-30",
		Title = "The Street",
		Lines = {
			"10 plots along one street",
			"One Shiba per expansion, themed decor",
			"Shibas swing their own stick",
		},
	},
}

local Updates = {
	-- Newest first; the board shows the first `ShownEntries`.
	ShownEntries = 2,
	Entries = entries,

	-- Updates ship every week on this day (1 = Sunday … 7 = Saturday, UTC) at this hour.
	NextUpdate = {
		Weekday = 6,
		HourUtc = 16,
	},

	Board = {
		Width = 24,
		-- Gap between the ground and the bottom of the board (the poles).
		Height = 6,
		-- Street: the board stands this far inside the west end of the road, at the road's middle.
		StreetEndInset = 6,
		-- Island hub (Features.Street off): X and Z offset from the hub centre; the board faces the hub spawn (+Z).
		HubOffset = Vector2.new(-30, 22),
		Color = Color3.fromRGB(90, 200, 255),
		TitleText = "UPDATE LOG",
	},
}

-- Unix time of the next update after `now` (an update happening this very second counts as past).
function Updates.NextUpdateAt(now: number): number
	local offset = (Updates.NextUpdate.Weekday - 1) * SECONDS_PER_DAY + Updates.NextUpdate.HourUtc * 60 * 60
	local weekStart = FIRST_SUNDAY + (now - FIRST_SUNDAY - offset) // SECONDS_PER_WEEK * SECONDS_PER_WEEK
	local at = weekStart + offset
	if at <= now then
		at += SECONDS_PER_WEEK
	end
	return at
end

return Updates
