--!strict
-- Server events (Config/Events, docs/GAME_DESIGN.md → Server events): every ~15 minutes one random event runs for
-- everyone in the server. This service only keeps the schedule and answers questions; the effects live where the
-- numbers are computed:
-- * GoldenMinute: ProjectileService rolls every projectile golden (IsActive).
-- * MegaStick: ProjectileService plans each player's next shot as a giant stick (HasMegaPending / TakeMega),
--   BonkService pays RewardMultiplier(true).
-- * DoublePoints: BonkService multiplies every reward (RewardMultiplier).
-- * StickStorm: NPCShooterService multiplies the fire interval (FireIntervalMultiplier).
-- It requires no other gameplay service, so everything above can require it without a cycle.
-- Clients learn about events through ServerEvent(eventId, time): eventId = the running event and time = when it
-- ends, or eventId "" and time = when the next one starts. Times are server clock (Workspace:GetServerTimeNow()).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Events = require(ReplicatedStorage.Shared.Config.Events)
local Net = require(ReplicatedStorage.Shared.Net)

local serverEvent = Net.Get(Net.ServerEvent)
local random = Random.new()

-- The running event (nil = none), when it ends and when the next one starts (server clock).
local currentId: Events.EventId? = nil
local endsAt = 0
local nextAt = 0
-- Players whose Shibas still have to throw their giant stick in the running MegaStick event.
local megaPending: { [Player]: boolean } = {}

local EventService = {}

local function now(): number
	return Workspace:GetServerTimeNow()
end

local function scheduleNext(from: number)
	nextAt = from + Events.Interval + random:NextNumber(-Events.IntervalJitter, Events.IntervalJitter)
end

local function announce(player: Player?)
	local id: string = currentId or ""
	local time = if currentId then endsAt else nextAt
	if player then
		serverEvent:FireClient(player, id, time)
	else
		serverEvent:FireAllClients(id, time)
	end
end

local function pickRandom(): Events.EventId
	local total = 0
	for _, id in Events.Order do
		total += Events.Defs[id].Weight
	end
	local roll = random:NextNumber() * total
	for _, id in Events.Order do
		roll -= Events.Defs[id].Weight
		if roll <= 0 then
			return Events.Defs[id].Id
		end
	end
	return Events.Defs[Events.Order[1]].Id
end

local function stop()
	if not currentId then
		return
	end
	currentId = nil
	table.clear(megaPending)
	announce(nil)
end

local function start(id: Events.EventId)
	stop()
	local def = Events.Defs[id]
	local startedAt = now()
	currentId = id
	endsAt = startedAt + def.Duration
	-- The next event is timed from this one's start (Interval is far longer than any Duration).
	scheduleNext(startedAt)
	if id == "MegaStick" then
		for _, player in Players:GetPlayers() do
			megaPending[player] = true
		end
	end
	print(`[4M] Server event started: {id} ({def.Duration} s)`)
	announce(nil)
end

-- Whether this event is running right now.
function EventService.IsActive(id: Events.EventId): boolean
	return currentId == id
end

-- The running event and when it ends (server clock), or nil.
function EventService.GetCurrent(): (Events.EventId?, number)
	return currentId, endsAt
end

-- Multiplier for a bonk's reward: DoublePoints, and the giant MegaStick stick (`mega`).
function EventService.RewardMultiplier(mega: boolean): number
	local multiplier = if currentId == "DoublePoints" then Events.DoublePoints.RewardMultiplier else 1
	if mega then
		multiplier *= Events.MegaStick.RewardMultiplier
	end
	return multiplier
end

-- Multiplier for every Shiba's fire interval (StickStorm: faster).
function EventService.FireIntervalMultiplier(): number
	return if currentId == "StickStorm" then Events.StickStorm.FireIntervalMultiplier else 1
end

-- Whether this player's next planned shot should be the MegaStick giant stick.
function EventService.HasMegaPending(player: Player): boolean
	return megaPending[player] == true
end

-- Uses up the player's giant stick. Returns false if it was already thrown (or the event ended).
function EventService.TakeMega(player: Player): boolean
	if not megaPending[player] then
		return false
	end
	megaPending[player] = nil
	return true
end

-- Admin hook: starts this event right away (ending the running one). Returns false for an unknown id.
function EventService.StartNow(id: string): boolean
	local def = Events.Defs[id]
	if not def then
		return false
	end
	start(def.Id)
	return true
end

-- Admin hook: ends the running event right away.
function EventService.StopNow()
	stop()
end

function EventService.Start()
	nextAt = now() + Events.FirstDelay

	local function onPlayerAdded(player: Player)
		if currentId == "MegaStick" then
			megaPending[player] = true
		end
		-- Late joiners see the running event (or the countdown to the next one).
		announce(player)
	end
	Players.PlayerAdded:Connect(onPlayerAdded)
	for _, player in Players:GetPlayers() do
		task.spawn(onPlayerAdded, player)
	end
	Players.PlayerRemoving:Connect(function(player)
		megaPending[player] = nil
	end)

	task.spawn(function()
		while true do
			task.wait(0.5)
			local time = now()
			if currentId and time >= endsAt then
				print(`[4M] Server event ended: {currentId}`)
				stop()
			elseif not currentId and time >= nextAt then
				start(pickRandom())
			end
		end
	end)
end

return EventService
