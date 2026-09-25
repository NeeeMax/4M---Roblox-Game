--!strict
-- Small building blocks for code-built UI: screen guis, panels with a title and close button, buttons, labels,
-- icons, price pills, sliders and checkboxes. Panels register here so only one menu is open at a time
-- (Widgets.Open / Widgets.CloseAll).
-- Look (docs/GAME_DESIGN.md → UI): black panel inside a thick studded border, big white outlined title, red square
-- close button over the top-right corner, chunky bright buttons, yellow price pills.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextService = game:GetService("TextService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Icons = require(ReplicatedStorage.Shared.Config.Icons)
local Format = require(ReplicatedStorage.Shared.Util.Format)

local Theme = require(script.Parent.Theme)

export type Panel = {
	Name: string,
	Frame: Frame,
	-- Put the panel's content in here.
	Content: Frame,
	OnOpen: (() -> ())?,
}

export type Slider = {
	Frame: Frame,
	-- Moves the knob without calling onChanged.
	Set: (value: number) -> (),
	IsDragging: () -> boolean,
}

export type Checkbox = {
	Frame: Frame,
	-- Sets the tick without calling onChanged.
	Set: (checked: boolean) -> (),
}

-- How Bonk Dollars text is drawn (Widgets.MoneySymbol / MoneyText).
export type MoneyStyle = {
	-- Thickness of a thick outline (like Widgets.Outline); without it the plain text stroke below is used.
	Outline: number?,
	-- TextStrokeTransparency without Outline (default like Widgets.Label: 0.45 from size 18 up, else none).
	StrokeTransparency: number?,
	Font: Enum.Font?,
	-- Where the lines line up (default centred).
	Align: Enum.TextXAlignment?,
}

export type MoneyText = {
	-- Sizes itself to the text (AutomaticSize); place it with AnchorPoint and Position.
	Frame: Frame,
	-- New text; every Format.CurrencySymbol ("B$") in it is drawn as the symbol. "\n" starts a new line.
	Set: (text: string) -> (),
	SetColor: (color: Color3) -> (),
}

-- Panel border: thickness and gap between studs (pixels).
local BORDER = 18
local STUD_GAP = 30

local panels: { [string]: Panel } = {}
local openName: string? = nil

local Widgets = {}

local function darker(color: Color3, factor: number): Color3
	local h, s, v = color:ToHSV()
	return Color3.fromHSV(h, s, v * factor)
end

local function lighter(color: Color3, amount: number): Color3
	return color:Lerp(Color3.new(1, 1, 1), amount)
end

function Widgets.Corner(instance: GuiObject, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = instance
end

function Widgets.Stroke(instance: GuiObject, thickness: number, color: Color3?)
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = thickness
	stroke.Color = color or Theme.Stroke
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	stroke.Parent = instance
end

-- A thick dark outline around a label's text (titles, the money counter). Use on labels without a border stroke.
function Widgets.Outline(label: TextLabel | TextButton, thickness: number?)
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = thickness or 3
	stroke.Color = Theme.Stroke
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	stroke.LineJoinMode = Enum.LineJoinMode.Round
	stroke.Parent = label
end

-- Vertical gradient from `color` to a darker shade.
function Widgets.Gradient(instance: GuiObject, color: Color3)
	local gradient = Instance.new("UIGradient")
	gradient.Color = ColorSequence.new(color, darker(color, 0.72))
	gradient.Rotation = 90
	gradient.Parent = instance
end

function Widgets.Label(parent: Instance, text: string, size: number, color: Color3?): TextLabel
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Font = Theme.Font
	label.Text = text
	label.TextSize = size
	label.TextColor3 = color or Theme.Text
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.TextYAlignment = Enum.TextYAlignment.Center
	-- Bigger text gets a dark edge so it reads on any background.
	label.TextStrokeColor3 = Theme.Stroke
	label.TextStrokeTransparency = if size >= 18 then 0.45 else 1
	label.Parent = parent
	return label
end

-- A big chunky title: white, thick outline, centred.
function Widgets.Title(parent: Instance, text: string, size: number, tint: Color3?): TextLabel
	local label = Widgets.Label(parent, text, size)
	label.Font = Theme.TitleFont
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextStrokeTransparency = 1
	Widgets.Outline(label, math.clamp(size / 12, 2, 4))
	if tint then
		-- White on top, a light shade of the tint at the bottom (tints the text).
		local gradient = Instance.new("UIGradient")
		gradient.Color = ColorSequence.new(Color3.new(1, 1, 1), lighter(tint, 0.35))
		gradient.Rotation = 90
		gradient.Parent = label
	end
	return label
end

-- Makes a button shrink a little while pressed.
local function addPress(button: GuiButton)
	local scale = Instance.new("UIScale")
	scale.Parent = button
	button.MouseButton1Down:Connect(function()
		TweenService:Create(scale, TweenInfo.new(0.06), { Scale = 0.92 }):Play()
	end)
	button.MouseButton1Up:Connect(function()
		TweenService:Create(scale, TweenInfo.new(0.12, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	end)
	button.MouseLeave:Connect(function()
		scale.Scale = 1
	end)
end

-- A chunky button with a gradient and outline that pops a little when pressed.
function Widgets.Button(parent: Instance, text: string, color: Color3, textSize: number?): TextButton
	local button = Instance.new("TextButton")
	button.BackgroundColor3 = color
	button.AutoButtonColor = false
	button.Font = Theme.Font
	button.Text = text
	button.TextSize = textSize or 20
	button.TextColor3 = Theme.Text
	button.TextStrokeColor3 = Theme.Stroke
	button.TextStrokeTransparency = 0.25
	button.Parent = parent
	Widgets.Corner(button, 12)
	Widgets.Stroke(button, 3)
	-- A UIGradient tints the button's text too, so shade from white to grey and keep the colour in the background.
	local shade = Instance.new("UIGradient")
	shade.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)),
		ColorSequenceKeypoint.new(0.55, Color3.fromRGB(235, 235, 235)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(175, 175, 175)),
	})
	shade.Rotation = 90
	shade.Parent = button
	addPress(button)
	return button
end

-- Recolours a Widgets.Button (e.g. green when affordable, grey when not).
function Widgets.SetButtonColor(button: TextButton, color: Color3)
	button.BackgroundColor3 = color
end

-- An icon from Config/Icons: the uploaded image, or its glyph while no image id is set.
function Widgets.Icon(parent: Instance, name: Icons.IconName, size: number): GuiObject
	local id = Icons.Ids[name]
	if id ~= "" then
		local image = Instance.new("ImageLabel")
		image.Name = `{name}Icon`
		image.BackgroundTransparency = 1
		image.Image = id
		image.ScaleType = Enum.ScaleType.Fit
		image.Size = UDim2.fromOffset(size, size)
		image.Parent = parent
		return image
	end
	if name == "Menu" then
		-- The ☰ glyph is missing from the game fonts (it showed an empty button): draw three bars instead.
		local bars = Instance.new("Frame")
		bars.Name = "MenuIcon"
		bars.BackgroundTransparency = 1
		bars.Size = UDim2.fromOffset(size, size)
		bars.Parent = parent
		for index = 0, 2 do
			local bar = Instance.new("Frame")
			bar.AnchorPoint = Vector2.new(0.5, 0.5)
			bar.Position = UDim2.fromScale(0.5, 0.25 + index * 0.25)
			bar.Size = UDim2.fromScale(0.72, 0.13)
			bar.BackgroundColor3 = Theme.Text
			bar.BorderSizePixel = 0
			bar.Parent = bars
			Widgets.Corner(bar, 4)
			Widgets.Stroke(bar, 2, Theme.Stroke)
		end
		return bars
	end
	local glyph = Instance.new("TextLabel")
	glyph.Name = `{name}Icon`
	glyph.BackgroundTransparency = 1
	glyph.Font = Theme.Font
	glyph.Text = Icons.Glyphs[name]
	glyph.TextScaled = true
	glyph.TextColor3 = Theme.Text
	glyph.TextStrokeColor3 = Theme.Stroke
	glyph.TextStrokeTransparency = 0.4
	glyph.Size = UDim2.fromOffset(size, size)
	glyph.Parent = parent
	return glyph
end

-- A square button showing an icon (HUD menu / manage buttons).
function Widgets.IconButton(parent: Instance, icon: Icons.IconName, color: Color3, size: number): TextButton
	local button = Widgets.Button(parent, "", color)
	button.Size = UDim2.fromOffset(size, size)
	local image = Widgets.Icon(button, icon, math.floor(size * 0.72))
	image.AnchorPoint = Vector2.new(0.5, 0.5)
	image.Position = UDim2.fromScale(0.5, 0.5)
	return button
end

-- A red "!" dot for the top-right corner of a button. Hidden until you show it.
function Widgets.Badge(parent: GuiObject): TextLabel
	local dot = Widgets.Label(parent, "!", 20)
	dot.Name = "Badge"
	dot.AnchorPoint = Vector2.new(0.5, 0.5)
	dot.Position = UDim2.new(1, -4, 0, 4)
	dot.Size = UDim2.fromOffset(26, 26)
	dot.BackgroundTransparency = 0
	dot.BackgroundColor3 = Theme.Bad
	dot.TextXAlignment = Enum.TextXAlignment.Center
	dot.TextStrokeTransparency = 0.3
	dot.ZIndex = 5
	dot.Visible = false
	Widgets.Corner(dot, 13)
	Widgets.Stroke(dot, 2, Color3.new(1, 1, 1))
	return dot
end

-- Bonk Dollars symbol (docs/GAME_DESIGN.md → Economy): a bold "B" with a vertical bar through it, like "฿". The game
-- fonts have no such glyph, so it is built from a TextLabel and two bar Frames, all sized from the text size:
-- a bar with the outline behind the letter (its outline shows only where the bar sticks out above and below),
-- the letter, and the same bar without outline on top (hides the letter's outline inside the bowls).
local SYMBOL_TEXT = Format.CurrencySymbol
-- Relative to the text size. A capital is ~0.7 of the text size tall, so the bar sticks out ~0.14 above and below.
local SYMBOL_BAR_WIDTH = 0.11
local SYMBOL_BAR_LENGTH = 0.98
-- Where the bar crosses the letter (0 = left edge, 1 = right edge of the "B").
local SYMBOL_BAR_X = 0.47
-- Height of a line of money text relative to its text size.
local MONEY_LINE_HEIGHT = 1.2
-- SetMoneyText on a TextScaled label draws at this size and scales it to fit (UIScale).
local MONEY_SCALED_SIZE = 40

local function moneyLineHeight(size: number): number
	return math.ceil(size * MONEY_LINE_HEIGHT)
end

local function baseZIndex(parent: Instance): number
	return if parent:IsA("GuiObject") then parent.ZIndex else 1
end

-- The symbol for text of `size` in `color`; about as wide as a "B". Put it in a horizontal UIListLayout next to
-- the amount, or use Widgets.MoneyText / SetMoneyText which do that for you.
function Widgets.MoneySymbol(parent: Instance, size: number, color: Color3, style: MoneyStyle?): Frame
	local options: MoneyStyle = style or {}
	local font = options.Font or Theme.Font
	local base = baseZIndex(parent)
	local width = TextService:GetTextSize("B", size, font, Vector2.new(10000, 10000)).X

	local holder = Instance.new("Frame")
	holder.Name = "MoneySymbol"
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.fromOffset(math.ceil(width), moneyLineHeight(size))
	holder.ZIndex = base
	holder.Parent = parent

	local function bar(name: string, zIndex: number): Frame
		local frame = Instance.new("Frame")
		frame.Name = name
		frame.AnchorPoint = Vector2.new(0.5, 0.5)
		frame.Position = UDim2.fromScale(SYMBOL_BAR_X, 0.5)
		frame.Size =
			UDim2.fromOffset(math.max(2, math.round(size * SYMBOL_BAR_WIDTH)), math.round(size * SYMBOL_BAR_LENGTH))
		frame.BackgroundColor3 = color
		frame.BorderSizePixel = 0
		frame.ZIndex = zIndex
		frame.Parent = holder
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0.5, 0)
		corner.Parent = frame
		return frame
	end
	local under = bar("BarUnder", base)

	local letter = Instance.new("TextLabel")
	letter.Name = "Letter"
	letter.BackgroundTransparency = 1
	letter.Size = UDim2.fromScale(1, 1)
	letter.Font = font
	letter.Text = "B"
	letter.TextSize = size
	letter.TextColor3 = color
	letter.TextStrokeColor3 = Theme.Stroke
	letter.ZIndex = base + 1
	letter.Parent = holder

	bar("BarOver", base + 2)

	local outline = options.Outline
	if outline then
		letter.TextStrokeTransparency = 1
		Widgets.Outline(letter, outline)
		local stroke = Instance.new("UIStroke")
		stroke.Thickness = outline
		stroke.Color = Theme.Stroke
		stroke.LineJoinMode = Enum.LineJoinMode.Round
		stroke.Parent = under
	else
		local transparency = options.StrokeTransparency or (if size >= 18 then 0.45 else 1)
		letter.TextStrokeTransparency = transparency
		if transparency < 1 then
			local stroke = Instance.new("UIStroke")
			stroke.Thickness = 1
			stroke.Color = Theme.Stroke
			stroke.Transparency = transparency
			stroke.Parent = under
		end
	end
	return holder
end

type MoneyPiece = { Text: string? }

-- "+B$ 1,234 today" → "+", symbol, "1,234 today". Spaces next to a symbol are dropped (the layout adds the gap).
local function moneyPieces(line: string): { MoneyPiece }
	local pieces: { MoneyPiece } = {}
	local start = 1
	while true do
		local first, last = string.find(line, SYMBOL_TEXT, start, true)
		local chunk = string.sub(line, start, if first then first - 1 else #line)
		if start > 1 then
			chunk = string.gsub(chunk, "^ +", "")
		end
		if first then
			chunk = string.gsub(chunk, " +$", "")
		end
		if chunk ~= "" then
			table.insert(pieces, { Text = chunk })
		end
		if not first or not last then
			break
		end
		table.insert(pieces, { Text = nil })
		start = last + 1
	end
	return pieces
end

-- Text with Bonk Dollars amounts: every "B$" in `text` is drawn as the symbol, e.g. Format.Money(1234) →
-- [symbol] 1,234. Lines don't wrap; use "\n" for a second line.
function Widgets.MoneyText(parent: Instance, text: string, size: number, color: Color3, style: MoneyStyle?): MoneyText
	local options: MoneyStyle = style or {}
	local align = options.Align or Enum.TextXAlignment.Center
	local base = baseZIndex(parent)

	local frame = Instance.new("Frame")
	frame.Name = "MoneyText"
	frame.BackgroundTransparency = 1
	frame.AutomaticSize = Enum.AutomaticSize.XY
	frame.Size = UDim2.new()
	frame.ZIndex = base
	frame.Parent = parent
	local lines = Instance.new("UIListLayout")
	lines.SortOrder = Enum.SortOrder.LayoutOrder
	lines.HorizontalAlignment = if align == Enum.TextXAlignment.Left
		then Enum.HorizontalAlignment.Left
		elseif align == Enum.TextXAlignment.Right then Enum.HorizontalAlignment.Right
		else Enum.HorizontalAlignment.Center
	lines.Parent = frame

	local currentText = ""
	local currentColor = color
	local function build()
		for _, child in frame:GetChildren() do
			if child:IsA("GuiObject") then
				child:Destroy()
			end
		end
		local lineOrder = 0
		for line in string.gmatch(currentText .. "\n", "([^\n]*)\n") do
			lineOrder += 1
			local row = Instance.new("Frame")
			row.Name = "Line"
			row.BackgroundTransparency = 1
			row.AutomaticSize = Enum.AutomaticSize.X
			row.Size = UDim2.fromOffset(0, moneyLineHeight(size))
			row.LayoutOrder = lineOrder
			row.ZIndex = base
			row.Parent = frame
			local layout = Instance.new("UIListLayout")
			layout.FillDirection = Enum.FillDirection.Horizontal
			layout.VerticalAlignment = Enum.VerticalAlignment.Center
			layout.SortOrder = Enum.SortOrder.LayoutOrder
			layout.Padding = UDim.new(0, math.max(1, math.round(size * 0.12)))
			layout.Parent = row
			for index, piece in moneyPieces(line) do
				local item: GuiObject
				local pieceText = piece.Text
				if pieceText then
					local label = Widgets.Label(row, pieceText, size, currentColor)
					label.Font = options.Font or Theme.Font
					label.AutomaticSize = Enum.AutomaticSize.X
					label.Size = UDim2.fromOffset(0, moneyLineHeight(size))
					label.ZIndex = base
					if options.Outline then
						label.TextStrokeTransparency = 1
						Widgets.Outline(label, options.Outline)
					elseif options.StrokeTransparency then
						label.TextStrokeTransparency = options.StrokeTransparency
					end
					item = label
				else
					item = Widgets.MoneySymbol(row, size, currentColor, options)
				end
				item.LayoutOrder = index
			end
		end
	end

	local money: MoneyText = {
		Frame = frame,
		Set = function(newText: string)
			if newText ~= currentText then
				currentText = newText
				build()
			end
		end,
		SetColor = function(newColor: Color3)
			if newColor ~= currentColor then
				currentColor = newColor
				build()
			end
		end,
	}
	money.Set(text)
	return money
end

-- "[symbol] 1,234" for an amount of Bonk Dollars.
function Widgets.Money(parent: Instance, amount: number, size: number, color: Color3, style: MoneyStyle?): MoneyText
	return Widgets.MoneyText(parent, Format.Money(amount), size, color, style)
end

type MoneyEntry = { Money: MoneyText, Scale: UIScale? }
-- Label → its money overlay (weak keys: destroyed labels drop out).
-- `:: any`: the weak-keys metatable doesn't change the table's type, it only lets the analyzer accept the cast.
local moneyEntries: { [GuiObject]: MoneyEntry } = setmetatable({} :: any, { __mode = "k" })

-- The analyzer can't write a property on a TextLabel | TextButton union; narrow it first.
local function setText(object: TextLabel | TextButton, text: string)
	if object:IsA("TextButton") then
		object.Text = text
	else
		local label = object :: TextLabel
		label.Text = text
	end
end

-- Sets a label's or button's text; when it contains "B$" (Format.Money …) the text is drawn by a MoneyText inside
-- the label instead, in the label's font, colour, stroke and alignment. TextScaled labels are fitted into their box.
-- Set the label's TextColor3 before calling this. `size` overrides the label's TextSize.
function Widgets.SetMoneyText(label: TextLabel | TextButton, text: string, size: number?)
	local entry = moneyEntries[label]
	if not string.find(text, SYMBOL_TEXT, 1, true) then
		if entry then
			entry.Money.Frame.Visible = false
		end
		setText(label, text)
		return
	end
	setText(label, "")
	if entry then
		entry.Money.SetColor(label.TextColor3)
		entry.Money.Set(text)
		entry.Money.Frame.Visible = true
		return
	end

	local scaled = label.TextScaled
	local style: MoneyStyle = {
		Font = label.Font,
		Align = label.TextXAlignment,
		StrokeTransparency = label.TextStrokeTransparency,
	}
	local stroke = label:FindFirstChildOfClass("UIStroke")
	if stroke and stroke.ApplyStrokeMode == Enum.ApplyStrokeMode.Contextual then
		style.Outline = stroke.Thickness
	end
	local textSize = size or (if scaled then MONEY_SCALED_SIZE else label.TextSize)
	local money = Widgets.MoneyText(label, text, textSize, label.TextColor3, style)
	local frame = money.Frame
	local x = if label.TextXAlignment == Enum.TextXAlignment.Left
		then 0
		elseif label.TextXAlignment == Enum.TextXAlignment.Right then 1
		else 0.5
	frame.AnchorPoint = Vector2.new(x, 0.5)
	frame.Position = UDim2.fromScale(x, 0.5)
	local newEntry: MoneyEntry = { Money = money }
	moneyEntries[label] = newEntry

	if scaled then
		local scale = Instance.new("UIScale")
		scale.Parent = frame
		newEntry.Scale = scale
		local limit = label:FindFirstChildOfClass("UITextSizeConstraint")
		local function fit()
			local current = scale.Scale
			-- AbsoluteSize includes this UIScale; divide it out to get the unscaled size.
			local own = frame.AbsoluteSize / current
			local box = label.AbsoluteSize
			if own.X <= 0 or own.Y <= 0 or box.X <= 0 or box.Y <= 0 then
				return
			end
			local fitted = math.min(box.X * 0.95 / own.X, box.Y / own.Y)
			if limit then
				fitted = math.min(fitted, limit.MaxTextSize / textSize)
			end
			fitted = math.max(fitted, 0.01)
			if math.abs(fitted - current) > 0.001 then
				scale.Scale = fitted
			end
		end
		label:GetPropertyChangedSignal("AbsoluteSize"):Connect(fit)
		frame:GetPropertyChangedSignal("AbsoluteSize"):Connect(fit)
		task.defer(fit)
	end
end

-- Fades a GUI and everything in it (texts, backgrounds, strokes) out over `seconds`.
function Widgets.FadeOut(root: GuiObject, seconds: number)
	local info = TweenInfo.new(seconds)
	local function fade(object: Instance)
		if object:IsA("TextLabel") or object:IsA("TextButton") then
			TweenService
				:Create(object, info, { TextTransparency = 1, TextStrokeTransparency = 1, BackgroundTransparency = 1 })
				:Play()
		elseif object:IsA("Frame") then
			TweenService:Create(object, info, { BackgroundTransparency = 1 }):Play()
		elseif object:IsA("UIStroke") then
			TweenService:Create(object, info, { Transparency = 1 }):Play()
		end
	end
	fade(root)
	for _, descendant in root:GetDescendants() do
		fade(descendant)
	end
end

-- A yellow price pill: coin icon (Robux) or the Bonk Dollars symbol and the price. Place and size it yourself
-- (default 130 × 44). Returns the pill and its text label.
function Widgets.PricePill(parent: Instance, text: string, isRobux: boolean): (Frame, TextLabel)
	local pill = Instance.new("Frame")
	pill.Name = "PricePill"
	pill.BackgroundColor3 = Theme.Price
	pill.Size = UDim2.fromOffset(130, 44)
	pill.Parent = parent
	Widgets.Corner(pill, 14)
	Widgets.Stroke(pill, 3)
	local shade = Instance.new("UIGradient")
	shade.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(225, 225, 225))
	shade.Rotation = 90
	shade.Parent = pill
	if isRobux then
		local icon = Widgets.Icon(pill, "Coin", 30)
		icon.AnchorPoint = Vector2.new(0, 0.5)
		icon.Position = UDim2.new(0, 8, 0.5, 0)
		icon.Size = UDim2.new(0, 30, 1, -12)
	else
		local symbol = Widgets.MoneySymbol(pill, 28, Theme.DarkText, { StrokeTransparency = 1 })
		symbol.AnchorPoint = Vector2.new(0.5, 0.5)
		symbol.Position = UDim2.new(0, 23, 0.5, 0)
	end
	local label = Widgets.Label(pill, text, 26, Theme.DarkText)
	label.Name = "Text"
	label.Position = UDim2.fromOffset(44, 0)
	label.Size = UDim2.new(1, -50, 1, 0)
	label.TextStrokeTransparency = 1
	label.TextScaled = true
	local limit = Instance.new("UITextSizeConstraint")
	limit.MaxTextSize = 28
	limit.Parent = label
	return pill, label
end

-- Rows of small studs along the inside of a frame's border (pixel-sized frames only).
function Widgets.StudBorder(frame: Frame, thickness: number, studColor: Color3)
	local width = frame.Size.X.Offset
	local height = frame.Size.Y.Offset
	local studSize = math.max(6, math.floor(thickness * 0.5))
	local holder = Instance.new("Frame")
	holder.Name = "Studs"
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.fromScale(1, 1)
	holder.Parent = frame
	local edgeColor = lighter(frame.BackgroundColor3, 0.35)
	local function stud(x: number, y: number)
		local dot = Instance.new("Frame")
		dot.AnchorPoint = Vector2.new(0.5, 0.5)
		dot.Position = UDim2.fromOffset(x, y)
		dot.Size = UDim2.fromOffset(studSize, studSize)
		dot.BackgroundColor3 = studColor
		dot.BorderSizePixel = 0
		dot.Parent = holder
		Widgets.Corner(dot, 3)
		Widgets.Stroke(dot, 1, edgeColor)
	end
	local half = thickness / 2
	-- Evenly spaced between the corners, corners included.
	local across = math.max(1, math.floor((width - thickness) / STUD_GAP))
	for index = 0, across do
		local x = half + (width - thickness) * index / across
		stud(x, half)
		stud(x, height - half)
	end
	local down = math.max(1, math.floor((height - thickness) / STUD_GAP))
	for index = 1, down - 1 do
		local y = half + (height - thickness) * index / down
		stud(half, y)
		stud(width - half, y)
	end
end

-- A faint grid of dots over a frame (the HUD money bar), pixel-sized frames only.
function Widgets.DotPattern(frame: Frame, color: Color3, gap: number, transparency: number)
	local holder = Instance.new("Frame")
	holder.Name = "Dots"
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.fromScale(1, 1)
	holder.ClipsDescendants = true
	holder.Parent = frame
	local columns = math.floor(frame.Size.X.Offset / gap)
	local rows = math.max(1, math.floor(frame.Size.Y.Offset / gap))
	for row = 0, rows - 1 do
		for column = 0, columns - 1 do
			local dot = Instance.new("Frame")
			dot.AnchorPoint = Vector2.new(0.5, 0.5)
			dot.Position = UDim2.fromOffset(gap / 2 + column * gap, gap / 2 + row * gap)
			dot.Size = UDim2.fromOffset(math.floor(gap * 0.42), math.floor(gap * 0.42))
			dot.BackgroundColor3 = color
			dot.BackgroundTransparency = transparency
			dot.BorderSizePixel = 0
			dot.Parent = holder
			Widgets.Corner(dot, 3)
		end
	end
end

-- The red square X, centred on the top-right corner of `frame`.
function Widgets.CloseButton(frame: GuiObject, onClose: () -> ()): TextButton
	local close = Widgets.Button(frame, "", Theme.Bad, 40)
	close.Name = "Close"
	close.AnchorPoint = Vector2.new(0.5, 0.5)
	close.Position = UDim2.new(1, -10, 0, 10)
	close.Size = UDim2.fromOffset(60, 60)
	close.ZIndex = 5
	local mark = Widgets.Title(close, "X", 44)
	mark.Font = Theme.TitleFont
	mark.Size = UDim2.fromScale(1, 1)
	mark.Position = UDim2.fromOffset(0, 3)
	mark.ZIndex = 6
	close.Activated:Connect(onClose)
	return close
end

-- A ScreenGui for this player that scales down on small screens.
function Widgets.Screen(name: string, displayOrder: number?): ScreenGui
	local gui = Instance.new("ScreenGui")
	gui.Name = name
	gui.ResetOnSpawn = false
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.DisplayOrder = displayOrder or 0
	local scale = Instance.new("UIScale")
	scale.Parent = gui
	local function update()
		local camera = Workspace.CurrentCamera
		if camera then
			-- Theme.UIScale keeps menus and the HUD compact; big screens don't blow them up.
			scale.Scale = math.clamp(camera.ViewportSize.Y / 820 * Theme.UIScale, Theme.UIScaleMin, Theme.UIScaleMax)
		end
	end
	update()
	local camera = Workspace.CurrentCamera
	if camera then
		camera:GetPropertyChangedSignal("ViewportSize"):Connect(update)
	end
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	return gui
end

-- A centred window: studded border (green unless `border` is given, e.g. Theme.BorderGrey), black inside, big title,
-- red X over the corner. `size` is the old window size: Content keeps the size it always had
-- (size - 28 × 80), the border is added around it. `accent` tints the title. Hidden until Widgets.Open(name).
function Widgets.Panel(name: string, title: string, size: Vector2, accent: Color3, border: Color3?): Panel
	local gui = Widgets.Screen(`{name}Panel`, 10)
	local borderColor = border or Theme.BorderGreen
	local studColor = if borderColor == Theme.BorderGreen
		then Theme.StudGreen
		elseif borderColor == Theme.BorderGrey then Theme.StudGrey
		else darker(borderColor, 0.7)

	local contentSize = Vector2.new(size.X - 28, size.Y - 80)
	local innerSize = contentSize + Vector2.new(24, 70)
	local outerSize = innerSize + Vector2.new(BORDER * 2, BORDER * 2)

	local frame = Instance.new("Frame")
	frame.Name = name
	frame.AnchorPoint = Vector2.new(0.5, 0.5)
	frame.Position = UDim2.fromScale(0.5, 0.5)
	frame.Size = UDim2.fromOffset(outerSize.X, outerSize.Y)
	frame.BackgroundColor3 = borderColor
	frame.Visible = false
	frame.Parent = gui
	Widgets.Corner(frame, 24)
	Widgets.Stroke(frame, 3, darker(borderColor, 0.45))
	Widgets.StudBorder(frame, BORDER, studColor)

	local inner = Instance.new("Frame")
	inner.Name = "Inner"
	inner.Position = UDim2.fromOffset(BORDER, BORDER)
	inner.Size = UDim2.fromOffset(innerSize.X, innerSize.Y)
	inner.BackgroundColor3 = Theme.Panel
	inner.Parent = frame
	Widgets.Corner(inner, 16)
	Widgets.Stroke(inner, 2, darker(borderColor, 0.45))

	local titleLabel = Widgets.Title(inner, title, 42, accent)
	titleLabel.Name = "Title"
	titleLabel.Position = UDim2.fromOffset(40, 6)
	titleLabel.Size = UDim2.new(1, -80, 0, 50)

	Widgets.CloseButton(frame, function()
		Widgets.CloseAll()
	end)

	local content = Instance.new("Frame")
	content.Name = "Content"
	content.BackgroundTransparency = 1
	content.Position = UDim2.fromOffset(12, 58)
	content.Size = UDim2.fromOffset(contentSize.X, contentSize.Y)
	content.Parent = inner

	local panel: Panel = { Name = name, Frame = frame, Content = content }
	panels[name] = panel
	return panel
end

function Widgets.Open(name: string)
	local panel = panels[name]
	if not panel then
		return
	end
	Widgets.CloseAll()
	openName = name
	panel.Frame.Visible = true
	local scale = panel.Frame:FindFirstChildOfClass("UIScale") or Instance.new("UIScale")
	scale.Parent = panel.Frame
	scale.Scale = 0.85
	TweenService:Create(scale, TweenInfo.new(0.18, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	if panel.OnOpen then
		panel.OnOpen()
	end
end

function Widgets.Toggle(name: string)
	if openName == name then
		Widgets.CloseAll()
	else
		Widgets.Open(name)
	end
end

function Widgets.CloseAll()
	for _, panel in panels do
		panel.Frame.Visible = false
	end
	openName = nil
end

function Widgets.IsOpen(name: string): boolean
	return openName == name
end

-- True when a controller registered this panel (e.g. a menu another feature adds later).
function Widgets.HasPanel(name: string): boolean
	return panels[name] ~= nil
end

-- A scrolling list that grows with its content.
function Widgets.List(parent: Instance, padding: number): ScrollingFrame
	local list = Instance.new("ScrollingFrame")
	list.BackgroundTransparency = 1
	list.BorderSizePixel = 0
	list.ScrollBarThickness = 8
	list.ScrollBarImageColor3 = Theme.CardLight
	list.AutomaticCanvasSize = Enum.AutomaticSize.Y
	list.CanvasSize = UDim2.new()
	list.Size = UDim2.fromScale(1, 1)
	list.Parent = parent
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, padding)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = list
	local pad = Instance.new("UIPadding")
	pad.PaddingRight = UDim.new(0, 12)
	pad.PaddingTop = UDim.new(0, 2)
	pad.Parent = list
	return list
end

-- A rounded dark card (Settings sections, list rows).
function Widgets.Card(parent: Instance, height: number): Frame
	local card = Instance.new("Frame")
	card.BackgroundColor3 = Theme.Card
	card.Size = UDim2.new(1, 0, 0, height)
	card.Parent = parent
	Widgets.Corner(card, 14)
	return card
end

-- "Name ——●——" slider for 0..1. onChanged(value, final): final = true when the finger/mouse lets go.
function Widgets.Slider(
	parent: Instance,
	text: string,
	color: Color3,
	initial: number,
	onChanged: (value: number, final: boolean) -> ()
): Slider
	local row = Instance.new("Frame")
	row.Name = text
	row.BackgroundTransparency = 1
	row.Size = UDim2.new(1, 0, 0, 50)
	row.Parent = parent

	local label = Widgets.Label(row, text, 28)
	label.Size = UDim2.fromScale(0.34, 1)
	label.TextXAlignment = Enum.TextXAlignment.Right

	local track = Instance.new("TextButton")
	track.Name = "Track"
	track.Text = ""
	track.AutoButtonColor = false
	track.AnchorPoint = Vector2.new(0, 0.5)
	track.Position = UDim2.new(0.34, 30, 0.5, 0)
	track.Size = UDim2.new(0.66, -56, 0, 10)
	track.BackgroundColor3 = Theme.CardLight
	track.Parent = row
	Widgets.Corner(track, 5)
	-- Taller invisible hit area, easier to grab on touch screens.
	local hit = Instance.new("Frame")
	hit.BackgroundTransparency = 1
	hit.AnchorPoint = Vector2.new(0, 0.5)
	hit.Position = UDim2.fromScale(0, 0.5)
	hit.Size = UDim2.new(1, 0, 0, 44)
	hit.Parent = track

	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.BackgroundColor3 = darker(color, 0.8)
	fill.BorderSizePixel = 0
	fill.Size = UDim2.fromScale(0, 1)
	fill.Parent = track
	Widgets.Corner(fill, 5)

	local knob = Instance.new("Frame")
	knob.Name = "Knob"
	knob.AnchorPoint = Vector2.new(0.5, 0.5)
	knob.Size = UDim2.fromOffset(36, 36)
	knob.BackgroundColor3 = color
	knob.ZIndex = 2
	knob.Parent = track
	Widgets.Corner(knob, 18)
	Widgets.Stroke(knob, 2, darker(color, 0.55))

	local value = math.clamp(initial, 0, 1)
	local dragging = false
	local function show(newValue: number)
		value = math.clamp(newValue, 0, 1)
		fill.Size = UDim2.fromScale(value, 1)
		knob.Position = UDim2.fromScale(value, 0.5)
	end
	local function fromScreenX(x: number): number
		local width = track.AbsoluteSize.X
		if width <= 0 then
			return value
		end
		return (x - track.AbsolutePosition.X) / width
	end
	show(value)

	track.InputBegan:Connect(function(input: InputObject)
		if
			input.UserInputType == Enum.UserInputType.MouseButton1
			or input.UserInputType == Enum.UserInputType.Touch
		then
			dragging = true
			show(fromScreenX(input.Position.X))
			onChanged(value, false)
		end
	end)
	UserInputService.InputChanged:Connect(function(input: InputObject)
		if
			dragging
			and (
				input.UserInputType == Enum.UserInputType.MouseMovement
				or input.UserInputType == Enum.UserInputType.Touch
			)
		then
			show(fromScreenX(input.Position.X))
			onChanged(value, false)
		end
	end)
	UserInputService.InputEnded:Connect(function(input: InputObject)
		if
			dragging
			and (
				input.UserInputType == Enum.UserInputType.MouseButton1
				or input.UserInputType == Enum.UserInputType.Touch
			)
		then
			dragging = false
			onChanged(value, true)
		end
	end)

	return {
		Frame = row,
		Set = show,
		IsDragging = function()
			return dragging
		end,
	}
end

-- "Text [✓]" checkbox row. onChanged(checked) runs when the player clicks it.
function Widgets.Checkbox(
	parent: Instance,
	text: string,
	initial: boolean,
	onChanged: (checked: boolean) -> ()
): Checkbox
	local row = Instance.new("Frame")
	row.Name = text
	row.BackgroundTransparency = 1
	row.Size = UDim2.new(1, 0, 0, 58)
	row.Parent = parent

	local label = Widgets.Label(row, text, 28)
	label.Size = UDim2.new(1, -90, 1, 0)
	label.TextXAlignment = Enum.TextXAlignment.Right

	local box = Instance.new("TextButton")
	box.Name = "Box"
	box.AutoButtonColor = false
	box.AnchorPoint = Vector2.new(1, 0.5)
	box.Position = UDim2.new(1, -24, 0.5, 0)
	box.Size = UDim2.fromOffset(50, 50)
	box.BackgroundColor3 = Theme.Panel
	box.Font = Theme.TitleFont
	box.Text = ""
	box.TextSize = 40
	box.TextColor3 = Theme.Good
	box.Parent = row
	Widgets.Corner(box, 10)
	Widgets.Stroke(box, 3, Theme.Muted)
	addPress(box)

	local checked = initial
	local function show(value: boolean)
		checked = value
		box.Text = if value then "✓" else ""
	end
	show(checked)
	box.Activated:Connect(function()
		show(not checked)
		onChanged(checked)
	end)
	return { Frame = row, Set = show }
end

-- "1h 02m", "4m 10s", "12s"
function Widgets.Duration(seconds: number): string
	local total = math.max(0, math.floor(seconds))
	local hours = total // 3600
	local minutes = (total % 3600) // 60
	local rest = total % 60
	if hours > 0 then
		return string.format("%dh %02dm", hours, minutes)
	elseif minutes > 0 then
		return string.format("%dm %02ds", minutes, rest)
	end
	return `{rest}s`
end

return Widgets
