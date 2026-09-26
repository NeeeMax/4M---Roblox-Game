--!strict
-- Shop items (docs/GAME_DESIGN.md → Shop). Robux items need a real id from the Creator Hub
-- (Monetization → Passes / Developer Products). While an id is 0, buying it in Studio grants it as a free test
-- purchase; in a live server the button says "Coming soon".
-- Bonk Points are never sold for Robux (coin flips exist): Robux buys boosts, cosmetics and time savers only.

local EconomyConfig = require(script.Parent.EconomyConfig)

-- Trophy prices come from EconomyConfig (each about as much as the Shiba bought around then).
local TROPHY_PRICES = EconomyConfig.TrophyThresholds

export type PassId = "DoublePoints" | "VIP" | "LuckySticks" | "ExtraShibas" | "Manage" | "RunFaster" | "StackUpgrade"

export type Pass = {
	Id: PassId,
	-- Game pass id from the Creator Hub.
	GamePassId: number,
	DisplayName: string,
	Description: string,
	-- Shown price; the real price is set on the Creator Hub (keep both the same).
	Robux: number,
	Color: Color3,
}

export type Product = {
	Id: string,
	-- Developer product id from the Creator Hub.
	ProductId: number,
	DisplayName: string,
	Description: string,
	Robux: number,
	Color: Color3,
	-- What buying it gives (ShopService.Grant).
	-- InstantUpgrade: one level of `Upgrade` (an UpgradeId) right away. DoubleOffline: doubles the pending
	-- offline earnings.
	Kind: "BonkRain" | "Boost" | "TierSkip" | "StarterPack" | "Trophy" | "InstantUpgrade" | "DoubleOffline",
	Upgrade: string?,
	Boost: string?,
	Seconds: number?,
	Trophy: string?,
}

export type Trophy = {
	Id: string,
	DisplayName: string,
	-- Bonk Points price, or nil if it is Robux-only (then a Product with Kind "Trophy" sells it) or a reward.
	Points: number?,
	Color: Color3,
	-- Model: ReplicatedStorage.Assets.Trophy_<Id>; without it a coloured placeholder cup.
	Rarity: "Common" | "Rare" | "Epic" | "Legendary" | "Exclusive",
	-- Shown in the Shiba-Index but not needed for its completion bonus (e.g. it needs a friend). Default false.
	Optional: boolean?,
}

local passes: { Pass } = {
	{
		Id = "DoublePoints",
		GamePassId = 0,
		DisplayName = "2× Bonk Dollars",
		Description = "Every bonk pays double. Forever.",
		Robux = 199,
		Color = Color3.fromRGB(255, 190, 40),
	},
	{
		Id = "VIP",
		GamePassId = 0,
		DisplayName = "VIP",
		Description = "+25% Bonk Dollars, golden VIP name, VIP trophy, 2 daily spins.",
		Robux = 299,
		Color = Color3.fromRGB(255, 215, 60),
	},
	{
		Id = "LuckySticks",
		GamePassId = 0,
		DisplayName = "Lucky Sticks",
		Description = "Golden sticks (5× Bonk Dollars) come 3× as often.",
		Robux = 149,
		Color = Color3.fromRGB(120, 230, 120),
	},
	{
		Id = "ExtraShibas",
		GamePassId = 0,
		DisplayName = "+2 Shiba Slots",
		Description = "Up to 10 Shibas around your island instead of 8.",
		Robux = 249,
		Color = Color3.fromRGB(255, 140, 60),
	},
	{
		Id = "Manage",
		GamePassId = 0,
		DisplayName = "Manage",
		Description = "Manage all income sources from one place: open the upgrade menu anywhere.",
		Robux = 199,
		Color = Color3.fromRGB(255, 190, 60),
	},
	{
		Id = "RunFaster",
		GamePassId = 0,
		DisplayName = "Run Faster",
		Description = "Gotta go fast! Walk speed x1.5.",
		Robux = 99,
		Color = Color3.fromRGB(240, 240, 250),
	},
	{
		Id = "StackUpgrade",
		GamePassId = 0,
		DisplayName = "Stack Upgrade",
		Description = "Upgrade multiple times at once (hold E / buy x10).",
		Robux = 149,
		Color = Color3.fromRGB(255, 220, 60),
	},
}

local products: { Product } = {
	{
		Id = "BonkRain",
		ProductId = 0,
		DisplayName = "Bonk Rain",
		Description = "30 seconds of sticks raining on your field!",
		Robux = 49,
		Color = Color3.fromRGB(90, 180, 255),
		Kind = "BonkRain",
	},
	{
		Id = "PointsBoost30",
		ProductId = 0,
		DisplayName = "2× Dollars · 30 min",
		Description = "Double Bonk Dollars for 30 minutes (stacks with the pass).",
		Robux = 39,
		Color = Color3.fromRGB(255, 200, 40),
		Kind = "Boost",
		Boost = "Points",
		Seconds = 1800,
	},
	{
		Id = "Magnet15",
		ProductId = 0,
		DisplayName = "Magnet · 15 min",
		Description = "A magnet catches every stick within 10 studs of you for 15 minutes. No aiming needed!",
		Robux = 49,
		Color = Color3.fromRGB(120, 200, 255),
		Kind = "Boost",
		Boost = "Magnet",
		Seconds = 900,
	},
	{
		Id = "FireBoost30",
		ProductId = 0,
		DisplayName = "2× Fire Rate · 30 min",
		Description = "Your Shibas throw twice as fast for 30 minutes.",
		Robux = 39,
		Color = Color3.fromRGB(255, 110, 60),
		Kind = "Boost",
		Boost = "FireRate",
		Seconds = 1800,
	},
	{
		Id = "TierSkip",
		ProductId = 0,
		DisplayName = "Shiba Tier Skip",
		Description = "Instantly evolve your Shibas to the next tier.",
		Robux = 99,
		Color = Color3.fromRGB(190, 110, 255),
		Kind = "TierSkip",
	},
	{
		Id = "StarterPack",
		ProductId = 0,
		DisplayName = "Starter Pack",
		Description = "2× Dollars 1 h + 3 Bonk Rains + Starter trophy. Once only!",
		Robux = 49,
		Color = Color3.fromRGB(80, 220, 160),
		Kind = "StarterPack",
	},
	{
		Id = "TrophyDiamond",
		ProductId = 0,
		DisplayName = "Diamond Bonk Trophy",
		Description = "Exclusive trophy for your island.",
		Robux = 99,
		Color = Color3.fromRGB(90, 220, 255),
		Kind = "Trophy",
		Trophy = "Diamond",
	},
	{
		Id = "TrophyRainbow",
		ProductId = 0,
		DisplayName = "Rainbow Shiba Trophy",
		Description = "The rarest trophy in the game.",
		Robux = 249,
		Color = Color3.fromRGB(255, 90, 200),
		Kind = "Trophy",
		Trophy = "Rainbow",
	},
	{
		Id = "DoubleOffline",
		ProductId = 0,
		DisplayName = "Double Offline Earnings",
		Description = "Double what your Shibas earned while you were away.",
		Robux = 39,
		Color = Color3.fromRGB(80, 220, 120),
		Kind = "DoubleOffline",
	},
	{
		Id = "InstantShooterTier",
		ProductId = 0,
		DisplayName = "Instant Shiba Tier",
		Description = "Buy the next Shiba tier right now.",
		Robux = 99,
		Color = Color3.fromRGB(190, 110, 255),
		Kind = "InstantUpgrade",
		Upgrade = "ShooterTier",
	},
	{
		Id = "InstantProjectileTier",
		ProductId = 0,
		DisplayName = "Instant Projectile Tier",
		Description = "Buy the next projectile tier right now.",
		Robux = 79,
		Color = Color3.fromRGB(255, 200, 40),
		Kind = "InstantUpgrade",
		Upgrade = "ProjectileTier",
	},
	{
		Id = "InstantShooters",
		ProductId = 0,
		DisplayName = "Instant Shiba",
		Description = "Get your next Shiba right now.",
		Robux = 49,
		Color = Color3.fromRGB(255, 140, 60),
		Kind = "InstantUpgrade",
		Upgrade = "Shooters",
	},
	{
		Id = "InstantMoveSpeed",
		ProductId = 0,
		DisplayName = "Instant Speed",
		Description = "Buy the next Move Speed level right now.",
		Robux = 25,
		Color = Color3.fromRGB(80, 200, 255),
		Kind = "InstantUpgrade",
		Upgrade = "MoveSpeed",
	},
}

local trophies: { Trophy } = {
	{
		Id = "Wood",
		DisplayName = "Wooden Stick",
		Points = TROPHY_PRICES.Wood,
		Color = Color3.fromRGB(150, 100, 60),
		Rarity = "Common",
	},
	{
		Id = "Bronze",
		DisplayName = "Bronze Bonk",
		Points = TROPHY_PRICES.Bronze,
		Color = Color3.fromRGB(205, 127, 50),
		Rarity = "Common",
	},
	{
		Id = "Silver",
		DisplayName = "Silver Bonk",
		Points = TROPHY_PRICES.Silver,
		Color = Color3.fromRGB(200, 205, 220),
		Rarity = "Rare",
	},
	{
		Id = "Gold",
		DisplayName = "Golden Bonk",
		Points = TROPHY_PRICES.Gold,
		Color = Color3.fromRGB(255, 200, 40),
		Rarity = "Epic",
	},
	{
		Id = "Galaxy",
		DisplayName = "Galaxy Bonk",
		Points = TROPHY_PRICES.Galaxy,
		Color = Color3.fromRGB(150, 80, 255),
		Rarity = "Legendary",
	},
	{
		Id = "Starter",
		DisplayName = "Starter Trophy",
		Points = nil,
		Color = Color3.fromRGB(80, 220, 160),
		Rarity = "Exclusive",
	},
	{
		Id = "Streak",
		DisplayName = "7-Day Streak",
		Points = nil,
		Color = Color3.fromRGB(255, 120, 60),
		Rarity = "Exclusive",
	},
	{
		Id = "VIP",
		DisplayName = "VIP Trophy",
		Points = nil,
		Color = Color3.fromRGB(255, 215, 60),
		Rarity = "Exclusive",
	},
	{
		Id = "Diamond",
		DisplayName = "Diamond Bonk",
		Points = nil,
		Color = Color3.fromRGB(90, 220, 255),
		Rarity = "Exclusive",
	},
	{
		Id = "Rainbow",
		DisplayName = "Rainbow Shiba",
		Points = nil,
		Color = Color3.fromRGB(255, 90, 200),
		Rarity = "Exclusive",
	},
	-- Social + Bonk Party (feat/social-party): rewards, never sold.
	{
		-- Inviter and invited friend, the first time a friend joins through an invite (EconomyConfig.Social).
		Id = "BonkBuddies",
		DisplayName = "Bonk Buddies",
		Points = nil,
		Color = Color3.fromRGB(255, 150, 60),
		Rarity = "Exclusive",
		Optional = true,
	},
	{
		-- Weekend Bonk Party quest (EconomyConfig.Party); the island sign counts parties ("×3").
		Id = "Party",
		DisplayName = "Bonk Party",
		Points = nil,
		Color = Color3.fromRGB(255, 90, 200),
		Rarity = "Exclusive",
	},
}

local Shop = {
	Passes = passes,
	Products = products,
	Trophies = trophies,

	StarterPack = {
		-- New players see the offer for this long after their first join.
		OfferHours = 48,
		PointsBoostSeconds = 3600,
		BonkRains = 3,
		Trophy = "Starter",
	},

	BonkRain = {
		Seconds = 30,
		-- Sticks per second on the field during a rain.
		Rate = 5,
		-- Start height above the field.
		DropHeight = 45,
	},

	Pass = {
		DoublePointsMultiplier = 2,
		VIPMultiplier = 1.25,
		VIPDailySpins = 2,
		LuckyGoldenChance = 0.15,
		ExtraShibas = 2,
		-- Magnet boost (AutoCatchService, product "Magnet15", timed): every AutoCatchInterval seconds, sticks within
		-- AutoCatchRadius studs of the character are collected as a Normal bonk (no head bonus; the combo still counts).
		AutoCatchRadius = 10,
		AutoCatchInterval = 0.25,
	},
}

function Shop.GetPass(id: string): Pass?
	for _, pass in passes do
		if pass.Id == id then
			return pass
		end
	end
	return nil
end

function Shop.GetProduct(id: string): Product?
	for _, product in products do
		if product.Id == id then
			return product
		end
	end
	return nil
end

function Shop.GetTrophy(id: string): Trophy?
	for _, trophy in trophies do
		if trophy.Id == id then
			return trophy
		end
	end
	return nil
end

return Shop
