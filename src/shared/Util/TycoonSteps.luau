--!strict
-- The floor pads of the street (docs/GAME_DESIGN.md → Street, plots and buttons, "Progression chain"): one row per pad,
-- in walkthrough order. For every Shiba n the chain is
--   Bay n      unlocks Shiba n (it is spawned; at first the player earns with it by clicking/bonking it by hand),
--   Auto n     the Cash Register: automates it,
--   (level)    the Shiba has to reach a level (Street.LevelGate...) before its decoration unlocks,
--   Decor n_k  the parts of its theme (Config/TycoonDecor), in order: REQUIRED,
-- and only then the pad for Shiba n + 1 (its bay and surrounding) shows up. Pure data and formulas, shared by the server
-- (buying, drawing the pads) and the client (texts, the walkthrough arrow).

local EconomyConfig = require(script.Parent.Parent.Config.EconomyConfig)
local TycoonConfig = require(script.Parent.Parent.Config.Tycoon)
local TycoonDecor = require(script.Parent.Parent.Config.TycoonDecor)
local Types = require(script.Parent.Parent.Types)
local TycoonMath = require(script.Parent.TycoonMath)

type TycoonState = Types.TycoonState

export type Step = {
	Id: string,
	Kind: "Bay" | "Automate" | "Decor",
	-- The bay (and Shiba number) the pad belongs to, 1 … Bays.
	Bay: number,
	-- Step ids that must be bought before this pad shows up.
	Needs: { string },
	-- Decor only: the part of the bay's theme (Config/TycoonDecor), its position in the theme's Parts.
	PartIndex: number?,
	PartId: string?,
	-- The Shiba of `Bay` must be at least this level before the pad shows up (the first decor part of a bay).
	LevelGate: number?,
}

local STREET = TycoonConfig.Street

-- Level a Shiba needs before its decor unlocks: Base, plus Step for every five bays, at most Max.
local function levelGate(bay: number): number
	return math.min(STREET.LevelGateMax, STREET.LevelGateBase + STREET.LevelGateStep * math.floor((bay - 1) / 5))
end

local list: { Step } = {}
local decorList: { Step } = {}
local byId: { [string]: Step } = {}

local function add(step: Step)
	table.insert(list, step)
	byId[step.Id] = step
end

-- The id of the last decor part of a bay's theme (what the next Shiba waits for), nil without a theme.
local function lastDecorId(bay: number): string?
	local theme = TycoonDecor.Themes[bay]
	if theme and #theme.Parts > 0 then
		return `Decor{bay}_{theme.Parts[#theme.Parts].Id}`
	end
	return nil
end

-- Order matters: the first MaxPads visible ones are shown, so the pads follow the walkthrough.
for bay = 1, STREET.Bays do
	local needs: { string } = {}
	if bay > 1 then
		-- The next Shiba: the previous one is automated and its decoration is complete.
		table.insert(needs, `Auto{bay - 1}`)
		local lastDecor = lastDecorId(bay - 1)
		if lastDecor then
			table.insert(needs, lastDecor)
		end
	end
	add({ Id = `Bay{bay}`, Kind = "Bay", Bay = bay, Needs = needs })
	add({ Id = `Auto{bay}`, Kind = "Automate", Bay = bay, Needs = { `Bay{bay}` } })

	local theme = TycoonDecor.Themes[bay]
	if theme then
		for index, part in theme.Parts do
			local step: Step = {
				Id = `Decor{bay}_{part.Id}`,
				Kind = "Decor",
				Bay = bay,
				-- The first part follows the automation (and needs the level); every other part the one before it.
				Needs = if index == 1 then { `Auto{bay}` } else { `Decor{bay}_{theme.Parts[index - 1].Id}` },
				PartIndex = index,
				PartId = part.Id,
				LevelGate = if index == 1 then levelGate(bay) else nil,
			}
			add(step)
			table.insert(decorList, step)
		end
	end
end

local TycoonSteps = {
	-- Every pad of the chain in walkthrough order (Shibas, automation and decor).
	List = list,
	-- Only the decor steps (a subset of List), for drawing what was bought.
	DecorList = decorList,
	ById = byId,
	Bays = STREET.Bays,
}

function TycoonSteps.IsBought(tycoon: TycoonState, id: string): boolean
	local steps = tycoon.Steps
	return steps ~= nil and steps[id] == true
end

-- The level the Shiba of bay `bay` has reached (0 without one).
function TycoonSteps.ShibaLevel(tycoon: TycoonState, bay: number): number
	local id = tycoon.Equipped[tostring(bay)]
	local shiba = if id then tycoon.Shibas[id] else nil
	return if shiba then shiba.Level else 0
end

local function needsMet(tycoon: TycoonState, step: Step): boolean
	for _, need in step.Needs do
		if not TycoonSteps.IsBought(tycoon, need) then
			return false
		end
	end
	return true
end

-- The pads to show now: not bought yet, everything they need bought and their level reached, at most Street.MaxPads, in
-- table order.
function TycoonSteps.Visible(tycoon: TycoonState): { Step }
	local visible: { Step } = {}
	for _, step in list do
		if not TycoonSteps.IsBought(tycoon, step.Id) and needsMet(tycoon, step) then
			local gate = step.LevelGate
			if gate == nil or TycoonSteps.ShibaLevel(tycoon, step.Bay) >= gate then
				table.insert(visible, step)
				if #visible >= STREET.MaxPads then
					break
				end
			end
		end
	end
	return visible
end

-- The first step that is held back only by a Shiba's level (nothing to buy yet: the player has to level up), or nil.
function TycoonSteps.Waiting(tycoon: TycoonState): Step?
	for _, step in list do
		local gate = step.LevelGate
		if
			gate ~= nil
			and not TycoonSteps.IsBought(tycoon, step.Id)
			and needsMet(tycoon, step)
			and TycoonSteps.ShibaLevel(tycoon, step.Bay) < gate
		then
			return step
		end
	end
	return nil
end

local function decorPart(step: Step): TycoonDecor.Part?
	local theme = TycoonDecor.Themes[step.Bay]
	local index = step.PartIndex
	return if theme and index then theme.Parts[index] else nil
end

-- What the pad costs right now (an automation gets dearer with every Shiba already automated).
function TycoonSteps.Price(step: Step, tycoon: TycoonState): number
	if step.Kind == "Decor" then
		local part = decorPart(step)
		return if part then math.floor(TycoonMath.TierIncome(step.Bay - 1) * part.PriceSeconds) else 0
	end
	if step.Kind == "Bay" then
		if step.Bay <= 1 then
			return 0
		end
		return math.floor(TycoonMath.TierIncome(step.Bay - 1) * STREET.BaySeconds)
	end
	return TycoonMath.AutomationPrice(step.Bay - 1, TycoonMath.AutomatedCount(tycoon))
end

local function shibaName(bay: number): string
	local def = EconomyConfig.Shibas[bay]
	return if def then def.Name else "Shiba"
end

function TycoonSteps.ShibaName(bay: number): string
	return shibaName(bay)
end

function TycoonSteps.Title(step: Step): string
	if step.Kind == "Decor" then
		local part = decorPart(step)
		return if part then part.Name else "Decor"
	end
	if step.Kind == "Automate" then
		return "Cash Register"
	end
	return if step.Bay == 1 then "First Shiba" else `Expansion {step.Bay}`
end

function TycoonSteps.Description(step: Step): string
	if step.Kind == "Decor" then
		local part = decorPart(step)
		return if part then part.Description else ""
	end
	local name = shibaName(step.Bay)
	if step.Kind == "Automate" then
		return `automates {name}`
	end
	return if step.Bay == 1 then "spawns your first Shiba" else `the plot grows, {name} joins`
end

return TycoonSteps
