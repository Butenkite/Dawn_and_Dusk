# Dawn and Dusk

A standalone Hearts of Iron IV total conversion set from 1 January 2000. The old world order frays in the background; the story is Africa's.

- **Game version:** 1.19.x
- **Design bible:** kept as a Claude Doc, outside the repo
- **Status:** the 2000 start boots with the new ideology spectrum. All of Africa, the Levant, Iraq, the Arabian Peninsula and Cyprus are rebuilt from real geography, with the Second Congo War, the Second Sudanese Civil War and the Eritrean-Ethiopian War running; Sierra Leone split along the Lomé ceasefire line; Somalia divided among its 2000 administrations and factions; Anjouan apart from the Comoros; the SADR's Free Zone beyond the Western Sahara berm; the Palestinian self-rule areas, Israel's security zone in south Lebanon and the Golan; the two Kurdish administrations in northern Iraq; and divided Cyprus. The rest of the world is still on vanilla borders.

## Repository layout

```
Dawn_and_Dusk/
  mod/        what the game loads; the launcher points here
  tools/      generators, the map builder and setup helpers (never loaded by the game)
  docs/       conventions, testing notes, credits
```

| Folder | What lives there |
| --- | --- |
| `mod/common`, `mod/events`, `mod/interface`, `mod/localisation` | Game script and text |
| `mod/history` | Countries, states and starting armies, almost all generated (see below) |
| `mod/map` | The map, rebuilt region by region by `tools/map` |
| `mod/gfx/flags` | Flags for countries vanilla does not have, drawn by `tools/countries/make_flags.py` |
| `tools/data` | The hand-edited sources: countries, parties, region specs |
| `tools/map` | Map builder and validator ([tools/map/README.md](tools/map/README.md)) |
| `tools/countries` | Country histories, starting armies, flags |
| `tools/politics` | Party names, ideology text |
| `tools/vanilla` | Stand-ins for vanilla ids and patched vanilla screens; re-run after HOI4 updates |
| `tools/setup` | Launcher `.mod` template, placeholder ideology flags |

## Installing for development

1. Clone this repo into your HOI4 user mod folder:
   `Documents/Paradox Interactive/Hearts of Iron IV/mod/Dawn_and_Dusk/`
2. Copy `tools/setup/dawn_and_dusk.mod` into `Documents/Paradox Interactive/Hearts of Iron IV/mod/`, next to the clone.
3. In the copy, set `path` to the `mod` folder **inside** the clone, with forward slashes:
   `path="C:/Users/YOUR_NAME/Documents/Paradox Interactive/Hearts of Iron IV/mod/Dawn_and_Dusk/mod"`
4. Optional: run `tools/setup/make_placeholder_flags.bat` once. It copies vanilla flags under the new ideology names in your local copy only, which silences the missing-flag lines in the error log.
5. Restart the launcher, enable **Dawn and Dusk** in a playset with no other mods, and launch in debug mode.

The tools need Python 3 with `numpy`, `scipy`, `scikit-image`, `shapely` and `Pillow`. See [docs/TESTING.md](docs/TESTING.md) for what to check after each change.

## Generated files

Do not edit these by hand. Change the source and re-run the tool, from the repo root.

| Output in `mod/` | Source | Tool |
| --- | --- | --- |
| `map/*`, `history/states/*`, `localisation/english/replace/dnd_map_*` | `tools/data/map/<region>.json` | `tools/map/build.py` |
| `history/countries/*` | `tools/data/countries.csv` (capitals from `tools/data/map/built.json`) | `tools/countries/generate_country_history.py` |
| `history/units/*` | the built map | `tools/countries/generate_armies.py` |
| `gfx/flags/<TAG>.tga` | drawing code | `tools/countries/make_flags.py` |
| `localisation/english/replace/dnd_parties_l_english.yml` | `tools/data/parties.csv` | `tools/politics/generate_party_names.py` |
| `common/scripted_localisation/dnd_subideology.txt` | `common/ideologies/dnd_ideologies.txt` | `tools/politics/generate_subideology_loc.py` |
| `events/`, `common/national_focus/`, `common/decisions/`, `common/bop/` stand-ins, `common/ai_strategy/SOV.txt` and `ITA.txt` | the installed game | `tools/vanilla/generate_vanilla_stubs.py` |
| `interface/countrypoliticsview.gui`, `interface/countrydiplomacyview.gui` | the installed game | `tools/vanilla/patch_vanilla_gui.py` |

Generated files say so in their first lines, except state files, map files and flags.

## Conventions

Every new key starts with `dnd_` (or `DND_` in localisation). Full rules in [docs/CONVENTIONS.md](docs/CONVENTIONS.md).

## Legal

This is a fan mod for Hearts of Iron IV by Paradox Interactive. Most of it is original, but it carries files derived from Paradox's: the map bitmaps and map tables in `mod/map` (rebuilt from vanilla's), state files that replace vanilla states of the same name, the two patched interface screens, and empty stand-ins that keep vanilla ids. Placeholder flags copied from vanilla are kept out of the repository. Real-world geodata sources and licences are in [docs/CREDITS.md](docs/CREDITS.md).
