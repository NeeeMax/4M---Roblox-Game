--!strict
-- The cell around a street plot's reached stages (docs/GAME_DESIGN.md → "Terraces and walls"): brown rock cliffs on both sides
-- that follow each reached stage's width, a back wall behind the last reached stage, and a front wall that closes the rest of
-- the plot's width next to the road. The player can only walk inside the cell, which starts small (stage 1) and grows with
-- every Shiba that becomes available. Built again by StreetService.SetReach when the reach changes.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Street = require(ReplicatedStorage.Shared.Config.Street)
local TycoonWorld = require(ReplicatedStorage.Shared.Config.TycoonWorld)
local StreetLayout = require(ReplicatedStorage.Shared.Util.StreetLayout)

local LAYOUT = TycoonWorld.Street

export type Frame = {
	-- Where the plot meets the road (on the centre line), the direction away from the road and the plot's right.
	RoadEnd: Vector3,
	Back: Vector3,
	Right: Vector3,
}

local PlotWalls = {}

-- Builds the cell for stages 1 … `reached` and returns its folder (parented to `parent`).
function PlotWalls.Build(parent: Instance, frame: Frame, layout: StreetLayout.Layout, reached: number): Folder
	local folder = Instance.new("Folder")
	folder.Name = "Walls"
	local thick = LAYOUT.WallThickness

	-- A cliff piece: `depth` away from the road, `lateral` to the right of the path, from the ground (-1) up to `top`.
	local function piece(name: string, depth: number, lateral: number, length: number, width: number, top: number)
		local at = frame.RoadEnd + frame.Back * depth + frame.Right * lateral + Vector3.new(0, (top - 1) / 2, 0)
		local part = Instance.new("Part")
		part.Name = name
		part.Size = Vector3.new(width, top + 1, length)
		part.CFrame = CFrame.lookAt(at, at + frame.Back)
		part.Anchored = true
		part.CastShadow = false
		part.Color = LAYOUT.CliffColor
		part.Material = Enum.Material.Rock
		part.TopSurface = Enum.SurfaceType.Smooth
		part.BottomSurface = Enum.SurfaceType.Smooth
		part.Parent = folder
	end

	local last = math.clamp(reached, 1, #layout.Starts)
	for bay = 1, last do
		local first = bay > 1 and (bay - 1) % LAYOUT.GroupSize == 0
		local from = if bay == 1 then 0 else layout.Starts[bay] - (if first then layout.Ramp else 0)
		local to = layout.Starts[bay] + layout.Depths[bay]
		local top = layout.Elev[bay] + LAYOUT.CliffHeight
		local half = layout.HalfWidth[bay]
		for _, side in { -1, 1 } do
			piece(`Side{bay}`, (from + to) / 2, side * half, to - from, thick, top)
			-- The cell gets wider at this stage: close the step.
			if bay > 1 and half ~= layout.HalfWidth[bay - 1] then
				local inner = layout.HalfWidth[bay - 1]
				piece(`Step{bay}`, from, side * (inner + half) / 2, thick, math.abs(half - inner) + thick, top)
			end
		end
	end

	-- Back wall behind the last reached stage.
	local to = layout.Starts[last] + layout.Depths[last]
	piece("Back", to - thick / 2, 0, thick, 2 * layout.HalfWidth[last] + thick, layout.Elev[last] + LAYOUT.CliffHeight)

	-- Front wall: closes the plot's width next to the road, beside the cell's opening.
	local opening = layout.HalfWidth[1]
	local wing = Street.PlotWidth / 2 - opening
	for _, side in { -1, 1 } do
		piece("Front", thick / 2, side * (opening + wing / 2), thick, wing, LAYOUT.CliffHeight)
	end

	folder.Parent = parent
	return folder
end

return PlotWalls
