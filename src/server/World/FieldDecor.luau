--!strict
-- The drop zone's decoration (Config/FieldDecor, docs/GAME_DESIGN.md → World → Field look), built once per plot by
-- IslandService: paint in the sand (a SurfaceGui on an invisible plate, so nothing flickers), the rope border with
-- posts, caps, pennants and soft lights, mini BONK signs on the posts, beach props round the edge (PropService) and a
-- faint sand glitter. Everything is anchored and visual only (no collisions, queries or touches). About 77 parts per
-- plot with every prop still a placeholder.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config.FieldDecor)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)

local PropService = require(script.Parent.Parent.Services.PropService)
local Signs = require(script.Parent.Signs)

local ISLAND = Gameplay.Island
local PAINT = Config.Paint
local BORDER = Config.Border

local BUILDERS: { [string]: PropService.Builder } = {
	Prop_Sandcastle = PropService.Builders.Sandcastle,
	Prop_BeachBall = PropService.Builders.BeachBall,
	Prop_BucketSpade = PropService.Builders.BucketSpade,
	Prop_BoneToy = PropService.Builders.BoneToy,
	Prop_GrassTuft = PropService.Builders.GrassTuft,
}

local FieldDecor = {}

local function direction(angle: number): Vector3
	return Vector3.new(math.sin(angle), 0, -math.cos(angle))
end

local function visualOnly(part: BasePart)
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
end

local function newPart(
	name: string,
	shape: Enum.PartType,
	size: Vector3,
	cframe: CFrame,
	color: Color3,
	material: Enum.Material,
	parent: Instance
): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Shape = shape
	part.Size = size
	part.CFrame = cframe
	part.Color = color
	part.Material = material
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	visualOnly(part)
	part.Parent = parent
	return part
end

-- --- Paint -----------------------------------------------------------------------------------------------------

-- Canvas helpers: positions and sizes in studs from the field centre (X right, Y toward the far side, seen from the
-- centre looking at the bridge), converted to scale so the pixel density does not matter.
type Canvas = { Frame: Frame, Size: number, PixelsPerStud: number, Z: number }

local function blob(canvas: Canvas, x: number, y: number, width: number, height: number): Frame
	local frame = Instance.new("Frame")
	frame.AnchorPoint = Vector2.new(0.5, 0.5)
	frame.Position = UDim2.fromScale(0.5 + x / canvas.Size, 0.5 + y / canvas.Size)
	frame.Size = UDim2.fromScale(width / canvas.Size, height / canvas.Size)
	frame.BorderSizePixel = 0
	canvas.Z += 1
	frame.ZIndex = canvas.Z
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0.5, 0)
	corner.Parent = frame
	frame.Parent = canvas.Frame
	return frame
end

local function fill(canvas: Canvas, spot: Config.Blob, color: Color3, transparency: number)
	local frame = blob(canvas, spot.X, spot.Y, spot.Width, spot.Height)
	frame.Rotation = spot.Rotation
	frame.BackgroundColor3 = color
	frame.BackgroundTransparency = transparency
end

-- A painted band from `radius` outward, `width` studs wide (a UIStroke draws outside the frame's edge).
local function ring(canvas: Canvas, radius: number, width: number, color: Color3, transparency: number)
	local frame = blob(canvas, 0, 0, radius * 2, radius * 2)
	frame.BackgroundTransparency = 1
	local stroke = Instance.new("UIStroke")
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	stroke.Thickness = width * canvas.PixelsPerStud
	stroke.Color = color
	stroke.Transparency = transparency
	stroke.Parent = frame
end

local function lettering(canvas: Canvas, spot: Config.Blob, text: string)
	local label = Instance.new("TextLabel")
	label.AnchorPoint = Vector2.new(0.5, 0.5)
	label.Position = UDim2.fromScale(0.5 + spot.X / canvas.Size, 0.5 + spot.Y / canvas.Size)
	label.Size = UDim2.fromScale(spot.Width / canvas.Size, spot.Height / canvas.Size)
	label.Rotation = spot.Rotation
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.Text = text
	label.TextColor3 = PAINT.LetteringColor
	label.TextTransparency = PAINT.LetteringTransparency
	canvas.Z += 1
	label.ZIndex = canvas.Z
	local stroke = Instance.new("UIStroke")
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	stroke.Thickness = 0.3 * canvas.PixelsPerStud
	stroke.Color = PAINT.LetteringStroke
	stroke.Transparency = PAINT.LetteringTransparency
	stroke.Parent = label
	label.Parent = canvas.Frame
end

local function between(random: Random, range: { number }): number
	return random:NextNumber(range[1], range[2])
end

-- A random spot inside `radius` (uniform over the disc).
local function spotInDisc(random: Random, radius: number): (number, number)
	local angle = random:NextNumber(0, 2 * math.pi)
	local distance = radius * math.sqrt(random:NextNumber())
	return math.cos(angle) * distance, math.sin(angle) * distance
end

local function buildPaint(center: Vector3, hubAngle: number, slot: number, parent: Instance)
	local size = ISLAND.FieldRadius * 2 + 1
	local thickness = 0.05
	local top = center.Y + ISLAND.FieldTop + PAINT.Lift
	local position = Vector3.new(center.X, top - thickness / 2, center.Z)
	-- Front (−Z) toward the bridge: the canvas's top edge points at the bridge.
	local plate = newPart(
		"FieldPaint",
		Enum.PartType.Block,
		Vector3.new(size, thickness, size),
		CFrame.lookAt(position, position + direction(hubAngle)),
		Color3.new(1, 1, 1),
		Enum.Material.SmoothPlastic,
		parent
	)
	plate.Transparency = 1
	plate.CastShadow = false

	local gui = Instance.new("SurfaceGui")
	gui.Name = "Paint"
	gui.Face = Enum.NormalId.Top
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = PAINT.PixelsPerStud
	-- Lit like the sand around it (not glowing), drawn in the world (sticks and the landing ring cover it).
	gui.LightInfluence = 1
	gui.AlwaysOnTop = false
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = plate

	local root = Instance.new("Frame")
	root.Name = "Canvas"
	root.Size = UDim2.fromScale(1, 1)
	root.BackgroundTransparency = 1
	root.Rotation = PAINT.CanvasRotation
	root.Parent = gui
	local canvas: Canvas = { Frame = root, Size = size, PixelsPerStud = PAINT.PixelsPerStud, Z = 0 }

	-- Sand patches first (under everything), then the target, the emblem and the lettering on top.
	local patches = PAINT.Patches
	local random = Random.new(slot * 7919 + 17)
	for index = 1, patches.Count do
		local x, y = spotInDisc(random, patches.PatchRadius)
		local width = between(random, patches.Size)
		fill(canvas, {
			X = x,
			Y = y,
			Width = width,
			Height = width * between(random, patches.Aspect),
			Rotation = random:NextNumber(0, 180),
		}, patches.Colors[(index - 1) % #patches.Colors + 1], patches.Transparency)
	end
	for index = 1, patches.Pebbles do
		local x, y = spotInDisc(random, patches.PebbleRadius)
		local pebble = between(random, patches.PebbleSize)
		fill(canvas, {
			X = x,
			Y = y,
			Width = pebble,
			Height = pebble * random:NextNumber(0.7, 1),
			Rotation = random:NextNumber(0, 180),
		}, patches.PebbleColors[(index - 1) % #patches.PebbleColors + 1], patches.PebbleTransparency)
	end

	for _, band in PAINT.Rings do
		ring(canvas, band.Radius, band.Width, band.Color, band.Transparency)
	end
	local bullseye = PAINT.Bullseye
	fill(canvas, {
		X = 0,
		Y = 0,
		Width = bullseye.Radius * 2,
		Height = bullseye.Radius * 2,
		Rotation = 0,
	}, bullseye.Color, bullseye.Transparency)
	for _, pad in PAINT.Paw do
		fill(canvas, pad, PAINT.PawColor, PAINT.PawTransparency)
	end
	for _, text in PAINT.Lettering do
		lettering(canvas, text, text.Text)
	end

	-- Faint glitter rising from the sand (the emitter's cylinder fills the plate's footprint).
	local sparkles = Config.Sparkles
	local emitter = Instance.new("ParticleEmitter")
	emitter.Name = "SandGlitter"
	emitter.Shape = Enum.ParticleEmitterShape.Cylinder
	emitter.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	emitter.EmissionDirection = Enum.NormalId.Top
	emitter.Rate = sparkles.Rate
	emitter.Lifetime = NumberRange.new(sparkles.Lifetime[1], sparkles.Lifetime[2])
	emitter.Speed = NumberRange.new(sparkles.Speed[1], sparkles.Speed[2])
	emitter.SpreadAngle = Vector2.new(20, 20)
	emitter.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.3, sparkles.Size),
		NumberSequenceKeypoint.new(1, 0),
	})
	emitter.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.6),
		NumberSequenceKeypoint.new(0.4, 0.2),
		NumberSequenceKeypoint.new(1, 1),
	})
	emitter.Color = ColorSequence.new(sparkles.Color)
	emitter.LightEmission = sparkles.LightEmission
	emitter.Texture = sparkles.Texture
	emitter.Rotation = NumberRange.new(0, 360)
	emitter.RotSpeed = NumberRange.new(-60, 60)
	emitter.Parent = plate
end

-- --- Border ----------------------------------------------------------------------------------------------------

type Post = { Angle: number, Part: Part, Rope: Attachment, Arc: number }

-- Bezier parameter at which a sagging rope (control points straight below both ends) has covered `share` of the
-- way horizontally: share = t² (3 − 2t), solved by bisection.
local function ropeParameter(share: number): number
	local low, high = 0, 1
	for _ = 1, 20 do
		local t = (low + high) / 2
		if t * t * (3 - 2 * t) < share then
			low = t
		else
			high = t
		end
	end
	return (low + high) / 2
end

local function buildBorder(center: Vector3, hubAngle: number, parent: Instance): { Post }
	local posts: { Post } = {}
	local upright = CFrame.Angles(0, 0, math.rad(90))
	local sink = 0.3
	for arcIndex, arc in BORDER.Arcs do
		local from, to = arc[1], arc[2]
		local spans = math.max(1, math.ceil((to - from) / BORDER.MaxSpanDegrees))
		for step = 0, spans do
			local angle = from + (to - from) * step / spans
			local ground = center + direction(hubAngle + math.rad(angle)) * BORDER.Radius
			local height = BORDER.PostHeight + sink
			local post = newPart(
				"BorderPost",
				Enum.PartType.Cylinder,
				Vector3.new(height, BORDER.PostWidth, BORDER.PostWidth),
				CFrame.new(ground + Vector3.new(0, BORDER.PostHeight - height / 2, 0)) * upright,
				BORDER.PostColor,
				Enum.Material.Wood,
				parent
			)
			local number = #posts + 1
			local cap = newPart(
				"BorderCap",
				Enum.PartType.Ball,
				Vector3.one * BORDER.CapSize,
				CFrame.new(ground + Vector3.new(0, BORDER.PostHeight + BORDER.CapSize * 0.25, 0)),
				BORDER.CapColors[(number - 1) % #BORDER.CapColors + 1],
				Enum.Material.SmoothPlastic,
				parent
			)
			if number % BORDER.LightEvery == 0 then
				local light = Instance.new("PointLight")
				light.Range = BORDER.LightRange
				light.Brightness = BORDER.LightBrightness
				light.Color = BORDER.LightColor
				light.Shadows = false
				light.Parent = cap
			end
			-- The rope's attachment: its X axis points down, so both beam control points hang below the posts.
			local rope = Instance.new("Attachment")
			rope.Name = "Rope"
			rope.Parent = post
			rope.WorldCFrame = CFrame.new(ground + Vector3.new(0, BORDER.RopeHeight, 0))
				* CFrame.Angles(0, 0, -math.pi / 2)
			table.insert(posts, { Angle = angle, Part = post, Rope = rope, Arc = arcIndex })
		end
	end

	-- Mid-span sag of a cubic Bezier with both control points `curve` below the ends is 0.75 × curve.
	local curve = BORDER.RopeSag / 0.75
	local flagNumber = 0
	for index = 1, #posts - 1 do
		local a, b = posts[index], posts[index + 1]
		if a.Arc ~= b.Arc then
			continue
		end
		local beam = Instance.new("Beam")
		beam.Name = "Rope"
		beam.Attachment0 = a.Rope
		beam.Attachment1 = b.Rope
		beam.CurveSize0 = curve
		beam.CurveSize1 = -curve
		beam.Width0 = BORDER.RopeWidth
		beam.Width1 = BORDER.RopeWidth
		beam.Segments = 12
		beam.FaceCamera = true
		beam.LightInfluence = 1
		beam.Color = ColorSequence.new(BORDER.RopeColor)
		beam.Transparency = NumberSequence.new(0)
		beam.Parent = a.Part

		-- Pennants hanging from the rope: right-angled wedges turned upside down, the long edge along the rope.
		local from, to = a.Rope.WorldPosition, b.Rope.WorldPosition
		local along = Vector3.new(to.X - from.X, 0, to.Z - from.Z).Unit
		local outward = along:Cross(Vector3.yAxis)
		for spotIndex, share in BORDER.FlagSpots do
			local t = ropeParameter(share)
			local position = from:Lerp(to, share) - Vector3.new(0, 3 * t * (1 - t) * curve, 0)
			flagNumber += 1
			local flagSize = BORDER.FlagSize
			local flag = Instance.new("WedgePart")
			flag.Name = "Pennant"
			flag.Size = Vector3.new(0.06, flagSize.Y, flagSize.X)
			local sideways = if spotIndex % 2 == 0 then along else -along
			flag.CFrame = CFrame.fromMatrix(
				position - Vector3.new(0, flagSize.Y / 2 + 0.02, 0),
				outward,
				Vector3.yAxis,
				sideways
			) * CFrame.Angles(0, 0, math.pi)
			flag.Color = BORDER.FlagColors[(flagNumber - 1) % #BORDER.FlagColors + 1]
			flag.Material = Enum.Material.Fabric
			flag.CastShadow = false
			visualOnly(flag)
			flag.Parent = parent
		end
	end
	return posts
end

-- Mini signs on border posts, facing the field centre.
local function buildSigns(center: Vector3, posts: { Post }, parent: Instance)
	local signs = Config.Signs
	for _, sign in signs.Posts do
		local post = posts[sign.Post]
		if not post then
			continue
		end
		local base = post.Part.Position
		local inward = Vector3.new(center.X - base.X, 0, center.Z - base.Z).Unit
		local position = Vector3.new(base.X, center.Y + signs.BoardHeight, base.Z)
			+ inward * (BORDER.PostWidth / 2 + signs.BoardSize.Z / 2)
		local board = newPart(
			"BonkSign",
			Enum.PartType.Block,
			signs.BoardSize,
			CFrame.lookAt(position, position + inward),
			signs.BoardColor,
			Enum.Material.WoodPlanks,
			parent
		)
		Signs.Text(board, Enum.NormalId.Front, sign.Text, signs.TextColor, 60)
	end
end

-- --- Edge props --------------------------------------------------------------------------------------------------

local function buildProps(center: Vector3, hubAngle: number, parent: Instance)
	for _, prop in Config.EdgeProps do
		local builder = BUILDERS[prop.Name]
		if not builder then
			warn(`[FieldDecor] No placeholder builder for {prop.Name}`)
			continue
		end
		local position = center + direction(hubAngle + math.rad(prop.Angle)) * prop.Radius
		local facing = CFrame.lookAt(position, Vector3.new(center.X, position.Y, center.Z))
			* CFrame.Angles(0, math.rad(prop.Yaw), 0)
		local model = PropService.Place(prop.Name, facing, prop.Height, builder, parent)
		for _, descendant in model:GetDescendants() do
			if descendant:IsA("BasePart") then
				visualOnly(descendant)
			end
		end
	end
end

-- Builds the whole decoration of one plot's field into a "FieldDecor" model under `parent`.
function FieldDecor.Build(center: Vector3, hubAngle: number, slot: number, parent: Instance)
	local model = Instance.new("Model")
	model.Name = "FieldDecor"
	buildPaint(center, hubAngle, slot, model)
	local posts = buildBorder(center, hubAngle, model)
	buildSigns(center, posts, model)
	buildProps(center, hubAngle, model)
	model.Parent = parent
end

return FieldDecor
