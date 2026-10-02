# Tuning decor and scatter by hand (Studio)

You can scale, turn and move any decor model or scatter prop yourself, with Studio's normal tools, and let a small script
turn what you did into lines you paste into the theme files. No programming needed.

## What can be tuned

| What | Where it goes | Fields |
|------|---------------|--------|
| A decor part (house, fence, stall ...) | its entry in `src/shared/Config/DecorTheme<NN>.luau` | `Yaw` (degrees), `Scale` (0.3 to 3), `Nudge = Vector3.new(x, y, z)` (y = lift) |
| A scatter prop (tree, bush, rock ...) you moved | `Pins[bay]` in `src/shared/Config/StageScatter.luau` | `{ Name, X, Z, Yaw, Scale }` |
| A scatter prop you do not want | `Skip[bay][index] = true` in the same file | |

A decor part's pad does not move with it: the pad stays where the theme says.

## Steps

1. Start a playtest (F5) or Run mode (F8) and get the stage you want to tune: decor shows up once the part is bought, the scatter
   shows up for every stage that is reached.
2. Make sure Studio looks at the **Server**: in the Test tab choose "Current: Server" (in Run mode there is only the server).
   Everything below is done in that view.
3. Select a model: click it in the viewport, or find it in the Explorer. Decor models are called `Decor_Decor<bay>_<Id>` (for
   example `Decor_Decor1_House`), scatter props have the prop's name (`OakA`, `Bush` ...). Each is ONE model: moving it moves the
   pieces and the invisible colliders with it. Select several if you like.
4. Use Studio's **Move**, **Rotate** and **Scale** tools on it. Rotate around the vertical axis only (the green ring); scale
   uniformly. The model's pivot sits at its centre (decor) or at its foot (scatter), so rotating turns it on the spot.
5. Open View, Command Bar. Open `docs/tools/studio_tuner.luau`, copy PART 1 (down to just before the PART 2 comment block), paste it into the
   command bar and press Enter.
6. Look at the Output window. The lines are grouped by bay, each group names the file to edit:
   - `Part House (bay 1): Yaw = 25, Scale = 1.2, Nudge = Vector3.new(3, 0, -4.5),`: in `DecorTheme01.luau` find the part with
     `Id = "House"` and put `Yaw = 25,` `Scale = 1.2,` `Nudge = Vector3.new(3, 0, -4.5),` into its table (replace old values).
   - `Pins[1] add: { Name = "OakA", ... },` plus `Skip[1][17] = true`: a prop you moved becomes a pin, and the random prop it came
     from is skipped. Add the pin to `Pins[1] = { ... }` and the index to `Skip[1] = { [17] = true }` in `StageScatter.luau`.
   - A scatter prop you **deleted** in the Explorer (select, Delete) shows up as `Skip[bay][index] = true`. Run the snippet
     after deleting; you do not have to select anything.
7. Optional: PART 2 of the same file (a commented block, paste it on its own) shows the invisible colliders as red boxes, so you
   can see what the player bumps into. Run it again to hide them.
8. Paste the lines into the files, run `lune run docs/tools/theme_check src/shared/Config/DecorTheme<NN>.luau <bay>` for a theme
   you changed (it must say 0 errors: Scale, Yaw and Nudge are checked against the Area, the path, the pads and the Shiba zone),
   then commit and push as usual (CLAUDE.md).

## Limits to know

- Nothing is saved by the tuning itself. When you stop the playtest everything you moved is gone: only the pasted lines count.
- The tuner only knows rotation about the vertical axis and uniform scale. Tilting a model or stretching one side is ignored.
- Scale is limited to 0.3 to 3 per decor part (the checker complains beyond that).
- `Nudge` is in the unscaled theme units of the file (the game multiplies it by `StageScale` like every other coordinate), the output
  already accounts for this. Pins use unscaled units too.
- The `Skip` index of a scatter prop is its place in the stage's random sequence, which is seeded by the bay only: every plot of every player shows the same scatter for a bay, so `Skip` and `Pins` apply to everyone. If the scatter generation code changes, indices move: re-check the skips then.
- A pin is built with its own small random tilt, and is not checked against the path, pads or the Shiba zone: keep it clear yourself
  (look at it in the playtest).
- Decor models cannot be deleted this way (a part is bought through its pad): to remove one, delete it from the theme file.
- The Studio Scale tool and `Model:ScaleTo` both work: the tuner compares the model's measured box to the one at build time, so it
  does not matter how the model was resized or where its pivot ended up.
- The `Tune*` attributes exist only in Studio (`RunService:IsStudio()`), production models carry none.
