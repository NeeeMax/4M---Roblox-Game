--!strict
-- The floor pads of the street (docs/GAME_DESIGN.md → Street, plots and buttons, "Gameplay flow"). For every Shiba n:
--   Bay n      the pad that spawns Shiba n (n = 1: the first, free one). The player earns by standing in front of the Shiba
--              and clicking it: the Shiba bonks them and pays.
--   Decor n_i  the pieces of the Shiba's themed surrounding (Config/TycoonDecor), 10 to 30 pads depending on the tier. They
--              are bought in TWO parallel chains (odd and even pieces), so two decor pads are visible at once; buying one
--              reveals the next of its chain. All of them are needed.
--   Auto n     separate from the decor, next to the Shiba: the Bonk Intern that gets bonked automatically. Optional.
--   Ascend     one repeatable pad (not in List / ById: it is never "bought"): shown once the best Shiba of the run reaches
--              AscendRequirement(ascensions) (Config/Tycoon → Ascension). The server resets the plot (TycoonService).
-- Only when ALL decor of Shiba n is bought, the pad of Shiba n + 1 shows up. Pure data and formulas, shared by the server
-- (buying, drawing the pads) and the client (texts, the walkthrough arrow).

local EconomyConfig = require(script.Parent.Parent.Config.EconomyConfig)
local TycoonConfig = require(script.Parent.Parent.Config.Tycoon)
local TycoonDecor = require(script.Parent.Parent.Config.TycoonDecor)
local Types = require(script.Parent.Parent.Types)
local TycoonMath = require(script.Parent.TycoonMath)

type TycoonState = Types.TycoonState

export type Step = {
	Id: string,
	Kind: "Bay" | "Automate" | "Decor" | "Ascend",
	-- The bay (and Shiba number) the pad belongs to, 1 … Bays.
	Bay: number,
	-- Step ids that must be bought before this pad shows up.
	Needs: { string },
	-- Decor only: the part of the bay's theme (Config/TycoonDecor), its position in the theme's Parts.
	PartIndex: number?,
	PartId: string?,
}

local STREET = TycoonConfig.Street
-- Decor is bought in this many parallel chains (so this many decor pads are visible at the same time).
local CHAINS = STREET.DecorChains

local list: { Step } = {}
local decorList: { Step } = {}
local byId: { [string]: Step } = {}

local function add(step: Step)
	table.insert(list, step)
	byId[step.Id] = step
end

local function decorId(bay: number, partId: string): string
	return `Decor{bay}_{partId}`
end

-- What the next Shiba waits for: the end of every decor chain of the bay's theme (without a theme: just the bay itself).
local function finishedNeeds(bay: number): { string }
	local theme = TycoonDecor.Themes[bay]
	local needs: { string } = {}
	if theme and #theme.Parts > 0 then
		local count = #theme.Parts
		for index = math.max(1, count - CHAINS + 1), count do
			table.insert(needs, decorId(bay, theme.Parts[index].Id))
		end
	else
		table.insert(needs, `Bay{bay}`)
	end
	return needs
end

-- Order matters: the first MaxPads visible Bay/Decor pads are shown, so the pads follow the flow.
for bay = 1, STREET.Bays do
	add({ Id = `Bay{bay}`, Kind = "Bay", Bay = bay, Needs = if bay > 1 then finishedNeeds(bay - 1) else {} })
	add({ Id = `Auto{bay}`, Kind = "Automate", Bay = bay, Needs = { `Bay{bay}` } })

	local theme = TycoonDecor.Themes[bay]
	if theme then
		for index, part in theme.Parts do
			local step: Step = {
				Id = decorId(bay, part.Id),
				Kind = "Decor",
				Bay = bay,
				-- The first pieces of every chain follow the Shiba; every other piece the one CHAINS before it.
				Needs = if index <= CHAINS then { `Bay{bay}` } else { decorId(bay, theme.Parts[index - CHAINS].Id) },
				PartIndex = index,
				PartId = part.Id,
			}
			add(step)
			table.insert(decorList, step)
		end
	end
end

-- Id of the Ascension pad. It is not in ById (so it is never saved in tycoon.Steps); TycoonService.Actions.BuyStep knows it.
local ASCEND_ID = "Ascend"
local ascendStep: Step = { Id = ASCEND_ID, Kind = "Ascend", Bay = 0, Needs = {} }

local TycoonSteps = {
	AscendId = ASCEND_ID,
	AscendStep = ascendStep,
	-- Every pad in flow order (Shibas, decor and the interns).
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

local function needsMet(tycoon: TycoonState, step: Step): boolean
	for _, need in step.Needs do
		if not TycoonSteps.IsBought(tycoon, need) then
			return false
		end
	end
	return true
end

-- The highest Shiba number (bay) the player owns in this run: tier + 1 of the best Shiba, 0 without one.
function TycoonSteps.BestShiba(tycoon: TycoonState): number
	local best = 0
	for _, shiba in tycoon.Shibas do
		best = math.max(best, shiba.Tier + 1)
	end
	return best
end

-- The Shiba number the player must own for the next Ascension: StreetFirstShiba + StreetShibaStep per Ascension done, at most Bays.
function TycoonSteps.AscendRequirement(ascensions: number): number
	local rule = TycoonConfig.Ascension
	return math.min(STREET.Bays, rule.StreetFirstShiba + rule.StreetShibaStep * math.max(0, ascensions))
end

-- Whether the Ascension pad is available (street mode only).
function TycoonSteps.CanAscend(tycoon: TycoonState): boolean
	return tycoon.Street == true and TycoonSteps.BestShiba(tycoon) >= TycoonSteps.AscendRequirement(tycoon.Ascensions)
end

-- The pads to show now: not bought yet and everything they need bought. At most Street.MaxPads Shiba/decor pads (in flow
-- order); the intern pads (optional, one beside each Shiba) and the Ascension pad (once available) are always shown, the latter last.
function TycoonSteps.Visible(tycoon: TycoonState): { Step }
	local visible: { Step } = {}
	local counted = 0
	for _, step in list do
		if not TycoonSteps.IsBought(tycoon, step.Id) and needsMet(tycoon, step) then
			if step.Kind == "Automate" then
				table.insert(visible, step)
			elseif counted < STREET.MaxPads then
				table.insert(visible, step)
				counted += 1
			end
		end
	end
	if TycoonSteps.CanAscend(tycoon) then
		table.insert(visible, ascendStep)
	end
	return visible
end

-- How many decor pads the bay's theme has, and how many of them are bought.
function TycoonSteps.DecorProgress(tycoon: TycoonState, bay: number): (number, number)
	local theme = TycoonDecor.Themes[bay]
	if not theme then
		return 0, 0
	end
	local bought = 0
	for _, part in theme.Parts do
		if TycoonSteps.IsBought(tycoon, decorId(bay, part.Id)) then
			bought += 1
		end
	end
	return bought, #theme.Parts
end

local function decorPart(step: Step): TycoonDecor.Part?
	local theme = TycoonDecor.Themes[step.Bay]
	local index = step.PartIndex
	return if theme and index then theme.Parts[index] else nil
end

-- What the pad costs right now (an intern gets dearer with every Shiba already automated).
function TycoonSteps.Price(step: Step, tycoon: TycoonState): number
	if step.Kind == "Ascend" then
		return 0
	end
	if step.Kind == "Decor" then
		local part = decorPart(step)
		return if part
			then math.floor(
				TycoonMath.StreetReadyIncome(step.Bay - 1)
					* part.PriceSeconds
					* STREET.DecorScale
					* (STREET.StageFactor[step.Bay] or 1)
			)
			else 0
	end
	if step.Kind == "Bay" then
		if step.Bay <= 1 then
			return 0
		end
		return math.floor(
			TycoonMath.StreetReadyIncome(step.Bay - 2) * STREET.BaySeconds * (STREET.StageFactor[step.Bay - 1] or 1)
		)
	end
	return TycoonMath.StreetAutomationPrice(step.Bay - 1, TycoonMath.AutomatedCount(tycoon))
end

local function shibaName(bay: number): string
	local def = EconomyConfig.Shibas[bay]
	return if def then def.Name else "Shiba"
end

function TycoonSteps.ShibaName(bay: number): string
	return shibaName(bay)
end

function TycoonSteps.Title(step: Step): string
	if step.Kind == "Ascend" then
		return "Ascend"
	end
	if step.Kind == "Decor" then
		local part = decorPart(step)
		return if part then part.Name else "Decor"
	end
	if step.Kind == "Automate" then
		return "Bonk Intern"
	end
	return if step.Bay == 1 then "Spawn Shiba" else shibaName(step.Bay)
end

function TycoonSteps.Description(step: Step): string
	if step.Kind == "Ascend" then
		return "start over with more income"
	end
	if step.Kind == "Decor" then
		local part = decorPart(step)
		if not part then
			return ""
		end
		local bonus = part.RewardMult
		return if bonus and bonus > 1 then `{part.Description} (x{bonus} cash)` else part.Description
	end
	local name = shibaName(step.Bay)
	if step.Kind == "Automate" then
		return `an intern gets bonked for {name}`
	end
	return if step.Bay == 1 then "spawns your first Shiba" else "a new Shiba joins the plot"
end

return TycoonSteps
