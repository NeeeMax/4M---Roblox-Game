--!strict
-- Client entry point. Loads every ModuleScript in Controllers/ (sorted by name),
-- calls every Init() and only then every Start(). See docs/ARCHITECTURE.md → Module lifecycle.

type Module = {
	Init: (() -> ())?,
	Start: (() -> ())?,
}

-- Controllers index ReplicatedStorage.Shared directly, so wait until the initial replication is done.
if not game:IsLoaded() then
	game.Loaded:Wait()
end

local modules: { Module } = {}
local controllersFolder = script.Parent:FindFirstChild("Controllers")
if controllersFolder then
	local children = controllersFolder:GetChildren()
	table.sort(children, function(a, b)
		return a.Name < b.Name
	end)
	for _, child in children do
		if child:IsA("ModuleScript") then
			-- A ModuleScript found at runtime has no static type; the Module shape is all Main relies on.
			local module = require(child) :: any
			table.insert(modules, module)
		end
	end
end

for _, module in modules do
	if module.Init then
		module.Init()
	end
end

for _, module in modules do
	if module.Start then
		module.Start()
	end
end
