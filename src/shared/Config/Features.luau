--!strict
-- Feature flags. The server reads them; the client learns the result from state.Tycoon.Enabled (no extra remote).
-- Flip a default only in its own one-line PR (see docs/TYCOON_HANDOFF.md, phase 6). Keep every push playable with the
-- flags at their defaults.

return {
	-- The tycoon core loop ("Shiba Workers", docs/decisions/0006). False = the old throw-and-catch loop runs unchanged.
	Tycoon = true,
	-- The street with 10 plots instead of the islands (docs/GAME_DESIGN.md → Street, plots and buttons, StreetService).
	-- Only has an effect together with Tycoon = true. False keeps the islands.
	Street = true,
}
