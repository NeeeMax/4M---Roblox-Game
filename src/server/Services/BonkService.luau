--!strict
-- Validates hits reported by clients and awards Bonk Points. The client says "this projectile touched me"
-- (what the player saw); the server checks the claim against the projectile's exact flight path and the
-- character's position on the server, and alone decides. See docs/decisions/0003.
-- Catch quality depends on WHEN the stick was caught compared with its first landing (docs/decisions/0005):
-- after it touched the ground = Normal, in the air = Good, in the air just before it lands = Perfect.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local ProjectilePath = require(ReplicatedStorage.Shared.Util.ProjectilePath)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local IndexService = require(script.Parent.IndexService)
local PartyService = require(script.Parent.PartyService)
local ProjectileService = require(script.Parent.ProjectileService)
local QuestService = require(script.Parent.QuestService)
local RewardService = require(script.Parent.RewardService)
local UpgradeService = require(script.Parent.UpgradeService)

local HITS = Gameplay.Hits
local COMBO = Gameplay.Combo
-- Qualities that count for the "PERFECT BONKS" quest (event name kept: saved quest progress uses it).
local HARD_QUALITIES = { Perfect = true }
-- Without a head, the body line ends this far above the root part.
local DEFAULT_HEAD_HEIGHT = 2.5

type Combo = {
	Count: number,
	-- os.clock() until which the next hit continues the combo.
	Until: number,
}

local qualities: { [string]: Economy.HitQualityDef } = {}
for _, quality in Economy.HitQualities do
	qualities[quality.Name] = quality
end

local bonkHit = Net.Get(Net.BonkHit)
local reportLimiter = RateLimiter.New(HITS.MaxReportsPerSecond, 1)
local immuneUntil: { [Player]: number } = {}
local combos: { [Player]: Combo } = {}

local BonkService = {}

-- The definition of a quality by name (Economy.HitQualities); unknown names fall back to Normal.
function BonkService.GetQuality(name: Types.HitQuality): Economy.HitQualityDef
	return qualities[name] or qualities.Normal or Economy.HitQualities[1]
end

-- Quality of a catch at `hitTime` seconds after launch, on a path that first touches the ground at `landingTime`.
function BonkService.QualityForTiming(hitTime: number, landingTime: number): Economy.HitQualityDef
	if hitTime >= landingTime then
		return BonkService.GetQuality("Normal")
	elseif landingTime - hitTime <= HITS.PerfectWindow then
		return BonkService.GetQuality("Perfect")
	end
	return BonkService.GetQuality("Good")
end

-- How long after a hit the next one still continues the combo: longer when shots come less often (the real throw
-- rate, after the stick density cap).
local function comboWindow(player: Player): number
	local throwsPerSecond = UpgradeService.GetThrowRate(player)
	local timeBetweenShots = 1 / math.max(throwsPerSecond, 1e-3)
	return COMBO.BaseWindow + COMBO.ShotsWindow * timeBetweenShots
end

-- Counts this hit into the player's combo. Returns the combo length (1 = first hit), its multiplier and the window.
local function registerCombo(player: Player, now: number): (number, number, number)
	local existing = combos[player]
	local combo: Combo = if existing and now <= existing.Until then existing else { Count = 0, Until = 0 }
	combos[player] = combo
	local window = comboWindow(player)
	combo.Count += 1
	combo.Until = now + window
	local multiplier = math.min(1 + COMBO.Step * (combo.Count - 1), COMBO.MaxMultiplier)
	return combo.Count, multiplier, window
end

-- True (once per player, ever) for a brand-new player's first paid hit: marks it done in the save.
local function takeFirstBonk(player: Player): boolean
	local state = DataService.GetState(player)
	if not state or state.Tutorial.FirstBonkDone then
		return false
	end
	state.Tutorial.FirstBonkDone = true
	DataService.Replicate(player)
	return true
end

local function onReportHit(player: Player, projectileId: unknown, onHeadClaim: unknown)
	if not RateLimiter.Allow(reportLimiter, player) or typeof(projectileId) ~= "number" then
		return
	end
	local info = ProjectileService.GetById(projectileId)
	if not info or info.Owner ~= player or info.Paid or not ProjectileService.AcceptsReports(info) then
		return
	end
	if (immuneUntil[player] or 0) > os.clock() then
		return
	end
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
	if not root or not root:IsA("BasePart") or not humanoid or humanoid.Health <= 0 then
		return
	end

	-- Only the part of the path the projectile has already travelled (flight, bounces, settling hops) counts; the
	-- resting position at its end is the last point. The pickup sphere is radius + PickupPadding, as on the client.
	local plan = info.Plan
	local travelled = os.clock() - info.LaunchedAt
	local pickupRadius = plan.Radius + HITS.PickupPadding
	local distance, projectileVelocity = ProjectileService.ClosestApproach(plan, root.Position, travelled)
	if distance > pickupRadius + HITS.HitTolerance then
		return
	end
	-- Head bonus: the client saw the head touch it, and the path really passed close to the head.
	local head = (character :: Model):FindFirstChild("Head")
	local headPart: BasePart? = if head and head:IsA("BasePart") then head else nil
	local onHead = false
	if onHeadClaim == true and headPart then
		local headDistance = ProjectileService.ClosestApproach(plan, headPart.Position, travelled)
		onHead = headDistance <= pickupRadius + HITS.HeadTolerance
	end

	immuneUntil[player] = os.clock() + HITS.ImmunityTime

	-- Catch moment: the client reports as soon as it sees the touch, so only the last moments before the report
	-- arrived count (ping + slack). In there: when the path first touched the body line (feet to head), as the
	-- client saw it; if it never came that close on the server (network delay), when it was closest to the root.
	local lookback = math.min(player:GetNetworkPing() + HITS.ReportLookbackSlack, HITS.ReportLookbackMax)
	local fromTime = travelled - lookback
	local bodyBottom = root.Position - Vector3.new(0, HITS.ContactLegLength, 0)
	local bodyTop = if headPart then headPart.Position else root.Position + Vector3.new(0, DEFAULT_HEAD_HEIGHT, 0)
	local contactTime = ProjectileService.FirstContactTime(
		plan,
		bodyBottom,
		bodyTop,
		pickupRadius + HITS.ContactBodyRadius,
		fromTime,
		travelled
	)
	local hitTime: number
	if contactTime then
		hitTime = contactTime
	else
		local _, _, closestTime = ProjectileService.ClosestApproach(plan, root.Position, travelled, fromTime)
		hitTime = closestTime
	end
	local quality = BonkService.QualityForTiming(hitTime, ProjectilePath.GetFirstLandingTime(plan.Path))

	local flat = Vector3.new(projectileVelocity.X, 0, projectileVelocity.Z)
	local knockbackDirection = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.zero
	BonkService.AwardHit(player, info, quality, onHead, knockbackDirection)
end

-- Pays out a validated hit: marks the projectile paid, counts the combo, adds the reward (× FirstBonkMultiplier for
-- a new player's very first paid hit), records quests and tells the client (popup, sound, knockback). Used for
-- reported hits and by AutoCatchService (Normal quality, no head).
function BonkService.AwardHit(
	player: Player,
	info: ProjectileService.ProjectileInfo,
	quality: Economy.HitQualityDef,
	onHead: boolean,
	knockbackDirection: Vector3
)
	if info.Paid then
		return
	end
	ProjectileService.MarkPaid(info)
	local plan = info.Plan

	local combo, comboMultiplier, window = registerCombo(player, os.clock())
	local headMultiplier = if onHead then HITS.HeadMultiplier else 1
	local firstBonk = takeFirstBonk(player)
	local firstMultiplier = if firstBonk then EconomyConfig.Bonk.FirstBonkMultiplier else 1
	local stickValue =
		RewardService.GetStickValue(player, plan.Def.BaseReward, plan.Golden, plan.Mega, plan.ValueMultiplier)
	local reward =
		math.max(1, math.floor(stickValue * quality.Multiplier * headMultiplier * comboMultiplier * firstMultiplier))
	-- Weekend Bonk Party quest (before AddPoints: its StateChanged carries the new count).
	PartyService.RecordCatch(player)
	EconomyService.AddPoints(player, reward)
	if plan.Golden then
		IndexService.DiscoverGolden(player) -- Shiba-Index: first golden catch
	end
	QuestService.Record(player, "Hit", 1)
	QuestService.Record(player, "Combo", combo)
	if onHead then
		QuestService.Record(player, "HeadHit", 1)
	end
	if HARD_QUALITIES[quality.Name] then
		QuestService.Record(player, "HardHit", 1)
	end

	bonkHit:FireClient(player, reward, quality.Name, knockbackDirection, onHead, combo, window, plan.Golden, firstBonk)
end

function BonkService.Start()
	Net.Get(Net.ReportHit).OnServerEvent:Connect(onReportHit)
	Players.PlayerRemoving:Connect(function(player)
		immuneUntil[player] = nil
		combos[player] = nil
		RateLimiter.Remove(reportLimiter, player)
	end)
end

return BonkService
