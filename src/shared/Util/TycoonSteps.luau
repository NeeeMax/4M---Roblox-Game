--!strict
-- The floor pads of the street (docs/GAME_DESIGN.md → Street, plots and buttons, "One Shiba per expansion"): one row per
-- pad, in walkthrough order. Bay n extends the plot by one bay and spawns Shiba n (tier n - 1); Auto n automates that Shiba.
-- Pure data and formulas, shared by the server (buying, drawing the pads) and the client.

local EconomyConfig = require(script.Parent.Parent.Config.EconomyConfig)
local TycoonConfig = require(script.Parent.Parent.Config.Tycoon)
local Types = require(script.Parent.Parent.Types)
local TycoonMath = require(script.Parent.TycoonMath)

type TycoonState = Types.TycoonState

export type Step = {
	Id: string,
	Kind: "Bay" | "Automate",
	-- The bay (and Shiba number) the pad belongs to, 1 … Bays.
	Bay: number,
	-- Step ids that must be bought before this pad shows up.
	Needs: { string },
}

local STREET = TycoonConfig.Street

local list: { Step } = {}
local byId: { [string]: Step } = {}

-- Order matters: the first MaxPads visible ones are shown, so the pads follow the walkthrough.
for bay = 1, STREET.Bays do
	local expand: Step = {
		Id = `Bay{bay}`,
		Kind = "Bay",
		Bay = bay,
		Needs = if bay > 1 then { `Bay{bay - 1}` } else {},
	}
	local automate: Step = {
		Id = `Auto{bay}`,
		Kind = "Automate",
		Bay = bay,
		Needs = { `Bay{bay}` },
	}
	for _, step in { expand, automate } do
		table.insert(list, step)
		byId[step.Id] = step
	end
end

local TycoonSteps = {
	List = list,
	ById = byId,
	Bays = STREET.Bays,
}

function TycoonSteps.IsBought(tycoon: TycoonState, id: string): boolean
	local steps = tycoon.Steps
	return steps ~= nil and steps[id] == true
end

-- The pads to show now: not bought yet, everything they need bought, at most Street.MaxPads, in table order.
function TycoonSteps.Visible(tycoon: TycoonState): { Step }
	local visible: { Step } = {}
	for _, step in list do
		if not TycoonSteps.IsBought(tycoon, step.Id) then
			local ready = true
			for _, need in step.Needs do
				if not TycoonSteps.IsBought(tycoon, need) then
					ready = false
					break
				end
			end
			if ready then
				table.insert(visible, step)
				if #visible >= STREET.MaxPads then
					break
				end
			end
		end
	end
	return visible
end

-- What the pad costs right now (an automation gets dearer with every Shiba already automated).
function TycoonSteps.Price(step: Step, tycoon: TycoonState): number
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

function TycoonSteps.Title(step: Step): string
	if step.Kind == "Automate" then
		return "Cash Register"
	end
	return if step.Bay == 1 then "First Shiba" else `Expansion {step.Bay}`
end

function TycoonSteps.Description(step: Step): string
	local name = shibaName(step.Bay)
	if step.Kind == "Automate" then
		return `automates {name}`
	end
	return if step.Bay == 1 then "spawns your first Shiba" else `the plot grows, {name} joins`
end

return TycoonSteps
