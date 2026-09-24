--!strict
-- Clean text on signs and boards: a SurfaceGui with padding, an outlined font and a capped text size, so titles
-- look sharp from near and far. Mirror() puts the same text on the back face.

local Signs = {}

local mirrors: { [TextLabel]: TextLabel } = {}

-- Writes `text` on `face` of `part`. `maxTextSize` caps the scaled text (default 100).
function Signs.Text(
	part: BasePart,
	face: Enum.NormalId,
	text: string,
	color: Color3,
	maxTextSize: number?,
	font: Enum.Font?
): TextLabel
	local gui = Instance.new("SurfaceGui")
	gui.Face = face
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 50
	gui.LightInfluence = 0
	gui.Parent = part

	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Font = font or Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextWrapped = true
	label.TextColor3 = color
	label.Text = text
	label.Parent = gui

	local padding = Instance.new("UIPadding")
	padding.PaddingLeft = UDim.new(0.05, 0)
	padding.PaddingRight = UDim.new(0.05, 0)
	padding.PaddingTop = UDim.new(0.12, 0)
	padding.PaddingBottom = UDim.new(0.12, 0)
	padding.Parent = label

	local size = Instance.new("UITextSizeConstraint")
	size.MaxTextSize = maxTextSize or 100
	size.Parent = label

	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 3
	stroke.Color = Color3.fromRGB(15, 12, 25)
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	stroke.Parent = label
	return label
end

-- Copies the label onto the part's back face; SetText keeps both in sync.
function Signs.Mirror(part: BasePart, label: TextLabel)
	local back = Signs.Text(part, Enum.NormalId.Back, label.Text, label.TextColor3)
	mirrors[label] = back
end

function Signs.SetText(label: TextLabel, text: string)
	label.Text = text
	local back = mirrors[label]
	if back then
		back.Text = text
	end
end

-- A floating text above something (names, subtitles), outlined and size-capped.
function Signs.Billboard(
	adornee: BasePart,
	text: string,
	color: Color3,
	size: Vector2,
	offsetY: number,
	maxDistance: number?
): TextLabel
	local billboard = Instance.new("BillboardGui")
	billboard.Size = UDim2.fromOffset(size.X, size.Y)
	billboard.StudsOffset = Vector3.new(0, offsetY, 0)
	billboard.MaxDistance = maxDistance or 150
	billboard.LightInfluence = 0
	billboard.Parent = adornee
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = color
	label.Text = text
	label.Parent = billboard
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 2.5
	stroke.Color = Color3.fromRGB(15, 12, 25)
	stroke.Parent = label
	return label
end

return Signs
