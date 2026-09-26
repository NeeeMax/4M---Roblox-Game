--!strict
-- Weekend Bonk Party quest and hub sign (Config/Events → Party, EconomyConfig.Party, docs/GAME_DESIGN.md → Weekend
-- Bonk Party). EventService owns the schedule (IsPartyActive, GetPartyWindow); this service:
-- * counts sticks caught with your hands during the party (BonkService calls RecordCatch before paying, so the state
--   goes out with that payment's StateChanged);
-- * pays the party quest (ClaimPartyQuest): RewardHits bonks + the Party trophy, whose counter (state.Party.Count)
--   the island sign shows;
-- * keeps the countdown sign above the hub plaza up to date.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Events = require(ReplicatedStorage.Shared.Config.Events)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Types = require(ReplicatedStorage.Shared.Types)
local World = require(ReplicatedStorage.Shared.Config.World)

local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local EventService = require(script.Parent.EventService)
local NotifyService = require(script.Parent.NotifyService)
local RewardService = require(script.Parent.RewardService)
local Signs = require(script.Parent.Parent.World.Signs)

local PARTY = Events.Party
local HUB = World.Hub
-- The sign hangs above the two plaza boards (how-to-play, obby best times), facing the hub spawn.
local SIGN_OFFSET = Vector3.new(0, 16, 19)
-- Wide enough that the poles stand outside both boards (they reach x = ±13.4).
local SIGN_SIZE = Vector3.new(28, 3.4, 0.5)

local claimLimiter = RateLimiter.New(5, 1)
local signLabel: TextLabel? = nil

local PartyService = {}

-- Moves the player's party quest to the party `partyId` (a new party starts at 0 catches).
local function ensureParty(state: Types.PlayerState, partyId: number)
	if state.Party.Id ~= partyId then
		state.Party.Id = partyId
		state.Party.Catches = 0
		state.Party.Claimed = false
	end
end

-- BonkService: the player caught a stick with their hands. Does not replicate (the payment right after does).
function PartyService.RecordCatch(player: Player)
	if not EventService.IsPartyActive() then
		return
	end
	local state = DataService.GetState(player)
	if not state then
		return
	end
	local partyId = EventService.GetPartyWindow()
	ensureParty(state, partyId)
	if state.Party.Catches >= PARTY.QuestCatches then
		return
	end
	state.Party.Catches += 1
	if state.Party.Catches >= PARTY.QuestCatches then
		NotifyService.Send(player, "Bonk Party quest complete! Claim it in QUESTS.", "Good")
	end
end

local function onClaimPartyQuest(player: Player)
	if not RateLimiter.Allow(claimLimiter, player) then
		return
	end
	local state = DataService.GetState(player)
	-- The saved party's quest (the running one, or the last one if it ended before the player claimed it).
	if not state or state.Party.Claimed or state.Party.Catches < PARTY.QuestCatches then
		return
	end
	state.Party.Claimed = true
	state.Party.Count += 1
	state.Trophies[EconomyConfig.Party.Trophy] = true
	local amount = RewardService.Hits(player, EconomyConfig.Party.RewardHits)
	-- AddPoints replicates the state (party and trophy included).
	EconomyService.AddPoints(player, amount)
	NotifyService.Send(
		player,
		`Bonk Party quest: +{Format.Money(amount)} and Party trophy ×{state.Party.Count}!`,
		"Good"
	)
end

-- Admin testing: fills the running party's quest.
function PartyService.CompleteQuest(player: Player)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	local partyId = EventService.GetPartyWindow()
	ensureParty(state, partyId)
	state.Party.Catches = PARTY.QuestCatches
	DataService.Replicate(player)
end

local function buildSign()
	local folder = Instance.new("Folder")
	folder.Name = "BonkPartySign"
	local center = HUB.Center + SIGN_OFFSET
	local facing = CFrame.lookAt(center, center + Vector3.new(0, 0, 20))
	local board = Instance.new("Part")
	board.Name = "Board"
	board.Size = SIGN_SIZE
	board.CFrame = facing
	board.Anchored = true
	board.CanCollide = false
	board.CanQuery = false
	board.Color = Color3.fromRGB(40, 20, 50)
	board.Material = Enum.Material.SmoothPlastic
	board.Parent = folder
	local frame = Instance.new("Part")
	frame.Name = "Frame"
	frame.Size = SIGN_SIZE + Vector3.new(0.8, 0.8, -0.2)
	frame.CFrame = facing * CFrame.new(0, 0, 0.3)
	frame.Anchored = true
	frame.CanCollide = false
	frame.CanQuery = false
	frame.Color = PARTY.Color
	frame.Material = Enum.Material.Neon
	frame.Parent = folder
	for _, x in { -1, 1 } do
		local pole = Instance.new("Part")
		pole.Name = "Pole"
		pole.Size = Vector3.new(0.6, SIGN_OFFSET.Y + 1, 0.6)
		pole.CFrame =
			CFrame.new(HUB.Center + Vector3.new(x * (SIGN_SIZE.X / 2 + 0.8), (SIGN_OFFSET.Y + 1) / 2, SIGN_OFFSET.Z))
		pole.Anchored = true
		pole.Color = Color3.fromRGB(60, 55, 70)
		pole.Parent = folder
	end
	local label = Signs.Text(board, Enum.NormalId.Front, "", PARTY.Color, 80)
	Signs.Mirror(board, label)
	signLabel = label
	folder.Parent = Workspace
end

local function updateSign()
	local label = signLabel
	if not label then
		return
	end
	local startsAt, endsAt = EventService.GetPartyWindow()
	local time = os.time()
	local text = if startsAt <= time and time < endsAt
		then `BONK PARTY NOW! Luck ×{PARTY.VariantLuck} · events every {PARTY.PartyInterval // 60} min · {Format.Countdown(
			endsAt - time
		)} left`
		else `BONK PARTY in {Format.Countdown(startsAt - time)} · Saturdays 12:00 UTC`
	if label.Text ~= text then
		Signs.SetText(label, text)
	end
end

function PartyService.Start()
	Net.Get(Net.ClaimPartyQuest).OnServerEvent:Connect(onClaimPartyQuest)
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(claimLimiter, player)
	end)
	buildSign()
	task.spawn(function()
		while true do
			updateSign()
			task.wait(1)
		end
	end)
end

return PartyService
