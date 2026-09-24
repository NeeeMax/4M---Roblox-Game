# assets/ui

UI icons: bold cartoony shapes, thick dark outline, 256 × 256 PNG, transparent background.
Regenerate with `python assets/ui/make_icons.py assets/ui <preview.png>` (needs Pillow: `pip install pillow`).

To use one in game: upload the PNG (Creator Hub → Development Items → Decals, or Studio → Asset Manager → Import),
copy its image id and paste it into `src/shared/Config/Icons.luau` → `Icons.Ids` as `"rbxassetid://<id>"`.
While an id is `""`, `Widgets.Icon` shows the glyph from `Icons.Glyphs` instead.

| File | Icons.luau name | Intended use |
|------|-----------------|--------------|
| `cash.png` | `Cash` | Bonk Points: HUD money counter, Bonk Point price pills |
| `coin.png` | `Coin` | Robux price pills (generic hexagon coin, not the official Robux logo) |
| `clipboard.png` | `Clipboard` | HUD MANAGE button (upgrade menu / Manage pass) |
| `menu.png` | `Menu` | HUD menu button (list of menus) |
| `settings.png` | `Settings` | SETTINGS menu entry (also ADMIN for now) |
| `shop.png` | `Shop` | SHOP menu entry |
| `gift.png` | `Gift` | GIFTS menu entry (login streak, playtime gifts) |
| `quest.png` | `Quest` | QUESTS menu entry |
| `spin.png` | `Spin` | SPIN menu entry (daily wheel) |
| `index.png` | `Index` | INDEX menu entry (Shiba-Index) |
| `trophy.png` | `Trophy` | Trophies (shop tab, leaderboard) |
| `bonk_rain.png` | `BonkRain` | Bonk Rain button |
| `speed.png` | `Speed` | Run Faster pass / MoveSpeed upgrade |
| `paw.png` | `Paw` | Shibas (More Shibas upgrade, Shiba passes) |
| `lock.png` | `Lock` | Locked tabs / items (e.g. MANAGE without the pass) |
| `arrow_up.png` | `ArrowUp` | Upgrade buttons (the big round upgrade button) |
