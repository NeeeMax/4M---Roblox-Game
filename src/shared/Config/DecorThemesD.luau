--!strict
-- The newer themes (Config/DecorTheme01 … 05: winding walkway, Shiba spots and pads where the props stand). A theme that is
-- false is not written yet; the older one of the same bay (DecorThemesA/B/C) stays. Keyed by the bay number.

local DecorTypes = require(script.Parent.DecorTypes)

local candidates: { [number]: DecorTypes.Theme | boolean } = {
	require(script.Parent.DecorTheme01),
	require(script.Parent.DecorTheme02),
	require(script.Parent.DecorTheme03),
	require(script.Parent.DecorTheme04),
	require(script.Parent.DecorTheme05),
}

local themes: { [number]: DecorTypes.Theme } = {}
for bay, theme in candidates do
	if typeof(theme) == "table" then
		themes[bay] = theme
	end
end

return themes
