--!strict
-- Where the stages of a street plot lie (docs/GAME_DESIGN.md → "Gameplay flow", terraces). Pure data and formulas, shared by
-- StreetService (the walls of free plots) and StreetPlot (the owner's plot). Distances are measured from where the plot meets
-- the road, along the plot away from the road.
--   Starts[n]     where stage n begins (every GroupSize-th Shiba has a staircase of Ramp studs before its stage)
--   Depths[n]     how deep stage n is: its theme's Area plus the margin
--   Elev[n]       the height of its terrace above the plot's ground

local TycoonDecor = require(script.Parent.Parent.Config.TycoonDecor)
local TycoonWorld = require(script.Parent.Parent.Config.TycoonWorld)
local TycoonSteps = require(script.Parent.TycoonSteps)

local LAYOUT = TycoonWorld.Street

export type Layout = {
	Starts: { [number]: number },
	Depths: { [number]: number },
	Elev: { [number]: number },
	Ramp: number,
}

local cached: Layout? = nil

local StreetLayout = {}

function StreetLayout.AreaOf(bay: number): Vector2
	local theme = TycoonDecor.Themes[bay]
	return if theme then theme.Area else LAYOUT.DefaultArea
end

function StreetLayout.Compute(): Layout
	if cached then
		return cached
	end
	local starts: { [number]: number } = {}
	local depths: { [number]: number } = {}
	local elev: { [number]: number } = {}
	local ramp = math.floor(LAYOUT.Rise / LAYOUT.StairRise + 0.5) * LAYOUT.StairRun
	local depth = LAYOUT.FirstStageDepth
	for bay = 1, TycoonSteps.Bays do
		if bay > 1 and (bay - 1) % LAYOUT.GroupSize == 0 then
			depth += ramp
		end
		local area = StreetLayout.AreaOf(bay)
		starts[bay] = depth
		elev[bay] = math.floor((bay - 1) / LAYOUT.GroupSize) * LAYOUT.Rise
		depths[bay] = area.Y + LAYOUT.StageMargin
		depth += depths[bay]
	end
	local layout: Layout = { Starts = starts, Depths = depths, Elev = elev, Ramp = ramp }
	cached = layout
	return layout
end

return StreetLayout
