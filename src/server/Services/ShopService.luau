--!strict
-- The shop (Config/Shop): game passes, developer products (Robux) and trophies (Bonk Points).
-- Robux: MarketplaceService prompts the purchase; ProcessReceipt grants products exactly once per receipt
-- (handled receipt ids are saved). Pass ownership is checked with Roblox on every join.
-- While an item's Roblox id is still 0, buying it in Studio grants it as a free test purchase.

local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Format = require(ReplicatedStorage.Shared.Util.Format)
local Net = require(ReplicatedStorage.Shared.Net)
local RateLimiter = require(ReplicatedStorage.Shared.Util.RateLimiter)
local Shop = require(ReplicatedStorage.Shared.Config.Shop)
local Types = require(ReplicatedStorage.Shared.Types)
local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)

local BoostService = require(script.Parent.BoostService)
local DataService = require(script.Parent.DataService)
local EconomyService = require(script.Parent.EconomyService)
local NotifyService = require(script.Parent.NotifyService)
local RainService = require(script.Parent.RainService)
local UpgradeService = require(script.Parent.UpgradeService)

local MAX_RECEIPTS = 50
local TROPHY_PREFIX = "Trophy_"

local buyLimiter = RateLimiter.New(3, 1)

local ShopService = {}

local function isStudioTest(robloxId: number): boolean
	return robloxId == 0 and RunService:IsStudio()
end

local function setPass(player: Player, id: string, owned: boolean)
	local state = DataService.GetState(player)
	if not state then
		return
	end
	if owned then
		state.Passes[id] = true
	else
		state.Passes[id] = nil
	end
	if owned and id == "VIP" then
		state.Trophies.VIP = true
	end
	DataService.Replicate(player)
end

-- Why this product can't be bought right now, or nil.
local function blockedReason(player: Player, product: Shop.Product): string?
	local state = DataService.GetState(player)
	if not state then
		return "Still loading"
	end
	if product.Kind == "TierSkip" then
		local level = state.UpgradeLevels.ShooterTier or 0
		if level >= Upgrades.GetMaxLevel("ShooterTier", state.Passes) then
			return "Your Shibas are already at the top tier"
		end
	elseif product.Kind == "StarterPack" and state.StarterPackBought then
		return "You already have the Starter Pack"
	elseif product.Kind == "Trophy" and product.Trophy and state.Trophies[product.Trophy] then
		return "You already own this trophy"
	end
	return nil
end

-- Gives what a developer product contains. Returns false if it couldn't (the receipt is then retried by Roblox).
function ShopService.Grant(player: Player, product: Shop.Product): boolean
	local state = DataService.GetState(player)
	if not state then
		return false
	end
	if product.Kind == "BonkRain" then
		state.BonkRains += 1
		DataService.Replicate(player)
		RainService.TryStart(player)
	elseif product.Kind == "Boost" and product.Boost and product.Seconds then
		BoostService.Give(player, product.Boost :: Types.BoostId, product.Seconds)
	elseif product.Kind == "TierSkip" then
		UpgradeService.SetLevel(player, "ShooterTier", UpgradeService.GetLevel(player, "ShooterTier") + 1)
	elseif product.Kind == "StarterPack" then
		state.StarterPackBought = true
		state.BonkRains += Shop.StarterPack.BonkRains
		state.Trophies[Shop.StarterPack.Trophy] = true
		BoostService.Give(player, "Points", Shop.StarterPack.PointsBoostSeconds)
	elseif product.Kind == "Trophy" and product.Trophy then
		state.Trophies[product.Trophy] = true
	end
	DataService.Replicate(player)
	NotifyService.Send(player, `Thanks for buying {product.DisplayName}!`, "Good")
	return true
end

local function productByRobloxId(productId: number): Shop.Product?
	for _, product in Shop.Products do
		if product.ProductId == productId and productId ~= 0 then
			return product
		end
	end
	return nil
end

local function processReceipt(receipt: { [string]: any }): Enum.ProductPurchaseDecision
	local player = Players:GetPlayerByUserId(receipt.PlayerId)
	local state = if player then DataService.GetState(player) else nil
	local product = productByRobloxId(receipt.ProductId)
	if not player or not state or not product then
		-- Not in this server or still loading: Roblox tries again later.
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	local purchaseId = tostring(receipt.PurchaseId)
	if table.find(state.Receipts, purchaseId) then
		return Enum.ProductPurchaseDecision.PurchaseGranted
	end
	if not ShopService.Grant(player, product) then
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	table.insert(state.Receipts, purchaseId)
	while #state.Receipts > MAX_RECEIPTS do
		table.remove(state.Receipts, 1)
	end
	DataService.SaveNow(player)
	return Enum.ProductPurchaseDecision.PurchaseGranted
end

local function buyPass(player: Player, pass: Shop.Pass)
	if ShopService.HasPass(player, pass.Id) then
		NotifyService.Send(player, "You already own this pass", "Info")
	elseif pass.GamePassId > 0 then
		MarketplaceService:PromptGamePassPurchase(player, pass.GamePassId)
	elseif isStudioTest(pass.GamePassId) then
		setPass(player, pass.Id, true)
		NotifyService.Send(player, `Studio test: {pass.DisplayName} granted (no pass id yet)`, "Info")
	else
		NotifyService.Send(player, "Coming soon!", "Info")
	end
end

local function buyProduct(player: Player, product: Shop.Product)
	local reason = blockedReason(player, product)
	if reason then
		NotifyService.Send(player, reason, "Bad")
	elseif product.ProductId > 0 then
		MarketplaceService:PromptProductPurchase(player, product.ProductId)
	elseif isStudioTest(product.ProductId) then
		ShopService.Grant(player, product)
		NotifyService.Send(player, "Studio test purchase (no product id yet)", "Info")
	else
		NotifyService.Send(player, "Coming soon!", "Info")
	end
end

local function buyTrophy(player: Player, trophy: Shop.Trophy)
	local state = DataService.GetState(player)
	if not state or not trophy.Points then
		return
	end
	if state.Trophies[trophy.Id] then
		NotifyService.Send(player, "You already own this trophy", "Info")
		return
	end
	if not EconomyService.TrySpend(player, trophy.Points) then
		NotifyService.Send(player, `You need {Format.Number(trophy.Points - state.BonkPoints)} more Bonk Points`, "Bad")
		return
	end
	state.Trophies[trophy.Id] = true
	DataService.Replicate(player)
	NotifyService.Send(player, `{trophy.DisplayName} added to your island!`, "Good")
end

local function onShopBuy(player: Player, itemId: unknown)
	if not RateLimiter.Allow(buyLimiter, player) or typeof(itemId) ~= "string" then
		return
	end
	local pass = Shop.GetPass(itemId)
	if pass then
		buyPass(player, pass)
		return
	end
	local product = Shop.GetProduct(itemId)
	if product then
		buyProduct(player, product)
		return
	end
	if string.sub(itemId, 1, #TROPHY_PREFIX) == TROPHY_PREFIX then
		local trophy = Shop.GetTrophy(string.sub(itemId, #TROPHY_PREFIX + 1))
		if trophy then
			buyTrophy(player, trophy)
		end
	end
end

function ShopService.HasPass(player: Player, id: string): boolean
	local state = DataService.GetState(player)
	return state ~= nil and state.Passes[id] == true
end

-- Admin testing tool: toggles a pass on/off for this session.
function ShopService.TogglePass(player: Player, id: string)
	if Shop.GetPass(id) then
		setPass(player, id, not ShopService.HasPass(player, id))
	end
end

-- Admin testing tool: makes the starter pack buyable again and the offer show.
function ShopService.ResetStarterPack(player: Player)
	local state = DataService.GetState(player)
	if state then
		state.StarterPackBought = false
		state.FirstJoinAt = os.time()
		DataService.Replicate(player)
	end
end

-- Asks Roblox which passes the player owns. Passes without an id keep their saved (Studio test) value in Studio.
local function refreshPasses(player: Player, state: Types.PlayerState)
	for _, pass in Shop.Passes do
		if pass.GamePassId > 0 then
			local ok, owned = pcall(function()
				return MarketplaceService:UserOwnsGamePassAsync(player.UserId, pass.GamePassId)
			end)
			if ok then
				if owned then
					state.Passes[pass.Id] = true
				else
					state.Passes[pass.Id] = nil
				end
			end
		elseif not RunService:IsStudio() then
			state.Passes[pass.Id] = nil
		end
	end
	if state.Passes.VIP then
		state.Trophies.VIP = true
	end
	DataService.Replicate(player)
end

-- Golden "VIP" above the heads of VIP owners (everyone sees it).
local function addVipTag(player: Player, character: Model)
	if not ShopService.HasPass(player, "VIP") then
		return
	end
	local head = character:WaitForChild("Head", 10)
	if not head or not head:IsA("BasePart") or head:FindFirstChild("VipTag") then
		return
	end
	local tag = Instance.new("BillboardGui")
	tag.Name = "VipTag"
	tag.Size = UDim2.fromOffset(90, 30)
	tag.StudsOffset = Vector3.new(0, 2.6, 0)
	tag.MaxDistance = 120
	tag.Parent = head
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = Color3.fromRGB(255, 215, 60)
	label.Text = "VIP"
	label.Parent = tag
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 2
	stroke.Color = Color3.fromRGB(90, 60, 0)
	stroke.Parent = label
end

function ShopService.Start()
	MarketplaceService.ProcessReceipt = processReceipt
	Net.Get(Net.ShopBuy).OnServerEvent:Connect(onShopBuy)
	MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(player, gamePassId, purchased)
		if not purchased then
			return
		end
		for _, pass in Shop.Passes do
			if pass.GamePassId == gamePassId then
				setPass(player, pass.Id, true)
				NotifyService.Send(player, `Thanks for buying {pass.DisplayName}!`, "Good")
				if player.Character then
					addVipTag(player, player.Character)
				end
			end
		end
	end)
	DataService.OnLoaded(function(player, state)
		refreshPasses(player, state)
		if player.Character then
			addVipTag(player, player.Character)
		end
	end)
	local function onPlayerAdded(player: Player)
		player.CharacterAdded:Connect(function(character)
			addVipTag(player, character)
		end)
	end
	Players.PlayerAdded:Connect(onPlayerAdded)
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		RateLimiter.Remove(buyLimiter, player)
	end)
end

return ShopService
