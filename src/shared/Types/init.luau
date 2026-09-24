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

-- Everything saved per player. Created by DataService and sent to the owning client as a copy (StateChanged).
export type PlayerState = {
	BonkPoints: number,
	-- Bonk Points ever earned by playing (not admin gifts); the leaderboard ranks by this.
	TotalEarned: number,
	-- Keyed by UpgradeId. A plain string key because the table also crosses the network and the DataStore.
	UpgradeLevels: { [string]: number },
	ActiveShooters: number,
	-- Unix time of the last daily spin (0 = never).
	LastSpinAt: number,
	-- BoostId → Unix time the boost runs out.
	Boosts: { [string]: number },
	Quests: QuestState,
}

return {}
