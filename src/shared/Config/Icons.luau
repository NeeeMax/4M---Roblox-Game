--!strict
-- UI icons (assets/ui/*.png, see assets/ui/README.md). Upload a PNG in the Creator Hub (or Studio's Asset
-- Manager) and paste its id here as "rbxassetid://123…". While an id is "", Widgets.Icon shows the glyph instead.

export type IconName =
	"Cash"
	| "Coin"
	| "Clipboard"
	| "Menu"
	| "Settings"
	| "Shop"
	| "Gift"
	| "Quest"
	| "Spin"
	| "Index"
	| "Trophy"
	| "BonkRain"
	| "Speed"
	| "Paw"
	| "Lock"
	| "ArrowUp"

local Icons = {}

-- Icon name → image asset id ("" = not uploaded yet).
Icons.Ids = {
	Cash = "", -- assets/ui/cash.png
	Coin = "", -- assets/ui/coin.png
	Clipboard = "", -- assets/ui/clipboard.png
	Menu = "", -- assets/ui/menu.png
	Settings = "", -- assets/ui/settings.png
	Shop = "", -- assets/ui/shop.png
	Gift = "", -- assets/ui/gift.png
	Quest = "", -- assets/ui/quest.png
	Spin = "", -- assets/ui/spin.png
	Index = "", -- assets/ui/index.png
	Trophy = "", -- assets/ui/trophy.png
	BonkRain = "", -- assets/ui/bonk_rain.png
	Speed = "", -- assets/ui/speed.png
	Paw = "", -- assets/ui/paw.png
	Lock = "", -- assets/ui/lock.png
	ArrowUp = "", -- assets/ui/arrow_up.png
} :: { [IconName]: string }

-- Shown as text while the id is empty.
Icons.Glyphs = {
	Cash = "💵",
	Coin = "🪙",
	Clipboard = "📋",
	Menu = "☰",
	Settings = "⚙️",
	Shop = "🛒",
	Gift = "🎁",
	Quest = "📜",
	Spin = "🎡",
	Index = "📖",
	Trophy = "🏆",
	BonkRain = "☔",
	Speed = "🏃",
	Paw = "🐾",
	Lock = "🔒",
	ArrowUp = "⬆️",
} :: { [IconName]: string }

return Icons
