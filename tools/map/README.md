# Map tools

The mod's map is rebuilt region by region from real geography, not painted
by hand. Everything here is reproducible: change a spec, re-run, validate.

## Pipeline

```
python tools/map/build.py tools/data/map/southern_africa.json --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"
python tools/map/build.py tools/data/map/central_africa.json --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"
python tools/countries/generate_country_history.py      # capitals of rebuilt countries move
python tools/countries/generate_congo_war.py --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"   # troops on the 2000 front
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
  country's `claims` are claims on all of it.
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
