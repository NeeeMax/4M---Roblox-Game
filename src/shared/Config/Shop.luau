--!strict
-- Shop items (docs/GAME_DESIGN.md → Shop). Robux items need a real id from the Creator Hub
-- (Monetization → Passes / Developer Products). While an id is 0, buying it in Studio grants it as a free test
-- purchase; in a live server the button says "Coming soon".
-- Bonk Points are never sold for Robux (coin flips exist): Robux buys boosts, cosmetics and time savers only.

export type PassId = "DoublePoints" | "VIP" | "LuckySticks" | "ExtraShibas"

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
	Kind: "BonkRain" | "Boost" | "TierSkip" | "StarterPack" | "Trophy",
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
}

local passes: { Pass } = {
	{
		Id = "DoublePoints",
		GamePassId = 0,
		DisplayName = "2× Bonk Points",
		Description = "Every bonk pays double. Forever.",
		Robux = 199,
		Color = Color3.fromRGB(255, 190, 40),
	},
	{
		Id = "VIP",
		GamePassId = 0,
		DisplayName = "VIP",
		Description = "+25% points, golden VIP name, VIP trophy, 2 daily spins.",
		Robux = 299,
		Color = Color3.fromRGB(255, 215, 60),
	},
	{
		Id = "LuckySticks",
		GamePassId = 0,
		DisplayName = "Lucky Sticks",
		Description = "Golden sticks (5× points) come 3× as often.",
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
		DisplayName = "2× Points · 30 min",
		Description = "Double points for 30 minutes (stacks with the pass).",
		Robux = 39,
		Color = Color3.fromRGB(255, 200, 40),
		Kind = "Boost",
		Boost = "Points",
		Seconds = 1800,
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
		Description = "2× Points 1 h + 3 Bonk Rains + Starter trophy. Once only!",
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
}

local trophies: { Trophy } = {
	{
		Id = "Wood",
		DisplayName = "Wooden Stick",
		Points = 5000,
		Color = Color3.fromRGB(150, 100, 60),
		Rarity = "Common",
	},
	{
		Id = "Bronze",
		DisplayName = "Bronze Bonk",
		Points = 50000,
		Color = Color3.fromRGB(205, 127, 50),
		Rarity = "Common",
	},
	{
		Id = "Silver",
		DisplayName = "Silver Bonk",
		Points = 500000,
		Color = Color3.fromRGB(200, 205, 220),
		Rarity = "Rare",
	},
	{
		Id = "Gold",
		DisplayName = "Golden Bonk",
		Points = 5000000,
		Color = Color3.fromRGB(255, 200, 40),
		Rarity = "Epic",
	},
	{
		Id = "Galaxy",
		DisplayName = "Galaxy Bonk",
		Points = 100000000,
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
