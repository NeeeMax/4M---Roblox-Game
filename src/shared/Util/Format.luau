--!strict
-- Text formatting helpers for UI.

local Economy = require(script.Parent.Parent.Config.Economy)

local SYMBOL = Economy.Currency.Symbol

local Format = {}

-- The currency's name and plain-text symbol ("Bonk Dollars", "B$"), see Config/Economy → Currency.
Format.CurrencyName = Economy.Currency.Name
Format.CurrencySymbol = SYMBOL

-- 1234567 → "1,234,567"
function Format.Number(value: number): string
	local digits = tostring(math.floor(value))
	local sign = ""
	if string.sub(digits, 1, 1) == "-" then
		sign = "-"
		digits = string.sub(digits, 2)
	end
	local grouped = string.reverse((string.gsub(string.reverse(digits), "(%d%d%d)", "%1,")))
	if string.sub(grouped, 1, 1) == "," then
		grouped = string.sub(grouped, 2)
	end
	return sign .. grouped
end

-- Names for 10^3, 10^6, 10^9 …
local NAMES = {
	"thousand",
	"million",
	"billion",
	"trillion",
	"quadrillion",
	"quintillion",
	"sextillion",
	"septillion",
	"octillion",
	"nonillion",
	"decillion",
	"undecillion",
	"duodecillion",
	"tredecillion",
	"quattuordecillion",
	"quindecillion",
}

-- Up to 3 decimals, rounded down (never shows more than you have), no trailing zeros: 14.750 → "14.75".
local function decimals(value: number): string
	local text = string.format("%.3f", math.floor(value * 1000 + 1e-6) / 1000)
	text = string.gsub(text, "0+$", "")
	text = string.gsub(text, "%.$", "")
	return text
end

-- magnitude (>= 1000) = scaled * 1000^group with 1 <= scaled < 1000.
local function split(magnitude: number): (number, number)
	local group = math.floor(math.log10(magnitude) / 3)
	local scaled = magnitude / 10 ^ (group * 3)
	-- Floating point can land just below or above a group boundary.
	if scaled >= 1000 then
		group += 1
		scaled /= 1000
	elseif scaled < 1 then
		group -= 1
		scaled *= 1000
	end
	return group, scaled
end

-- Big numbers for the HUD: 999 → "999", 1234 → "1.234 thousand", 324316000000000000 → "324.316 quadrillion".
-- Beyond the named range: "1.234e51".
function Format.Abbreviate(value: number): string
	if value ~= value then
		return "0"
	end
	local sign = if value < 0 then "-" else ""
	local magnitude = math.abs(value)
	if magnitude < 1000 then
		return sign .. Format.Number(magnitude)
	end
	if magnitude == math.huge then
		return sign .. "∞"
	end
	local group, scaled = split(magnitude)
	local name = NAMES[group]
	if not name then
		return `{sign}{decimals(scaled)}e{group * 3}`
	end
	return `{sign}{decimals(scaled)} {name}`
end

-- Short form for tight spots (price pills, leaderboard-like lists): 1234 → "1.23K", 5.6e15 → "5.6Qd".
local SHORT = { "K", "M", "B", "T", "Qd", "Qn", "Sx", "Sp", "Oc", "No", "Dc" }
function Format.Short(value: number): string
	if value ~= value then
		return "0"
	end
	local sign = if value < 0 then "-" else ""
	local magnitude = math.abs(value)
	if magnitude < 1000 then
		return sign .. tostring(math.floor(magnitude))
	end
	if magnitude == math.huge then
		return sign .. "∞"
	end
	local group, scaled = split(magnitude)
	if group > #SHORT then
		scaled *= 10 ^ ((group - #SHORT) * 3)
		group = #SHORT
	end
	local text = string.format("%.2f", math.floor(scaled * 100 + 1e-6) / 100)
	text = string.gsub(text, "0+$", "")
	text = string.gsub(text, "%.$", "")
	return `{sign}{text}{SHORT[group]}`
end

-- A Bonk Dollars amount as plain text: 1234 → "B$ 1,234". Menus draw the symbol (Widgets.SetMoneyText).
function Format.Money(value: number): string
	return `{SYMBOL} {Format.Number(value)}`
end

-- Short form for tight spots: 1234 → "B$ 1.23K".
function Format.MoneyShort(value: number): string
	return `{SYMBOL} {Format.Short(value)}`
end

return Format
