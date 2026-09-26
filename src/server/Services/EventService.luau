--!strict
-- Server events (Config/Events, docs/GAME_DESIGN.md → Server events): every ~15 minutes one random event runs for
-- everyone in the server. This service only keeps the schedule and answers questions; the effects live where the
-- numbers are computed:
-- * GoldenMinute: ProjectileService rolls every projectile golden (IsActive).
-- * MegaStick: ProjectileService plans each player's next shot as a giant stick (HasMegaPending / TakeMega),
--   BonkService pays RewardMultiplier(true).
-- * DoublePoints: BonkService multiplies every reward (RewardMultiplier).
-- * StickStorm: UpgradeService.GetThrowRate multiplies the fire interval (FireIntervalMultiplier) and the stick
--   density cap (MaxThrowsMultiplier).
-- Weekend Bonk Party (Config/Events → Party): every Saturday 12:00 UTC for 24 h, computed from the UTC clock
-- (Events.PartyWindow) so every server agrees. During the party the next event comes after PartyInterval (7 min)
-- instead of Interval, and VariantLuckMultiplier() returns Party.VariantLuck. PartyService runs the party quest.
-- Clients learn the party window through PartyChanged(startsAt, endsAt) (Unix time).
-- It requires no other gameplay service, so everything above can require it without a cycle.
-- Clients learn about events through ServerEvent(eventId, time): eventId = the running event and time = when it
-- ends, or eventId "" and time = when the next one starts. Times are server clock (Workspace:GetServerTimeNow()).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Events = require(ReplicatedStorage.Shared.Config.Events)
local Net = require(ReplicatedStorage.Shared.Net)

local serverEvent = Net.Get(Net.ServerEvent)
local partyChanged = Net.Get(Net.PartyChanged)
local random = Random.new()

-- The running event (nil = none), when it ends and when the next one starts (server clock).
local currentId: Events.EventId? = nil
local endsAt = 0
local nextAt = 0
-- Players whose Shibas still have to throw their giant stick in the running MegaStick event.
local megaPending: { [Player]: boolean } = {}

-- Bonk Party admin overrides (Unix time): a party started by an admin, and "the scheduled party is switched off
-- until then" after an admin ended it.
local adminPartyStartsAt = 0
local adminPartyEndsAt = 0
local partySuppressedUntil = 0
-- The window last sent to clients.
local sentPartyStartsAt = -1
local sentPartyEndsAt = -1

local EventService = {}

local function now(): number
	return Workspace:GetServerTimeNow()
end

local function scheduleNext(from: number)
	local interval = if EventService.IsPartyActive() then Events.Party.PartyInterval else Events.Interval
	nextAt = from + interval + random:NextNumber(-Events.IntervalJitter, Events.IntervalJitter)
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

-- Multiplier for the stick density cap (StickStorm: a few more sticks at once).
function EventService.MaxThrowsMultiplier(): number
	return if currentId == "StickStorm" then Events.StickStorm.MaxThrowsMultiplier else 1
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

-- ==== Weekend Bonk Party (feat/social-party) ====

-- The running Bonk Party (partyStart <= now < partyEnd) or the next one, Unix time. Admin overrides included.
function EventService.GetPartyWindow(): (number, number)
	local time = os.time()
	if adminPartyEndsAt > time then
		return adminPartyStartsAt, adminPartyEndsAt
	end
	local partyStart, partyEnd = Events.PartyWindow(time)
	if partyStart <= time and time < partySuppressedUntil then
		-- An admin ended this party early: show the next one.
		return Events.PartyWindow(partyEnd)
	end
	return partyStart, partyEnd
end

-- Whether the Weekend Bonk Party runs right now.
function EventService.IsPartyActive(): boolean
	local partyStart, partyEnd = EventService.GetPartyWindow()
	local time = os.time()
	return partyStart <= time and time < partyEnd
end

-- Variant luck multiplier (the variant system multiplies its chances by it): Party.VariantLuck during the Bonk
-- Party, else 1.
function EventService.VariantLuckMultiplier(): number
	return if EventService.IsPartyActive() then Events.Party.VariantLuck else 1
end

-- Tells clients the party window (everyone when `player` is nil) if it changed or when asked for one player.
local function announceParty(player: Player?)
	local partyStart, partyEnd = EventService.GetPartyWindow()
	if player then
		partyChanged:FireClient(player, partyStart, partyEnd)
		return
	end
	if partyStart == sentPartyStartsAt and partyEnd == sentPartyEndsAt then
		return
	end
	local wasActive = sentPartyStartsAt <= os.time() and os.time() < sentPartyEndsAt
	sentPartyStartsAt, sentPartyEndsAt = partyStart, partyEnd
	partyChanged:FireAllClients(partyStart, partyEnd)
	local active = EventService.IsPartyActive()
	if active and not wasActive then
		print(`[4M] Bonk Party started (ends {os.date("!%Y-%m-%d %H:%M", partyEnd)} UTC)`)
		-- The faster event rhythm starts right away.
		if not currentId then
			nextAt = math.min(nextAt, now() + Events.Party.PartyInterval)
		end
	elseif wasActive and not active then
		print("[4M] Bonk Party ended")
	end
end

-- Admin hook: starts a Bonk Party now for Party.AdminDurationMinutes.
function EventService.StartPartyNow()
	adminPartyStartsAt = os.time()
	adminPartyEndsAt = adminPartyStartsAt + Events.Party.AdminDurationMinutes * 60
	partySuppressedUntil = 0
	announceParty(nil)
end

-- Admin hook: ends the running Bonk Party (an admin party, or the scheduled one until its normal end).
function EventService.StopPartyNow()
	adminPartyEndsAt = 0
	local time = os.time()
	local partyStart, partyEnd = Events.PartyWindow(time)
	if partyStart <= time then
		partySuppressedUntil = partyEnd
	end
	announceParty(nil)
end

-- ==== end Weekend Bonk Party ====

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
		announceParty(player)
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
			-- Party start / end (scheduled or admin): tell everyone, switch the event rhythm.
			announceParty(nil)
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
