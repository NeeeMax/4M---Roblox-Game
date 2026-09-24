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
	-- S→C (reward: number, quality: HitQuality, knockbackDirection: Vector3)
	BonkHit = "BonkHit",
	-- S→C (bonkPoints: number, upgradeLevels: { [UpgradeId]: number }, activeShooters: number)
	StateChanged = "StateChanged",
}

local ALL_NAMES = { Net.RequestPurchase, Net.SetActiveShooters, Net.BonkHit, Net.StateChanged }

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
