--!strict
-- Shared type definitions. Changing this file is a contract change: own PR, both approve.

export type UpgradeId = "MoveSpeed" | "ProjectileSize" | "FireRate" | "Shooters"

export type HitQuality = "Normal" | "Good" | "Hard" | "Massive" | "Legendary"

-- Everything saved per player. Created by DataService; changed only by EconomyService and UpgradeService.
export type PlayerState = {
	BonkPoints: number,
	-- Keyed by UpgradeId. A plain string key because the table also crosses the network and the DataStore.
	UpgradeLevels: { [string]: number },
	ActiveShooters: number,
}

return {}
