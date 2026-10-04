--!strict
-- Theme of the Shiba of bay 30: Void Portal (Config/DecorTypes -> Theme). 190 x 190, the biggest stage of the game: Void Shiba stands on a dark
-- plaza in the middle left; the walkway winds from a floating obsidian gate through rune stones, crystal fields, a void pool and a ruined
-- garden to the back, where everything gets bigger: a Void Citadel in the front left, a guardian Sentinel, a portal ring with a swirling
-- gate, a flying island, a twisted spire, a black hole with its accretion disc and, last of all, a giant floating Void Eye over the exit.
-- Stage frame: +X right, -Z deeper, +Z toward the road. No Neon: purple and cyan glow is plain bright colour.

local DecorTypes = require(script.Parent.DecorTypes)

type Piece = DecorTypes.Piece
type Pieces = { Piece }

local function C(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local BLACK = C(18, 14, 28)
local OBS = C(34, 28, 48)
local DSTONE = C(54, 46, 74)
local STONE = C(80, 70, 104)
local LSTONE = C(112, 100, 142)
local VIOLET = C(120, 56, 210)
local PURPLE = C(160, 80, 255)
local MAGENTA = C(226, 84, 236)
local CYAN = C(72, 228, 255)
local DCYAN = C(28, 150, 190)
local PALE = C(226, 214, 255)

local Slate = Enum.Material.Slate
local Basalt = Enum.Material.Basalt
local Granite = Enum.Material.Granite
local Plastic = Enum.Material.SmoothPlastic
local Metal = Enum.Material.Metal

-- Block centred at (x, y, z), size (sx, sy, sz); optional rotation in degrees.
local function B(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	mat: Enum.Material,
	rx: number?,
	ry: number?,
	rz: number?
): Piece
	local piece: Piece = {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Block,
	}
	if rx or ry or rz then
		piece.Rotation = Vector3.new(rx or 0, ry or 0, rz or 0)
	end
	return piece
end

-- Standing cylinder (axis up): diameter d, height h, centre y.
local function Cy(x: number, y: number, z: number, d: number, h: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(h, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 0, 90),
	}
end

-- Disc facing the road (axis along Z): diameter d, thickness len.
local function Cz(x: number, y: number, z: number, d: number, len: number, color: Color3, mat: Enum.Material): Piece
	return {
		Size = Vector3.new(len, d, d),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Cylinder,
		Rotation = Vector3.new(0, 90, 0),
	}
end

local function Ball(
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	color: Color3,
	mat: Enum.Material
): Piece
	return {
		Size = Vector3.new(sx, sy, sz),
		Offset = Vector3.new(x, y, z),
		Color = color,
		Material = mat,
		Shape = Enum.PartType.Ball,
	}
end

local PATH = {
	Vector2.new(0, 95),
	Vector2.new(-6, 72),
	Vector2.new(40, 56),
	Vector2.new(62, 24),
	Vector2.new(24, 6),
	Vector2.new(-8, -18),
	Vector2.new(-12, -42),
	Vector2.new(-56, -58),
	Vector2.new(-22, -78),
	Vector2.new(0, -95),
}

-- 1: black floor slab, a dark plaza with a violet rune ring under the Shiba and flagstones along the whole walkway.
local function ground(): Pieces
	local pieces: Pieces = {
		B(0, 0.15, 0, 190, 0.3, 190, BLACK, Slate),
		B(-26, 0.4, -30, 32, 0.2, 32, DSTONE, Slate),
		B(-26, 0.52, -30, 24, 0.08, 24, VIOLET, Plastic),
		B(-26, 0.55, -30, 17, 0.06, 17, OBS, Slate),
		Ball(66, 0.35, 70, 34, 0.3, 16, OBS, Slate),
		Ball(-70, 0.35, -40, 30, 0.3, 18, OBS, Slate),
	}
	-- the flagstones along the walkway are only drawn in the model (a turned flat piece would count as solid)
	table.insert(pieces, B(0, 0.36, 83, 8, 0.12, 24, STONE, Slate))
	table.insert(pieces, B(0, 0.36, -88, 8, 0.12, 14, STONE, Slate))
	return pieces
end

-- 2: two obsidian pylons with cyan orbs flank the entrance, a floating arch of shards between them.
local function gate(): Pieces
	local pieces: Pieces = {}
	for _, sx in { -15, 15 } do
		table.insert(pieces, B(sx, 0.9, 90, 7, 1.8, 7, STONE, Slate))
		table.insert(pieces, B(sx, 8, 90, 4.6, 12.4, 4.6, OBS, Basalt))
		table.insert(pieces, B(sx, 14.8, 90, 6, 1.2, 6, VIOLET, Plastic))
		table.insert(pieces, Ball(sx, 18, 90, 3.2, 3.2, 3.2, CYAN, Plastic))
	end
	table.insert(pieces, B(0, 17, 90, 22, 1.4, 2.2, PURPLE, Plastic))
	return pieces
end

-- 3: 22 x 1.4, 9 tall: a black board on two posts that reads THE VOID seen from the road.
local function sign(): Pieces
	return {
		B(-26, 3.8, 84, 22, 6.4, 1.4, OBS, Basalt),
		B(-35, 1.8, 84, 1.8, 3.6, 1.8, STONE, Slate),
		B(-17, 1.8, 84, 1.8, 3.6, 1.8, STONE, Slate),
		B(-26, 7.8, 84, 23, 1.2, 2.2, VIOLET, Plastic),
		Ball(-37.5, 8.6, 84, 2.6, 2.6, 2.6, CYAN, Plastic),
		Ball(-14.5, 8.6, 84, 2.6, 2.6, 2.6, CYAN, Plastic),
	}
end

-- 4: six leaning rune stones in a ring around a violet rune disc with a floating cyan orb.
local function runeStones(): Pieces
	local pieces: Pieces =
		{ B(-64, 0.35, 78, 13, 0.2, 13, VIOLET, Plastic), Ball(-64, 10, 78, 3.4, 3.4, 3.4, CYAN, Plastic) }
	for k = 0, 5 do
		local a = math.rad(k * 60)
		table.insert(
			pieces,
			B(-64 + 9.5 * math.cos(a), 3.5, 78 + 9.5 * math.sin(a), 3.4, 7, 1.6, DSTONE, Slate, 0, -(k * 60 + 90), 0)
		)
	end
	return pieces
end

-- 5: three stone braziers with tall purple flames.
local function braziers(): Pieces
	local pieces: Pieces = {}
	for _, p in { { 28, 86 }, { 40, 81 }, { 52, 86 } } do
		table.insert(pieces, B(p[1], 0.9, p[2], 3.6, 1.8, 3.6, STONE, Slate))
		table.insert(pieces, Cy(p[1], 2.1, p[2], 4.6, 1.2, OBS, Basalt))
		table.insert(pieces, Ball(p[1], 4.4, p[2], 2.8, 4.4, 2.8, PURPLE, Plastic))
	end
	return pieces
end

-- 6: a field of tall crystals on a black rock bed.
local function crystals(): Pieces
	return {
		Ball(76, 0.5, 84, 20, 1.2, 16, OBS, Slate),
		B(76, 9, 84, 4.6, 16, 4.6, VIOLET, Plastic),
		B(70.5, 6, 85.5, 3.6, 10.4, 3.6, PURPLE, Plastic),
		B(81.5, 5.5, 82.5, 3.4, 10, 3.4, MAGENTA, Plastic),
		B(73, 3.5, 80, 2.4, 6, 2.4, CYAN, Plastic),
		B(79, 3, 87.5, 2.6, 5.6, 2.6, VIOLET, Plastic),
		B(83.5, 2.6, 86, 2, 4.8, 2, PURPLE, Plastic),
		B(68, 2.8, 82.5, 2.2, 5, 2.2, DCYAN, Plastic),
	}
end

-- 7: a field of black spikes.
local function spikes(): Pieces
	local pieces: Pieces = { Ball(-80, 0.4, 18, 26, 0.8, 22, OBS, Slate) }
	local spots = {
		{ -80, 18, 11 },
		{ -74, 12, 8 },
		{ -86, 12, 7 },
		{ -72, 24, 9 },
		{ -86, 24, 10 },
		{ -79, 27, 6 },
		{ -79, 8, 5.5 },
	}
	for _, s in spots do
		table.insert(pieces, B(s[1], s[3] / 2, s[2], 2.6, s[3], 2.6, OBS, Basalt))
	end
	return pieces
end

-- 8: a glowing crack in the floor with floating pebbles above it.
local function rift(): Pieces
	return {
		B(22, 0.2, 30, 36, 0.4, 3.6, PURPLE, Plastic),
		B(10, 0.2, 36, 3, 0.4, 14, VIOLET, Plastic),
		B(34, 0.2, 24, 3, 0.4, 14, VIOLET, Plastic),
		B(28, 0.2, 38, 14, 0.4, 2.2, VIOLET, Plastic),
		Ball(14, 9, 33, 2.2, 2.2, 2.2, DSTONE, Slate),
		Ball(24, 11.5, 28, 1.8, 1.8, 1.8, CYAN, Plastic),
		Ball(30, 8.5, 36, 2.4, 2.4, 2.4, DSTONE, Slate),
		Ball(19, 13, 25, 1.6, 1.6, 1.6, PURPLE, Plastic),
	}
end

-- 9: four lamp posts with floating cyan orbs.
local function lanterns(): Pieces
	local pieces: Pieces = {}
	for _, p in { { 2, 46 }, { 34, 40 }, { 38, 32 }, { 4, 20 } } do
		table.insert(pieces, Cy(p[1], 4, p[2], 0.9, 8, OBS, Metal))
		table.insert(pieces, B(p[1], 8.8, p[2], 2.6, 1.6, 2.6, DCYAN, Plastic))
		table.insert(pieces, Ball(p[1], 11.2, p[2], 2.4, 2.4, 2.4, CYAN, Plastic))
	end
	return pieces
end

-- 10: three dead trees with purple leaf clouds.
local function voidTrees(): Pieces
	local pieces: Pieces = {}
	for _, t in
		{
			{ -26, 44, 11 },
			{ -37, 52, 9 },
			{ -19, 57, 8 },
		}
	do
		local h = t[3]
		table.insert(pieces, Cy(t[1], h / 2, t[2], 1.6, h, OBS, Basalt))
		table.insert(pieces, B(t[1] + 2, h * 0.8, t[2], 5, 0.9, 0.9, OBS, Basalt, 0, 0, 35))
		table.insert(pieces, B(t[1] - 2, h * 0.85, t[2], 5, 0.9, 0.9, OBS, Basalt, 0, 0, -35))
		table.insert(pieces, Ball(t[1], h + 1.5, t[2], 7, 4.4, 7, VIOLET, Plastic))
	end
	return pieces
end

-- 11: stepped altar with a floating purple orb.
local function altar(): Pieces
	return {
		B(86, 0.7, -28, 13, 1.4, 13, STONE, Slate),
		B(86, 2.1, -28, 9, 1.4, 9, DSTONE, Slate),
		B(86, 4.5, -28, 5, 3.4, 5, OBS, Basalt),
		B(86, 6.5, -28, 6.4, 0.8, 6.4, VIOLET, Plastic),
		Ball(86, 11, -28, 4.4, 4.4, 4.4, PURPLE, Plastic),
		B(81, 1.8, -28, 1.4, 3.6, 1.4, CYAN, Plastic),
		B(91, 1.8, -28, 1.4, 3.6, 1.4, CYAN, Plastic),
	}
end

-- 12: three giant glowing mushrooms.
local function shrooms(): Pieces
	local pieces: Pieces = {}
	for _, m in
		{
			{ -44, 72, 9, 12 },
			{ -35, 68, 6, 8 },
			{ -37, 78, 7.5, 9 },
		}
	do
		table.insert(pieces, Cy(m[1], m[3] / 2, m[2], 2.2, m[3], PALE, Plastic))
		table.insert(pieces, Ball(m[1], m[3] + 0.5, m[2], m[4], m[4] * 0.55, m[4], PURPLE, Plastic))
	end
	return pieces
end

-- 13: three hooded void knights on pedestals.
local function statues(): Pieces
	local pieces: Pieces = {}
	for _, s in { { -52, -86 }, { -44, -90 }, { -36, -86 } } do
		table.insert(pieces, B(s[1], 1, s[2], 5, 2, 5, STONE, Slate))
		table.insert(pieces, B(s[1], 6, s[2], 3.4, 8, 2.4, OBS, Basalt))
		table.insert(pieces, Ball(s[1], 11, s[2], 3, 3.4, 3, DSTONE, Slate))
		table.insert(pieces, B(s[1], 7.5, s[2] + 1.4, 0.6, 5, 0.6, CYAN, Plastic))
	end
	return pieces
end

-- 14: a round pool of glowing void liquid with a stone rim.
local function pool(): Pieces
	return {
		B(84, 0.3, 40, 20, 0.6, 20, STONE, Slate),
		B(84, 0.55, 40, 17, 0.2, 17, VIOLET, Plastic),
		B(84, 0.9, 30, 22, 1.4, 2.4, OBS, Basalt),
		B(84, 0.9, 50, 22, 1.4, 2.4, OBS, Basalt),
		B(74, 0.9, 40, 2.4, 1.4, 18, OBS, Basalt),
		B(92, 0.9, 40, 2.4, 1.4, 18, OBS, Basalt),
		Ball(80, 1, 38, 4, 0.5, 4, CYAN, Plastic),
		Ball(88, 1, 43, 3.2, 0.5, 3.2, MAGENTA, Plastic),
	}
end

-- 15: broken columns with their capitals floating above.
local function ruins(): Pieces
	local pieces: Pieces = {}
	for _, c in
		{
			{ -60, -12, 12 },
			{ -52, -4, 9 },
			{ -44, -12, 14 },
			{ -37, -5, 6 },
		}
	do
		table.insert(pieces, B(c[1], 0.6, c[2], 4.4, 1.2, 4.4, STONE, Slate))
		table.insert(pieces, Cy(c[1], c[3] / 2 + 1, c[2], 3, c[3], DSTONE, Granite))
		table.insert(pieces, B(c[1], c[3] + 5, c[2], 4.6, 1.4, 4.6, LSTONE, Granite))
	end
	return pieces
end

-- 16: three shadow tentacles rising out of the floor.
local function tentacles(): Pieces
	local pieces: Pieces = {}
	for _, t in
		{
			{ 24, -50, 1 },
			{ 36, -56, -1 },
			{ 30, -46, 1 },
		}
	do
		local x, z, s = t[1], t[2], t[3]
		table.insert(pieces, Cy(x, 3, z, 5, 6, OBS, Basalt))
		table.insert(pieces, Cy(x + s * 1.5, 8, z, 3.8, 6, DSTONE, Basalt))
		table.insert(pieces, Cy(x + s * 3.5, 13, z, 2.8, 6, OBS, Basalt))
		table.insert(pieces, Ball(x + s * 5.8, 17.5, z, 2.6, 4.4, 2.6, VIOLET, Plastic))
	end
	return pieces
end

-- 17: three tall obelisks with cyan tips and floating rune rings.
local function obelisks(): Pieces
	local pieces: Pieces = {}
	for _, o in
		{
			{ 88, 22, 20 },
			{ 88, 10, 15 },
			{ 76, 15, 24 },
		}
	do
		table.insert(pieces, B(o[1], 0.6, o[2], 5.6, 1.2, 5.6, STONE, Slate))
		table.insert(pieces, B(o[1], o[3] / 2 + 1, o[2], 3.2, o[3], 3.2, OBS, Basalt))
		table.insert(pieces, Ball(o[1], o[3] + 2.6, o[2], 2.6, 3.6, 2.6, CYAN, Plastic))
		table.insert(pieces, B(o[1], o[3] * 0.62 + 2, o[2], 7, 0.5, 7, PURPLE, Plastic))
	end
	return pieces
end

-- 18: a black throne on a stepped dais, a floating crown above it.
local function throne(): Pieces
	return {
		B(34, 0.8, -26, 16, 1.6, 14, STONE, Slate),
		B(34, 2.2, -26, 12, 1.2, 10, DSTONE, Slate),
		B(34, 4, -26, 5.6, 2.4, 5, OBS, Basalt),
		B(34, 9, -28.4, 6.4, 12, 1.6, OBS, Basalt),
		B(30.4, 5.5, -26, 1.2, 3.6, 5, OBS, Basalt),
		B(37.6, 5.5, -26, 1.2, 3.6, 5, OBS, Basalt),
		B(31, 16.4, -28.4, 1.6, 4, 1.4, PURPLE, Plastic),
		B(37, 16.4, -28.4, 1.6, 4, 1.4, PURPLE, Plastic),
		B(34, 17.8, -28.4, 1.6, 6.4, 1.4, VIOLET, Plastic),
		B(34, 21, -26, 7, 1.2, 7, CYAN, Plastic),
	}
end

-- 19: a dark watchtower with glowing windows and a purple flame on top.
local function watchtower(): Pieces
	return {
		B(-86, 1, -46, 14, 2, 14, STONE, Slate),
		B(-86, 12, -46, 9, 20, 9, OBS, Basalt),
		B(-86, 23.5, -46, 12, 3, 12, DSTONE, Slate),
		B(-86, 28.5, -46, 8, 7, 8, OBS, Basalt),
		B(-86, 33.2, -46, 10.4, 2.4, 10.4, VIOLET, Plastic),
		Ball(-86, 36.5, -46, 4, 5, 4, PURPLE, Plastic),
		B(-86, 14, -41.2, 3, 5, 0.6, CYAN, Plastic),
		B(-86, 28.5, -41.6, 3.4, 3.4, 0.6, CYAN, Plastic),
	}
end

-- 20: nine large crystal shards floating in a ring above the rift.
local function shards(): Pieces
	local pieces: Pieces = {}
	for k = 0, 8 do
		local a = k * 40
		local r = if k % 2 == 0 then 15 else 9
		local y = 15 + (k * 7 % 5) * 3.5
		local s = 5 + (k % 3) * 1.6
		local col = if k % 3 == 0 then PURPLE elseif k % 3 == 1 then VIOLET else CYAN
		table.insert(
			pieces,
			B(
				22 + r * math.cos(math.rad(a)),
				y,
				30 + r * math.sin(math.rad(a)),
				3.4,
				s + 4,
				3,
				col,
				Plastic,
				0,
				a,
				(k % 3 - 1) * 14
			)
		)
	end
	return pieces
end

-- 21: an orrery: a violet sun and three rings on a stone stand.
local function orrery(): Pieces
	return {
		B(-32, 0.7, 18, 12, 1.4, 12, STONE, Slate),
		Cy(-32, 3.4, 18, 3.4, 4, OBS, Basalt),
		Ball(-32, 11, 18, 5, 5, 5, PURPLE, Plastic),
		B(-32, 11, 18, 17, 0.6, 17, VIOLET, Plastic),
		B(-32, 11, 18, 12, 0.6, 12, CYAN, Plastic),
		Ball(-23.8, 11, 18, 2.2, 2.2, 2.2, CYAN, Plastic),
		Ball(-35, 11, 24.4, 1.8, 1.8, 1.8, MAGENTA, Plastic),
		Ball(-38.6, 11, 13, 1.6, 1.6, 1.6, PALE, Plastic),
	}
end

-- 22: a colossal guardian statue holding a floating cyan sword, a violet gem in its chest.
local function sentinel(): Pieces
	return {
		B(80, 1.2, 66, 20, 2.4, 20, STONE, Slate),
		B(76, 9, 66, 5.6, 14, 6, OBS, Basalt),
		B(84, 9, 66, 5.6, 14, 6, OBS, Basalt),
		B(80, 20, 66, 15, 8, 9, DSTONE, Slate),
		B(80, 28.5, 66, 13, 10, 8, OBS, Basalt),
		B(71, 26, 66, 4.6, 14, 5, OBS, Basalt),
		B(89, 26, 66, 4.6, 14, 5, OBS, Basalt),
		Ball(80, 37.5, 66, 8, 8, 8, DSTONE, Slate),
		B(76.4, 38, 70.2, 2, 1.2, 0.6, CYAN, Plastic),
		B(83.6, 38, 70.2, 2, 1.2, 0.6, CYAN, Plastic),
		B(80, 30, 70.2, 3.6, 3.6, 0.8, PURPLE, Plastic),
		B(91.5, 27, 66, 1.2, 22, 2.4, CYAN, Plastic),
		B(91.5, 17, 66, 4, 1.2, 2.4, PURPLE, Plastic),
		Ball(80, 48, 66, 7, 7, 7, VIOLET, Plastic),
	}
end

-- 23: the portal ring: eight stone arcs on a plinth, runes between them.
local function portalFrame(): Pieces
	local pieces: Pieces = { B(66, 3.5, -4, 14, 7, 6, STONE, Slate), B(66, 7.4, -4, 9, 0.8, 5, VIOLET, Plastic) }
	local cx, cy, cz, r = 66, 24, -4, 17
	for k = 0, 7 do
		local a = math.rad(k * 45 + 22.5)
		local len = 2 * r * math.sin(math.rad(22.5)) + 1.2
		table.insert(
			pieces,
			B(
				cx + r * math.cos(a),
				cy + r * math.sin(a),
				cz,
				len,
				3.4,
				4.6,
				if k % 2 == 0 then OBS else DSTONE,
				Basalt,
				0,
				0,
				k * 45 + 22.5 + 90
			)
		)
	end
	table.insert(pieces, B(66, 41.6, -4, 4, 2.4, 5, PURPLE, Plastic))
	return pieces
end

-- 24: the swirl filling the ring: stacked discs of purple, violet, magenta and cyan.
local function portalSwirl(): Pieces
	return {
		Cz(66, 24, -4, 30, 1, VIOLET, Plastic),
		Cz(66, 24, -3.4, 24, 1, PURPLE, Plastic),
		Cz(66, 24, -2.8, 17, 1, MAGENTA, Plastic),
		Cz(66, 24, -2.2, 10, 1, CYAN, Plastic),
		Cz(66, 24, -1.6, 4, 1, PALE, Plastic),
	}
end

-- 25: the Void Citadel: a black keep with four towers and a glowing great hall, a violet spire on top.
local function citadel(): Pieces
	local pieces: Pieces = {
		B(-62, 1.2, 50, 42, 2.4, 30, STONE, Slate),
		B(-62, 11, 50, 22, 17, 16, OBS, Basalt),
		B(-62, 21, 50, 24, 3, 18, DSTONE, Slate),
		B(-62, 29, 50, 12, 13, 10, OBS, Basalt),
		B(-62, 37, 50, 14, 3, 12, VIOLET, Plastic),
		B(-62, 45, 50, 5, 14, 5, PURPLE, Plastic),
		B(-62, 7, 58.2, 8, 9, 0.6, CYAN, Plastic),
	}
	for _, t in { { -80, 38 }, { -44, 38 }, { -80, 62 }, { -44, 62 } } do
		table.insert(pieces, B(t[1], 13, t[2], 7, 22, 7, OBS, Basalt))
		table.insert(pieces, Ball(t[1], 25.5, t[2], 8, 6.4, 8, VIOLET, Plastic))
	end
	table.insert(pieces, B(-62, 3, 63.4, 10, 1, 2, DSTONE, Slate))
	return pieces
end

-- 26: a swarm of comets streaking over the entrance, purple and cyan heads with long tails.
local function comets(): Pieces
	local pieces: Pieces = {}
	local spots = {
		{ -20, 40, 52, CYAN },
		{ 0, 30, 60, PURPLE },
		{ 24, 44, 48, MAGENTA },
		{ -40, 28, 40, VIOLET },
		{ 8, 52, 70, CYAN },
	}
	for _, s in spots do
		table.insert(pieces, Ball(s[1], s[2], s[3], 5, 5, 5, s[4], Plastic))
		table.insert(pieces, B(s[1] - 7, s[2] + 3.4, s[3] + 2, 14, 1.6, 2, s[4], Plastic, 0, 12, -22))
		table.insert(pieces, B(s[1] - 5, s[2] + 2.2, s[3] - 2.6, 9, 1.2, 1.4, PALE, Plastic, 0, 12, -22))
	end
	return pieces
end

-- 27: a flying island: a floating rock with a ruined temple, a crystal and a purple waterfall running off the edge.
local function island(): Pieces
	return {
		Ball(-58, 22, 6, 46, 20, 46, DSTONE, Granite),
		Ball(-58, 16.5, 6, 24, 14, 24, OBS, Basalt),
		B(-58, 32.4, 6, 52, 3.6, 52, OBS, Granite),
		B(-58, 34.4, 6, 46, 1, 46, STONE, Slate),
		B(-58, 41, 6, 16, 11, 12, DSTONE, Slate),
		B(-58, 48, 6, 18, 3, 14, OBS, Basalt),
		B(-48, 40, 14, 3, 10, 3, STONE, Slate),
		B(-68, 40, 14, 3, 10, 3, STONE, Slate),
		B(-70, 38.5, -6, 3, 7, 3, STONE, Slate),
		B(-44, 38, -6, 3, 6, 3, STONE, Slate),
		B(-58, 43, -12, 4, 12, 4, PURPLE, Plastic),
		B(-82, 22, 10, 2, 22, 5, CYAN, Plastic),
		Ball(-58, 53, 6, 4, 5, 4, VIOLET, Plastic),
	}
end

-- 28: a twisted spire: black tiers turning on each other, floating rings, a violet crown.
local function spire(): Pieces
	local pieces: Pieces = {
		B(-80, 1.5, -78, 22, 3, 22, STONE, Slate),
		B(-80, 5, -78, 17, 4, 17, DSTONE, Slate, 0, 8, 0),
	}
	local y = 7
	for k = 0, 6 do
		local w = 12 - k * 1.3
		table.insert(pieces, B(-80, y + 5, -78, w, 10, w, if k % 2 == 0 then OBS else DSTONE, Basalt, 0, 14 * k, 0))
		y += 10
	end
	table.insert(pieces, B(-80, y + 3, -78, 4, 6, 4, VIOLET, Plastic, 0, 20, 0))
	table.insert(pieces, Ball(-80, y + 9, -78, 4.4, 8, 4.4, PURPLE, Plastic))
	table.insert(pieces, B(-80, 52, -78, 26, 0.8, 26, CYAN, Plastic))
	return pieces
end

-- 29: the black hole: a dark core over the floor, a wide flat accretion disc and jets of cyan light.
local function blackHole(): Pieces
	return {
		B(66, 0.25, -64, 12, 0.5, 12, DSTONE, Slate),
		Ball(66, 28, -64, 18, 18, 18, BLACK, Plastic),
		B(66, 28, -64, 52, 1.2, 52, VIOLET, Plastic),
		B(66, 28.3, -64, 40, 1.2, 40, PURPLE, Plastic),
		B(66, 28.6, -64, 29, 1.2, 29, MAGENTA, Plastic),
		B(66, 28.9, -64, 22, 1.2, 22, PALE, Plastic),
		Cy(66, 44, -64, 2.4, 20, CYAN, Plastic),
		Cy(66, 12, -64, 2.4, 16, CYAN, Plastic),
		Ball(50, 36, -50, 3, 3, 3, DSTONE, Slate),
		Ball(82, 20, -78, 3.4, 3.4, 3.4, DSTONE, Slate),
		Ball(78, 38, -50, 2.4, 2.4, 2.4, PURPLE, Plastic),
		Ball(54, 17, -76, 2.6, 2.6, 2.6, MAGENTA, Plastic),
	}
end

-- 30: the Void Eye: a giant eye hovering over the exit, held by a black spire, iris of purple and cyan, lids and lashes of black shards.
local function voidEye(): Pieces
	return {
		B(24, 1.2, -86, 14, 2.4, 10, STONE, Slate),
		B(24, 14, -86, 6, 24, 5, OBS, Basalt),
		B(24, 30, -86, 9, 8, 7, DSTONE, Slate),
		Ball(24, 48, -86, 46, 28, 12, PALE, Plastic),
		Cz(24, 48, -80.6, 19, 1.8, PURPLE, Plastic),
		Cz(24, 48, -79.4, 12, 1.4, CYAN, Plastic),
		Cz(24, 48, -78.4, 6, 1.2, BLACK, Plastic),
		B(24, 63, -86, 44, 3, 8, OBS, Basalt),
		B(24, 33.2, -86, 40, 2.4, 8, OBS, Basalt),
		B(5, 55, -86, 3.4, 12, 3, VIOLET, Plastic, 0, 0, 20),
		B(43, 55, -86, 3.4, 12, 3, VIOLET, Plastic, 0, 0, -20),
		B(24, 70, -86, 5, 12, 5, PURPLE, Plastic),
		B(12, 68, -86, 3.4, 10, 3, CYAN, Plastic, 0, 0, 25),
		B(36, 68, -86, 3.4, 10, 3, CYAN, Plastic, 0, 0, -25),
	}
end

local theme: DecorTypes.Theme = {
	Key = "VoidPortal",
	Name = "Void Portal",
	Area = Vector2.new(190, 190),
	Shiba = { Position = Vector2.new(-26, -30), Facing = 0 },
	Path = PATH,
	BayPad = Vector2.new(-2, -22),
	AutoPad = Vector2.new(-2, -34),
	Parts = {
		-- 1
		{
			Id = "Ground",
			Name = "Dark Platform",
			Description = "Black void stone with flagstones along the path and a violet rune ring under the Void Shiba.",
			Pad = Vector2.new(-9, 80),
			PriceSeconds = 70,
			Pieces = ground(),
		},
		-- 2
		{
			Id = "Gate",
			Name = "Obsidian Gate",
			Description = "Two obsidian pylons with cyan orbs guard the entrance, a floating arch of shards between them.",
			Pad = Vector2.new(7, 82),
			PriceSeconds = 81,
			Pieces = gate(),
		},
		-- 3
		{
			Id = "Sign",
			Name = "Void Sign",
			Description = "A black board with violet trim that reads THE VOID, with a cyan orb on each end.",
			Pad = Vector2.new(-20, 76),
			PriceSeconds = 94,
			Pieces = sign(),
		},
		-- 4
		{
			Id = "RuneStones",
			Name = "Rune Stones",
			Description = "Six leaning stones around a violet rune disc, a cyan orb hovering in the middle.",
			Pad = Vector2.new(-64, 78),
			PriceSeconds = 109,
			Pieces = runeStones(),
		},
		-- 5
		{
			Id = "Braziers",
			Name = "Purple Braziers",
			Description = "Three stone braziers burning with tall purple flames.",
			Pad = Vector2.new(40, 72),
			PriceSeconds = 127,
			Pieces = braziers(),
		},
		-- 6
		{
			Id = "Crystals",
			Name = "Void Crystals",
			Description = "A field of tall violet, magenta and cyan crystals growing from a black rock bed.",
			Pad = Vector2.new(62, 78),
			PriceSeconds = 147,
			Pieces = crystals(),
		},
		-- 7
		{
			Id = "Spikes",
			Name = "Obsidian Spikes",
			Description = "A field of black glass spikes of all heights.",
			Pad = Vector2.new(-66, 18),
			PriceSeconds = 171,
			Pieces = spikes(),
		},
		-- 8
		{
			Id = "Rift",
			Name = "Glowing Rift",
			Description = "A branching crack in the floor shining purple, pebbles drifting up out of it.",
			Pad = Vector2.new(16, 24),
			PriceSeconds = 198,
			Pieces = rift(),
		},
		-- 9
		{
			Id = "Lanterns",
			Name = "Void Lanterns",
			Description = "Four dark lamp posts with floating cyan orbs.",
			Pad = Vector2.new(14, 44),
			PriceSeconds = 230,
			Pieces = lanterns(),
		},
		-- 10
		{
			Id = "VoidTrees",
			Name = "Dead Trees",
			Description = "Three bare black trees carrying clouds of purple leaves.",
			Pad = Vector2.new(-22, 36),
			PriceSeconds = 267,
			Pieces = voidTrees(),
		},
		-- 11
		{
			Id = "Altar",
			Name = "Void Altar",
			Description = "A stepped black altar with cyan pillars and a purple orb floating over it.",
			Pad = Vector2.new(72, -28),
			RewardMult = 1.25,
			PriceSeconds = 310,
			Pieces = altar(),
		},
		-- 12
		{
			Id = "Shrooms",
			Name = "Glow Mushrooms",
			Description = "Three giant mushrooms with pale stems and bright purple caps.",
			Pad = Vector2.new(-30, 62),
			PriceSeconds = 359,
			Pieces = shrooms(),
		},
		-- 13
		{
			Id = "Statues",
			Name = "Void Knights",
			Description = "Three hooded knights of black stone with glowing cyan swords, standing in a half circle.",
			Pad = Vector2.new(-44, -78),
			PriceSeconds = 417,
			Pieces = statues(),
		},
		-- 14
		{
			Id = "Pool",
			Name = "Void Pool",
			Description = "A square pool of glowing purple liquid inside a black rim, cyan lilies on top.",
			Pad = Vector2.new(70, 52),
			PriceSeconds = 484,
			Pieces = pool(),
		},
		-- 15
		{
			Id = "Ruins",
			Name = "Floating Ruins",
			Description = "Broken stone columns whose capitals have drifted up and hang above them.",
			Pad = Vector2.new(-46, -22),
			PriceSeconds = 562,
			Pieces = ruins(),
		},
		-- 16
		{
			Id = "Tentacles",
			Name = "Shadow Tentacles",
			Description = "Three black tentacles with violet tips rising out of the floor and curling over.",
			Pad = Vector2.new(14, -48),
			PriceSeconds = 652,
			Pieces = tentacles(),
		},
		-- 17
		{
			Id = "Obelisks",
			Name = "Rune Obelisks",
			Description = "Three black obelisks with cyan tips, a purple rune ring floating around each.",
			Pad = Vector2.new(82, 16),
			PriceSeconds = 757,
			Pieces = obelisks(),
		},
		-- 18
		{
			Id = "Throne",
			Name = "Void Throne",
			Description = "A tall black throne on a stepped dais, a crown of purple spikes and a cyan ring floating above it.",
			Pad = Vector2.new(20, -22),
			PriceSeconds = 879,
			Pieces = throne(),
		},
		-- 19
		{
			Id = "Watchtower",
			Name = "Dark Watchtower",
			Description = "A black tower with glowing cyan windows and a purple flame burning on top.",
			Pad = Vector2.new(-74, -32),
			PriceSeconds = 1020,
			Pieces = watchtower(),
		},
		-- 20
		{
			Id = "Shards",
			Name = "Floating Shards",
			Description = "Nine big crystal shards drift in a ring high above the glowing rift.",
			Pad = Vector2.new(22, 30),
			RewardMult = 1.3,
			PriceSeconds = 1185,
			Pieces = shards(),
		},
		-- 21
		{
			Id = "Orrery",
			Name = "Void Orrery",
			Description = "A purple sun held by a stone stand, with glowing rings and little planets turning around it.",
			Pad = Vector2.new(-22, 12),
			PriceSeconds = 1375,
			Pieces = orrery(),
		},
		-- 22
		{
			Id = "Sentinel",
			Name = "Void Sentinel",
			Description = "A colossal guardian of black stone with a purple gem in its chest and a floating cyan sword.",
			Pad = Vector2.new(64, 66),
			RewardMult = 1.4,
			PriceSeconds = 1595,
			Pieces = sentinel(),
		},
		-- 23
		{
			Id = "PortalFrame",
			Name = "Portal Frame",
			Description = "A huge ring of black and grey stone arcs on a plinth, a violet keystone on top.",
			Pad = Vector2.new(50, 0),
			PriceSeconds = 1850,
			Pieces = portalFrame(),
		},
		-- 24
		{
			Id = "PortalSwirl",
			Name = "Portal Swirl",
			Description = "The ring fills with a swirling gate of violet, purple, magenta and cyan.",
			Pad = Vector2.new(66, 4),
			PriceSeconds = 2145,
			Pieces = portalSwirl(),
		},
		-- 25
		{
			Id = "Citadel",
			Name = "Void Citadel",
			Description = "A black fortress with four round towers, a glowing great hall and a purple spire.",
			Pad = Vector2.new(-34, 40),
			RewardMult = 1.5,
			PriceSeconds = 2490,
			Pieces = citadel(),
		},
		-- 26
		{
			Id = "Comets",
			Name = "Comet Swarm",
			Description = "Five comets in purple, cyan and magenta streak across the sky over the entrance.",
			Pad = Vector2.new(-10, 56),
			PriceSeconds = 2890,
			Pieces = comets(),
		},
		-- 27
		{
			Id = "Island",
			Name = "Flying Island",
			Description = "A rock island floats above the plot with a ruined temple, a crystal and a purple waterfall.",
			Pad = Vector2.new(-40, 8),
			RewardMult = 1.5,
			PriceSeconds = 3350,
			Pieces = island(),
		},
		-- 28
		{
			Id = "Spire",
			Name = "Twisted Spire",
			Description = "Black tiers twist on top of each other up to a violet crown, a cyan ring floating high above.",
			Pad = Vector2.new(-64, -66),
			PriceSeconds = 3890,
			Pieces = spire(),
		},
		-- 29
		{
			Id = "BlackHole",
			Name = "Black Hole Core",
			Description = "A pitch black core hangs over the floor inside a glowing disc, jets of cyan light shoot up and down.",
			Pad = Vector2.new(66, -48),
			RewardMult = 1.5,
			PriceSeconds = 4510,
			Pieces = blackHole(),
		},
		-- 30
		{
			Id = "VoidEye",
			Name = "Void Eye",
			Description = "A giant eye with a purple and cyan iris stares down from a black spire over the exit.",
			Pad = Vector2.new(10, -76),
			PriceSeconds = 5230,
			Pieces = voidEye(),
		},
	},
}

return theme
