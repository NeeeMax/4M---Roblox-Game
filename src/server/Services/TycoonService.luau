--!strict
-- The tycoon core loop "Shiba Workers" (docs/decisions/0006, docs/TYCOON_HANDOFF.md). Server-authoritative:
-- * Income: a 1 Hz tick pays TycoonMath.TotalIncome × RewardService.GetIncomeMultiplier (+ boop boosts) in ONE
--   EconomyService.AddPoints per player and second, and tells the client per lane with TycoonPayout (visual only).
-- * Purchases: egg hatching, purchase pads (equip slots, Mill rings, zones, Ascension), equipping, per-Shiba levels,
--   arches and merging. Every remote validates type, range, ownership and rate; the same logic is exposed as plain
--   functions in TycoonService.Actions for the world's ProximityPrompts (src/server/World/TycoonPlot).
-- * Golden Crates: every CRATE_INTERVAL seconds a crate rides a random equipped lane's belt; collecting it before it
--   ends pays CRATE_MULT × the lane's income of CRATE_SECONDS; an uncollected one auto-pays AUTO_CRATE_MULT × at the end.
-- * Boop mats: a lane pays x2 for BOOP_DURATION seconds, cooldown BOOP_COOLDOWN seconds (server-side).
-- * Vault: state.Tycoon.VaultStored stays 0 for now (offline income comes later); CollectVault pays and clears it.
-- Does nothing while Config/Features.Tycoon is false (Init and Start return at once).
-- Not done yet: Shiba-Index discovery (IndexService still reads the old UpgradeLevels/Variants slots), variant pity.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Features = require(ReplicatedStorage.Shared.Config.Features)
local Format = require(ReplicatedStorage.Shared.Util.Format)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Street = require(ReplicatedStorage.Shared.Config.Street)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local TycoonConfig = require(ReplicatedStorage.Shared.Config.Tycoon)
local TycoonMath = require(ReplicatedStorage.Shared.Util.TycoonMath)
local TycoonSteps = require(ReplicatedStorage.Shared.Util.TycoonSteps)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local IslandService = require(script.Parent.IslandService)
local StreetService = require(script.Parent.StreetService)
local NotifyService = require(script.Parent.NotifyService)
local RewardService = require(script.Parent.RewardService)
local VariantService = require(script.Parent.VariantService)
local StreetPlot = require(script.Parent.Parent.World.StreetPlot)
local TycoonPlot = require(script.Parent.Parent.World.TycoonPlot)

type TycoonState = Types.TycoonState

-- What the world's ProximityPrompts may call (all validate their own arguments; none returns anything).
export type Actions = {
	UpgradeShiba: (player: Player, slot: number, quantity: number) -> (),
	HatchEgg: (player: Player, eggId: string, count: number) -> (),
	BuyPad: (player: Player, padId: string) -> (),
	UpgradeLane: (player: Player, kind: string, slot: number) -> (),
	CollectVault: (player: Player) -> (),
	BoopLane: (player: Player, slot: number) -> (),
	EquipShiba: (player: Player, shibaId: string, slot: number) -> (),
	UnequipShiba: (player: Player, slot: number) -> (),
	MergeShibas: (player: Player, targetShibaId: string, sourceShibaId: string) -> (),
	SwingShiba: (player: Player, slot: number) -> (),
	BuyAutomation: (player: Player, slot: number) -> (),
	BuyStep: (player: Player, stepId: string) -> (),
}

type Crate = { Slot: number, EndsAt: number }

type Boop = { Start: number, Until: number }

-- Income tick (seconds) and the longest step one tick may pay for (a stalled server must not pay a huge lump).
local TICK_SECONDS = 1
local MAX_TICK_STEP = 5
-- Golden Crates.
local CRATE_INTERVAL = 90
local CRATE_TRAVEL = 8 -- seconds on the belt (the client animates the ride)
local CRATE_MULT = 10
local CRATE_SECONDS = 5
local AUTO_CRATE_MULT = 5
-- Boop mats.
local BOOP_MULT = 2
local BOOP_DURATION = 3
local BOOP_COOLDOWN = 10
-- A character must be this close to the island centre for crate / boop / vault requests from the client
-- (Gameplay.Island.Radius + a margin: the belts, mats and the vault are all on the island).
local REACH = Gameplay.Island.Radius + 20
-- Swing, click start, automation and the Bonk hit (Config/Tycoon → Swing).
local SWING = TycoonConfig.Swing
-- How often the automated Shibas are checked for their next swing (seconds).
local AUTO_SWING_STEP = 0.2

local EGG_PATTERN = "^Egg(%d+)$"
local SLOT_PAD_PATTERN = "^Slot(%d+)$"
local ZONE_PAD_PATTERN = "^Zone(%d+)$"
local ASCEND_PAD = "Ascend"
local ARCH_KIND = "Arch"

local VARIANT_IDS: { [string]: Types.VariantId } = {
	Normal = "Normal",
	Shiny = "Shiny",
	Rainbow = "Rainbow",
	Huge = "Huge",
}
local NORMAL: Types.VariantId = "Normal"

local random = Random.new()

local buyPadLimiter = RateLimiter.New(5, 1)
local hatchLimiter = RateLimiter.New(3, 1)
local equipLimiter = RateLimiter.New(5, 1)
local unequipLimiter = RateLimiter.New(5, 1)
local upgradeShibaLimiter = RateLimiter.New(10, 1)
local mergeLimiter = RateLimiter.New(3, 1)
local upgradeLaneLimiter = RateLimiter.New(5, 1)
local collectCrateLimiter = RateLimiter.New(5, 1)
local boopLimiter = RateLimiter.New(2, 1)
local vaultLimiter = RateLimiter.New(2, 1)
local swingLimiter = RateLimiter.New(12, 1)
local automateLimiter = RateLimiter.New(3, 1)
local limiters = {
	buyPadLimiter,
	hatchLimiter,
	equipLimiter,
	unequipLimiter,
	upgradeShibaLimiter,
	mergeLimiter,
	upgradeLaneLimiter,
	collectCrateLimiter,
	boopLimiter,
	vaultLimiter,
	swingLimiter,
	automateLimiter,
}

-- Per-player runtime state (not saved).
local crates: { [Player]: { [number]: Crate } } = {}
local nextCrateAt: { [Player]: number } = {}
local boops: { [Player]: { [number]: Boop } } = {}
local boopReadyAt: { [Player]: { [number]: number } } = {}
-- Fractions of a point that AddPoints (whole numbers) could not pay yet.
local carry: { [Player]: number } = {}
local plotBuilt: { [Player]: boolean } = {}
local nextCrateId = 1
-- Swing state: when each slot may swing again, and when the owner may be bonked (and paid) again.
local swingReadyAt: { [Player]: { [number]: number } } = {}
local bonkReadyAt: { [Player]: number } = {}

local TycoonService = {}
TycoonService.Actions = {} :: Actions

local actions = TycoonService.Actions

-- ==== helpers ==========================================================================================================

local function tycoonOf(player: Player): (Types.PlayerState?, TycoonState?)
	local state = DataService.GetState(player)
	-- PlayerState.Tycoon is optional in the type; DataService always fills it.
	local tycoon = if state then state.Tycoon else nil
	if not state or not tycoon or not tycoon.Enabled then
		return nil, nil
	end
	return state, tycoon
end

-- `value` is a whole number in [min, max] (rejects fractions, NaN and infinity).
local function isWhole(value: unknown, min: number, max: number): boolean
	return typeof(value) == "number" and value == math.floor(value) and value >= min and value <= max
end

local function isId(value: unknown): boolean
	return typeof(value) == "string" and #value > 0 and #value <= TycoonConfig.MaxIdLength
end

-- Whole number parsed from the digits of `pattern` in `text` (nil if it does not match or is not a small number).
local function numberFrom(text: string, pattern: string): number?
	local digits = string.match(text, pattern)
	if not digits or #digits > 3 then
		return nil
	end
	return tonumber(digits)
end

local function needMoney(player: Player, price: number)
	NotifyService.Send(player, `You need {Format.Money(price - EconomyService.GetPoints(player))} more`, "Bad")
end

-- The character stands on the player's island (crate / boop / vault requests from the client).
local function isNearIsland(player: Player): boolean
	local island = IslandService.GetIsland(player)
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if not island or not root or not root:IsA("BasePart") then
		return false
	end
	if StreetService.IsEnabled() then
		return StreetService.IsNearPlot(player, Street.ReachMargin)
	end
	local offset = root.Position - island.Center
	return Vector3.new(offset.X, 0, offset.Z).Magnitude <= REACH
end

local function levelCap(tycoon: TycoonState): number
	return TycoonMath.LevelCap(tycoon.Ascensions)
end

-- Rough strength of a Shiba, for "equip the best".
local function shibaScore(shiba: Types.OwnedShiba): number
	return TycoonMath.TierIncome(shiba.Tier)
		* TycoonMath.LevelMultiplier(shiba.Level)
		* TycoonConfig.VariantMult[shiba.Variant]
end

local function shibaNumber(id: string): number
	return tonumber(string.sub(id, 2)) or 0
end

-- Equip slot (as a number) the Shiba `shibaId` stands on, or nil.
local function slotOf(tycoon: TycoonState, shibaId: string): string?
	for key, id in tycoon.Equipped do
		if id == shibaId then
			return key
		end
	end
	return nil
end

local function firstEmptySlot(tycoon: TycoonState): number?
	for slot = 1, tycoon.EquipSlots do
		if not tycoon.Equipped[tostring(slot)] then
			return slot
		end
	end
	return nil
end

-- Income per second of one lane including the multipliers that apply to every lane (Global perks, passes, boosts,
-- events, Friend Boost). Boops and crates are not included.
local function laneRate(player: Player, tycoon: TycoonState, slot: number): number
	return TycoonMath.LaneIncome(tycoon, slot)
		* TycoonMath.GlobalMultiplier(tycoon)
		* RewardService.GetIncomeMultiplier(player)
end

-- Drops equipped Shibas that no longer exist and slots beyond EquipSlots (defensive: the save is validated, but a
-- merge or an Ascension must never leave a dangling id).
local function pruneEquipped(tycoon: TycoonState)
	for key, id in tycoon.Equipped do
		local slot = tonumber(key)
		local shiba = tycoon.Shibas[id]
		if not shiba or not slot or slot > tycoon.EquipSlots or not TycoonMath.IsEquippable(tycoon, shiba.Tier) then
			tycoon.Equipped[key] = nil
		end
	end
end

-- Puts the best unequipped Shibas whose zone is unlocked into the empty slots.
local function fillEmptySlots(tycoon: TycoonState)
	local ids: { string } = {}
	for id, shiba in tycoon.Shibas do
		if not slotOf(tycoon, id) and TycoonMath.IsEquippable(tycoon, shiba.Tier) then
			table.insert(ids, id)
		end
	end
	table.sort(ids, function(a, b)
		local scoreA, scoreB = shibaScore(tycoon.Shibas[a]), shibaScore(tycoon.Shibas[b])
		if scoreA ~= scoreB then
			return scoreA > scoreB
		end
		return shibaNumber(a) < shibaNumber(b)
	end)
	local nextIndex = 1
	for slot = 1, tycoon.EquipSlots do
		if not tycoon.Equipped[tostring(slot)] and ids[nextIndex] then
			tycoon.Equipped[tostring(slot)] = ids[nextIndex]
			nextIndex += 1
		end
	end
end

-- ==== eggs =============================================================================================================

local function rollVariant(player: Player): Types.VariantId
	local luck = VariantService.GetLuck(player)
	local draw = random:NextNumber()
	local threshold = 0
	for _, variant in EconomyConfig.Variants.Order do
		threshold += luck / EconomyConfig.Variants.OneIn[variant]
		if draw < threshold then
			-- Straight from the map: a refined local loses its VariantId type in the type checker.
			return VARIANT_IDS[variant]
		end
	end
	return NORMAL
end

-- The highest-level owned Shiba of `tier` and `variant`, or nil.
local function findDuplicate(tycoon: TycoonState, tier: number, variant: Types.VariantId): (string?, Types.OwnedShiba?)
	local bestId: string? = nil
	local best: Types.OwnedShiba? = nil
	for id, shiba in tycoon.Shibas do
		if shiba.Tier == tier and shiba.Variant == variant then
			if
				not best
				or shiba.Level > best.Level
				or (shiba.Level == best.Level and shibaNumber(id) < shibaNumber(bestId or id))
			then
				bestId, best = id, shiba
			end
		end
	end
	return bestId, best
end

local function ownedCount(tycoon: TycoonState): number
	local count = 0
	for _ in tycoon.Shibas do
		count += 1
	end
	return count
end

function actions.HatchEgg(player: Player, eggId: string, count: number)
	local state, tycoon = tycoonOf(player)
	if not state or not tycoon or not isId(eggId) or not table.find(TycoonConfig.HatchCounts, count) then
		return
	end
	local zone = numberFrom(eggId, EGG_PATTERN)
	-- "Egg0" is zone 0; the egg of a zone opens with the zone (Zone <= the unlocked zone).
	if not zone or not TycoonConfig.Zones[zone + 1] or zone > tycoon.Zone then
		return
	end
	if ownedCount(tycoon) + count > TycoonConfig.MaxOwnedShibas then
		NotifyService.Send(player, "Your collection is full! Merge some Shibas first.", "Bad")
		return
	end
	local price = TycoonMath.EggPrice(zone) * count
	if not EconomyService.TrySpend(player, price) then
		needMoney(player, price)
		return
	end

	local cap = levelCap(tycoon)
	local results: { Types.HatchResult } = {}
	for _ = 1, count do
		local tier = TycoonMath.TierFromRoll(zone, random:NextNumber() * 100)
		local fresh: Types.OwnedShiba = { Tier = tier, Level = 1, Variant = rollVariant(player) }
		local existingId, existing = findDuplicate(tycoon, tier, fresh.Variant)
		local result: Types.HatchResult = { ShibaId = "", Tier = tier, Variant = fresh.Variant, Duplicate = false }
		if existingId and existing then
			-- A duplicate of the same type and variant merges into the strongest copy.
			existing.Level, existing.Variant = TycoonMath.MergeResult(existing, fresh, cap)
			result.ShibaId = existingId
			result.Duplicate = true
		else
			local id = `s{tycoon.NextShibaId}`
			tycoon.NextShibaId += 1
			tycoon.Shibas[id] = fresh
			local slot = firstEmptySlot(tycoon)
			if slot then
				tycoon.Equipped[tostring(slot)] = id
			end
			result.ShibaId = id
		end
		table.insert(results, result)
	end
	tycoon.EggsHatched[eggId] = (tycoon.EggsHatched[eggId] or 0) + count

	DataService.Replicate(player)
	Net.Get(Net.HatchResults):FireClient(player, eggId, results)
end

-- ==== equip, levels, lanes, merge ======================================================================================

function actions.EquipShiba(player: Player, shibaId: string, slot: number)
	local _, tycoon = tycoonOf(player)
	if not tycoon or not isId(shibaId) or not isWhole(slot, 1, tycoon.EquipSlots) or not tycoon.Shibas[shibaId] then
		return
	end
	if not TycoonMath.IsEquippable(tycoon, tycoon.Shibas[shibaId].Tier) then
		NotifyService.Send(player, "Unlock this Shiba's zone first!", "Bad")
		return
	end
	local key = tostring(slot)
	local displaced = tycoon.Equipped[key]
	if displaced == shibaId then
		return
	end
	-- A Shiba stands on one slot only: equipping it elsewhere moves it (the Shiba that was there swaps into its old slot).
	local oldKey = slotOf(tycoon, shibaId)
	if oldKey then
		tycoon.Equipped[oldKey] = displaced
	end
	tycoon.Equipped[key] = shibaId
	DataService.Replicate(player)
end

function actions.UnequipShiba(player: Player, slot: number)
	local _, tycoon = tycoonOf(player)
	if not tycoon or not isWhole(slot, 1, tycoon.EquipSlots) or not tycoon.Equipped[tostring(slot)] then
		return
	end
	tycoon.Equipped[tostring(slot)] = nil
	DataService.Replicate(player)
end

function actions.UpgradeShiba(player: Player, slot: number, quantity: number)
	local state, tycoon = tycoonOf(player)
	if not state or not tycoon or not isWhole(slot, 1, tycoon.EquipSlots) or not table.find({ 1, 10, 0 }, quantity) then
		return
	end
	local id = tycoon.Equipped[tostring(slot)]
	local shiba = if id then tycoon.Shibas[id] else nil
	if not shiba then
		return
	end
	local cap = levelCap(tycoon)
	if shiba.Level >= cap then
		NotifyService.Send(player, "This Shiba is at its level cap! Ascend to raise it.", "Info")
		return
	end
	local levels, spent = TycoonMath.LevelUpPlan(shiba.Tier, shiba.Level, quantity, state.BonkPoints, cap)
	if levels <= 0 then
		needMoney(player, TycoonMath.LevelCost(shiba.Tier, shiba.Level))
		return
	end
	if not EconomyService.TrySpend(player, spent) then
		needMoney(player, spent)
		return
	end
	shiba.Level += levels
	DataService.Replicate(player)
end

function actions.UpgradeLane(player: Player, kind: string, slot: number)
	local _, tycoon = tycoonOf(player)
	if not tycoon or kind ~= ARCH_KIND or not isWhole(slot, 1, tycoon.EquipSlots) then
		return
	end
	local key = tostring(slot)
	local id = tycoon.Equipped[key]
	local shiba = if id then tycoon.Shibas[id] else nil
	local arches = tycoon.Arches[key] or 0
	if not shiba or arches >= TycoonConfig.Arch.Max then
		return
	end
	local price = TycoonMath.ArchPrice(shiba.Tier, arches + 1)
	if not EconomyService.TrySpend(player, price) then
		needMoney(player, price)
		return
	end
	tycoon.Arches[key] = arches + 1
	DataService.Replicate(player)
end

function actions.MergeShibas(player: Player, targetShibaId: string, sourceShibaId: string)
	local _, tycoon = tycoonOf(player)
	if not tycoon or not isId(targetShibaId) or not isId(sourceShibaId) or targetShibaId == sourceShibaId then
		return
	end
	local target = tycoon.Shibas[targetShibaId]
	local source = tycoon.Shibas[sourceShibaId]
	if not target or not source or target.Tier ~= source.Tier or slotOf(tycoon, sourceShibaId) then
		return
	end
	target.Level, target.Variant = TycoonMath.MergeResult(target, source, levelCap(tycoon))
	tycoon.Shibas[sourceShibaId] = nil
	DataService.Replicate(player)
end

-- ==== pads =============================================================================================================

-- Ascension (pad "Ascend", Config/Tycoon → Ascension): resets money (to the first egg's price), Shiba levels, arches,
-- pads, zone and equip slots; keeps the collection, variants, Index, trophies, quests and streaks. Then equips the
-- best Shibas again.
-- The plot of the current mode: the street's (StreetPlot, floor pads and bays) or the island's ring (TycoonPlot).
local STREET = StreetService.IsEnabled()

local function plotBuild(player: Player, island: IslandService.Island)
	if STREET then
		StreetPlot.Build(player, island, actions)
	else
		TycoonPlot.Build(player, island, actions)
	end
end

local function plotRefresh(player: Player, state: Types.PlayerState)
	if STREET then
		StreetPlot.Refresh(player, state)
	else
		TycoonPlot.Refresh(player, state)
	end
end

local function plotDestroy(player: Player)
	if STREET then
		StreetPlot.Destroy(player)
	else
		TycoonPlot.Destroy(player)
	end
end

local function plotAim(player: Player, slot: number): { Origin: Vector3, Forward: Vector3 }?
	if STREET then
		return StreetPlot.GetLaneAim(player, slot)
	end
	return TycoonPlot.GetLaneAim(player, slot)
end

-- ==== swing, click start, automation and the Bonk hit ===============================================================
-- docs/GAME_DESIGN.md → Swing, click and Bonk hit. A Shiba that is not automated pays only when it is clicked; an automated
-- one is paid by the income tick like before and swings for show. The Bonk bonus never takes money away.

local function shibaOnSlot(tycoon: TycoonState, slot: number): Types.OwnedShiba?
	local id = tycoon.Equipped[tostring(slot)]
	return if id then tycoon.Shibas[id] else nil
end

local function isAutomated(tycoon: TycoonState, slot: number): boolean
	local shiba = shibaOnSlot(tycoon, slot)
	return shiba ~= nil and shiba.Automated == true
end

-- Pays `amount` (the fraction of a point is carried to the next payment: AddPoints takes whole numbers).
local function payPoints(player: Player, amount: number): number
	local total = amount + (carry[player] or 0)
	local whole = math.floor(total)
	carry[player] = total - whole
	if whole >= 1 then
		EconomyService.AddPoints(player, whole)
	end
	return whole
end

-- The stick has landed: the owner standing in the zone in front of the Shiba is flung and paid the Bonk bonus.
local function checkBonkHit(player: Player, tycoon: TycoonState, slot: number)
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	local aim = plotAim(player, slot)
	if not root or not root:IsA("BasePart") or not aim then
		return
	end
	local now = os.clock()
	if now < (bonkReadyAt[player] or 0) then
		return
	end
	local offset = root.Position - aim.Origin
	local flat = Vector3.new(offset.X, 0, offset.Z)
	if math.abs(offset.Y) > SWING.HitHeight or flat.Magnitude > SWING.HitRange then
		return
	end
	if flat.Magnitude > 0.5 and flat.Unit:Dot(aim.Forward) < math.cos(math.rad(SWING.HitHalfAngle)) then
		return
	end
	bonkReadyAt[player] = now + SWING.BonusCooldown
	local amount = payPoints(player, laneRate(player, tycoon, slot) * SWING.BonusSeconds)
	if amount >= 1 then
		Net.Get(Net.TycoonPayout):FireClient(player, slot, amount, "Bonk")
	end
	local away = if flat.Magnitude > 0.5 then flat.Unit else aim.Forward
	local launch = (away + Vector3.new(0, SWING.LaunchLift, 0)).Unit * SWING.LaunchSpeed
	Net.Get(Net.PlayerBonked):FireClient(player, slot, launch)
end

-- The stick lands (HitDelay after the swing started): pay a clicked swing, then check the hit zone.
local function landSwing(player: Player, slot: number, pay: boolean)
	local _, tycoon = tycoonOf(player)
	local shiba = if tycoon then shibaOnSlot(tycoon, slot) else nil
	if not tycoon or not shiba then
		return
	end
	if pay then
		local amount = payPoints(player, laneRate(player, tycoon, slot) * TycoonMath.SwingTimer(shiba.Tier))
		if amount >= 1 then
			Net.Get(Net.TycoonPayout):FireClient(player, slot, amount, "Swing")
		end
	end
	checkBonkHit(player, tycoon, slot)
end

local function startSwing(player: Player, tycoon: TycoonState, slot: number, pay: boolean)
	local ready = swingReadyAt[player]
	if not ready then
		return
	end
	local shiba = shibaOnSlot(tycoon, slot)
	ready[slot] = os.clock() + (if shiba then TycoonMath.SwingTimer(shiba.Tier) else SWING.Cooldown)
	Net.Get(Net.ShibaSwung):FireClient(player, slot, Workspace:GetServerTimeNow(), isAutomated(tycoon, slot))
	task.delay(SWING.HitDelay, landSwing, player, slot, pay)
end

-- Click / tap / Q on a Shiba. Automated Shibas ignore clicks (they pay the same rate on their own).
function actions.SwingShiba(player: Player, slot: number)
	if not RateLimiter.Allow(swingLimiter, player) then
		return
	end
	local _, tycoon = tycoonOf(player)
	if not tycoon or not isWhole(slot, 1, tycoon.EquipSlots) or not shibaOnSlot(tycoon, slot) then
		return
	end
	local ready = swingReadyAt[player]
	if isAutomated(tycoon, slot) or not ready or os.clock() < (ready[slot] or 0) or not isNearIsland(player) then
		return
	end
	startSwing(player, tycoon, slot, true)
end

function actions.BuyAutomation(player: Player, slot: number)
	if not RateLimiter.Allow(automateLimiter, player) then
		return
	end
	local _, tycoon = tycoonOf(player)
	if not tycoon or not isWhole(slot, 1, tycoon.EquipSlots) then
		return
	end
	local shiba = shibaOnSlot(tycoon, slot)
	if not shiba or shiba.Automated == true then
		return
	end
	local price = TycoonMath.AutomationPrice(shiba.Tier, TycoonMath.AutomatedCount(tycoon))
	if not EconomyService.TrySpend(player, price) then
		needMoney(player, price)
		return
	end
	shiba.Automated = true
	DataService.Replicate(player)
	local def = EconomyConfig.Shibas[shiba.Tier + 1]
	NotifyService.Send(player, `{if def then def.Name else "Shiba"} works by itself now!`, "Good")
end

-- Street mode: stepping on a floor pad. Only the pads the walkthrough shows right now can be bought (Util/TycoonSteps).
function actions.BuyStep(player: Player, stepId: string)
	if not STREET or typeof(stepId) ~= "string" then
		return
	end
	local state, tycoon = tycoonOf(player)
	local step = TycoonSteps.ById[stepId]
	if not state or not tycoon or not step then
		return
	end
	local shown = false
	for _, candidate in TycoonSteps.Visible(tycoon) do
		if candidate.Id == step.Id then
			shown = true
			break
		end
	end
	if not shown then
		return
	end
	local price = TycoonSteps.Price(step, tycoon)
	if price > 0 and not EconomyService.TrySpend(player, price) then
		needMoney(player, price)
		return
	end
	local bought: { [string]: boolean } = tycoon.Steps or {}
	tycoon.Steps = bought
	bought[step.Id] = true
	local def = EconomyConfig.Shibas[step.Bay]
	local name = if def then def.Name else "Shiba"
	if step.Kind == "Bay" then
		-- The expansion spawns its Shiba: tier n - 1, no luck (variants come later).
		local id = `s{tycoon.NextShibaId}`
		tycoon.NextShibaId += 1
		tycoon.Shibas[id] = { Tier = step.Bay - 1, Level = 1, Variant = "Normal" }
		tycoon.Equipped[tostring(step.Bay)] = id
		tycoon.EquipSlots = math.max(tycoon.EquipSlots, step.Bay)
		NotifyService.Send(player, `{name} joined your plot!`, "Good")
	else
		local id = tycoon.Equipped[tostring(step.Bay)]
		local shiba = if id then tycoon.Shibas[id] else nil
		if shiba then
			shiba.Automated = true
		end
		NotifyService.Send(player, `{name} works by itself now!`, "Good")
	end
	DataService.Replicate(player)
end

local function autoSwings(now: number)
	for _, player in Players:GetPlayers() do
		local _, tycoon = tycoonOf(player)
		local ready = swingReadyAt[player]
		if tycoon and ready then
			for slot = 1, tycoon.EquipSlots do
				if isAutomated(tycoon, slot) and now >= (ready[slot] or 0) then
					startSwing(player, tycoon, slot, false)
				end
			end
		end
	end
end

local function swingLoop()
	while true do
		task.wait(AUTO_SWING_STEP)
		xpcall(autoSwings, function(message: string)
			warn(`[TycoonService] automated swings failed: {message}\n{debug.traceback()}`)
		end, os.clock())
	end
end

local function ascend(player: Player, tycoon: TycoonState)
	tycoon.Ascensions += 1
	tycoon.Zone = 0
	tycoon.Pads = {}
	tycoon.Arches = {}
	tycoon.EquipSlots = TycoonConfig.StartEquipSlots
	tycoon.Equipped = {}
	for _, shiba in tycoon.Shibas do
		shiba.Level = 1
		-- The automation is bought again after an Ascension (docs/GAME_DESIGN.md → Swing, click and Bonk hit).
		shiba.Automated = nil
	end
	fillEmptySlots(tycoon)
	-- SetPoints replicates the state.
	EconomyService.SetPoints(player, TycoonConfig.Zones[1].EggPrice)
	NotifyService.Send(
		player,
		`Ascension {tycoon.Ascensions}! All income x{TycoonMath.AscensionMultiplier(tycoon.Ascensions)}`,
		"Good"
	)
end

function actions.BuyPad(player: Player, padId: string)
	local state, tycoon = tycoonOf(player)
	if not state or not tycoon or not isId(padId) or tycoon.Pads[padId] then
		return
	end

	if padId == ASCEND_PAD then
		if tycoon.Zone < TycoonConfig.Ascension.MinZone then
			NotifyService.Send(player, "Unlock the last zone first!", "Bad")
			return
		end
		ascend(player, tycoon)
		return
	end

	local price: number
	local apply: () -> ()
	local slotNumber = numberFrom(padId, SLOT_PAD_PATTERN)
	local zoneNumber = numberFrom(padId, ZONE_PAD_PATTERN)
	if slotNumber then
		-- Equip slots are bought in order: the next one only.
		local slotPrice = TycoonConfig.SlotPrices[slotNumber]
		if not slotPrice or slotNumber ~= tycoon.EquipSlots + 1 or slotNumber > TycoonConfig.MaxEquipSlots then
			return
		end
		price = slotPrice
		apply = function()
			tycoon.EquipSlots = slotNumber
			-- The free slot takes the best unequipped Shiba, if any.
			fillEmptySlots(tycoon)
		end
	elseif zoneNumber then
		-- Zones open in order, each with its egg.
		local zone = TycoonConfig.Zones[zoneNumber + 1]
		if not zone or zoneNumber ~= tycoon.Zone + 1 then
			return
		end
		price = zone.Price
		apply = function()
			tycoon.Zone = zoneNumber
			-- Shibas of the new zone can work now.
			fillEmptySlots(tycoon)
		end
	else
		-- Mill rings, in the order of Config/Tycoon → Rings.
		local ringIndex: number? = nil
		for index, ring in TycoonConfig.Rings do
			if ring.Id == padId then
				ringIndex = index
			end
		end
		if not ringIndex then
			return
		end
		local previous = TycoonConfig.Rings[ringIndex - 1]
		if previous and not tycoon.Pads[previous.Id] then
			NotifyService.Send(player, `Buy the {previous.Id} first!`, "Bad")
			return
		end
		price = TycoonConfig.Rings[ringIndex].Price
		apply = function()
			-- Nothing else to change: the ring's multiplier comes from Pads (TycoonMath.RingsMultiplier).
		end
	end

	if not EconomyService.TrySpend(player, price) then
		needMoney(player, price)
		return
	end
	apply()
	tycoon.Pads[padId] = true
	pruneEquipped(tycoon)
	DataService.Replicate(player)
end

-- ==== vault, boop, crates ==============================================================================================

function actions.CollectVault(player: Player)
	local _, tycoon = tycoonOf(player)
	if not tycoon or tycoon.VaultStored <= 0 then
		return
	end
	local amount = tycoon.VaultStored
	tycoon.VaultStored = 0
	-- AddPoints replicates the state (VaultStored included).
	EconomyService.AddPoints(player, amount)
	Net.Get(Net.TycoonPayout):FireClient(player, 0, math.floor(amount), "Vault")
end

function actions.BoopLane(player: Player, slot: number)
	local _, tycoon = tycoonOf(player)
	if not tycoon or not isWhole(slot, 1, tycoon.EquipSlots) or not tycoon.Equipped[tostring(slot)] then
		return
	end
	local now = os.clock()
	local ready = boopReadyAt[player]
	if not ready or now < (ready[slot] or 0) then
		return
	end
	ready[slot] = now + BOOP_COOLDOWN
	local active = boops[player]
	if active then
		active[slot] = { Start = now, Until = now + BOOP_DURATION }
	end
end

local function payCrate(player: Player, tycoon: TycoonState, crate: Crate, multiplier: number)
	local amount = math.floor(laneRate(player, tycoon, crate.Slot) * CRATE_SECONDS * multiplier)
	if amount >= 1 then
		EconomyService.AddPoints(player, amount)
		Net.Get(Net.TycoonPayout):FireClient(player, crate.Slot, amount, "Crate")
	end
end

local function spawnCrate(player: Player, tycoon: TycoonState)
	local slots: { number } = {}
	for slot = 1, tycoon.EquipSlots do
		if tycoon.Equipped[tostring(slot)] then
			table.insert(slots, slot)
		end
	end
	local owned = crates[player]
	if #slots == 0 or not owned then
		return
	end
	local crate: Crate = {
		Slot = slots[random:NextInteger(1, #slots)],
		EndsAt = Workspace:GetServerTimeNow() + CRATE_TRAVEL,
	}
	local id = nextCrateId
	nextCrateId += 1
	owned[id] = crate
	Net.Get(Net.CrateSpawned):FireClient(player, id, crate.Slot, crate.EndsAt)
end

local function onCollectCrate(player: Player, crateId: unknown)
	if not RateLimiter.Allow(collectCrateLimiter, player) or typeof(crateId) ~= "number" then
		return
	end
	local _, tycoon = tycoonOf(player)
	local owned = crates[player]
	local crate = if owned and isWhole(crateId, 1, nextCrateId) then owned[crateId] else nil
	-- The crate exists for this player, has not ended and not been collected (collecting removes it).
	if not tycoon or not owned or not crate or Workspace:GetServerTimeNow() >= crate.EndsAt then
		return
	end
	if not isNearIsland(player) then
		return
	end
	owned[crateId] = nil
	payCrate(player, tycoon, crate, CRATE_MULT)
end

-- ==== income tick ======================================================================================================

local function tickPlayer(player: Player, now: number, dt: number)
	local state, tycoon = tycoonOf(player)
	if not state or not tycoon then
		return
	end
	local mult = RewardService.GetIncomeMultiplier(player)
	local global = TycoonMath.GlobalMultiplier(tycoon)
	local active = boops[player] or {}
	local lastTick = now - dt

	local total = 0
	local payouts: { [number]: number } = {}
	for slot = 1, tycoon.EquipSlots do
		local base = TycoonMath.LaneIncome(tycoon, slot) * global * mult
		if base > 0 and isAutomated(tycoon, slot) then
			local seconds = dt
			local boop = active[slot]
			if boop then
				-- Boosted seconds inside this tick's window [lastTick, now].
				local boosted = math.max(0, math.min(now, boop.Until) - math.max(lastTick, boop.Start))
				seconds += boosted * (BOOP_MULT - 1)
				if boop.Until <= now then
					active[slot] = nil
				end
			end
			local amount = base * seconds
			total += amount
			payouts[slot] = amount
		end
	end

	total += carry[player] or 0
	local whole = math.floor(total)
	carry[player] = total - whole
	if whole >= 1 then
		EconomyService.AddPoints(player, whole)
	end
	-- One popup per lane and tick (1 per second, below the 2/s limit of docs/NETWORK.md).
	local payoutRemote = Net.Get(Net.TycoonPayout)
	for slot, amount in payouts do
		if amount >= 1 then
			payoutRemote:FireClient(player, slot, math.floor(amount), "Belt")
		end
	end

	-- Golden Crates: pay the ones that reached the Mill, then maybe send a new one.
	local owned = crates[player]
	if owned then
		local serverNow = Workspace:GetServerTimeNow()
		local live = 0
		for id, crate in owned do
			if serverNow >= crate.EndsAt then
				owned[id] = nil
				payCrate(player, tycoon, crate, AUTO_CRATE_MULT)
			else
				live += 1
			end
		end
		if live == 0 and now >= (nextCrateAt[player] or math.huge) then
			nextCrateAt[player] = now + CRATE_INTERVAL * random:NextNumber(0.8, 1.2)
			spawnCrate(player, tycoon)
		end
	end
end

local function incomeLoop()
	local last = os.clock()
	while true do
		task.wait(TICK_SECONDS)
		local now = os.clock()
		local dt = math.min(now - last, MAX_TICK_STEP)
		last = now
		for _, player in Players:GetPlayers() do
			xpcall(tickPlayer, function(message: string)
				warn(`[TycoonService] income tick failed for {player.Name}: {message}\n{debug.traceback()}`)
			end, player, now, dt)
		end
	end
end

-- ==== plot and player lifecycle ========================================================================================

local ISLAND_WAIT_SECONDS = 30

local function buildPlot(player: Player)
	local island = IslandService.GetIsland(player)
	local deadline = os.clock() + ISLAND_WAIT_SECONDS
	while not island and player.Parent and os.clock() < deadline do
		task.wait(0.2)
		island = IslandService.GetIsland(player)
	end
	if not island or not player.Parent then
		-- No free island (server full): nothing to build on.
		return
	end
	if plotBuilt[player] then
		plotDestroy(player)
	end
	plotBuilt[player] = true
	plotBuild(player, island)
	local state = DataService.GetState(player)
	if state then
		plotRefresh(player, state)
	end
end

local function onLoaded(player: Player, state: Types.PlayerState)
	local tycoon = state.Tycoon
	if not tycoon or not tycoon.Enabled then
		return
	end
	crates[player] = {}
	swingReadyAt[player] = {}
	boops[player] = {}
	boopReadyAt[player] = {}
	carry[player] = 0
	if not STREET then
		nextCrateAt[player] = os.clock() + CRATE_INTERVAL * random:NextNumber(0.5, 1)
		-- A player with nothing must be able to hatch the first egg (the old starting money is not tied to the tycoon).
		local firstEgg = TycoonConfig.Zones[1].EggPrice
		if next(tycoon.Shibas) == nil and state.BonkPoints < firstEgg then
			EconomyService.SetPoints(player, firstEgg)
		end
	end
	buildPlot(player)
end

local function onPlayerRemoving(player: Player)
	for _, limiter in limiters do
		RateLimiter.Remove(limiter, player)
	end
	crates[player] = nil
	swingReadyAt[player] = nil
	bonkReadyAt[player] = nil
	nextCrateAt[player] = nil
	boops[player] = nil
	boopReadyAt[player] = nil
	carry[player] = nil
	if plotBuilt[player] then
		plotBuilt[player] = nil
		plotDestroy(player)
	end
end

-- ==== remotes ==========================================================================================================

local function connectRemotes()
	Net.Get(Net.BuyTycoonPad).OnServerEvent:Connect(function(player, padId: unknown)
		if RateLimiter.Allow(buyPadLimiter, player) and isId(padId) then
			actions.BuyPad(player, padId :: string)
		end
	end)

	Net.Get(Net.HatchEgg).OnServerEvent:Connect(function(player, eggId: unknown, count: unknown)
		if RateLimiter.Allow(hatchLimiter, player) and isId(eggId) and typeof(count) == "number" then
			actions.HatchEgg(player, eggId :: string, count)
		end
	end)

	Net.Get(Net.EquipShiba).OnServerEvent:Connect(function(player, shibaId: unknown, slot: unknown)
		if RateLimiter.Allow(equipLimiter, player) and isId(shibaId) and typeof(slot) == "number" then
			actions.EquipShiba(player, shibaId :: string, slot)
		end
	end)

	Net.Get(Net.UnequipShiba).OnServerEvent:Connect(function(player, slot: unknown)
		if RateLimiter.Allow(unequipLimiter, player) and typeof(slot) == "number" then
			actions.UnequipShiba(player, slot)
		end
	end)

	Net.Get(Net.UpgradeShiba).OnServerEvent:Connect(function(player, slot: unknown, quantity: unknown)
		if
			RateLimiter.Allow(upgradeShibaLimiter, player)
			and typeof(slot) == "number"
			and typeof(quantity) == "number"
		then
			actions.UpgradeShiba(player, slot, quantity)
		end
	end)

	Net.Get(Net.MergeShibas).OnServerEvent:Connect(function(player, targetId: unknown, sourceId: unknown)
		if RateLimiter.Allow(mergeLimiter, player) and isId(targetId) and isId(sourceId) then
			actions.MergeShibas(player, targetId :: string, sourceId :: string)
		end
	end)

	Net.Get(Net.UpgradeLane).OnServerEvent:Connect(function(player, kind: unknown, slot: unknown)
		if RateLimiter.Allow(upgradeLaneLimiter, player) and typeof(kind) == "string" and typeof(slot) == "number" then
			actions.UpgradeLane(player, kind, slot)
		end
	end)

	Net.Get(Net.CollectCrate).OnServerEvent:Connect(onCollectCrate)

	Net.Get(Net.BoopLane).OnServerEvent:Connect(function(player, slot: unknown)
		if RateLimiter.Allow(boopLimiter, player) and typeof(slot) == "number" and isNearIsland(player) then
			actions.BoopLane(player, slot)
		end
	end)

	Net.Get(Net.CollectVault).OnServerEvent:Connect(function(player)
		if RateLimiter.Allow(vaultLimiter, player) and isNearIsland(player) then
			actions.CollectVault(player)
		end
	end)
end

function TycoonService.Init()
	if not Features.Tycoon then
		return
	end
	assert(#EconomyConfig.Shibas == TycoonConfig.TierCount, "Config/Tycoon TierCount must equal #EconomyConfig.Shibas")
end

function TycoonService.Start()
	if not Features.Tycoon then
		return
	end
	connectRemotes()
	DataService.OnLoaded(onLoaded)
	DataService.OnReplicated(function(player)
		local state = DataService.GetState(player)
		local tycoon = if state then state.Tycoon else nil
		if state and tycoon and tycoon.Enabled and plotBuilt[player] then
			plotRefresh(player, state)
		end
	end)
	Players.PlayerRemoving:Connect(onPlayerRemoving)
	task.spawn(incomeLoop)
	task.spawn(swingLoop)
end

return TycoonService
