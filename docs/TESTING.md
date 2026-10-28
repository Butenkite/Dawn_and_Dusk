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
python tools/patch_vanilla_gui.py "C:/Steam/steamapps/common/Hearts of Iron IV"
python tools/generate_vanilla_stubs.py "C:/Steam/steamapps/common/Hearts of Iron IV"
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

## Foundation checks

- [ ] The mod shows up in the launcher and the game reaches the main menu.
- [ ] Game rules show a **Dawn and Dusk** group with Outside World, The 2040 Deadline and the war goal rule set to Focuses Only.
- [ ] The bookmark screen shows **The New Millennium**, dated 1 January 2000.
- [ ] South Africa, Egypt and Liberia can be picked.
- [ ] The politics screen shows the new ideology names (Social Democrat, Authoritarian, ...) and hovering the leader shows a flavour.
- [ ] The date in game reads 2000.
- [ ] Console: `tag SAF`, then try to justify a war goal on a neighbour. The option should not be offered.

## Known gaps (expected, not bugs)

- Borders are vanilla's. Some 1939 border changes are applied, because the start date is past them. The map pass fixes this.
- Ideology icons reuse vanilla's four icons.
- No armies, technology, focus trees or events yet.
- Vanilla files we still load (ideas, characters, MIOs) are 1936 content. Their references now resolve to empty stand-ins, so they log few errors, but they still exist until each system gets its 2000 replacement.
- Most countries have placeholder party names ("Liberal Party"); real ones live in `tools/data/parties.csv`.
