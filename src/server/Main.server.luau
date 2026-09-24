--!strict
-- Server entry point. Creates the remotes, then loads every ModuleScript in Services/ (sorted by name),
-- calls every Init() and only then every Start(). See docs/ARCHITECTURE.md → Module lifecycle.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Build = require(ReplicatedStorage.Shared.Config.Build)
local Net = require(ReplicatedStorage.Shared.Net)

type Module = {
	Init: (() -> ())?,
	Start: (() -> ())?,
}

print(`[4M] Server code version: {Build.Label}`)

-- Before any service is required: services fetch their remotes at load time.
Net.CreateRemotes()

local modules: { Module } = {}
local servicesFolder = script.Parent:FindFirstChild("Services")
if servicesFolder then
	local children = servicesFolder:GetChildren()
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
