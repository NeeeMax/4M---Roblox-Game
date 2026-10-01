--!strict
-- Badges for first milestones and the onboarding funnel (Config/Milestones, docs/GAME_DESIGN.md → Milestones).
-- Both only READ the saved state every Milestones.CheckInterval seconds; nothing is saved and no remote is used:
-- * Badges: when a goal is reached, BadgeService:AwardBadgeAsync (Roblox ignores a badge the player already owns).
--   A badge whose BadgeId is 0 (not created on the Creator Hub yet) is skipped, so the list is inert until ids are filled in.
-- * Funnel: AnalyticsService:LogOnboardingFunnelStepEvent for players whose save is younger than
--   Funnel.NewPlayerHours, so the Creator Hub funnel shows where new players drop off (Roblox keeps one event per step
--   and player, a repeated call is harmless).
-- Both lists are remembered per server visit only, so a rejoin checks them once more (cheap, and it fills a badge
-- that failed to award earlier).

local AnalyticsService = game:GetService("AnalyticsService")
local BadgeService = game:GetService("BadgeService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Milestones = require(ReplicatedStorage.Shared.Config.Milestones)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)

type Kind = Milestones.Kind

type Session = {
	-- os.clock() when the save loaded.
	LoadedAt: number,
	-- Badge ids / funnel step numbers already handled this visit.
	Badges: { [string]: boolean },
	Steps: { [number]: boolean },
}

local sessions: { [Player]: Session } = {}

local MilestoneService = {}

local function countKeys(values: { [string]: boolean }?): number
	local count = 0
	if values then
		for _, set in values do
			if set then
				count += 1
			end
		end
	end
	return count
end

local function countRareVariants(state: Types.PlayerState): number
	local count = 0
	for _, variant in state.Variants.Slots do
		if variant == "Rainbow" or variant == "Huge" then
			count += 1
		end
	end
	local tycoon = state.Tycoon
	if tycoon then
		for _, shiba in tycoon.Shibas do
			if shiba.Variant == "Rainbow" or shiba.Variant == "Huge" then
				count += 1
			end
		end
	end
	return count
end

-- The number a milestone of this kind compares with its goal.
local function measure(kind: Kind, state: Types.PlayerState, session: Session): number
	local tycoon = state.Tycoon
	if kind == "Joined" then
		return 1
	elseif kind == "SessionSeconds" then
		return os.clock() - session.LoadedAt
	elseif kind == "Purchases" then
		return if tycoon then countKeys(tycoon.Steps) + countKeys(tycoon.Pads) else 0
	elseif kind == "Shibas" then
		return if tycoon then tycoon.EquipSlots else 0
	elseif kind == "TotalEarned" then
		return state.TotalEarned
	elseif kind == "Ascensions" then
		return math.max(state.Rebirths, if tycoon then tycoon.Ascensions else 0)
	elseif kind == "IndexSeen" then
		return countKeys(state.Index.Seen)
	elseif kind == "StreakDay" then
		return state.Streak.Count
	elseif kind == "Parties" then
		return state.Party.Count
	elseif kind == "RareVariants" then
		return countRareVariants(state)
	end
	return 0
end

local function awardBadge(player: Player, badge: Milestones.Badge)
	local ok, err = pcall(function()
		BadgeService:AwardBadgeAsync(player.UserId, badge.BadgeId)
	end)
	if not ok then
		-- Not retried this visit (it would warn every check); the next join tries again.
		warn(`[MilestoneService] Badge "{badge.Name}" ({badge.BadgeId}) was not awarded: {err}`)
	end
end

local function logFunnelStep(player: Player, step: Milestones.FunnelStep)
	local ok, err = pcall(function()
		AnalyticsService:LogOnboardingFunnelStepEvent(player, step.Step, step.Name)
	end)
	if not ok then
		warn(`[MilestoneService] Funnel step {step.Step} "{step.Name}" was not logged: {err}`)
	end
end

local function check(player: Player, session: Session)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	for _, badge in Milestones.Badges do
		if badge.BadgeId > 0 and not session.Badges[badge.Id] and measure(badge.Kind, state, session) >= badge.Goal then
			session.Badges[badge.Id] = true
			task.spawn(awardBadge, player, badge)
		end
	end
	local funnelAgeLimit = Milestones.Funnel.NewPlayerHours * 60 * 60
	if os.time() - state.FirstJoinAt > funnelAgeLimit then
		return
	end
	for _, step in Milestones.Funnel.Steps do
		if not session.Steps[step.Step] and measure(step.Kind, state, session) >= step.Goal then
			session.Steps[step.Step] = true
			task.spawn(logFunnelStep, player, step)
		end
	end
end

local function onLoaded(player: Player)
	-- DataService.Reset (admin) loads again: keep the first visit's memory and clock.
	if not sessions[player] then
		sessions[player] = { LoadedAt = os.clock(), Badges = {}, Steps = {} }
	end
end

function MilestoneService.Start()
	-- OnLoaded also runs for players whose data was loaded before this Start.
	DataService.OnLoaded(onLoaded)
	Players.PlayerRemoving:Connect(function(player)
		sessions[player] = nil
	end)
	task.spawn(function()
		while true do
			task.wait(Milestones.CheckInterval)
			for player, session in sessions do
				check(player, session)
			end
		end
	end)
end

return MilestoneService
