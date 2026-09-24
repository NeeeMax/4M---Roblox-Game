--!strict
-- Settings menu (opened from the HUD menu): Volume (Master, Music, Effects) and Gameplay ("Show "New" Hints").
-- Music, Effects and Hints are saved on the server (Net.SaveSettings → state.Settings). Master only scales the other
-- two on this device and is not saved. Effects scales the bonk sound; Music plays MUSIC_ID in a loop (0 = no music).

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")

local Net = require(ReplicatedStorage.Shared.Net)

local BonkController = require(script.Parent.BonkController)
local State = require(script.Parent.Parent.UI.State)
local Theme = require(script.Parent.Parent.UI.Theme)
local Widgets = require(script.Parent.Parent.UI.Widgets)

-- Background music: a Roblox audio id you may use (e.g. from the Creator Store's free music). 0 = no music.
local MUSIC_ID = 0
-- Volume of the music at Music = 1, Master = 1.
local MUSIC_VOLUME = 0.5
-- Wait this long after the last change before saving (sliders change many times per second).
local SAVE_DELAY = 0.6

local master = 1
local music = 0.5
local effects = 1
local hints = true
-- True from a local change until it is saved, so a StateChanged in between doesn't move the sliders back.
local pending = false
local saveVersion = 0

local musicSound: Sound? = nil
local masterSlider: Widgets.Slider
local musicSlider: Widgets.Slider
local effectsSlider: Widgets.Slider
local hintsBox: Widgets.Checkbox

local SettingsController = {}

local function apply()
	BonkController.SetVolumeScale(master * effects)
	if musicSound then
		musicSound.Volume = MUSIC_VOLUME * master * music
	end
end

local function scheduleSave()
	pending = true
	saveVersion += 1
	local version = saveVersion
	task.delay(SAVE_DELAY, function()
		if version ~= saveVersion then
			return
		end
		Net.Get(Net.SaveSettings):FireServer(music, effects, hints)
		-- The server replicates the new state; keep local values until then.
		task.delay(1, function()
			if version == saveVersion then
				pending = false
			end
		end)
	end)
end

-- Takes the saved settings from the server (on join and when they change), unless the player is editing.
local function refresh()
	local state = State.Get()
	if not state or pending then
		return
	end
	if masterSlider.IsDragging() or musicSlider.IsDragging() or effectsSlider.IsDragging() then
		return
	end
	music = state.Settings.Music
	effects = state.Settings.Effects
	hints = state.Settings.Hints ~= false
	musicSlider.Set(music)
	effectsSlider.Set(effects)
	hintsBox.Set(hints)
	apply()
end

-- Whether "NEW" hints and "you can afford …" popups should show.
function SettingsController.HintsEnabled(): boolean
	return hints
end

local function section(parent: Instance, title: string, order: number, rows: number, rowHeight: number): Frame
	local card = Widgets.Card(parent, 58 + rows * rowHeight)
	card.LayoutOrder = order
	local heading = Widgets.Label(card, title, 32)
	heading.Position = UDim2.fromOffset(22, 6)
	heading.Size = UDim2.new(1, -44, 0, 44)
	local rowsFrame = Instance.new("Frame")
	rowsFrame.Name = "Rows"
	rowsFrame.BackgroundTransparency = 1
	rowsFrame.Position = UDim2.fromOffset(0, 52)
	rowsFrame.Size = UDim2.new(1, -10, 1, -58)
	rowsFrame.Parent = card
	local layout = Instance.new("UIListLayout")
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = rowsFrame
	return rowsFrame
end

function SettingsController.Init()
	local panel = Widgets.Panel("Settings", "SETTINGS", Vector2.new(560, 520), Color3.new(1, 1, 1), Theme.BorderGrey)
	local list = Widgets.List(panel.Content, 12)

	local volume = section(list, "Volume", 1, 3, 50)
	masterSlider = Widgets.Slider(volume, "Master", Theme.SliderMaster, master, function(value)
		master = value
		apply()
	end)
	masterSlider.Frame.LayoutOrder = 1
	musicSlider = Widgets.Slider(volume, "Music", Theme.SliderMusic, music, function(value, final)
		music = value
		apply()
		if final then
			scheduleSave()
		end
	end)
	musicSlider.Frame.LayoutOrder = 2
	effectsSlider = Widgets.Slider(volume, "Effects", Theme.SliderEffects, effects, function(value, final)
		effects = value
		apply()
		if final then
			scheduleSave()
		end
	end)
	effectsSlider.Frame.LayoutOrder = 3

	local gameplay = section(list, "Gameplay", 2, 1, 58)
	hintsBox = Widgets.Checkbox(gameplay, 'Show "New" Hints', hints, function(checked)
		hints = checked
		scheduleSave()
	end)

	if MUSIC_ID ~= 0 then
		local sound = Instance.new("Sound")
		sound.Name = "Music"
		sound.SoundId = `rbxassetid://{MUSIC_ID}`
		sound.Looped = true
		sound.Parent = SoundService
		musicSound = sound
	end
	panel.OnOpen = refresh
end

function SettingsController.Start()
	State.Start()
	State.Changed:Connect(refresh)
	refresh()
	apply()
	if musicSound then
		musicSound:Play()
	end
end

return SettingsController
