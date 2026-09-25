--!strict
-- Who counts as an admin, and what admins can do (docs/GAME_DESIGN.md → Admin).
-- The server checks IsAdmin on every admin request (AdminService); on the client it only decides whether the
-- ADMIN button is shown.

local RunService = game:GetService("RunService")

local Admin = {
	-- Roblox UserIds of extra admins (the number in the profile URL: roblox.com/users/<UserId>/profile).
	-- The experience owner is always an admin. Example: { 12345678 }
	UserIds = { 11710633859 } :: { number }, -- Marco
	-- In Studio playtests everyone is an admin, so testing needs no setup.
	EveryoneInStudio = true,
	-- The only amounts the admin menu's "+ points" buttons (and the server) allow. Prices go up to 1e33
	-- (EconomyConfig.FinalShibaCost), so the buttons go that far too.
	PointAmounts = { 1e3, 1e6, 1e9, 1e12, 1e15, 1e18, 1e21, 1e24, 1e27, 1e30, 1e33 } :: { number },
	-- Buttons per row in the admin menu's Bonk Dollars section.
	PointButtonsPerRow = 6,
}

function Admin.IsAdmin(userId: number): boolean
	if Admin.EveryoneInStudio and RunService:IsStudio() then
		return true
	end
	if game.CreatorType == Enum.CreatorType.User and userId == game.CreatorId then
		return true
	end
	return table.find(Admin.UserIds, userId) ~= nil
end

return Admin
