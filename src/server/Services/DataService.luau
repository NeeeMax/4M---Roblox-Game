--!strict
-- Owns every player's saved state: loads it on join, saves it on leave / every AutosaveInterval / on shutdown,
-- and sends it to the owning client (StateChanged). EconomyService and UpgradeService change the state;
-- nothing else does.

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economy = require(ReplicatedStorage.Shared.Config.Economy)
local Net = require(ReplicatedStorage.Shared.Net)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

type PlayerState = Types.PlayerState

type Session = {
	State: PlayerState,
	-- False when loading failed: the player can still play, but we never save,
	-- so a temporary DataStore outage can't overwrite their real progress with defaults.
	CanSave: boolean,
}

local SAVE_VERSION = 1

local stateChanged = Net.Get(Net.StateChanged)

local store: DataStore? = nil
local sessions: { [Player]: Session } = {}
local loadedCallbacks: { (Player, PlayerState) -> () } = {}

local DataService = {}

local function defaultState(): PlayerState
	local levels: { [string]: number } = {}
	for _, id in Upgrades.Order do
		levels[id] = 0
	end
	return {
		BonkPoints = Economy.StartingPoints,
		UpgradeLevels = levels,
		ActiveShooters = Upgrades.GetValue("Shooters", 0),
	}
end

-- Saved data is never trusted blindly: unknown fields are dropped, numbers are clamped to valid ranges.
local function stateFromSaved(saved: unknown): PlayerState
	local state = defaultState()
	if typeof(saved) ~= "table" then
		return state
	end
	local data = saved :: { [string]: any }

	if typeof(data.BonkPoints) == "number" and data.BonkPoints == data.BonkPoints then
		state.BonkPoints = math.max(0, math.floor(data.BonkPoints))
	end
	if typeof(data.UpgradeLevels) == "table" then
		for _, id in Upgrades.Order do
			local level = data.UpgradeLevels[id]
			if typeof(level) == "number" and level == level then
				state.UpgradeLevels[id] = math.clamp(math.floor(level), 0, Upgrades.Defs[id].MaxLevel)
			end
		end
	end
	local owned = Upgrades.GetValue("Shooters", state.UpgradeLevels.Shooters)
	state.ActiveShooters = owned
	if typeof(data.ActiveShooters) == "number" and data.ActiveShooters == data.ActiveShooters then
		state.ActiveShooters = math.clamp(math.floor(data.ActiveShooters), 1, owned)
	end
	return state
end

-- Studio without API access or an unpublished place fails the same way every time; retrying only delays play.
local function isPermanentError(message: string): boolean
	return string.find(message, "403", 1, true) ~= nil
		or string.find(message, "publish", 1, true) ~= nil
		or string.find(message, "StudioAccessToApisNotAllowed", 1, true) ~= nil
end

-- Calls `attempt` up to DataStoreAttempts times with 1 s, 2 s, ... backoff. Returns success and the result.
local function withRetries(description: string, attempt: () -> unknown): (boolean, unknown)
	for try = 1, Economy.DataStoreAttempts do
		local ok, result = pcall(attempt)
		if ok then
			return true, result
		end
		local message = tostring(result)
		warn(`[DataService] {description} failed (try {try}): {message}`)
		if isPermanentError(message) or try == Economy.DataStoreAttempts then
			break
		end
		task.wait(2 ^ (try - 1))
	end
	return false, nil
end

local function save(player: Player, session: Session)
	local currentStore = store
	if not session.CanSave or not currentStore then
		return
	end
	local state = session.State
	local data = {
		Version = SAVE_VERSION,
		BonkPoints = state.BonkPoints,
		UpgradeLevels = table.clone(state.UpgradeLevels),
		ActiveShooters = state.ActiveShooters,
	}
	withRetries(`Saving {player.Name}`, function()
		-- No session locking in MVP: the latest save wins.
		return currentStore:UpdateAsync(tostring(player.UserId), function()
			return data
		end)
	end)
end

local function onPlayerAdded(player: Player)
	local currentStore = store
	local loaded, saved = false, nil
	if currentStore then
		loaded, saved = withRetries(`Loading {player.Name}`, function()
			return currentStore:GetAsync(tostring(player.UserId))
		end)
	end
	if player.Parent == nil then
		-- Left while we were loading.
		return
	end
	if not loaded then
		warn(`[DataService] Playing without saving for {player.Name} this session.`)
	end

	local session: Session = {
		State = if loaded then stateFromSaved(saved) else defaultState(),
		CanSave = loaded,
	}
	sessions[player] = session
	DataService.Replicate(player)
	for _, callback in loadedCallbacks do
		task.spawn(callback, player, session.State)
	end
end

local function onPlayerRemoving(player: Player)
	local session = sessions[player]
	sessions[player] = nil
	if session then
		save(player, session)
	end
end

-- The player's state, or nil while it is still loading (or after they left).
-- Callers may change fields and must then call DataService.Replicate.
function DataService.GetState(player: Player): PlayerState?
	local session = sessions[player]
	return if session then session.State else nil
end

-- Runs `callback` once per player as soon as their data is loaded, including players already loaded.
function DataService.OnLoaded(callback: (Player, PlayerState) -> ())
	table.insert(loadedCallbacks, callback)
	for player, session in sessions do
		task.spawn(callback, player, session.State)
	end
end

-- Sends the player's current state to their client.
function DataService.Replicate(player: Player)
	local session = sessions[player]
	if not session then
		return
	end
	local state = session.State
	stateChanged:FireClient(player, state.BonkPoints, table.clone(state.UpgradeLevels), state.ActiveShooters)
end

function DataService.Init()
	local ok, result = pcall(function()
		return DataStoreService:GetDataStore(Economy.DataStoreName)
	end)
	if ok then
		store = result
	else
		warn(`[DataService] DataStores unavailable, progress will not be saved: {result}`)
	end
end

function DataService.Start()
	Players.PlayerAdded:Connect(onPlayerAdded)
	Players.PlayerRemoving:Connect(onPlayerRemoving)
	for _, player in Players:GetPlayers() do
		task.spawn(onPlayerAdded, player)
	end

	task.spawn(function()
		while true do
			task.wait(Economy.AutosaveInterval)
			for player, session in sessions do
				task.spawn(save, player, session)
			end
		end
	end)

	game:BindToClose(function()
		local pending = 0
		for player, session in sessions do
			pending += 1
			task.spawn(function()
				save(player, session)
				pending -= 1
			end)
		end
		while pending > 0 do
			task.wait()
		end
	end)
end

return DataService
