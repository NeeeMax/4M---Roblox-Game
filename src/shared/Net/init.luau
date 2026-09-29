--!strict
-- The only place remotes are created. Every remote is documented in docs/NETWORK.md.
-- No side effects on require: the server calls CreateRemotes() once from Main.server.luau.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local FOLDER_NAME = "Remotes"

local Net = {
	-- C→S (upgradeId: string)
	RequestPurchase = "RequestPurchase",
	-- C→S (count: number)
	SetActiveShooters = "SetActiveShooters",
	-- C→S (projectileId: number, onHead: boolean) — "this projectile touched me (on the head)"; the server validates it
	-- (docs/decisions/0003)
	ReportHit = "ReportHit",
	-- C→S (command: string, argument: string | number | nil) — admin-only testing tools, see Config/Admin
	AdminCommand = "AdminCommand",
	-- S→C (reward: number, quality: HitQuality, knockbackDirection: Vector3, onHead: boolean, combo: number,
	-- comboWindow: number, golden: boolean)
	BonkHit = "BonkHit",
	-- S→C (state: PlayerState) — a copy of the player's whole saved state
	StateChanged = "StateChanged",
	-- S→C (message: string, kind: "Info" | "Good" | "Bad") — short on-screen message
	Notify = "Notify",
	-- C→S () — spin the daily wheel
	RequestSpin = "RequestSpin",
	-- S→C (segmentIndex: number, text: string)
	SpinResult = "SpinResult",
	-- C→S (betFraction: number, side: "Heads" | "Tails") — coin flip against the house
	CoinFlip = "CoinFlip",
	-- S→C (won: boolean, side: "Heads" | "Tails", amount: number)
	CoinFlipResult = "CoinFlipResult",
	-- C→S (targetUserId: number, amount: number) — challenge another player to a coin flip duel
	DuelChallenge = "DuelChallenge",
	-- S→C (duelId: number, challengerName: string, amount: number)
	DuelInvite = "DuelInvite",
	-- C→S (duelId: number, accept: boolean)
	DuelRespond = "DuelRespond",
	-- S→C (won: boolean, opponentName: string, amount: number, side: "Heads" | "Tails")
	DuelResult = "DuelResult",
	-- C→S (questIndex: number)
	ClaimQuest = "ClaimQuest",
	-- C→S (itemId: string) — buy a shop item (Config/Shop); Robux items open Roblox's purchase prompt
	ShopBuy = "ShopBuy",
	-- C→S () — start one of your Bonk Rains
	UseBonkRain = "UseBonkRain",
	-- S→C (seconds: number) — a Bonk Rain started on your island
	BonkRainStarted = "BonkRainStarted",
	-- C→S () — claim today's login-streak reward
	ClaimStreak = "ClaimStreak",
	-- C→S (giftIndex: number) — claim a playtime gift
	ClaimPlaytime = "ClaimPlaytime",
	-- S→C (amount: number, seconds: number) — "Welcome back": offline earnings waiting to be claimed
	OfflineEarnings = "OfflineEarnings",
	-- C→S (double: boolean) — claim offline earnings; double = true opens the Robux purchase to double them
	ClaimOffline = "ClaimOffline",
	-- S→C () — the jump and run timer started (player touched the start)
	ObbyStarted = "ObbyStarted",
	-- S→C (time: number, reward: number, bestTime: number, nextRewardAt: number) — finished the jump and run
	ObbyFinished = "ObbyFinished",
	-- S→C (eventId: string, endsAt: number) — a server event started (eventId "" = the event ended)
	ServerEvent = "ServerEvent",
	-- C→S (entryId: string) — claim the discovery reward of a Shiba-Index entry
	ClaimIndex = "ClaimIndex",
	-- C→S (music: number, effects: number, hints: boolean) — save the settings menu
	SaveSettings = "SaveSettings",
	-- S→C (source: AutomationSource, projectileId: number, reward: number) — the basket or the intern caught one of the
	-- player's sticks and paid `reward` (visual only)
	AutomationCatch = "AutomationCatch",

	-- ==== Social + Bonk Party (feat/social-party) ====
	-- S→C (friends: number, multiplier: number) — Roblox friends in this server that count for the player's Friend
	-- Boost (capped) and the income multiplier it gives
	FriendBoostChanged = "FriendBoostChanged",
	-- S→C (startsAt: number, endsAt: number) — the running Weekend Bonk Party (startsAt <= now < endsAt) or the next
	-- one, Unix time (compare with Workspace:GetServerTimeNow())
	PartyChanged = "PartyChanged",
	-- C→S () — claim the Bonk Party quest reward
	ClaimPartyQuest = "ClaimPartyQuest",
	-- ==== end Social + Bonk Party ====
	-- ===== Shiba Variants =====
	-- S→C (finderUserId: number, finderName: string, slot: number, variant: VariantId, shibaName: string) — a Shiba
	-- slot rolled a better variant. Sent to the finder for every new variant (reveal card) and, for Huge, to everyone
	-- in the server (chat line).
	VariantRolled = "VariantRolled",
	-- ===== end Shiba Variants =====
	-- ==== Tycoon "Shiba Workers" (contract phase 0, docs/decisions/0006) ====
	-- C→S (padId: string) — buy a purchase pad (egg stand, Mill ring, vault upgrade, equip slot …), see Config/Tycoon
	BuyTycoonPad = "BuyTycoonPad",
	-- C→S (eggId: string, count: number) — hatch `count` (1, 3 or 10) eggs of this egg tier
	HatchEgg = "HatchEgg",
	-- S→C (eggId: string, results: { HatchResult }) — what the hatch produced (reveal animation, visual only)
	HatchResults = "HatchResults",
	-- C→S (shibaId: string, slot: number) — put an owned Shiba on an equip slot (ring position)
	EquipShiba = "EquipShiba",
	-- C→S (slot: number) — take the Shiba off an equip slot
	UnequipShiba = "UnequipShiba",
	-- C→S (slot: number, quantity: number) — level up the equipped Shiba on `slot`; quantity 1, 10 or 0 = as many as affordable
	UpgradeShiba = "UpgradeShiba",
	-- C→S (targetShibaId: string, sourceShibaId: string) — merge a duplicate into another Shiba of the same type
	MergeShibas = "MergeShibas",
	-- C→S (kind: string, slot: number) — buy a lane upgrade: kind "Arch" (lane arch on `slot`); Mill rings and the vault use BuyTycoonPad
	UpgradeLane = "UpgradeLane",
	-- S→C (slot: number, amount: number, source: string) — income the lane just paid (numbers/items on the belt, visual only;
	-- clients never award money)
	TycoonPayout = "TycoonPayout",
	-- S→C (crateId: number, slot: number, endsAt: number) — a Golden Crate rides the belt of `slot` until `endsAt` (server clock)
	CrateSpawned = "CrateSpawned",
	-- C→S (crateId: number) — tap/walk over a Golden Crate before it reaches the Mill
	CollectCrate = "CollectCrate",
	-- C→S (slot: number) — step on the boop mat of a lane (short lane boost, cooldown on the server)
	BoopLane = "BoopLane",
	-- C→S () — collect the vault (also happens automatically when the player is close)
	CollectVault = "CollectVault",
	-- ==== end Tycoon ====
}

local ALL_NAMES = {
	Net.RequestPurchase,
	Net.SetActiveShooters,
	Net.ReportHit,
	Net.AdminCommand,
	Net.BonkHit,
	Net.StateChanged,
	Net.Notify,
	Net.RequestSpin,
	Net.SpinResult,
	Net.CoinFlip,
	Net.CoinFlipResult,
	Net.DuelChallenge,
	Net.DuelInvite,
	Net.DuelRespond,
	Net.DuelResult,
	Net.ClaimQuest,
	Net.ShopBuy,
	Net.UseBonkRain,
	Net.BonkRainStarted,
	Net.ClaimStreak,
	Net.ClaimPlaytime,
	Net.OfflineEarnings,
	Net.ClaimOffline,
	Net.ObbyStarted,
	Net.ObbyFinished,
	Net.ServerEvent,
	Net.ClaimIndex,
	Net.SaveSettings,
	Net.AutomationCatch,
	-- Social + Bonk Party (feat/social-party)
	Net.FriendBoostChanged,
	Net.PartyChanged,
	Net.ClaimPartyQuest,
	-- Shiba Variants
	Net.VariantRolled,
	-- Tycoon "Shiba Workers"
	Net.BuyTycoonPad,
	Net.HatchEgg,
	Net.HatchResults,
	Net.EquipShiba,
	Net.UnequipShiba,
	Net.UpgradeShiba,
	Net.MergeShibas,
	Net.UpgradeLane,
	Net.TycoonPayout,
	Net.CrateSpawned,
	Net.CollectCrate,
	Net.BoopLane,
	Net.CollectVault,
}

function Net.CreateRemotes()
	assert(RunService:IsServer(), "Net.CreateRemotes is server-only")
	local folder = Instance.new("Folder")
	folder.Name = FOLDER_NAME
	for _, name in ALL_NAMES do
		local remote = Instance.new("RemoteEvent")
		remote.Name = name
		remote.Parent = folder
	end
	folder.Parent = ReplicatedStorage
end

-- Returns the remote with this name. Yields on the client until the server has created it.
function Net.Get(name: string): RemoteEvent
	assert(table.find(ALL_NAMES, name), `Unknown remote "{name}"`)
	local folder = if RunService:IsServer()
		then ReplicatedStorage:FindFirstChild(FOLDER_NAME)
		else ReplicatedStorage:WaitForChild(FOLDER_NAME)
	assert(folder, "Net.CreateRemotes() has not run yet")
	local remote = if RunService:IsServer() then folder:FindFirstChild(name) else folder:WaitForChild(name)
	assert(remote and remote:IsA("RemoteEvent"), `Remote "{name}" is missing`)
	return remote
end

return Net
