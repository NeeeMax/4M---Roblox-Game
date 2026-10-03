--!strict
-- The newer themes (Config/DecorTheme01 … 25: winding walkway, Shiba spots and pads where the props stand). A theme that is
-- false is not written yet; the older one of the same bay (DecorThemesA/B/C) stays. Keyed by the bay number.

local DecorTypes = require(script.Parent.DecorTypes)

local candidates: { [number]: DecorTypes.Theme | boolean } = {
	require(script.Parent.DecorTheme01),
	require(script.Parent.DecorTheme02),
	require(script.Parent.DecorTheme03),
	require(script.Parent.DecorTheme04),
	require(script.Parent.DecorTheme05),
	require(script.Parent.DecorTheme06),
	require(script.Parent.DecorTheme07),
	require(script.Parent.DecorTheme08),
	require(script.Parent.DecorTheme09),
	require(script.Parent.DecorTheme10),
	require(script.Parent.DecorTheme11),
	require(script.Parent.DecorTheme12),
	require(script.Parent.DecorTheme13),
	require(script.Parent.DecorTheme14),
	require(script.Parent.DecorTheme15),
	require(script.Parent.DecorTheme16),
	require(script.Parent.DecorTheme17),
	require(script.Parent.DecorTheme18),
	require(script.Parent.DecorTheme19),
	require(script.Parent.DecorTheme20),
	require(script.Parent.DecorTheme21),
	require(script.Parent.DecorTheme22),
	require(script.Parent.DecorTheme23),
	require(script.Parent.DecorTheme24),
	require(script.Parent.DecorTheme25),
}

local themes: { [number]: DecorTypes.Theme } = {}
for bay, theme in candidates do
	if typeof(theme) == "table" then
		themes[bay] = theme
	end
end

return themes
