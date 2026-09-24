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
	-- The only amounts the admin menu's "+ points" buttons (and the server) allow.
	PointAmounts = { 1000, 100000, 10000000, 1000000000 } :: { number },
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
