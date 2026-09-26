--!strict
-- Text formatting helpers for UI.

local Economy = require(script.Parent.Parent.Config.Economy)

local SYMBOL = Economy.Currency.Symbol

local Format = {}

-- The currency's name and plain-text symbol ("Bonk Dollars", "B$"), see Config/Economy → Currency.
Format.CurrencyName = Economy.Currency.Name
Format.CurrencySymbol = SYMBOL

-- Numbers from here on are written short ("1.23Qa"): doubles above ~1e15 have no exact digits left, and a
-- 30-digit number doesn't fit anywhere anyway.
local FULL_DIGITS_BELOW = 1e15

-- 1234567 → "1,234,567" (short form from FULL_DIGITS_BELOW on).
function Format.Number(value: number): string
	if math.abs(value) >= FULL_DIGITS_BELOW then
		return Format.Short(value)
	end
	local digits = string.format("%d", math.floor(value))
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
	"sexdecillion",
	"septendecillion",
	"octodecillion",
	"novemdecillion",
	"vigintillion",
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
-- Beyond the named range: the short form ("1.23UVg").
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
		return Format.Short(value)
	end
	return `{sign}{decimals(scaled)} {name}`
end

-- Short suffixes for 10^3, 10^6 … : K, M, B, T, Qa, Qi, Sx, Sp, Oc, No, Dc (1e33), then UDc, DDc, TDc, QaDc … NoDc,
-- Vg (1e63), UVg … NoVg, Tg (1e93) … up to 1e303. Built once (pure: no side effects).
local SHORT: { string } = { "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No" }
do
	local units = { "U", "D", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No" }
	for _, tens in { "Dc", "Vg", "Tg", "Qag", "Qig", "Sxg", "Spg", "Ocg", "Nog", "Ce" } do
		table.insert(SHORT, tens)
		for _, unit in units do
			table.insert(SHORT, unit .. tens)
		end
	end
end

-- Short form for tight spots (price pills, HUD, boards): 1234 → "1.23K", 5.6e15 → "5.6Qa", 1e33 → "1Dc".
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

-- Amounts up to this are written in full ("B$ 123,456"), bigger ones short ("B$ 1.23M").
local MONEY_FULL_BELOW = 1e6

-- A Bonk Dollars amount as plain text: 1234 → "B$ 1,234", 5.6e15 → "B$ 5.6Qa". Menus draw the symbol
-- (Widgets.SetMoneyText).
function Format.Money(value: number): string
	if math.abs(value) >= MONEY_FULL_BELOW then
		return `{SYMBOL} {Format.Short(value)}`
	end
	return `{SYMBOL} {Format.Number(value)}`
end

-- Short form for tight spots: 1234 → "B$ 1.23K".
function Format.MoneyShort(value: number): string
	return `{SYMBOL} {Format.Short(value)}`
end

-- A countdown with the two biggest units: 186000 → "2d 03h", 4500 → "1h 15m", 125 → "2m 05s", 9 → "9s".
function Format.Countdown(seconds: number): string
	local total = math.max(0, math.floor(seconds))
	local days = total // 86400
	local hours = (total % 86400) // 3600
	local minutes = (total % 3600) // 60
	local rest = total % 60
	if days > 0 then
		return string.format("%dd %02dh", days, hours)
	elseif hours > 0 then
		return string.format("%dh %02dm", hours, minutes)
	elseif minutes > 0 then
		return string.format("%dm %02ds", minutes, rest)
	end
	return `{rest}s`
end

return Format
