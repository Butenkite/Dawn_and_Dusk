# Conventions

## Naming

- **Prefix everything we add with `dnd_`:** focuses, events, ideas, decisions, flags, variables, scripted effects and triggers, on_actions files, interface sprites (`GFX_dnd_...`).
- **Localisation keys** use `DND_` in capitals for UI text (`DND_RULE_GROUP`). Keys whose name the engine derives from an object (ideology names, focus names) follow that object's own spelling.
- **Event namespaces** are `dnd_<area>` (for example `dnd_world`, `dnd_council`, `dnd_nga`).
- **Country-specific content** goes in files and keys that carry the tag: `dnd_NGA_focus.txt`, `dnd_NGA_delta_burns`.
- **Ideology groups** are lowercase single words or snake_case (`social_democrat`). Flavours (types) are snake_case nouns (`developmental_state`).

## Files

- **Vanilla script and art stay out of the repo.** If a vanilla folder has to go, add a `replace_path` line in `descriptor.mod` and write our own file. If we need a vanilla texture, point at its path; don't copy it.
- **Exception: interface layouts.** Screens we reshape (`interface/countrypoliticsview.gui`, `interface/countrydiplomacyview.gui`) are modified copies of vanilla, as most total conversions do. Each starts with a header listing what changed, and every change is marked `# DND`. New screen elements go in our own `dnd_` files where possible.
- **One file per system, per country.** Avoid giant shared files that everyone edits.
- **Encoding:** script files are UTF-8. Localisation `.yml` files must be UTF-8 **with BOM**, or the game silently ignores them.
- **Indentation:** tabs.

## Story structure in script

These rules come straight from the design bible.

- **No ideology bars.** A country changes branch only at an inflection point, by an event or focus that swaps its tree.
- **Extremes are story-only.** Extreme flavours (`year_zero`, `chrome_capitalism`, `holy_war`, ...) have `can_be_randomly_selected = no` and are only ever set by script at a failure point.
- **Wars come from content.** War goals come from focuses, decisions and events (`create_wargoal`); justification is off by default through the `allow_wargoals` game rule.
- **Game rules are read once.** `dnd_setup_game_rules` turns them into global flags at start (`dnd_world_random`, `dnd_dusk_epilogue`, ...). Check the flag, not the rule.

## Generated files

`history/countries/` is generated. Change `tools/data/countries.csv` and run `python tools/generate_country_history.py`. When a country gets a hand-written history, add its tag to `HAND_WRITTEN` in that script first.

## Commits

One system or one country per commit, with a message that says what changed in game terms ("Add Nigeria's Federal Balance", not "update files").
