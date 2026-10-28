version="0.0.1"
tags={
	"Alternative History"
	"Gameplay"
	"Ideologies"
}
name="Dawn and Dusk"
supported_version="1.19.*"

# --- step 11 ---------------------------------------------------------------
# Every country must have a focus tree or the game crashes at the end of
# loading ("Country focus tree is not set", found in the crash dump). Vanilla
# focus trees are replaced, so common/national_focus/dnd_generic_focus.txt
# is the default tree.
#
# Overridden vanilla screens are rebuilt from the installed game by
# tools/patch_vanilla_gui.py; re-run it after every HOI4 update.
#
# Vanilla scripts we still load (laws, factions, peace deals, AI...) name
# vanilla's ideologies, characters and events. A missing one crashes the
# game at the end of loading. So:
#  - ideologies: four of our eight groups reuse vanilla's keys, and vanilla's
#    flavours live on as story-only types (see common/ideologies)
#  - characters: vanilla's are loaded but nobody recruits them
#  - events: replaced by hidden do-nothing stand-ins with the same ids
#    (tools/generate_vanilla_stubs.py)
replace_path="common/bookmarks"
replace_path="history/countries"

# Vanilla story content
replace_path="common/national_focus"
replace_path="common/focus_inlay_windows"
replace_path="events"
replace_path="common/decisions"
replace_path="common/decisions/categories"
replace_path="common/bop"
replace_path="common/ai_strategy_plans"
replace_path="common/on_actions"

# Vanilla starting armies
replace_path="history/units"

# Vanilla politics
replace_path="common/ideologies"
