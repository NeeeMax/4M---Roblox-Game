--!strict
-- Hub features (docs/GAME_DESIGN.md → Hub): daily spin, coin flip + duels, daily quests, leaderboard, boosts,
-- login streak and playtime gifts.
-- "Hits" as a reward unit = what one normal bonk currently pays the player (projectile tier × Shiba tier),
-- so rewards stay worth it at every stage of the game.

export type SpinSegment = {
	Text: string,
	Kind: "Points" | "Boost" | "BonkRain" | "Nothing",
	-- Points: this many hits' worth. Boost: which boost, for how many seconds.
	Hits: number?,
	Boost: string?,
	Seconds: number?,
	-- Relative chance (the wheel shows each segment's chance in %).
	Weight: number,
	Color: Color3,
}

-- A reward from the login streak or a playtime gift.
export type Reward = {
	Text: string,
	Kind: "Points" | "Boost" | "BonkRain" | "Trophy",
	Hits: number?,
	Boost: string?,
	Seconds: number?,
	Trophy: string?,
}

export type QuestDef = {
	Id: string,
	-- "{n}" is replaced by the goal.
	Text: string,
	-- Event counted by QuestService.Record: "Hit", "HeadHit", "HardHit", "Combo" (highest), "CoinWin", "Spin", "Upgrade",
	-- "Obby" (finished the jump and run).
	Event: string,
	Goal: number,
	RewardHits: number,
}

-- Clockwise from the top. Small wins on purpose: the wheel is a daily treat, not the main income.
local spinSegments: { SpinSegment } = {
	{ Text = "5 Bonks", Kind = "Points", Hits = 5, Weight = 26, Color = Color3.fromRGB(90, 180, 255) },
	{ Text = "Nothing", Kind = "Nothing", Weight = 16, Color = Color3.fromRGB(90, 90, 110) },
	{ Text = "10 Bonks", Kind = "Points", Hits = 10, Weight = 20, Color = Color3.fromRGB(120, 220, 120) },
	{
		Text = "2× Points 5 min",
		Kind = "Boost",
		Boost = "Points",
		Seconds = 300,
		Weight = 12,
		Color = Color3.fromRGB(255, 200, 40),
	},
	{ Text = "20 Bonks", Kind = "Points", Hits = 20, Weight = 12, Color = Color3.fromRGB(190, 110, 255) },
	{
		Text = "2× Fire 5 min",
		Kind = "Boost",
		Boost = "FireRate",
		Seconds = 300,
		Weight = 8,
		Color = Color3.fromRGB(255, 110, 60),
	},
	{ Text = "Bonk Rain", Kind = "BonkRain", Weight = 4, Color = Color3.fromRGB(60, 200, 230) },
	{ Text = "JACKPOT 50", Kind = "Points", Hits = 50, Weight = 2, Color = Color3.fromRGB(255, 60, 120) },
}

-- Day 1 … 7 of the login streak; after day 7 it starts over at day 1.
local streakRewards: { Reward } = {
	{ Text = "10 Bonks", Kind = "Points", Hits = 10 },
	{ Text = "20 Bonks", Kind = "Points", Hits = 20 },
	{ Text = "2× Points 10 min", Kind = "Boost", Boost = "Points", Seconds = 600 },
	{ Text = "40 Bonks", Kind = "Points", Hits = 40 },
	{ Text = "Bonk Rain", Kind = "BonkRain" },
	{ Text = "80 Bonks", Kind = "Points", Hits = 80 },
	{ Text = "Streak Trophy + 150 Bonks", Kind = "Trophy", Trophy = "Streak", Hits = 150 },
}

-- Gifts after this many minutes of play in one UTC day.
local playtimeGifts: { { Minutes: number, Reward: Reward } } = {
	{ Minutes = 5, Reward = { Text = "5 Bonks", Kind = "Points", Hits = 5 } },
	{ Minutes = 10, Reward = { Text = "10 Bonks", Kind = "Points", Hits = 10 } },
	{ Minutes = 20, Reward = { Text = "2× Fire 5 min", Kind = "Boost", Boost = "FireRate", Seconds = 300 } },
	{ Minutes = 30, Reward = { Text = "25 Bonks", Kind = "Points", Hits = 25 } },
	{ Minutes = 60, Reward = { Text = "Bonk Rain", Kind = "BonkRain" } },
}

local quests: { QuestDef } = {
	{ Id = "Catch25", Text = "Catch {n} sticks", Event = "Hit", Goal = 25, RewardHits = 40 },
	{ Id = "Catch60", Text = "Catch {n} sticks", Event = "Hit", Goal = 60, RewardHits = 90 },
	{ Id = "Head10", Text = "Land {n} HEADBONKS", Event = "HeadHit", Goal = 10, RewardHits = 50 },
	{ Id = "Hard5", Text = "Get {n} Hard (or better) bonks", Event = "HardHit", Goal = 5, RewardHits = 60 },
	{ Id = "Combo8", Text = "Reach a x{n} combo", Event = "Combo", Goal = 8, RewardHits = 60 },
	{ Id = "Combo15", Text = "Reach a x{n} combo", Event = "Combo", Goal = 15, RewardHits = 120 },
	{ Id = "Coin2", Text = "Win {n} coin flips", Event = "CoinWin", Goal = 2, RewardHits = 30 },
	{ Id = "Spin1", Text = "Spin the daily wheel", Event = "Spin", Goal = 1, RewardHits = 20 },
	{ Id = "Upgrade3", Text = "Buy {n} upgrades", Event = "Upgrade", Goal = 3, RewardHits = 40 },
	{ Id = "Obby1", Text = "Climb the obby tower", Event = "Obby", Goal = 1, RewardHits = 30 },
}

return {
	DailySpin = {
		-- Free spins per UTC day (VIP: Shop.Pass.VIPDailySpins).
		FreeSpins = 1,
		Segments = spinSegments,
	},

	LoginStreak = {
		Rewards = streakRewards,
	},

	Playtime = {
		Gifts = playtimeGifts,
	},

	CoinFlip = {
		-- Bet sizes as a share of the current Bonk Points (1 = everything).
		BetFractions = { 0.1, 0.25, 0.5, 1 },
		MinBet = 10,
		-- Time the coin spins on screen before the result shows (the server decides instantly).
		FlipTime = 1.5,
	},

	Duel = {
		-- Fixed stake options offered in the duel menu (both players pay the stake, the winner gets both).
		Stakes = { 100, 1000, 10000, 100000 },
		InviteTimeout = 20,
	},

	Quests = {
		PerDay = 3,
		Pool = quests,
	},

	Leaderboard = {
		Size = 10,
		RefreshInterval = 60,
		StoreName = "TotalEarned_v1",
	},

	Boosts = {
		-- Multiplier while a boost runs: Points multiplies rewards, FireRate divides the fire interval.
		Points = 2,
		FireRate = 2,
	},
}
