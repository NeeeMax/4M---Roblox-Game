--!strict
-- UI checker: run in the Client DataModel during a playtest (Claude: execute_luau with this file's content).
-- Checks what is on screen right now; switch devices with the Device Simulator and run it once per size.
-- The 4 real screen sizes (StudioDeviceSimulatorService ids, SetDeviceAsync works from the Client DataModel):
--   samsung_galaxy_a06 (cheap Android, smallest) · iphone_16 · ipad_10th_generation · hd_1080 (PC)
--   1 thumb-sized buttons   2 nothing touches (each other or the screen edge)   3 centred to 1.5 px
--   4 no tiny / cut-off text   5 no rando boxes (default-coloured backgrounds, empty images, stretched icons)
-- Returns a plain-text report; an empty issue list means the screen passes.

local MIN_BUTTON = 44 -- px, Apple/Google thumb target
local MIN_GAP = 2 -- px between content elements and to the screen edge
local CENTRE_TOLERANCE = 1.5 -- px
local MIN_TEXT = 14 -- px
local ICON_STRETCH = 0.1 -- stretched non-square image boxes beyond 10 % look distorted

local DEFAULT_GREY = Color3.fromRGB(163, 162, 165)
local DEFAULT_WHITE = Color3.fromRGB(255, 255, 255)

local player = game:GetService("Players").LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local viewport = workspace.CurrentCamera.ViewportSize
local issues: { string } = {}

type Rect = { x1: number, y1: number, x2: number, y2: number }

local function add(kind: string, obj: Instance, detail: string)
	table.insert(
		issues,
		("%-9s %s  %s"):format(kind, (obj:GetFullName():gsub("^Players%.[^.]+%.PlayerGui%.", "")), detail)
	)
end

local function rectOf(g: GuiObject): Rect
	local p, s = g.AbsolutePosition, g.AbsoluteSize
	return { x1 = p.X, y1 = p.Y, x2 = p.X + s.X, y2 = p.Y + s.Y }
end

-- Visible rect after ClipsDescendants ancestors, nil when hidden or clipped away (e.g. scrolled out of a list).
local function visibleRect(g: GuiObject): Rect?
	local r = rectOf(g)
	local node: Instance? = g
	while node and not node:IsA("LayerCollector") do
		if node:IsA("GuiObject") then
			if not node.Visible then
				return nil
			end
			if node ~= g and node.ClipsDescendants then
				local c = rectOf(node)
				r = {
					x1 = math.max(r.x1, c.x1),
					y1 = math.max(r.y1, c.y1),
					x2 = math.min(r.x2, c.x2),
					y2 = math.min(r.y2, c.y2),
				}
			end
		end
		node = node.Parent
	end
	if not node or (node:IsA("ScreenGui") and not node.Enabled) then
		return nil
	end
	if r.x2 - r.x1 < 1 or r.y2 - r.y1 < 1 then
		return nil
	end
	return r
end

local function isText(g: GuiObject): boolean
	return (g:IsA("TextLabel") or g:IsA("TextButton") or g:IsA("TextBox"))
		and (g :: any).Text ~= ""
		and (g :: any).TextTransparency < 1
end

local function isImage(g: GuiObject): boolean
	return (g:IsA("ImageLabel") or g:IsA("ImageButton")) and (g :: any).Image ~= "" and (g :: any).ImageTransparency < 1
end

-- Content = what a player sees or taps; frames are only containers and may overlap freely.
local function isContent(g: GuiObject): boolean
	return g:IsA("GuiButton") or isText(g) or isImage(g)
end

local function gap(a: Rect, b: Rect): number
	return math.max(a.x1 - b.x2, b.x1 - a.x2, a.y1 - b.y2, b.y1 - a.y2)
end

local content: { [ScreenGui]: { { g: GuiObject, r: Rect } } } = {}

for _, gui in playerGui:GetChildren() do
	-- TouchGui is Roblox's own thumbstick/jump UI, not ours.
	if not (gui:IsA("ScreenGui") and gui.Enabled) or gui.Name == "TouchGui" then
		continue
	end
	content[gui] = {}
	for _, d in gui:GetDescendants() do
		if not d:IsA("GuiObject") then
			continue
		end
		local r = visibleRect(d)
		if not r then
			continue
		end
		local w, h = d.AbsoluteSize.X, d.AbsoluteSize.Y

		-- 1 thumb-sized buttons
		if d:IsA("GuiButton") and d.Active and (w < MIN_BUTTON or h < MIN_BUTTON) then
			add("BUTTON", d, ("%dx%d < %d"):format(w, h, MIN_BUTTON))
		end

		-- 3 centred to 1.5 px: only axes that are meant to be centred (AnchorPoint 0.5 at Position scale 0.5)
		local parent = d.Parent
		if parent and parent:IsA("GuiObject") then
			local pr = rectOf(parent)
			local dx = (r.x1 + r.x2) / 2 - (pr.x1 + pr.x2) / 2
			local dy = (r.y1 + r.y2) / 2 - (pr.y1 + pr.y2) / 2
			if d.AnchorPoint.X == 0.5 and d.Position.X.Scale == 0.5 and math.abs(dx) > CENTRE_TOLERANCE then
				add("CENTRE", d, ("x off by %.1f px"):format(dx))
			end
			if d.AnchorPoint.Y == 0.5 and d.Position.Y.Scale == 0.5 and math.abs(dy) > CENTRE_TOLERANCE then
				add("CENTRE", d, ("y off by %.1f px"):format(dy))
			end
		end

		-- 4 no tiny / cut-off text
		if isText(d) then
			local t = d :: any
			local lines = #string.split(t.ContentText, "\n")
			-- Rendered size from TextBounds, because TextScaled and UIScale both change it (TextSize 18 can render at 9 px).
			-- ponytail: lines only counts explicit "\n"; auto-wrapped text overestimates the size.
			local px = t.TextBounds.Y / lines
			if px < MIN_TEXT then
				add("TEXT", d, ("%.0f px < %d: %q"):format(px, MIN_TEXT, t.ContentText:sub(1, 30)))
			end
			if not t.TextFits then
				add("TEXT", d, ("cut off: %q"):format(t.ContentText:sub(1, 30)))
			end
		end

		-- 5 no rando boxes
		if
			d.BackgroundTransparency < 1
			and (
				d.BackgroundColor3 == DEFAULT_GREY or (
					d.BackgroundColor3 == DEFAULT_WHITE and (isText(d) or isImage(d))
				)
			)
		then
			add("BOX", d, "default background colour (forgot BackgroundTransparency?)")
		end
		if
			(d:IsA("ImageLabel") or d:IsA("ImageButton"))
			and d.Image == ""
			and d.BackgroundTransparency < 1
			and #d:GetChildren() == 0
		then
			add("BOX", d, "image without Image shows only its background")
		end
		if
			isImage(d)
			and (d :: any).ScaleType == Enum.ScaleType.Stretch
			and math.abs(w / h - 1) > ICON_STRETCH
			and (d :: any).ImageRectSize == Vector2.zero
			and w < 200
			and h < 200
		then
			add("ICON", d, ("stretched %dx%d (use ScaleType Fit or a square box)"):format(w, h))
		end

		if isContent(d) then
			table.insert(content[gui], { g = d, r = r })
			-- 2a nothing touches the screen edge
			local edge = math.min(r.x1, r.y1, viewport.X - r.x2, viewport.Y - r.y2)
			if edge < MIN_GAP then
				add("EDGE", d, ("%.0f px from screen edge"):format(edge))
			end
		end
	end
end

-- 2b nothing touches: content elements of the same ScreenGui that are not nested in each other
for _, list in content do
	for i = 1, #list do
		for j = i + 1, #list do
			local a, b = list[i], list[j]
			if a.g:IsAncestorOf(b.g) or b.g:IsAncestorOf(a.g) then
				continue
			end
			local gp = gap(a.r, b.r)
			if gp < MIN_GAP then
				add("TOUCH", a.g, ("%s with %s (gap %.0f px)"):format(gp < 0 and "overlaps" or "touches", b.g.Name, gp))
			end
		end
	end
end

table.sort(issues)
return ("viewport %dx%d · %d issues\n%s"):format(viewport.X, viewport.Y, #issues, table.concat(issues, "\n"))
