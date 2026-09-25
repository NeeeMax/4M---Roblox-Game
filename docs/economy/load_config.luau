-- Loads src/shared/Config/EconomyConfig.luau outside Roblox (for `lune run`): gives it Roblox's Color3.
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")

local source = fs.readFile("src/shared/Config/EconomyConfig.luau")
local chunk = luau.load(source, {
	debugName = "EconomyConfig",
	environment = { Color3 = roblox.Color3 },
	injectGlobals = true,
})
return chunk()
