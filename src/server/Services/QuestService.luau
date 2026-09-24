--!strict
-- Daily quests (Config/Hub → Quests): every UTC day everyone gets the same PerDay quests from the pool. Other
-- services report what happened with Record(player, event, amount); the player claims finished quests for Bonk
-- Points worth RewardHits normal bonks (RewardService).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Hub = require(ReplicatedStorage.Shared.Config.Hub)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local RewardService = require(script.Parent.RewardService)

local CONFIG = Hub.Quests
local SECONDS_PER_DAY = 24 * 60 * 60

local claimLimiter = RateLimiter.New(5, 1)
local defsById: { [string]: Hub.QuestDef } = {}
for _, def in CONFIG.Pool do
	defsById[def.Id] = def
end

local QuestService = {}

local function today(): number
	return os.time() // SECONDS_PER_DAY
end

-- Today's quest ids: the same for every player, different every day, never two of the same kind (event).
local function pickQuests(day: number): { string }
	local random = Random.new(day)
	local pool = table.clone(CONFIG.Pool)
	local picked: { string } = {}
	local usedEvents: { [string]: boolean } = {}
	while #picked < CONFIG.PerDay and #pool > 0 do
		local def = table.remove(pool, random:NextInteger(1, #pool)) :: Hub.QuestDef
		if not usedEvents[def.Event] then
			usedEvents[def.Event] = true
			table.insert(picked, def.Id)
		end
	end
	return picked
end

local function newQuests(day: number): Types.QuestState
	local ids = pickQuests(day)
	local progress, claimed = {}, {}
	for index in ids do
		progress[index] = 0
		claimed[index] = false
	end
	return { Day = day, Ids = ids, Progress = progress, Claimed = claimed }
end

-- Rolls the quests over when a new day started. Returns true if it did.
local function ensureToday(state: Types.PlayerState): boolean
	local day = today()
	if state.Quests.Day == day then
		return false
	end
	state.Quests = newQuests(day)
	return true
end

function QuestService.GetDef(id: string): Hub.QuestDef?
	return defsById[id]
end

-- Counts `amount` toward every open quest for `event` ("Combo" keeps the highest value instead of adding up).
function QuestService.Record(player: Player, event: string, amount: number)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	local changed = ensureToday(state)
	local quests = state.Quests
	for index, id in quests.Ids do
		local def = defsById[id]
		if not def or def.Event ~= event or quests.Claimed[index] then
			continue
		end
		local before = quests.Progress[index] or 0
		if before >= def.Goal then
			continue
		end
		local after = if event == "Combo" then math.max(before, amount) else before + amount
		after = math.min(after, def.Goal)
		if after ~= before then
			quests.Progress[index] = after
			changed = true
			if after >= def.Goal then
				NotifyService.Send(player, "Quest complete! Claim it at the quest board.", "Good")
			end
		end
	end
	if changed then
		DataService.Replicate(player)
	end
end

local function onClaimQuest(player: Player, index: unknown)
	if not RateLimiter.Allow(claimLimiter, player) or typeof(index) ~= "number" then
		return
	end
	local state = DataService.GetState(player)
	if not state then
		return
	end
	if ensureToday(state) then
		DataService.Replicate(player)
		return
	end
	local quests = state.Quests
	local id = quests.Ids[index]
	local def = if id then defsById[id] else nil
	if not def or quests.Claimed[index] or (quests.Progress[index] or 0) < def.Goal then
		return
	end
	quests.Claimed[index] = true
	local reward = RewardService.Hits(player, def.RewardHits)
	EconomyService.AddPoints(player, reward)
	NotifyService.Send(player, `Quest reward: +{Format.Number(reward)} Bonk Points`, "Good")
end

-- Admin testing tools.
function QuestService.Reset(player: Player)
	local state = DataService.GetState(player)
	if state then
		state.Quests = newQuests(today())
		DataService.Replicate(player)
	end
end

function QuestService.CompleteAll(player: Player)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	ensureToday(state)
	for index, id in state.Quests.Ids do
		local def = defsById[id]
		if def then
			state.Quests.Progress[index] = def.Goal
		end
	end
	DataService.Replicate(player)
end

function QuestService.Start()
	Net.Get(Net.ClaimQuest).OnServerEvent:Connect(onClaimQuest)
	DataService.OnLoaded(function(player, state)
		if ensureToday(state) then
			DataService.Replicate(player)
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(claimLimiter, player)
	end)
	-- New quests at midnight UTC for players who stay online.
	task.spawn(function()
		while true do
			task.wait(60)
			for _, player in Players:GetPlayers() do
				local state = DataService.GetState(player)
				if state and ensureToday(state) then
					DataService.Replicate(player)
				end
			end
		end
	end)
end

return QuestService
