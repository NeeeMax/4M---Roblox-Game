--!strict
-- Onboarding progress (Config/Tutorial, docs/GAME_DESIGN.md → Onboarding / first minute): counts a new player's
-- purchases in state.Tutorial.Step until Tutorial.GuidedPurchases, so the guided hints (TutorialController) stop
-- after the first few purchases and returning players don't see them again. A purchase = the sum of all upgrade
-- levels went up since the last state change (UpgradeService, stands, the pad, Robux instant upgrades; admin level
-- tools count too). Rebirths and resets lower the sum and are only remembered. The hints themselves are client-only.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Tutorial = require(ReplicatedStorage.Shared.Config.Tutorial)
local Types = require(ReplicatedStorage.Shared.Types)

local DataService = require(script.Parent.DataService)

-- Sum of all upgrade levels at the player's last state change.
local lastTotal: { [Player]: number } = {}

local TutorialService = {}

local function totalLevels(state: Types.PlayerState): number
	local total = 0
	for _, level in state.UpgradeLevels do
		total += level
	end
	return total
end

local function onReplicated(player: Player)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	local total = totalLevels(state)
	local last = lastTotal[player]
	lastTotal[player] = total
	if last == nil or total <= last or state.Tutorial.Step >= Tutorial.GuidedPurchases then
		return
	end
	state.Tutorial.Step = math.min(Tutorial.GuidedPurchases, state.Tutorial.Step + (total - last))
	-- Deferred: this runs inside a Replicate (same as IndexService). The next run sees no new levels.
	task.defer(DataService.Replicate, player)
end

function TutorialService.Start()
	DataService.OnLoaded(function(player, state)
		lastTotal[player] = totalLevels(state)
	end)
	DataService.OnReplicated(onReplicated)
	Players.PlayerRemoving:Connect(function(player)
		lastTotal[player] = nil
	end)
end

return TutorialService
