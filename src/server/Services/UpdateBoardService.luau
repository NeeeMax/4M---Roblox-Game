--!strict
-- Update log board (Config/Updates, docs/GAME_DESIGN.md → Update log board): the latest updates and a "Next update in …"
-- countdown. In street mode it stands at the west end of the road (where the first plots are), otherwise next to the
-- hub plaza. All servers compute the countdown from the UTC clock (Updates.NextUpdateAt), nothing is saved or sent.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Features = require(ReplicatedStorage.Shared.Config.Features)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Street = require(ReplicatedStorage.Shared.Config.Street)
local Updates = require(ReplicatedStorage.Shared.Config.Updates)
local World = require(ReplicatedStorage.Shared.Config.World)

local Signs = require(script.Parent.Parent.World.Signs)

-- The street tycoon replaces the hub (docs/GAME_DESIGN.md → Street, plots and buttons).
local STREET_MODE = Features.Tycoon and Features.Street
local BOARD = Updates.Board
local TITLE_HEIGHT = 3.6
local BODY_HEIGHT = 12
local FOOTER_HEIGHT = 3
local TEXT_COLOR = Color3.fromRGB(245, 245, 255)

local footerLabel: TextLabel? = nil

local UpdateBoardService = {}

local function newPart(name: string, size: Vector3, cframe: CFrame, color: Color3, parent: Instance): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.CFrame = cframe
	part.Anchored = true
	-- A sign must never block the road or a path.
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Color = color
	part.Material = Enum.Material.SmoothPlastic
	part.Parent = parent
	return part
end

local function bodyText(): string
	local lines: { string } = {}
	for index = 1, math.min(Updates.ShownEntries, #Updates.Entries) do
		local entry = Updates.Entries[index]
		table.insert(lines, `{entry.Date}  {entry.Title}`)
		for _, line in entry.Lines do
			table.insert(lines, `• {line}`)
		end
		table.insert(lines, "")
	end
	return table.concat(lines, "\n")
end

-- `ground` = where the poles stand, `facing` = the direction the readers stand in.
local function buildBoard(ground: Vector3, facing: Vector3)
	local totalHeight = TITLE_HEIGHT + BODY_HEIGHT + FOOTER_HEIGHT
	local center = ground + Vector3.new(0, BOARD.Height + totalHeight / 2, 0)
	local folder = Instance.new("Folder")
	folder.Name = "UpdateBoard"
	local width = BOARD.Width
	local base = CFrame.lookAt(center, center + facing)
	local titleY = (BODY_HEIGHT + TITLE_HEIGHT) / 2
	local footerY = -(BODY_HEIGHT + FOOTER_HEIGHT) / 2

	local title =
		newPart("Title", Vector3.new(width, TITLE_HEIGHT, 0.5), base * CFrame.new(0, titleY, 0), BOARD.Color, folder)
	local titleLabel = Signs.Text(title, Enum.NormalId.Front, BOARD.TitleText, Color3.fromRGB(20, 20, 35))
	Signs.Mirror(title, titleLabel)

	local body = newPart("Body", Vector3.new(width, BODY_HEIGHT, 0.5), base, Color3.fromRGB(30, 28, 42), folder)
	local text = Signs.Text(body, Enum.NormalId.Front, bodyText(), TEXT_COLOR, 40, Enum.Font.GothamBold)
	text.TextXAlignment = Enum.TextXAlignment.Left
	text.TextYAlignment = Enum.TextYAlignment.Top
	Signs.Mirror(body, text)

	local footer =
		newPart("Footer", Vector3.new(width, FOOTER_HEIGHT, 0.5), base * CFrame.new(0, footerY, 0), BOARD.Color, folder)
	local label = Signs.Text(footer, Enum.NormalId.Front, "", Color3.fromRGB(20, 20, 35), 70)
	Signs.Mirror(footer, label)
	footerLabel = label

	-- Two poles from the ground up to the board.
	local right = base.RightVector
	for _, side in { -1, 1 } do
		local position = ground + Vector3.new(0, BOARD.Height / 2, 0) + right * (side * (width / 2 - 1))
		newPart("Pole", Vector3.new(0.6, BOARD.Height, 0.6), CFrame.new(position), Color3.fromRGB(60, 55, 70), folder)
	end
	folder.Parent = Workspace
end

local function updateCountdown()
	local label = footerLabel
	if not label then
		return
	end
	local now = os.time()
	local text = `Next update in {Format.Countdown(Updates.NextUpdateAt(now) - now)}`
	if label.Text ~= text then
		Signs.SetText(label, text)
	end
end

function UpdateBoardService.Start()
	if STREET_MODE then
		local origin = Street.Origin
		local length = Street.PlotsPerSide * Street.PlotPitch + Street.Road.Margin * 2
		-- Readers walk west along the road, so they look toward -X and the board's front faces +X.
		buildBoard(origin + Vector3.new(-length / 2 + BOARD.StreetEndInset, 0, 0), Vector3.new(1, 0, 0))
	else
		local hub = World.Hub.Center
		buildBoard(hub + Vector3.new(BOARD.HubOffset.X, 0, BOARD.HubOffset.Y), Vector3.new(0, 0, 1))
	end
	task.spawn(function()
		while true do
			updateCountdown()
			task.wait(1)
		end
	end)
end

return UpdateBoardService
