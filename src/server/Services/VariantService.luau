--!strict
-- Shiba Variants (docs/GAME_DESIGN.md → Shiba Variants, numbers in EconomyConfig.Variants). Every slot of the ring
-- (1 … 10, the n-th Shiba) has a variant in state.Variants.Slots: Normal, Shiny, Rainbow or Huge. It multiplies the
-- value of every stick that Shiba throws (NPCShooterService stamps it on the ShotPlan), changes its look, and never
-- goes down: it stays through evolutions and rebirths.
-- * Rolls: UpgradeService.TryPurchase calls RollSlots after a Bonk-Dollar purchase of Shiba Tier (every owned slot,
--   once per level bought) or More Shibas (the new slots). Robux grants and admin levels go through
--   UpgradeService.SetLevel and never roll: no paid random items.
-- * One draw per roll, best first (Huge, Rainbow, Shiny, each Luck / OneIn); a result only counts if it beats the
--   slot. Pity: RollsSinceRainbow / RollsSinceHuge count rolls since the player last GAINED a Rainbow-or-better /
--   Huge slot; at Pity.Rainbow / Pity.Huge the next roll that can still improve its slot is that variant.
-- * Every improvement fires VariantRolled to the finder (reveal card); a Huge goes to everyone in the server (chat
--   line). The Shiba-Index variant pages are marked by IndexService's scan after the state replicates.
-- Admin tools (AdminService): SetSlot, ResetAll, SetAdminLuck.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyConfig = require(ReplicatedStorage.Shared.Config.EconomyConfig)
local Gameplay = require(ReplicatedStorage.Shared.Config.Gameplay)
local Net = require(ReplicatedStorage.Shared.Net)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local DataService = require(script.Parent.DataService)
local EventService = require(script.Parent.EventService)

local VARIANTS = EconomyConfig.Variants
-- Admin luck never goes past this (keeps tests sane).
local MAX_ADMIN_LUCK = 1000
-- String → VariantId (the saved type). Unknown strings map to nil.
local VARIANT_IDS: { [string]: Types.VariantId } = {
	Normal = "Normal",
	Shiny = "Shiny",
	Rainbow = "Rainbow",
	Huge = "Huge",
}

local variantRolled = Net.Get(Net.VariantRolled)
local random = Random.new()
-- Admin testing tool: extra luck per player (not saved).
local adminLuck: { [Player]: number } = {}

local VariantService = {}

local function rank(variant: string?): number
	return VARIANTS.Rank[variant or "Normal"] or 0
end

-- The variant of ring slot `slot` (1 = the first Shiba).
function VariantService.GetVariant(player: Player, slot: number): Types.VariantId
	local state = DataService.GetState(player)
	local saved: string? = if state then state.Variants.Slots[tostring(slot)] else nil
	return VARIANT_IDS[saved or "Normal"] or VARIANT_IDS.Normal
end

-- Stick value multiplier of ring slot `slot` (EconomyConfig.Variants.Multiplier).
function VariantService.GetMultiplier(player: Player, slot: number): number
	return VARIANTS.Multiplier[VariantService.GetVariant(player, slot)] or 1
end

-- Current luck: divides the "1 in N" numbers. Base EconomyConfig.Variants.Luck × the Weekend Bonk Party luck
-- (EventService.VariantLuckMultiplier) × the admin test luck.
-- (A weekend event / weather would multiply in here.)
function VariantService.GetLuck(player: Player): number
	return VARIANTS.Luck * EventService.VariantLuckMultiplier() * (adminLuck[player] or 1)
end

-- One roll for one slot that has `current`. Returns the variant to give the slot, or nil if nothing better came out.
local function rollOnce(player: Player, variants: Types.VariantState, current: string?): string?
	variants.TotalRolls += 1
	variants.RollsSinceRainbow += 1
	variants.RollsSinceHuge += 1
	local currentRank = rank(current)
	local result = "Normal"
	-- Pity first (only when it can improve this slot, else it waits for the next roll).
	if variants.RollsSinceHuge >= VARIANTS.Pity.Huge and currentRank < rank("Huge") then
		result = "Huge"
	elseif variants.RollsSinceRainbow >= VARIANTS.Pity.Rainbow and currentRank < rank("Rainbow") then
		result = "Rainbow"
	else
		local luck = VariantService.GetLuck(player)
		local draw = random:NextNumber()
		local threshold = 0
		for _, variant in VARIANTS.Order do
			threshold += luck / VARIANTS.OneIn[variant]
			if draw < threshold then
				result = variant
				break
			end
		end
	end
	local resultRank = rank(result)
	if resultRank <= currentRank then
		return nil
	end
	if resultRank >= rank("Rainbow") then
		variants.RollsSinceRainbow = 0
	end
	if resultRank >= rank("Huge") then
		variants.RollsSinceHuge = 0
	end
	return result
end

-- Tells the finder (and, for a Huge, the whole server) about a new variant.
local function announce(player: Player, slot: number, variant: string)
	if player.Parent == nil then
		return
	end
	local state = DataService.GetState(player)
	local level = if state then state.UpgradeLevels.ShooterTier or 0 else 0
	local tier = Gameplay.Shooters.Tiers[math.clamp(level + 1, 1, #Gameplay.Shooters.Tiers)]
	local shibaName = if tier then tier.Name else "Shiba"
	if variant == "Huge" then
		variantRolled:FireAllClients(player.UserId, player.DisplayName, slot, variant, shibaName)
	else
		variantRolled:FireClient(player, player.UserId, player.DisplayName, slot, variant, shibaName)
	end
end

-- Rolls each slot in `slots` `times` times (Shiba Tier ×N bought = N rolls per slot). Changes state only; the caller
-- replicates (UpgradeService.TryPurchase does right after). Returns how many slots got a better variant.
function VariantService.RollSlots(player: Player, slots: { number }, times: number?): number
	local state = DataService.GetState(player)
	if not state then
		return 0
	end
	local variants = state.Variants
	local improved = 0
	for _, slot in slots do
		local key = tostring(slot)
		local best: string? = nil
		for _ = 1, math.max(1, times or 1) do
			local result = rollOnce(player, variants, variants.Slots[key]) or ""
			if VARIANT_IDS[result] then
				-- Straight from the map: a refined local loses its VariantId type in the type checker.
				variants.Slots[key] = VARIANT_IDS[result]
				best = result
			end
		end
		if best then
			improved += 1
			-- After the state is sent, so the reveal and the new look arrive together.
			task.defer(announce, player, slot, best)
		end
	end
	return improved
end

-- The player's owned slots (1 … owned Shibas).
function VariantService.OwnedSlots(player: Player): { number }
	local state = DataService.GetState(player)
	local owned = if state then Upgrades.GetValue("Shooters", state.UpgradeLevels.Shooters or 0) else 1
	local slots: { number } = {}
	for slot = 1, owned do
		table.insert(slots, slot)
	end
	return slots
end

-- Admin testing tool: sets slot `slot` to `variant` (may go down; "Normal" clears it). Plays the reveal.
function VariantService.SetSlot(player: Player, slot: number, variant: unknown)
	local state = DataService.GetState(player)
	local name = if typeof(variant) == "string" then variant else ""
	-- `slot == math.floor(slot)` rejects fractions and NaN.
	if not state or not VARIANT_IDS[name] or slot ~= math.floor(slot) or slot < 1 or slot > 99 then
		return
	end
	local key = tostring(slot)
	if rank(name) == 0 then
		state.Variants.Slots[key] = nil
	else
		state.Variants.Slots[key] = VARIANT_IDS[name]
	end
	DataService.Replicate(player)
	if rank(name) > 0 then
		announce(player, slot, name)
	end
end

-- Admin testing tool: every slot back to Normal and the counters to 0.
function VariantService.ResetAll(player: Player)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	state.Variants = { Slots = {}, RollsSinceRainbow = 0, RollsSinceHuge = 0, TotalRolls = 0 }
	DataService.Replicate(player)
end

-- Admin testing tool: luck × `luck` for this player until they leave (1 = normal).
function VariantService.SetAdminLuck(player: Player, luck: number)
	if luck ~= luck then
		return
	end
	adminLuck[player] = math.clamp(luck, 1, MAX_ADMIN_LUCK)
end

function VariantService.Start()
	Players.PlayerRemoving:Connect(function(player)
		adminLuck[player] = nil
	end)
end

return VariantService
