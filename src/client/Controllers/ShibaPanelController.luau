--!strict
-- The Shiba menu of the street tycoon (docs/GAME_DESIGN.md → Gameplay flow → Shiba menu (client)). ONE clean widget per
-- own Shiba, nothing else upgrades a Shiba on the client:
--   "Name  Lv N"
--   [ pill-shaped green bar, fills left to right during the cooldown, countdown inside ]
--        [ UPGRADE  $1.2K ]   (grey when too dear, "MAX" at the cap; key E upgrades the nearest Shiba)
-- A BillboardGui adorned to Lane_<n>/Anchor, only while the character is within SHOW_DISTANCE of it. Purely visual and a
-- request: the click is handled by the server (SwingPart's ClickDetector), the upgrade by UpgradeShiba(slot, 1).
-- Does nothing at all while Config/Features.Street is false (Start returns early) and only works while state.Tycoon.Enabled
-- and state.Tycoon.Street are true. World names (Workspace/Islands/Island_<UserId>/Tycoon): Lane_<n> with Anchor, SwingPart,
-- Shiba; all optional and looked up again whenever they are missing (streaming).

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Features = require(ReplicatedStorage.Shared.Config.Features)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local TycoonMath = require(ReplicatedStorage.Shared.Util.TycoonMath)
local Types = require(ReplicatedStorage.Shared.Types)

local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

type TycoonState = Types.TycoonState

-- A panel appears when the character comes within SHOW_DISTANCE of the Shiba and goes away beyond HIDE_DISTANCE.
local SHOW_DISTANCE = 45
local HIDE_DISTANCE = 55
local KEY_DISTANCE = 14
local MAX_DISTANCE = 60
-- Seconds between the proximity scans and between the lookups of a missing world part.
local SCAN_INTERVAL = 0.25
-- Panel size (pixels) and the layout inside it.
local PANEL_WIDTH = 220
local PANEL_HEIGHT = 80
local NAME_HEIGHT = 16
local BAR_TOP = 18
local BAR_HEIGHT = 30
local BAR_WIDTH = 204
local BUTTON_TOP = 53
local BUTTON_HEIGHT = 24
local BUTTON_WIDTH = 150
-- Height of the panel above the Anchor when the Shiba model is not found, and the clamp of the computed one (studs).
local DEFAULT_LIFT = 7.5
local HEAD_GAP = 1.2
-- At or below this cooldown the bar of an automated Shiba is simply shown full (it would only flicker).
local BLUR_COOLDOWN = 0.25
-- An automated Shiba counts as swinging for this many cooldowns (at least MIN_ACTIVE seconds) after its last ShibaSwung.
local ACTIVE_COOLDOWNS = 3
local MIN_ACTIVE = 3
-- A ShibaSwung arriving this soon after the own click does not restart the bar (it is the answer to that click).
local ECHO_WINDOW = 0.6
-- Minimum seconds between two upgrade requests of one Shiba (key repeat, double taps).
local UPGRADE_GAP = 0.08

local COLOR_TRACK = Color3.fromRGB(12, 34, 16)

local player = Players.LocalPlayer

type Panel = {
	Slot: number,
	ShibaId: string,
	Anchor: BasePart,
	Gui: BillboardGui,
	Name: TextLabel,
	Fill: Frame,
	Time: TextLabel,
	Button: TextButton,
	ButtonScale: UIScale?,
	SwingPart: BasePart?,
	ClickConnection: RBXScriptConnection?,
	-- Cooldown of the current level (idle display, next bar).
	Cooldown: number,
	-- Duration and start (os.clock) of the running bar; StartedAt nil = idle.
	Duration: number,
	StartedAt: number?,
	Automated: boolean,
	LastSwingAt: number,
	LastUpgradeAt: number,
	-- Last written values, so nothing is set twice.
	ShownAlpha: number,
	ShownTime: string,
	ShownButton: string,
	ShownLook: string,
}

local started = false
local active = false
local connection: RBXScriptConnection? = nil
local panels: { [number]: Panel } = {}
local lastScan = 0
local tycoonFolder: Instance? = nil
local tycoonFolderAt = 0

local ShibaPanelController = {}

-- ==== state and world ============================================================================================

local function streetTycoon(): TycoonState?
	local state = State.Get()
	local tycoon = if state then state.Tycoon else nil
	if tycoon and tycoon.Enabled and tycoon.Street == true then
		return tycoon
	end
	return nil
end

local function findTycoonFolder(): Instance?
	local now = os.clock()
	if tycoonFolder and tycoonFolder.Parent and now - tycoonFolderAt < 5 then
		return tycoonFolder
	end
	tycoonFolder = nil
	local islands = Workspace:FindFirstChild("Islands")
	local island = if islands then islands:FindFirstChild(`Island_{player.UserId}`) else nil
	local folder = if island then island:FindFirstChild("Tycoon") else nil
	tycoonFolder = folder
	tycoonFolderAt = now
	return folder
end

local function findLane(slot: number): Instance?
	local folder = findTycoonFolder()
	return if folder then folder:FindFirstChild(`Lane_{slot}`) else nil
end

local function findPart(lane: Instance?, name: string): BasePart?
	local part = if lane then lane:FindFirstChild(name) else nil
	if part and part:IsA("BasePart") then
		return part
	end
	return nil
end

local function characterRoot(): BasePart?
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if root and root:IsA("BasePart") then
		return root
	end
	return nil
end

-- Height of the panel above the Anchor: the top of the Shiba model's bounding box plus a gap.
local function liftOf(lane: Instance, anchor: BasePart): number
	local shiba = lane:FindFirstChild("Shiba")
	if shiba and shiba:IsA("Model") then
		local ok, box, size = pcall(function()
			return shiba:GetBoundingBox()
		end)
		if ok then
			local top = (box :: CFrame).Position.Y + (size :: Vector3).Y / 2
			return math.clamp(top - anchor.Position.Y + HEAD_GAP, 3, 30)
		end
	end
	return DEFAULT_LIFT
end

-- ==== text ======================================================================================================

-- 1 s → "1.00s", 0.5 s → "0.50s", 0.042 s → "42ms", 0.005 s → "5ms".
local function formatSeconds(seconds: number): string
	if seconds >= 0.1 then
		return string.format("%.2fs", seconds)
	end
	return string.format("%dms", math.max(1, math.floor(seconds * 1000 + 0.5)))
end

local function shibaName(tier: number): string
	local entry = EconomyConfig.Shibas[tier + 1]
	return if entry then entry.Name else "Shiba"
end

-- ==== bar =======================================================================================================

-- (fill 0 … 1, seconds to show) of a panel at `now`.
local function barOf(panel: Panel, now: number): (number, number)
	local cooldown = panel.Cooldown
	if panel.Automated and now - panel.LastSwingAt < math.max(MIN_ACTIVE, cooldown * ACTIVE_COOLDOWNS) then
		if cooldown <= BLUR_COOLDOWN then
			return 1, cooldown
		end
		local phase = (now - (panel.StartedAt or panel.LastSwingAt)) % cooldown
		return phase / cooldown, cooldown - phase
	end
	local startedAt = panel.StartedAt
	if startedAt then
		local elapsed = now - startedAt
		if elapsed < panel.Duration then
			return elapsed / panel.Duration, panel.Duration - elapsed
		end
		panel.StartedAt = nil
	end
	return 0, cooldown
end

local function isAnimating(panel: Panel, now: number): boolean
	if panel.StartedAt ~= nil then
		return true
	end
	return panel.Automated and now - panel.LastSwingAt < math.max(MIN_ACTIVE, panel.Cooldown * ACTIVE_COOLDOWNS)
end

local function drawBar(panel: Panel, now: number)
	local alpha, seconds = barOf(panel, now)
	alpha = math.floor(alpha * 200 + 0.5) / 200
	if alpha ~= panel.ShownAlpha then
		panel.ShownAlpha = alpha
		panel.Fill.Size = UDim2.fromScale(alpha, 1)
		panel.Fill.Visible = alpha > 0
	end
	-- A Shiba that has to be clicked says so until it is clicked; then the time runs down.
	local text = if panel.Automated or isAnimating(panel, now) then formatSeconds(seconds) else "CLICK ME"
	if text ~= panel.ShownTime then
		panel.ShownTime = text
		panel.Time.Text = text
	end
end

local function startBar(panel: Panel, now: number)
	panel.StartedAt = now
	panel.Duration = math.max(panel.Cooldown, 0.001)
end

-- ==== panel =====================================================================================================

local function destroyPanel(panel: Panel)
	if panels[panel.Slot] == panel then
		panels[panel.Slot] = nil
	end
	if panel.ClickConnection then
		panel.ClickConnection:Disconnect()
		panel.ClickConnection = nil
	end
	panel.Gui:Destroy()
end

local function requestUpgrade(panel: Panel, animate: boolean)
	local tycoon = streetTycoon()
	local state = State.Get()
	local shiba: Types.OwnedShiba? = if tycoon then tycoon.Shibas[panel.ShibaId] else nil
	if not tycoon or not state or not shiba then
		return
	end
	local now = os.clock()
	if now - panel.LastUpgradeAt < UPGRADE_GAP then
		return
	end
	panel.LastUpgradeAt = now
	if animate and panel.ButtonScale then
		panel.ButtonScale.Scale = 0.86
		TweenService:Create(panel.ButtonScale, TweenInfo.new(0.16, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	end
	if shiba.Level >= TycoonMath.CapFor(tycoon) then
		return
	end
	if state.BonkPoints < TycoonMath.LevelCost(shiba.Tier, shiba.Level) then
		return
	end
	Net.Get(Net.UpgradeShiba):FireServer(panel.Slot, 1)
end

-- The own click on the SwingPart: starts the bar at once (the server answers with ShibaSwung).
local function onClicked(panel: Panel)
	local now = os.clock()
	if panel.Automated then
		return
	end
	local startedAt = panel.StartedAt
	if startedAt and now - startedAt < panel.Duration then
		return
	end
	startBar(panel, now)
	drawBar(panel, now)
end

-- Keeps the ClickDetector connection on the current SwingPart (re-found after streaming, rebuilds, destroys).
local function linkSwingPart(panel: Panel, lane: Instance?)
	local part = panel.SwingPart
	if part and part.Parent and part:IsDescendantOf(Workspace) then
		return
	end
	if panel.ClickConnection then
		panel.ClickConnection:Disconnect()
		panel.ClickConnection = nil
	end
	panel.SwingPart = nil
	local found = findPart(lane, "SwingPart")
	local detector = if found then found:FindFirstChildOfClass("ClickDetector") else nil
	if found and detector then
		panel.SwingPart = found
		panel.ClickConnection = detector.MouseClick:Connect(function()
			onClicked(panel)
		end)
	end
end

local function createPanel(slot: number, shibaId: string, lane: Instance, anchor: BasePart): Panel
	local gui = Instance.new("BillboardGui")
	gui.Name = `ShibaPanel_{slot}`
	gui.Size = UDim2.fromOffset(PANEL_WIDTH, PANEL_HEIGHT)
	gui.StudsOffset = Vector3.new(0, liftOf(lane, anchor), 0)
	gui.MaxDistance = MAX_DISTANCE
	gui.AlwaysOnTop = false
	gui.LightInfluence = 0
	gui.ResetOnSpawn = false
	gui.Adornee = anchor

	local name = Widgets.Label(gui, "", 15, Theme.Text)
	name.Name = "Name"
	name.Font = Theme.Font
	name.AnchorPoint = Vector2.new(0.5, 0)
	name.Position = UDim2.fromScale(0.5, 0)
	name.Size = UDim2.fromOffset(PANEL_WIDTH, NAME_HEIGHT)
	name.TextXAlignment = Enum.TextXAlignment.Center
	name.TextStrokeTransparency = 1
	Widgets.Outline(name, 2)

	-- The pill: dark green track, a fill with the same full corner radius, the countdown on top.
	local track = Instance.new("Frame")
	track.Name = "Bar"
	track.AnchorPoint = Vector2.new(0.5, 0)
	track.Position = UDim2.new(0.5, 0, 0, BAR_TOP)
	track.Size = UDim2.fromOffset(BAR_WIDTH, BAR_HEIGHT)
	track.BackgroundColor3 = COLOR_TRACK
	track.BorderSizePixel = 0
	track.Parent = gui
	Widgets.Corner(track, BAR_HEIGHT // 2)
	Widgets.Stroke(track, 3)

	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.Size = UDim2.fromScale(0, 1)
	fill.BackgroundColor3 = Theme.Good
	fill.BorderSizePixel = 0
	fill.Visible = false
	fill.Parent = track
	Widgets.Corner(fill, BAR_HEIGHT // 2)
	Widgets.Gradient(fill, Color3.fromRGB(70, 235, 85))

	local time = Widgets.Label(track, "", 18, Theme.Text)
	time.Name = "Time"
	time.Font = Theme.TitleFont
	time.Size = UDim2.fromScale(1, 1)
	time.TextXAlignment = Enum.TextXAlignment.Center
	time.TextStrokeTransparency = 1
	time.ZIndex = 3
	Widgets.Outline(time, 2)

	local button = Widgets.Button(gui, "", Theme.Good, 14)
	button.Name = "Upgrade"
	button.AnchorPoint = Vector2.new(0.5, 0)
	button.Position = UDim2.new(0.5, 0, 0, BUTTON_TOP)
	button.Size = UDim2.fromOffset(BUTTON_WIDTH, BUTTON_HEIGHT)
	local corner = button:FindFirstChildOfClass("UICorner")
	if corner then
		corner.CornerRadius = UDim.new(0, BUTTON_HEIGHT // 2)
	end

	local panel: Panel = {
		Slot = slot,
		ShibaId = shibaId,
		Anchor = anchor,
		Gui = gui,
		Name = name,
		Fill = fill,
		Time = time,
		Button = button,
		ButtonScale = button:FindFirstChildOfClass("UIScale"),
		SwingPart = nil,
		ClickConnection = nil,
		Cooldown = 1,
		Duration = 1,
		StartedAt = nil,
		Automated = false,
		LastSwingAt = -1000,
		LastUpgradeAt = -1000,
		ShownAlpha = -1,
		ShownTime = "",
		ShownButton = "",
		ShownLook = "",
	}
	button.Activated:Connect(function()
		requestUpgrade(panel, true)
	end)

	linkSwingPart(panel, lane)
	local playerGui = player:FindFirstChildOfClass("PlayerGui")
	gui.Parent = playerGui
	panels[slot] = panel
	return panel
end

-- Name, level, cooldown and button of a panel from the saved state.
local function refreshPanel(panel: Panel, tycoon: TycoonState, shiba: Types.OwnedShiba, money: number)
	panel.Automated = shiba.Automated == true
	panel.Cooldown = TycoonMath.SwingCooldown(shiba.Tier, shiba.Level)
	local title = `{shibaName(shiba.Tier)}  Lv {shiba.Level}`
	if panel.Name.Text ~= title then
		panel.Name.Text = title
	end

	local maxed = shiba.Level >= TycoonMath.CapFor(tycoon)
	local cost = TycoonMath.LevelCost(shiba.Tier, shiba.Level)
	local text = if maxed then "MAX" else `UPGRADE  ${Format.Short(cost)}`
	if text ~= panel.ShownButton then
		panel.ShownButton = text
		panel.Button.Text = text
	end
	local look = if maxed or money < cost then "grey" else "green"
	if look ~= panel.ShownLook then
		panel.ShownLook = look
		Widgets.SetButtonColor(panel.Button, if look == "green" then Theme.Good else Theme.Disabled)
	end
	drawBar(panel, os.clock())
end

-- ==== scan ======================================================================================================

-- Creates, updates and removes the panels of the own Shibas near the character.
local function scan()
	local tycoon = streetTycoon()
	local state = State.Get()
	if not tycoon or not state then
		return
	end
	local root = characterRoot()
	local keep: { [number]: boolean } = {}
	if root then
		for slot = 1, tycoon.EquipSlots do
			local id = tycoon.Equipped[tostring(slot)]
			local shiba: Types.OwnedShiba? = if id then tycoon.Shibas[id] else nil
			local lane = if shiba then findLane(slot) else nil
			local anchor = findPart(lane, "Anchor")
			if id and shiba and lane and anchor then
				local existing: Panel? = panels[slot]
				local limit = if existing then HIDE_DISTANCE else SHOW_DISTANCE
				if (anchor.Position - root.Position).Magnitude <= limit then
					keep[slot] = true
					if
						existing
						and (existing.ShibaId ~= id or existing.Anchor ~= anchor or not existing.Gui.Parent)
					then
						destroyPanel(existing)
						existing = nil
					end
					local panel = existing or createPanel(slot, id, lane, anchor)
					linkSwingPart(panel, lane)
					refreshPanel(panel, tycoon, shiba, state.BonkPoints)
				end
			end
		end
	end
	for slot, panel in panels do
		if not keep[slot] then
			destroyPanel(panel)
		end
	end
end

local function onFrame()
	local now = os.clock()
	if now - lastScan >= SCAN_INTERVAL then
		lastScan = now
		scan()
	end
	for _, panel in panels do
		if isAnimating(panel, now) then
			drawBar(panel, now)
		end
	end
end

-- ==== activation ================================================================================================

local function deactivate()
	if not active then
		return
	end
	active = false
	if connection then
		connection:Disconnect()
		connection = nil
	end
	for _, panel in panels do
		destroyPanel(panel)
	end
end

local function activate()
	if active then
		return
	end
	active = true
	lastScan = 0
	connection = RunService.RenderStepped:Connect(onFrame)
end

local function onStateChanged()
	if streetTycoon() == nil then
		deactivate()
		return
	end
	activate()
	lastScan = os.clock()
	scan()
end

-- ==== remotes and input =========================================================================================

local function onShibaSwung(slot: unknown, _serverTime: unknown, automated: unknown)
	if not active or typeof(slot) ~= "number" then
		return
	end
	local panel = panels[math.floor(slot)]
	if not panel then
		return
	end
	local now = os.clock()
	panel.LastSwingAt = now
	if automated == true then
		panel.Automated = true
		panel.StartedAt = now
		panel.Duration = math.max(panel.Cooldown, 0.001)
		return
	end
	local startedAt = panel.StartedAt
	if startedAt and now - startedAt < ECHO_WINDOW then
		return
	end
	startBar(panel, now)
end

local function onInputBegan(input: InputObject, processed: boolean)
	if processed or input.KeyCode ~= Enum.KeyCode.E or not active then
		return
	end
	local root = characterRoot()
	if not root then
		return
	end
	local nearest: Panel? = nil
	local nearestDistance = KEY_DISTANCE
	for _, panel in panels do
		local distance = (panel.Anchor.Position - root.Position).Magnitude
		if distance <= nearestDistance then
			nearest = panel
			nearestDistance = distance
		end
	end
	if nearest then
		requestUpgrade(nearest, true)
	end
end

function ShibaPanelController.Init()
	-- Nothing to set up before Start.
end

function ShibaPanelController.Start()
	if started or not Features.Street then
		return
	end
	started = true
	State.Start()
	State.Changed:Connect(onStateChanged)
	Net.Get(Net.ShibaSwung).OnClientEvent:Connect(onShibaSwung)
	UserInputService.InputBegan:Connect(onInputBegan)
	-- The old level prompts (E / F) of the street plot would take the E key before the menu does: hide them on this client.
	ProximityPromptService.PromptShown:Connect(function(prompt: ProximityPrompt)
		if active and (prompt.Name == "Tycoon_LevelUp" or prompt.Name == "Tycoon_LevelUp10") then
			prompt.Enabled = false
		end
	end)
	-- The state may have arrived before this controller started.
	onStateChanged()
end

return ShibaPanelController
