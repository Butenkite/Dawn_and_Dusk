# Conventions

## Naming

- **Prefix everything we add with `dnd_`:** focuses, events, ideas, decisions, flags, variables, scripted effects and triggers, on_actions files, interface sprites (`GFX_dnd_...`).
- **Localisation keys** use `DND_` in capitals for UI text (`DND_RULE_GROUP`). Keys whose name the engine derives from an object (ideology names, focus names) follow that object's own spelling.
- **Event namespaces** are `dnd_<area>` (for example `dnd_world`, `dnd_council`, `dnd_nga`).
- **Country-specific content** goes in files and keys that carry the tag: `dnd_NGA_focus.txt`, `dnd_NGA_delta_burns`.
- **Ideology groups** are lowercase single words or snake_case (`social_democrat`). Flavours (types) are snake_case nouns (`developmental_state`).

## Files

- **Vanilla script and art stay out of the repo.** If a vanilla folder has to go, add a `replace_path` line in `mod/descriptor.mod` (and the launcher template, `tools/setup/dawn_and_dusk.mod`) and write our own file. If we need a vanilla texture, point at its path; don't copy it.
- **Exception: interface layouts.** Screens we reshape (`mod/interface/countrypoliticsview.gui`, `mod/interface/countrydiplomacyview.gui`) are modified copies of vanilla, as most total conversions do. Each starts with a header listing what changed, and every change is marked `# DND`. New screen elements go in our own `dnd_` files where possible.
- **Exception: the map.** `mod/map` and the state files that replace vanilla states are rebuilt from vanilla's by `tools/map/build.py`. Never hand-edit them; change a region spec and rebuild.
- **One file per system, per country.** Avoid giant shared files that everyone edits.
- **Encoding:** script files (`common/`, `interface/`, `events/`) are UTF-8 **without** BOM: a BOM in a scripted GUI or scripted localisation file breaks parsing and crashed the game at load. Localisation `.yml` files are the opposite: UTF-8 **with BOM**, or the game silently ignores them. History files take either.
- **Indentation:** tabs.

## Story structure in script

These rules come straight from the design bible.

- **No ideology bars.** A country changes branch only at an inflection point, by an event or focus that swaps its tree.
- **Extremes are story-only.** Extreme flavours (`year_zero`, `chrome_capitalism`, `holy_war`, ...) have `can_be_randomly_selected = no` and are only ever set by script at a failure point.
- **Wars come from content.** War goals come from focuses, decisions and events (`create_wargoal`); justification is off by default through the `allow_wargoals` game rule.
- **Game rules are read once.** `dnd_setup_game_rules` turns them into global flags at start (`dnd_world_random`, `dnd_dusk_epilogue`, ...). Check the flag, not the rule.

## Generated files

Most of `mod/history`, all of `mod/map` and the vanilla stand-ins are
generated. The README has the full table of outputs, sources and tools. When a
country gets a hand-written history, add its tag to `HAND_WRITTEN` in
`tools/countries/generate_country_history.py` first.

## Layout

Everything the game loads lives in `mod/`. Tools, data and docs stay outside
it, so a Workshop upload of `mod/` carries nothing else. Run tools from the
repo root.

## Commits

One system or one country per commit, with a message that says what changed in game terms ("Add Nigeria's Federal Balance", not "update files").
