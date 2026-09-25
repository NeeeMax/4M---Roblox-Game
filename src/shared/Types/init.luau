--!strict
-- Shared type definitions. Changing this file is a contract change: own PR, both approve.

export type UpgradeId = "MoveSpeed" | "Shooters" | "ShooterTier" | "ProjectileTier" | "Basket" | "Intern"

-- Catch quality, by when the stick was caught (Config/EconomyConfig → Bonk): Normal = after it touched the ground,
-- Good = in the air, Perfect = in the air just before it lands.
export type HitQuality = "Normal" | "Good" | "Perfect"

-- Who caught a stick for the player (automation, Config/EconomyConfig → Automation).
export type AutomationSource = "Basket" | "Intern"

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

-- Offline income (Shiba Bank, Config/Economy → OfflineBank): while away, the Shibas keep earning a share of the
-- player's recent income. `Pending` waits for the player to claim it in the "Welcome back" popup.
export type BankState = {
	-- Unix time the player was last online (saved on leave / autosave).
	LastSeenAt: number,
	-- Bonk Points per minute earned by playing, averaged recently; the offline rate is a share of it.
	IncomePerMinute: number,
	-- Offline earnings not claimed yet.
	Pending: number,
	-- Seconds offline that produced `Pending`.
	PendingSeconds: number,
	-- Bonk Points per minute earned by the basket and the intern, averaged recently (drives offline earnings).
	AutomationPerMinute: number,
}

-- First-session tutorial (onboarding). Step counts the purchases the guided hints have walked the player through;
-- FirstBonkDone = the one-time first-bonk bonus was paid.
export type TutorialState = {
	Step: number,
	FirstBonkDone: boolean,
}

-- Jump and run on the hub (Config/Obby).
export type ObbyState = {
	-- Unix time of the last rewarded finish (reward cooldown).
	LastRewardAt: number,
	-- Best finishing time in seconds (0 = never finished).
	BestTime: number,
}

-- Shiba-Index (Config/Index): collection book of Shiba tiers, projectile tiers, trophies …
export type IndexState = {
	-- Entry id → discovered.
	Seen: { [string]: boolean },
	-- Entry id → discovery reward claimed.
	Claimed: { [string]: boolean },
}

-- Settings menu (client look and sound only; saved so they survive rejoins).
export type SettingsState = {
	Music: number,
	Effects: number,
	-- Show "NEW" hints and "you can afford …" popups.
	Hints: boolean,
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
	Bank: BankState,
	Obby: ObbyState,
	Index: IndexState,
	Settings: SettingsState,
	-- Rebirths done (Config/EconomyConfig → Rebirth): each one raises the income multiplier for good.
	Rebirths: number,
	Tutorial: TutorialState,
}

return {}
