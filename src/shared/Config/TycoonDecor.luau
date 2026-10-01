--!strict
-- Shiba themes: the decoration the player has to buy around every Shiba (docs/GAME_DESIGN.md → "Gameplay flow"). Pure data.
-- The themes are written in Config/DecorThemesA (bays 1 to 10), B (11 to 20) and C (21 to 30); this module puts them together.
-- Every part becomes the floor-pad step `Decor<bay>_<partId>` (Util/TycoonSteps) and is drawn by World/StreetPlot once bought.
-- If ReplicatedStorage.Assets has a model `Decor_<Key>_<PartId>` it is used instead of the Pieces.

local DecorThemesA = require(script.Parent.DecorThemesA)
local DecorThemesB = require(script.Parent.DecorThemesB)
local DecorThemesC = require(script.Parent.DecorThemesC)
local DecorThemesD = require(script.Parent.DecorThemesD)
local DecorTypes = require(script.Parent.DecorTypes)

export type Piece = DecorTypes.Piece
export type Part = DecorTypes.Part
export type Theme = DecorTypes.Theme
export type ShibaSpot = DecorTypes.ShibaSpot

local themes: { [number]: Theme } = {}
for _, group in { DecorThemesA, DecorThemesB, DecorThemesC, DecorThemesD } do
	for bay, theme in group do
		themes[bay] = theme
	end
end

return {
	-- Themes by bay number (the Shiba the theme belongs to).
	Themes = themes,
}
