--!strict
-- Where the stages of a street plot lie (docs/GAME_DESIGN.md → "Gameplay flow", "Terraces and wall"). Pure data and formulas, shared
-- by StreetService (the walls of free plots) and StreetPlot (the owner's plot). Distances are measured from where the plot meets
-- the road, along the plot away from the road.
--   Starts[n]     where stage n begins (its slope, Ramp[n] studs long, lies right before it)
--   Depths[n]     how deep stage n is: its theme's Area scaled by TycoonWorld.Street.StageScale, plus the margin
--   Elev[n]       the height of its floor above the plot's ground: stages 1 to GroupSize are flat on the ground, every later
--                 stage is higher than the one before (RiseFirst, then RiseGrowth more each)
--   Ramp[n]       length of the eased slope from stage n - 1 up to stage n (0 for the flat stages)

local TycoonDecor = require(script.Parent.Parent.Config.TycoonDecor)
local TycoonWorld = require(script.Parent.Parent.Config.TycoonWorld)
local TycoonSteps = require(script.Parent.TycoonSteps)

local LAYOUT = TycoonWorld.Street

export type Layout = {
	Starts: { [number]: number },
	Depths: { [number]: number },
	Elev: { [number]: number },
	Ramp: { [number]: number },
}

local cached: Layout? = nil

local StreetLayout = {}

-- The stage's Area after StageScale (themes are written unscaled; every coordinate of them is scaled the same way).
function StreetLayout.AreaOf(bay: number): Vector2
	local theme = TycoonDecor.Themes[bay]
	return (if theme then theme.Area else LAYOUT.DefaultArea) * LAYOUT.StageScale
end

-- Smooth step 0 → 1 (zero slope at both ends) for the ground between two stages.
function StreetLayout.Ease(t: number): number
	local clamped = math.clamp(t, 0, 1)
	return clamped * clamped * (3 - 2 * clamped)
end

function StreetLayout.Compute(): Layout
	if cached then
		return cached
	end
	local starts: { [number]: number } = {}
	local depths: { [number]: number } = {}
	local elev: { [number]: number } = {}
	local ramps: { [number]: number } = {}
	local depth = LAYOUT.FirstStageDepth
	local height = 0
	for bay = 1, TycoonSteps.Bays do
		local ramp = 0
		if bay > LAYOUT.GroupSize then
			local rise = LAYOUT.RiseFirst + (bay - LAYOUT.GroupSize - 1) * LAYOUT.RiseGrowth
			height += rise
			ramp = rise / LAYOUT.RampSlope
			depth += ramp
		end
		local area = StreetLayout.AreaOf(bay)
		starts[bay] = depth
		elev[bay] = height
		ramps[bay] = ramp
		depths[bay] = area.Y + LAYOUT.StageMargin
		depth += depths[bay]
	end
	local layout: Layout = { Starts = starts, Depths = depths, Elev = elev, Ramp = ramps }
	cached = layout
	return layout
end

return StreetLayout
