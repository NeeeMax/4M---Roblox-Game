--!nocheck
-- Exports a decor theme file (src/shared/Config/DecorThemeNN.luau, schema: Config/DecorTypes) as JSON, the blueprint for the Blender
-- decor models (assets/models/decor/decorkit.py):
--   lune run docs/tools/export_theme src/shared/Config/DecorTheme01.luau assets/models/decor/blueprint_LittleHouse.json
-- Positions are in the stage frame (+X right, +Y up, -Z deeper into the plot, +Z toward the road), sizes in studs.

local fs = require("@lune/fs")
local luau = require("@lune/luau")
local process = require("@lune/process")
local serde = require("@lune/serde")

local file, out = process.args[1], process.args[2]
if not file or not out then
	print("usage: lune run docs/tools/export_theme <theme file> <out.json>")
	process.exit(2)
end

local enum = setmetatable({}, {
	__index = function(_, k)
		return setmetatable({}, {
			__index = function(_, j)
				return k .. "." .. j
			end,
		})
	end,
})
local chunk = luau.load(fs.readFile(file), {
	debugName = file,
	environment = {
		Vector3 = {
			new = function(x, y, z)
				return { x, y, z }
			end,
			zero = { 0, 0, 0 },
		},
		Vector2 = {
			new = function(x, y)
				return { x, y }
			end,
		},
		Color3 = {
			fromRGB = function(r, g, b)
				return { r, g, b }
			end,
		},
		Enum = enum,
		require = function()
			return {}
		end,
		script = setmetatable({}, {
			__index = function(self)
				return self
			end,
		}),
	},
	injectGlobals = true,
})
local theme = chunk()
-- Vector3 / Vector2 / Color3 stubs are plain arrays: x, y, z (or r, g, b), so Size.X etc. do not exist; the theme only builds
-- them through the constructors, which is all this exporter needs.

local function vec2(v)
	return if v then { v[1], v[2] } else nil
end

local data = {
	Key = theme.Key,
	Name = theme.Name,
	Area = vec2(theme.Area),
	Shiba = if theme.Shiba then { Position = vec2(theme.Shiba.Position), Facing = theme.Shiba.Facing } else nil,
	BayPad = vec2(theme.BayPad),
	AutoPad = vec2(theme.AutoPad),
	Path = {},
	Parts = {},
}
for _, waypoint in theme.Path or {} do
	table.insert(data.Path, vec2(waypoint))
end
for _, part in theme.Parts do
	local pieces = {}
	for _, piece in part.Pieces do
		table.insert(pieces, {
			Size = piece.Size,
			Offset = piece.Offset,
			Color = piece.Color,
			Material = if piece.Material then tostring(piece.Material) else nil,
			Shape = if piece.Shape then tostring(piece.Shape) else nil,
			Rotation = piece.Rotation,
		})
	end
	table.insert(data.Parts, {
		Id = part.Id,
		Name = part.Name,
		Description = part.Description,
		Pad = vec2(part.Pad),
		RewardMult = part.RewardMult,
		Pieces = pieces,
	})
end
fs.writeFile(out, serde.encode("json", data, true))
print(`exported {theme.Key}: {#data.Parts} parts to {out}`)
