--!strict
-- Shared type definitions. Changing this file is a contract change: own PR, both approve.

export type UpgradeId = "MoveSpeed" | "Shooters" | "ShooterTier" | "ProjectileTier"

export type HitQuality = "Normal" | "Good" | "Hard" | "Massive" | "Legendary"

export type BoostId = "Points" | "FireRate"

-- Today's daily quests (Config/Hub → Quests). `Day` = days since 1970 (UTC); a new day gets new quests.
export type QuestState = {
	Day: number,
	Ids: { string },
	Progress: { number },
	Claimed: { boolean },
}

-- Login streak (Config/Hub → LoginStreak): Count = day of the 7-day cycle reached on `Day`.
export type StreakState = {
	Day: number,
	Count: number,
	-- Day whose reward was claimed (a new login day makes a new reward claimable).
	ClaimedDay: number,
}

-- Playtime gifts (Config/Hub → Playtime): seconds played on `Day`, and which gifts were claimed that day.
export type PlaytimeState = {
	Day: number,
	Seconds: number,
	Claimed: { boolean },
}

-- Everything saved per player. Created by DataService and sent to the owning client as a copy (StateChanged).
export type PlayerState = {
	BonkPoints: number,
	-- Bonk Points ever earned by playing (not admin gifts); the leaderboard ranks by this.
	TotalEarned: number,
	-- Keyed by UpgradeId. A plain string key because the table also crosses the network and the DataStore.
	UpgradeLevels: { [string]: number },
	ActiveShooters: number,
	-- Daily spins used on SpinDay (days since 1970, UTC).
	SpinDay: number,
	SpinsUsed: number,
	-- BoostId → Unix time the boost runs out.
	Boosts: { [string]: number },
	Quests: QuestState,
	Streak: StreakState,
	Playtime: PlaytimeState,
	-- Trophy id → owned (Config/Shop → Trophies).
	Trophies: { [string]: boolean },
	-- Bonk Rains the player can start (from the shop, wheel or rewards).
	BonkRains: number,
	-- Unix time of the first join (the starter pack offer runs out after Shop.StarterPack.OfferHours).
	FirstJoinAt: number,
	StarterPackBought: boolean,
	-- Game pass id (Config/Shop → Passes key) → owned. Checked with Roblox on every join, not trusted from the save.
	Passes: { [string]: boolean },
	-- Recently granted Robux purchase ids, so a receipt Roblox sends twice is only granted once.
	Receipts: { string },
}

return {}
