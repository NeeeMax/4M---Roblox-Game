--!strict
-- Colours and fonts shared by every menu, so the whole UI looks like one game.
-- Look: black panels inside a thick studded border (green, grey for settings), big white outlined titles,
-- chunky bright buttons, yellow price pills (docs/GAME_DESIGN.md → UI).

return {
	Font = Enum.Font.FredokaOne,
	-- Big panel titles, tabs and the money counter.
	TitleFont = Enum.Font.LuckiestGuy,
	BodyFont = Enum.Font.GothamBold,

	-- HUD bars and toasts.
	Background = Color3.fromRGB(22, 22, 26),
	-- Inside of a panel (inside the studded border).
	Panel = Color3.fromRGB(12, 12, 14),
	Card = Color3.fromRGB(36, 36, 40),
	CardLight = Color3.fromRGB(62, 62, 68),
	Stroke = Color3.fromRGB(10, 10, 12),

	Text = Color3.fromRGB(255, 255, 255),
	-- Text on yellow/white pills.
	DarkText = Color3.fromRGB(28, 26, 30),
	Muted = Color3.fromRGB(185, 185, 195),
	Accent = Color3.fromRGB(255, 214, 10),

	Good = Color3.fromRGB(40, 205, 60),
	Bad = Color3.fromRGB(228, 34, 44),
	Info = Color3.fromRGB(60, 165, 255),
	Disabled = Color3.fromRGB(92, 92, 100),
	Admin = Color3.fromRGB(200, 60, 70),

	-- The big money counter on the HUD.
	Money = Color3.fromRGB(50, 255, 70),
	-- Yellow price pill (Widgets.PricePill).
	Price = Color3.fromRGB(255, 222, 0),

	-- Studded panel borders: frame colour and the little studs on it.
	BorderGreen = Color3.fromRGB(38, 168, 44),
	StudGreen = Color3.fromRGB(26, 128, 32),
	BorderGrey = Color3.fromRGB(150, 150, 156),
	StudGrey = Color3.fromRGB(104, 104, 112),

	-- Settings sliders (pastel, like the reference).
	SliderMaster = Color3.fromRGB(246, 160, 160),
	SliderMusic = Color3.fromRGB(184, 152, 255),
	SliderEffects = Color3.fromRGB(255, 204, 150),

	-- HUD square buttons.
	MenuButton = Color3.fromRGB(60, 60, 72),
	-- Every ScreenGui built by Widgets.Screen is scaled by viewport height / 820 × UIScale, clamped to Min … Max.
	UIScale = 0.8,
	UIScaleMin = 0.5,
	UIScaleMax = 0.9,
	ManageButton = Color3.fromRGB(60, 215, 70),
}
