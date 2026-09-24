--!strict
-- Hub features (docs/GAME_DESIGN.md → Hub): daily spin, coin flip + duels, daily quests, leaderboard, boosts.
-- "Hits" as a reward unit = what one normal bonk currently pays the player (projectile tier × Shiba tier),
-- so rewards stay worth it at every stage of the game.

export type SpinSegment = {
	Text: string,
	Kind: "Points" | "Boost",
	-- Points: this many hits' worth. Boost: which boost, for how many seconds.
	Hits: number?,
	Boost: string?,
	Seconds: number?,
	-- Relative chance.
	Weight: number,
	Color: Color3,
}

export type QuestDef = {
	Id: string,
	-- "{n}" is replaced by the goal.
	Text: string,
	-- Event counted by QuestService.Record: "Hit", "HeadHit", "HardHit", "Combo" (highest), "CoinWin", "Spin", "Upgrade".
	Event: string,
	Goal: number,
	RewardHits: number,
}

local spinSegments: { SpinSegment } = {
	{ Text = "25 Bonks", Kind = "Points", Hits = 25, Weight = 30, Color = Color3.fromRGB(90, 180, 255) },
	{
		Text = "2× Points 10 min",
		Kind = "Boost",
		Boost = "Points",
		Seconds = 600,
		Weight = 15,
		Color = Color3.fromRGB(255, 200, 40),
	},
	{ Text = "50 Bonks", Kind = "Points", Hits = 50, Weight = 22, Color = Color3.fromRGB(120, 220, 120) },
	{
		Text = "2× Fire Rate 10 min",
		Kind = "Boost",
		Boost = "FireRate",
		Seconds = 600,
		Weight = 15,
		Color = Color3.fromRGB(255, 110, 60),
	},
	{ Text = "100 Bonks", Kind = "Points", Hits = 100, Weight = 12, Color = Color3.fromRGB(190, 110, 255) },
	{ Text = "JACKPOT 500", Kind = "Points", Hits = 500, Weight = 2, Color = Color3.fromRGB(255, 60, 120) },
	{
		Text = "2× Points 30 min",
		Kind = "Boost",
		Boost = "Points",
		Seconds = 1800,
		Weight = 4,
		Color = Color3.fromRGB(255, 230, 120),
	},
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
}

return {
	DailySpin = {
		Cooldown = 24 * 60 * 60,
		Segments = spinSegments,
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
