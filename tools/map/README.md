# Map tools

The mod's map is rebuilt region by region from real geography, not painted
by hand. Everything here is reproducible: change a spec, re-run, validate.

## Pipeline

```
python tools/map/build.py tools/data/map/southern_africa.json --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"
python tools/map/build.py tools/data/map/central_africa.json --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"
python tools/map/build.py tools/data/map/west_africa.json --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"
python tools/map/build.py tools/data/map/east_africa.json --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"
python tools/map/build.py tools/data/map/mena.json --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"   # north Africa + Middle East, one build (Gaza sits in a vanilla Sinai province)
python tools/countries/generate_country_history.py      # capitals of rebuilt countries move
python tools/countries/generate_armies.py --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"   # starting armies on the 2000 front lines
python tools/map/validate.py --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"
```

Regions are built in that order; each one leaves the earlier ones alone.

`build.py` takes every vanilla land province lying mostly inside the spec's
countries and redraws that area:

- **Projection:** longitude/latitude to HOI4 pixels uses a polynomial fitted
  to the HOI4 coastline (`tools/data/map/projection_africa.json`; median error
  0.8 px in Africa).
- **Provinces** are built from real district boundaries (geoBoundaries,
  ADM2, or ADM3 where the spec asks). Small districts are merged and large ones
  split until each province is near a target size that shrinks where people
  live (`province_size` in the spec), so cities and farmland are dense and
  deserts are open. Province borders prefer rivers. Metros listed in a state's
  `metros` become their own provinces, and `cities` with `city_province`
  get a small province carved around them.
- **States** come from the spec: hand-made groupings of districts (South
  Africa), or first-level regions split around their largest towns, with
  `groups` to merge small ones.
- **Lakes** listed in the spec (reservoirs built after 1936, and lakes
  vanilla leaves out) become lake provinces, with the heightmap lowered
  under them. Old lake provinces mostly inside the region are redrawn too,
  so a lake that has shrunk since 1936 (Lake Chad) comes back as land; any
  part of it beyond the region's borders joins the land around it.
- **Divided countries:** a country's `control` maps districts to the tag
  holding them (the Congo in 2000). States never straddle those lines;
  every state is a core of the country and of whoever holds it, and the
  country's `claims` are claims on all of it. `cores` adds cores for every
  state of the country (the SPLA on southern Sudan); `unit_claims` gives
  claims on states lying at least a fifth in the listed districts
  (Somaliland and Puntland over Sool and Sanaag). A country whose districts
  all belong to factions (Somalia) owns nothing at the start.
- **Occupied districts:** `occupied` lists districts (at any level, usually
  ADM3) the country owns but an enemy holds on the day (Zalambessa). They
  become states of their own, and their provinces are handed to the occupier
  with `set_province_controller`.
- **District states:** `state_units` builds states from the districts
  (`unit_level`) instead of the first-level regions (Ethiopia's zones);
  `groups` then names districts.
- **Territories of outside countries:** `adm1_only` takes just the listed
  regions (Mayotte, from France's Natural Earth regions), and `"capital":
  false` keeps the region from becoming that country's capital.
- **Lines that follow no district border** (the Western Sahara berm, the
  Golan ceasefire line, the Cyprus Green Line): `control_areas` lists
  polygons, in longitude/latitude, and the tag that holds what lies inside.
  `min_piece_px` (default 40) is the smallest piece of a region a line may
  leave as a state of its own; smaller pieces join their neighbour.
- **Names:** `state_names` renames states after every automatic step, by
  name, by `"TAG/name"`, or for all of a tag's states with `"TAG/*"`.
- **Several continents in one build:** a country's `continent` overrides the
  spec's.
- **Tiny regions** drawn as a broken thread of pixels (the Gaza Strip) are
  widened by a pixel so they hold together as one province.
- **Canals and straits:** when a province named by `adjacencies.csv` or
  `adjacency_rules.txt` is rebuilt, the builder points them at the new
  province holding most of its old pixels (the Suez Canal, Gibraltar, Hormuz)
  and writes `map/adjacency_rules.txt` into the mod.
- **Islands the projection cannot place** (far from the fitted coast):
  `retag_states` keeps vanilla states as drawn and rewrites their owner and
  2000 numbers (Mauritius, the Seychelles).
- **Regions too small for a province** (capital districts like Dakar or
  Bamako, a few pixels on this map) join the neighbouring state they border
  most; island groups with no neighbour stay small states of their own.
- **First-level regions** come from geoBoundaries, or from Natural Earth
  where a country's geoBoundaries set is unusable (`"adm1_source":
  "natural_earth"`, used for Niger).
- **Resources** are keyed by state key, or by `"ISO/first-level region"` to
  share an amount out over the states covering that region.
- It then writes state history (2000 population, category, factories,
  infrastructure, resources, victory points, ports), strategic region
  membership, building and unit positions, railways (from Natural Earth),
  supply hubs, and localisation, and records what it built in
  `tools/data/map/built.json` so later regions leave it alone.

Everything is written into `mod/`. Each run starts from the mod's current map files if they exist (so regions
build on each other) and vanilla's otherwise. To rebuild a region from
scratch, delete `mod/map/`, `mod/history/states/` and `tools/data/map/built.json`
first (this removes every region).

State ids are pinned by state key in `tools/data/map/state_ids.json` (kept
across rebuilds, and in git), so a state keeps its id and its file name
from one build to the next. The builder warns when an id has to change.

`validate.py` checks what crashes or quietly breaks the game: id gaps,
colours, provinces in no state or region or in two, state id gaps, victory
points and ports in the wrong state, ports inland, building and unit
positions outside their province, railways between provinces that do not
touch, supply nodes in water, capitals that are not states.

## Data

Downloaded on first use into `tools/map/cache/` (ignored by git). See
`docs/CREDITS.md` for sources and licences.
