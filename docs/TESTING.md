# Testing

## Every change

1. Launch with **Open game in Debug Mode** from the launcher.
2. Start a game, unpause for a few days, then open the error log:
   `Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log`
3. Search the log for `dnd`. Anything that mentions our files is ours to fix. Paste it into the chat when asking for help.

Useful console commands (open with the `` ` `` key):

- `tag SAF` switches to a country
- `event <id>` fires an event, once events exist
- `observe` lets the AI run every country
- `tdebug` shows ids and scopes when hovering things on the map

## After every HOI4 update

Patches change vanilla files we depend on, and an out-of-date copy can crash
the game at the end of loading. Re-run, with your HOI4 install folder:

```
python tools/vanilla/patch_vanilla_gui.py "C:/Steam/steamapps/common/Hearts of Iron IV"
python tools/vanilla/generate_vanilla_stubs.py "C:/Steam/steamapps/common/Hearts of Iron IV"
```

Then launch and check the error log before anything else.

## If the game crashes while loading

The crash folder (`Documents/Paradox Interactive/Hearts of Iron IV/crashes/`)
holds a `minidump.dmp`. The game's own assertion text is usually recoverable
from it with `hoi4.exe` at hand; that is how "Country focus tree is not set"
was found. Known causes so far:

- a country with no focus tree (keep a `default = yes` tree)
- a vanilla event id that no longer exists (keep the event stand-ins current)
- a UTF-8 BOM in a scripted GUI or scripted localisation file
- an overridden vanilla screen made from an older game version

## If the map will not load

The game refuses to start a map that logs any `MAP_ERROR`, and some map
mistakes show up only as missing or broken provinces in nudge. Run the
validator first; it checks everything below and more:

```
python tools/map/validate.py --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"
```

Causes found so far:

- a state split across two strategic regions
- four provinces meeting at one point ("Map invalid X crossing")
- a `victory_points` block with more than one province in it
- two state files with the same state id. Files in `mod/history/states` are
  named `<id>-<name>.txt`; when an update renames them, the old files must be
  deleted, not left next to the new ones. Update through git, not by
  unzipping over the folder. The map builder keeps state ids stable between
  builds (`tools/data/map/state_ids.json`) so this should be rare.
- a state left holding only a lake, which shows as a coloured blob owned by
  its 1936 owner

State files that replace vanilla states keep vanilla's file name even when
the state is now somewhere else (`770-Malawi.txt` holds a Congo state). That
is deliberate: a mod file replaces the vanilla file only if the names match,
so renaming it would load both and duplicate the state.

## After rebuilding a map region

```
python tools/map/build.py tools/data/map/<region>.json --vanilla "<HOI4>"
python tools/countries/generate_country_history.py
python tools/countries/generate_armies.py --vanilla "<HOI4>"
python tools/map/validate.py --vanilla "<HOI4>"
```

The second step moves capitals of rebuilt countries; the third re-places the
starting armies on the new provinces.

## Start checks

- [ ] The mod shows up in the launcher and the game reaches the main menu.
- [ ] Game rules show a **Dawn and Dusk** group with Outside World, The 2040 Deadline and the war goal rule set to Focuses Only.
- [ ] The bookmark screen shows **The New Millennium**, dated 1 January 2000.
- [ ] The politics screen shows the new ideology names (Social Democrat, Authoritarian, ...) and hovering the leader shows a flavour.
- [ ] Southern, central and west Africa show their rebuilt states; Lesotho, Swaziland, RCD-Goma, the MLC, RCD-ML and the RUF have names and flags; Benin, Burkina Faso and Côte d'Ivoire show their 2000 names.
- [ ] Sierra Leone and the RUF face each other across the ceasefire line, at peace, both with `dnd_lome_ceasefire` set.
- [ ] The Congo starts at war (Kinshasa against all three rebel movements, RCD-Goma against RCD-ML) with no war declaration popups.
- [ ] Console: `tag SAF`, then try to justify a war goal on a neighbour. The option should not be offered.

## Known gaps (expected, not bugs)

- Outside southern, central and west Africa, borders are vanilla's 1936 ones (North and East Africa included).
- Ideology icons reuse vanilla's four icons.
- Only the four Congo war sides, Sierra Leone and the RUF have armies and technology; no focus trees or events yet.
- Vanilla files we still load (ideas, characters, MIOs) are 1936 content. Their references resolve to empty stand-ins, so they log few errors, but they stay until each system gets its 2000 replacement.
- Without `tools/setup/make_placeholder_flags.bat`, the error log lists missing ideology flags. Harmless: the game falls back to the country's main flag.
- Most countries have placeholder party names ("Liberal Party"); real ones live in `tools/data/parties.csv`.
