--!strict
-- First-milestone badges and the onboarding funnel (Services/MilestoneService, docs/GAME_DESIGN.md → Milestones).
-- Both are lists of "a number from the player's saved state reaches a goal", so they share the Kinds below. Pure data.
-- Nothing here changes the economy: a badge or a funnel step only reads the state.

-- What is measured (MilestoneService, `measure`):
--   Joined           always 1 once the save is loaded
--   SessionSeconds   seconds since the save loaded in this server
--   Purchases        floor pads / purchase pads bought (state.Tycoon.Steps + Pads)
--   Shibas           Shiba bays in street mode (EquipSlots), equip slots in the island tycoon
--   TotalEarned      state.TotalEarned
--   Ascensions       the larger of state.Rebirths and state.Tycoon.Ascensions
--   IndexSeen        entries marked as seen in the Shiba-Index
--   StreakDay        day of the login streak reached (1 … 7)
--   Parties          Bonk Party quests completed (state.Party.Count)
--   RareVariants     Rainbow or Huge Shibas owned (tycoon Shibas + variant ring slots)
export type Kind =
	"Joined"
	| "SessionSeconds"
	| "Purchases"
	| "Shibas"
	| "TotalEarned"
	| "Ascensions"
	| "IndexSeen"
	| "StreakDay"
	| "Parties"
	| "RareVariants"

export type Badge = {
	-- Stable id for logs and the server's "already awarded" memory; never rename.
	Id: string,
	-- Roblox badge id from the Creator Hub (Monetization → Badges). 0 = not created yet: the badge is inert.
	BadgeId: number,
	-- Shown in warnings only; the Roblox toast and the profile use the name set on the Creator Hub.
	Name: string,
	Kind: Kind,
	Goal: number,
}

export type FunnelStep = {
	-- 1 … 100, unique, the order of the funnel in the Creator Hub analytics. Never renumber a step that was shipped.
	Step: number,
	Name: string,
	Kind: Kind,
	Goal: number,
}

local badges: { Badge } = {
	{ Id = "FirstShiba", BadgeId = 0, Name = "First Shiba", Kind = "Shibas", Goal = 1 },
	{ Id = "Shibas5", BadgeId = 0, Name = "Five Shibas", Kind = "Shibas", Goal = 5 },
	{ Id = "Shibas10", BadgeId = 0, Name = "Ten Shibas", Kind = "Shibas", Goal = 10 },
	{ Id = "Earned1M", BadgeId = 0, Name = "Bonk Millionaire", Kind = "TotalEarned", Goal = 1e6 },
	{ Id = "FirstAscension", BadgeId = 0, Name = "First Ascension", Kind = "Ascensions", Goal = 1 },
	{ Id = "Index10", BadgeId = 0, Name = "Index Collector", Kind = "IndexSeen", Goal = 10 },
	{ Id = "Streak7", BadgeId = 0, Name = "7-Day Streak", Kind = "StreakDay", Goal = 7 },
	{ Id = "FirstParty", BadgeId = 0, Name = "Party Bonker", Kind = "Parties", Goal = 1 },
	{ Id = "RareShiba", BadgeId = 0, Name = "Rare Find", Kind = "RareVariants", Goal = 1 },
}

local funnelSteps: { FunnelStep } = {
	{ Step = 1, Name = "Joined", Kind = "Joined", Goal = 1 },
	-- Roblox counts sessions under 60 s and under 180 s as "first play bounce" (docs/research/ROBLOX_PACING.md).
	{ Step = 2, Name = "Played1Min", Kind = "SessionSeconds", Goal = 60 },
	{ Step = 3, Name = "FirstPurchase", Kind = "Purchases", Goal = 1 },
	{ Step = 4, Name = "Played3Min", Kind = "SessionSeconds", Goal = 180 },
	{ Step = 5, Name = "ThreeShibas", Kind = "Shibas", Goal = 3 },
	{ Step = 6, Name = "TenPurchases", Kind = "Purchases", Goal = 10 },
	{ Step = 7, Name = "Played10Min", Kind = "SessionSeconds", Goal = 600 },
	{ Step = 8, Name = "FiveShibas", Kind = "Shibas", Goal = 5 },
	{ Step = 9, Name = "FirstAscension", Kind = "Ascensions", Goal = 1 },
	-- Came back the next day (the login streak counts days).
	{ Step = 10, Name = "ReturnedDay2", Kind = "StreakDay", Goal = 2 },
}

return {
	-- Seconds between two checks of every player (a check only reads the state).
	CheckInterval = 5,

	Badges = badges,

	Funnel = {
		-- Only players whose save is younger than this are logged: the funnel is about brand-new players, a veteran
		-- joining would otherwise report every step in the first second.
		NewPlayerHours = 72,
		Steps = funnelSteps,
	},
}
