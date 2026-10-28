version="0.0.1"
tags={
	"Alternative History"
	"Gameplay"
	"Ideologies"
}
name="Dawn and Dusk"
supported_version="1.19.*"

# The launcher reads its own copy of these lines from the .mod file next to
# the clone (template: tools/setup/dawn_and_dusk.mod); keep the two in step.
#
# Dawn and Dusk replaces vanilla's story content and keeps its systems. The
# kept systems still name vanilla ids, so those ids live on as empty
# stand-ins (tools/vanilla/generate_vanilla_stubs.py). See docs/TESTING.md
# for what crashes the game and why.

# The 2000 start and its countries
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
