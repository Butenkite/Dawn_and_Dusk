# Credits

## Map data

The map is generated from public geographic data (tools/map/):

- **Natural Earth** (public domain): coastlines, countries, populated
  places, rivers, lakes and railways. https://www.naturalearthdata.com
- **geoBoundaries** (William & Mary geoLab), gbOpen release: first and second
  level administrative boundaries. https://www.geoboundaries.org
  Licences per country, as stated in the geoBoundaries metadata:
  - South Africa, Zimbabwe, Mozambique, Lesotho, Malawi: CC BY 3.0 IGO
    (OCHA ROSEA and national statistics offices)
  - Zambia: CC BY 4.0 (GRID3, Office of the Surveyor General)
  - Namibia, Botswana, Angola: public domain
  - Eswatini: Open Database License 1.0 (OpenStreetMap contributors)

Population figures are taken from national censuses around 2000 and are
approximate by design (see `tools/data/map/southern_africa.json`).

## Flags

Lesotho and Swaziland flags are simple drawings made by `tools/make_flags.py`.
