# Dawn and Dusk

A standalone Hearts of Iron IV total conversion set from 1 January 2000. The old world order frays in the background; the story is Africa's.

- **Game version:** 1.19.x
- **Design bible:** kept as a Claude Doc, outside the repo
- **Status:** foundation only. The game boots into a 2000-dated world with the new ideology spectrum, but borders are still vanilla's until the map pass.

## Installing for development

1. Clone this repo into your HOI4 user mod folder, so the files land here:
   `Documents/Paradox Interactive/Hearts of Iron IV/mod/Dawn_and_Dusk/`
2. Copy `tools/dawn_and_dusk.mod` up one level, into
   `Documents/Paradox Interactive/Hearts of Iron IV/mod/`. The launcher only finds mods through `.mod` files in that folder; the copy inside `tools` does nothing.
3. Open the copied file and set `path` to the full path of your clone, with forward slashes, for example
   `path="C:/Users/YOUR_NAME/Documents/Paradox Interactive/Hearts of Iron IV/mod/Dawn_and_Dusk"`.
4. Restart the launcher, enable **Dawn and Dusk** in a playset with no other mods, and launch in debug mode.

See [docs/TESTING.md](docs/TESTING.md) for what to check after each change.

## Layout

| Folder | What lives there |
| --- | --- |
| `common/ideologies` | The eight-group spectrum and its flavours |
| `common/game_rules` | Focus-only war goals, world branches, the 2040 deadline |
| `common/bookmarks` | The 2000 start |
| `common/defines` | Start and end dates |
| `common/on_actions`, `common/scripted_effects` | Game-start setup |
| `history/countries` | Generated from `tools/data/countries.csv` |
| `interface` | Sprite definitions |
| `localisation/english` | All player-facing text |
| `tools` | Generators and the launcher `.mod` template |
| `docs` | Conventions and testing notes |

## Conventions

Short version: every new key starts with `dnd_` (or `DND_` in localisation), and vanilla files are never copied in. Full rules in [docs/CONVENTIONS.md](docs/CONVENTIONS.md).

## Legal

This is a fan mod for Hearts of Iron IV by Paradox Interactive. It contains no Paradox files. Vanilla assets are referenced by path where needed and are never copied into this repository.
