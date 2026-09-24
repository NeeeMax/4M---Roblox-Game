--!strict
-- Finds 3D models built in Studio (ReplicatedStorage.Assets, owned by Marco — see CONTRIBUTING.md) and prepares
-- copies of them. Every caller has a fallback, so the game runs without any assets.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local FOLDER_NAME = "Assets"

local Assets = {}

-- Whether ReplicatedStorage.Assets.<name> exists.
function Assets.Has(name: string): boolean
	local folder = ReplicatedStorage:FindFirstChild(FOLDER_NAME)
	return folder ~= nil and folder:FindFirstChild(name) ~= nil
end

-- A fresh copy of the asset as a Model (a single part gets wrapped in one), or nil if it doesn't exist.
function Assets.CloneModel(name: string): Model?
	local folder = ReplicatedStorage:FindFirstChild(FOLDER_NAME)
	local source = if folder then folder:FindFirstChild(name) else nil
	if not source then
		return nil
	end
	local copy = source:Clone()
	if copy:IsA("Model") then
		return copy
	end
	local model = Instance.new("Model")
	model.Name = name
	copy.Parent = model
	return model
end

-- Scales the model so its longest side (or its height, if `useHeight`) is `size` studs.
function Assets.ScaleTo(model: Model, size: number, useHeight: boolean?)
	local extents = model:GetExtentsSize()
	local current = if useHeight then extents.Y else math.max(extents.X, extents.Y, extents.Z)
	if current > 0 then
		model:ScaleTo(model:GetScale() * size / current)
	end
end

-- Makes every part a pure visual: no collisions, touches or spatial queries.
function Assets.MakeVisualOnly(model: Model, anchored: boolean)
	for _, descendant in model:GetDescendants() do
		if descendant:IsA("BasePart") then
			descendant.Anchored = anchored
			descendant.CanCollide = false
			descendant.CanTouch = false
			descendant.CanQuery = false
			descendant.Massless = true
		end
	end
end

return Assets
