--!nocheck
-- STUDIO TUNER: a Roblox Studio COMMAND BAR snippet (not lune, not part of the game). It turns what you did with the Move / Rotate /
-- Scale tools on decor models and scatter props into lines you paste into the theme files / Config/StageScatter.
-- Full plain-language steps: docs/TUNING.md.
--
-- HOW TO USE
--   1. Start a playtest (F5) or Run mode (F8) with the street built, and walk the plot until the Shiba stage you want to tune exists
--      (decor parts show up once bought; the scatter exists for every stage that is reached).
--   2. The command bar must run on the SERVER: in the Test tab / Home tab use "Current: Client" -> switch to "Server" (in Run mode
--      there is only the server). Edits you make in the Server view are what the snippet reads.
--   3. In the Explorer (Workspace -> Street -> ... -> your plot folder) or by clicking in the viewport, select a decor model
--      (Decor_Decor<bay>_<Id>) or a scatter prop (a model named OakA, Bush, ...), and move / rotate / scale it with Studio's normal
--      tools. Rotating about the vertical axis only and uniform scaling are what the output understands. You can select many.
--   4. Open View -> Command Bar, paste PART 1 below (everything from "local Selection" down to just before the PART 2 comment block) and press Enter. Read the
--      lines in the Output window and paste them into the file named above each group.
--   5. Props you do NOT want: simply delete them in the Explorer (select, Delete). PART 1 also lists every deleted scatter prop as a
--      "Skip[bay][index] = true" line. (Decor parts cannot be deleted this way: remove them from the theme file.)
--   Nothing is saved by this: stop the playtest and everything you did live is gone unless you pasted it into the files.
--
-- WHAT THE ATTRIBUTES ARE (set by World/StreetPlot and World/StageScatter, only in Studio): see the Tune* attributes in the
-- Properties window of a model. The snippet compares the model's current pivot and box with the ones recorded at build time:
--   yaw   = old yaw + the change of the model's rotation about Y in the stage frame
--   scale = old scale * (current box size / box size at build; measured in the model's own orientation)
--   nudge = old nudge + (change of the model's box centre, expressed in the stage frame) / StageScale
--   props = pivot position (X, Z) / StageScale, yaw about Y, scale.
-- Note: the Scale line only changes when the model's SIZE changed. A model made bigger with the Scale tool whose pivot moved is
-- fine too: the box centre is measured, not assumed.

-- ======================================== PART 1: print the values to paste ========================================
local Selection = game:GetService("Selection")

local function round(value, step)
	local rounded = math.round(value / step) * step
	if rounded == 0 then
		return 0
	end
	return tonumber(string.format("%.4f", rounded))
end

-- The box of a model in the orientation of its own pivot: (centre relative to the pivot, size).
local function measure(model)
	local probe = model:Clone()
	probe:PivotTo(CFrame.new())
	local box, size = probe:GetBoundingBox()
	probe:Destroy()
	return box.Position, size
end

-- The decor model or scatter prop a selected instance belongs to (or nil).
local function tunedModel(instance)
	local current = instance
	while current and current ~= workspace do
		if
			current:IsA("Model")
			and (current:GetAttribute("TunePartId") ~= nil or current:GetAttribute("TuneScatter") == true)
		then
			return current
		end
		current = current.Parent
	end
	return nil
end

-- How the model differs from how it was built: (yaw change in degrees, size ratio, stage-frame move of the box centre, stage frame,
-- pivot in the stage frame).
local function compare(model)
	local stage = model:GetAttribute("TuneFrame")
	local pivot0 = model:GetAttribute("TunePivot")
	local offset0 = model:GetAttribute("TuneBoxOffset")
	local size0 = model:GetAttribute("TuneSize")
	local pivotNow = model:GetPivot()
	local offsetNow, sizeNow = measure(model)

	local centre0 = stage:PointToObjectSpace(pivot0 * offset0)
	local centreNow = stage:PointToObjectSpace(pivotNow * offsetNow)
	local turn = stage:ToObjectSpace(pivotNow) * stage:ToObjectSpace(pivot0):Inverse()
	local _, turnY = turn:ToOrientation()

	-- Uniform scale: the geometric mean of the ratios of the sides that are not tiny.
	local product, sides = 1, 0
	for _, axis in { "X", "Y", "Z" } do
		if size0[axis] > 0.05 and sizeNow[axis] > 0.001 then
			product *= sizeNow[axis] / size0[axis]
			sides += 1
		end
	end
	local ratio = if sides > 0 then product ^ (1 / sides) else 1
	return math.deg(turnY), ratio, centreNow - centre0, stage, stage:ToObjectSpace(pivotNow)
end

local function wrap(degrees)
	return ((degrees + 180) % 360) - 180
end

local function vec(v)
	return string.format("Vector3.new(%s, %s, %s)", round(v.X, 0.01), round(v.Y, 0.01), round(v.Z, 0.01))
end

local function themeFile(bay)
	return string.format("src/shared/Config/DecorTheme%02d.luau", bay)
end

local SCATTER_FILE = "src/shared/Config/StageScatter.luau"
local decorLines = {} -- [bay] = { lines }
local scatterLines = {} -- [bay] = { lines }

local function add(group, bay, line)
	group[bay] = group[bay] or {}
	table.insert(group[bay], line)
end

local seen = {}
local count = 0
for _, selected in Selection:Get() do
	local model = tunedModel(selected)
	if model and not seen[model] then
		seen[model] = true
		count += 1
		local bay = model:GetAttribute("TuneBay")
		local stageScale = model:GetAttribute("TuneStageScale") or 1
		local dYaw, ratio, move, _, pivotStage = compare(model)
		if model:GetAttribute("TunePartId") ~= nil then
			-- ---- a decor part ----
			local id = model:GetAttribute("TunePartId")
			local yaw = wrap(model:GetAttribute("TuneYaw") + dYaw)
			local scale = model:GetAttribute("TuneScale") * ratio
			local nudge = model:GetAttribute("TuneNudge") + move / stageScale
			local note = ""
			if scale < 0.3 or scale > 3 then
				note = "   -- WARNING: Scale must stay between 0.3 and 3"
			end
			add(
				decorLines,
				bay,
				string.format(
					"Part %s (bay %d): Yaw = %s, Scale = %s, Nudge = %s,%s",
					id,
					bay,
					round(yaw, 0.1),
					round(scale, 0.01),
					vec(nudge),
					note
				)
			)
		else
			-- ---- a scatter prop ----
			local name = model:GetAttribute("TuneName")
			local _, yawNow = pivotStage:ToOrientation()
			local scale = model:GetAttribute("TuneScale") * ratio
			local pin = string.format(
				'{ Name = "%s", X = %s, Z = %s, Yaw = %s, Scale = %s },',
				name,
				round(pivotStage.X / stageScale, 0.1),
				round(pivotStage.Z / stageScale, 0.1),
				round(wrap(math.deg(yawNow)), 0.1),
				round(scale, 0.01)
			)
			local pinNumber = model:GetAttribute("TunePin")
			local index = model:GetAttribute("TuneIndex")
			local moved = (move.Magnitude > 0.05) or math.abs(dYaw) > 0.5 or math.abs(ratio - 1) > 0.005
			if pinNumber ~= nil then
				if moved then
					add(
						scatterLines,
						bay,
						string.format("Pins[%d] entry #%d (%s) becomes: %s", bay, pinNumber, name, pin)
					)
				else
					add(scatterLines, bay, string.format("Pins[%d] entry #%d (%s): not changed", bay, pinNumber, name))
				end
			elseif moved then
				add(scatterLines, bay, string.format("Pins[%d] add: %s", bay, pin))
				add(scatterLines, bay, string.format("Skip[%d][%d] = true   -- the original %s", bay, index, name))
			else
				add(scatterLines, bay, string.format("%s (index %d): not changed", name, index))
			end
		end
	end
end

-- Scatter props that were deleted in the Explorer: indices missing from their stage's folder, and pins that vanished.
local deleted = 0
for _, folder in workspace:GetDescendants() do
	local total = folder:IsA("Folder") and folder:GetAttribute("TuneCount")
	if total then
		local bay = folder:GetAttribute("TuneBay")
		local present, presentPins = {}, {}
		for _, child in folder:GetChildren() do
			local index = child:GetAttribute("TuneIndex")
			if index then
				present[index] = true
			end
			local pin = child:GetAttribute("TunePin")
			if pin then
				presentPins[pin] = true
			end
		end
		local already = {}
		for text in string.gmatch(folder:GetAttribute("TuneSkipped") or "", "%d+") do
			already[tonumber(text)] = true
		end
		for index = 1, total do
			if not present[index] and not already[index] then
				deleted += 1
				add(scatterLines, bay, string.format("Skip[%d][%d] = true   -- deleted in the Explorer", bay, index))
			end
		end
		for number = 1, folder:GetAttribute("TunePins") or 0 do
			if not presentPins[number] then
				deleted += 1
				add(
					scatterLines,
					bay,
					string.format("Pins[%d] entry #%d was deleted: remove it from the list", bay, number)
				)
			end
		end
	end
end

local function printGroups(title, file, groups)
	local bays = {}
	for bay in groups do
		table.insert(bays, bay)
	end
	table.sort(bays)
	for _, bay in bays do
		print(string.format("==== %s, bay %d -> %s ====", title, bay, file(bay)))
		for _, line in groups[bay] do
			print("  " .. line)
		end
	end
end

if count == 0 and deleted == 0 then
	print("[tuner] nothing to report: select a decor model or a scatter prop first (and run in the Server view).")
else
	print(
		string.format(
			"[tuner] %d selected model(s), %d deleted scatter entr(ies). Paste the lines below into the files named.",
			count,
			deleted
		)
	)
	print(
		"[tuner] Decor lines: find the part with that Id in the theme file and set Yaw, Scale and Nudge in its table (replace old values)."
	)
	print(
		"[tuner] Scatter lines: Pins[bay] = { ... } and Skip[bay] = { [index] = true } in Config/StageScatter (merge with existing entries)."
	)
	printGroups("DECOR", themeFile, decorLines)
	printGroups("SCATTER", function()
		return SCATTER_FILE
	end, scatterLines)
end

--[=[
-- ================= PART 2 (optional, paste on its own): show / hide the invisible colliders =================
-- Makes the invisible collider parts (decor "Collider<n>", scatter "Trunk" / "Boulder") of the SELECTED models visible as red
-- translucent boxes, so you can see what the player bumps into; with nothing selected it does every decor model and scatter prop.
-- Run it again to hide them. Purely visual (Server view only), lost when the playtest ends.
local Selection = game:GetService("Selection")
local targets = {}
for _, selected in Selection:Get() do
	local current = selected
	while current and current ~= workspace do
		if current:IsA("Model") and (current:GetAttribute("TunePartId") ~= nil or current:GetAttribute("TuneScatter") == true) then
			table.insert(targets, current)
			break
		end
		current = current.Parent
	end
end
if #targets == 0 then
	for _, instance in workspace:GetDescendants() do
		if instance:IsA("Model") and (instance:GetAttribute("TunePartId") ~= nil or instance:GetAttribute("TuneScatter") == true) then
			table.insert(targets, instance)
		end
	end
end
for _, model in targets do
	for _, part in model:GetDescendants() do
		if part:IsA("BasePart") and (string.match(part.Name, "^Collider") or part.Name == "Trunk" or part.Name == "Boulder") then
			if part:GetAttribute("TuneShown") then
				part.Transparency = 1
				part.Color = part:GetAttribute("TuneColor")
				part:SetAttribute("TuneShown", nil)
				part:SetAttribute("TuneColor", nil)
			else
				part:SetAttribute("TuneColor", part.Color)
				part:SetAttribute("TuneShown", true)
				part.Transparency = 0.6
				part.Color = Color3.fromRGB(255, 60, 60)
			end
		end
	end
end
print(string.format("[tuner] toggled the colliders of %d model(s)", #targets))
]=]
