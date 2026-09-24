--!strict
-- Small building blocks for code-built UI: screen guis, panels with a title and close button, buttons, labels.
-- Panels register here so only one menu is open at a time (Widgets.Open / Widgets.CloseAll).

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Theme = require(script.Parent.Theme)

export type Panel = {
	Name: string,
	Frame: Frame,
	-- Put the panel's content in here.
	Content: Frame,
	OnOpen: (() -> ())?,
}

local panels: { [string]: Panel } = {}
local openName: string? = nil

local Widgets = {}

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

-- Vertical gradient from `color` to a darker shade.
function Widgets.Gradient(instance: GuiObject, color: Color3)
	local h, s, v = color:ToHSV()
	local gradient = Instance.new("UIGradient")
	gradient.Color = ColorSequence.new(color, Color3.fromHSV(h, s, v * 0.72))
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
	label.Parent = parent
	return label
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
	button.TextStrokeTransparency = 0.6
	button.Parent = parent
	Widgets.Corner(button, 10)
	Widgets.Stroke(button, 2)
	-- A UIGradient tints the button's text too, so shade from white to grey and keep the colour in the background.
	local shade = Instance.new("UIGradient")
	shade.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(190, 190, 190))
	shade.Rotation = 90
	shade.Parent = button
	local scale = Instance.new("UIScale")
	scale.Parent = button
	button.MouseButton1Down:Connect(function()
		TweenService:Create(scale, TweenInfo.new(0.06), { Scale = 0.94 }):Play()
	end)
	button.MouseButton1Up:Connect(function()
		TweenService:Create(scale, TweenInfo.new(0.1, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	end)
	button.MouseLeave:Connect(function()
		scale.Scale = 1
	end)
	return button
end

-- Recolours a Widgets.Button (e.g. green when affordable, grey when not).
function Widgets.SetButtonColor(button: TextButton, color: Color3)
	button.BackgroundColor3 = color
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
			scale.Scale = math.clamp(camera.ViewportSize.Y / 820, 0.6, 1.15)
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

-- A centred window with a title bar and a close button. Hidden until Widgets.Open(name).
function Widgets.Panel(name: string, title: string, size: Vector2, accent: Color3): Panel
	local gui = Widgets.Screen(`{name}Panel`, 10)
	local frame = Instance.new("Frame")
	frame.Name = name
	frame.AnchorPoint = Vector2.new(0.5, 0.5)
	frame.Position = UDim2.fromScale(0.5, 0.5)
	frame.Size = UDim2.fromOffset(size.X, size.Y)
	frame.BackgroundColor3 = Theme.Panel
	frame.Visible = false
	frame.Parent = gui
	Widgets.Corner(frame, 16)
	Widgets.Stroke(frame, 3)

	local header = Instance.new("Frame")
	header.Size = UDim2.new(1, 0, 0, 54)
	header.BackgroundColor3 = Color3.new(1, 1, 1)
	header.Parent = frame
	Widgets.Corner(header, 16)
	Widgets.Gradient(header, accent)
	-- Square off the header's bottom corners.
	local filler = Instance.new("Frame")
	filler.Size = UDim2.new(1, 0, 0, 16)
	filler.Position = UDim2.new(0, 0, 1, -16)
	filler.BorderSizePixel = 0
	filler.BackgroundColor3 = Color3.new(1, 1, 1)
	filler.Parent = header
	Widgets.Gradient(filler, accent)

	local titleLabel = Widgets.Label(header, title, 30)
	titleLabel.Position = UDim2.fromOffset(18, 0)
	titleLabel.Size = UDim2.new(1, -80, 1, 0)
	titleLabel.TextStrokeTransparency = 0.3
	titleLabel.ZIndex = 2

	local close = Widgets.Button(header, "X", Theme.Bad, 24)
	close.AnchorPoint = Vector2.new(1, 0.5)
	close.Position = UDim2.new(1, -10, 0.5, 0)
	close.Size = UDim2.fromOffset(38, 38)
	close.ZIndex = 2
	close.Activated:Connect(function()
		Widgets.CloseAll()
	end)

	local content = Instance.new("Frame")
	content.Name = "Content"
	content.BackgroundTransparency = 1
	content.Position = UDim2.fromOffset(14, 66)
	content.Size = UDim2.new(1, -28, 1, -80)
	content.Parent = frame

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

-- A scrolling list that grows with its content.
function Widgets.List(parent: Instance, padding: number): ScrollingFrame
	local list = Instance.new("ScrollingFrame")
	list.BackgroundTransparency = 1
	list.BorderSizePixel = 0
	list.ScrollBarThickness = 6
	list.ScrollBarImageColor3 = Theme.Muted
	list.AutomaticCanvasSize = Enum.AutomaticSize.Y
	list.CanvasSize = UDim2.new()
	list.Size = UDim2.fromScale(1, 1)
	list.Parent = parent
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, padding)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = list
	local pad = Instance.new("UIPadding")
	pad.PaddingRight = UDim.new(0, 10)
	pad.PaddingTop = UDim.new(0, 2)
	pad.Parent = list
	return list
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
