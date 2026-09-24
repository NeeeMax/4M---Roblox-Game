--!strict
-- Text formatting helpers for UI.

local Format = {}

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

return Format
