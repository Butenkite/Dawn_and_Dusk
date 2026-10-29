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
  - DR Congo: territories CC BY 3.0 IGO (OCHA DR Congo, Référentiel
    Géographique Commun); provinces ODbL 1.0 (OpenStreetMap contributors)
  - Republic of the Congo, Equatorial Guinea, Chad, Uganda: provinces or
    regions ODbL 1.0 (OpenStreetMap contributors); districts public domain
    (Congo, Uganda), CC BY 4.0 (Equatorial Guinea: WRI Congo Basin Forest
    Atlas), CC BY 3.0 IGO (Chad: OCHA Chad)
  - Central African Republic: CC BY 2.5 (Wikimedia) and CC BY 3.0 (UNHCR)
  - Cameroon: CC BY 3.0 (Wikimedia) and CC BY 4.0 (Open Africa)
  - Gabon: provinces CC BY-SA 3.0 (Wikipedia), departments CC BY 3.0 (Wikimedia)
  - Rwanda: CC BY 4.0 (Rwanda Geo Portal, Open Data Rwanda)
  - Burundi: public domain / CC0
  - West Africa: CC BY 4.0 (Nigeria: GRID3; Ghana districts; Burkina Faso and
    Côte d'Ivoire: World Bank; Mali: DNCT and OCHA; The Gambia: World Bank),
    CC BY 3.0 IGO (Liberia, Sierra Leone, Guinea, Senegal, Mauritania
    departments, Cape Verde concelhos: OCHA ROWCA and national governments),
    ODbL 1.0 (Togo regions, Guinea-Bissau, Cape Verde islands: OpenStreetMap
    contributors), CC BY 3.0 (Niger departments), public domain (Benin);
    share-alike: Ghana regions and Togo districts (CC BY-SA 2.0,
    OpenStreetMap) and Mauritania regions (CC BY-SA 3.0, Princeton). Niger's
    regions come from Natural Earth (public domain).
  - East Africa: CC BY 3.0 IGO (Sudan and South Sudan: OCHA and the IMWGs;
    Eritrea subzones, Djibouti districts, Kenya constituencies, Tanzania
    districts, Madagascar districts: OCHA, FEWS NET, IEBC, NBS Tanzania,
    BNGRC), CC BY 4.0 (Ethiopia regions: Open Africa / Code for Ethiopia;
    Somalia districts: GPEI; Comoros districts: COSEP), ODbL 1.0 (Ethiopia
    zones and woredas: Open Africa; Eritrea, Somalia, Tanzania, Madagascar and
    Comoros regions: OpenStreetMap contributors), public domain (Kenya
    counties: RCMRD; Djibouti regions and Mayotte: Natural Earth).
  - North Africa and the Middle East: ODbL 1.0 (Morocco, Tunisia, Kuwait
    and Bahrain, and the regions of Algeria, Egypt, Saudi Arabia, Yemen, Oman,
    the UAE and Cyprus: OpenStreetMap contributors), CC BY 3.0 IGO (Syria:
    UN Cartographic Section and OCHA; Egypt, Iraq and Yemen districts: OCHA
    with CAPMAS, Iraq's Central Statistics Office and Yemen's CSO), CC BY 4.0
    (Palestine: Open Data Watch; Qatar: Qatar Open Data Portal), CC BY 2.5
    (Jordan governorates: Wikimedia), public domain or CC0 (Israel, Lebanon,
    Iraq governorates, Jordan districts, Algeria's wilayas as districts:
    Wikimedia; Libya: Natural Earth); share-alike: Saudi governorates (CC BY-SA
    2.0, OpenStreetMap) and Cyprus municipalities (CC BY-SA 3.0, Wikipedia).
    Oman's district set (licensed by direct permission) is not used.

Population figures are taken from national censuses around 2000 and are
approximate by design (see the `_sources` note in each region spec under
`tools/data/map/`). The Second Congo War front lines of 1 January 2000 follow
International Crisis Group Africa Reports 26 and 27 (2000-2001), Human Rights
Watch, "Uganda in Eastern DRC" (2001), and IRIN reporting from late 1999. The
RUF's zone in Sierra Leone under the Lomé ceasefire (Kailahun, Kono,
Koinadugu, Bombali, Tonkolili, Kambia) is an approximation from the same
period's reporting.

East Africa on 1 January 2000: Somalia's administrations and factions by
district follow the UK Home Office "Somalia Assessment" (April 2001), which
summarises UN and NGO reporting from 1998-2000; the Somaliland-Puntland line
through Sool and Sanaag and the split of Galkayo are approximations. The SPLA's
areas in southern Sudan, the Nuba Mountains and southern Blue Nile are drawn by
county from the record of Operation Thunderbolt (1997), the garrison towns the
government still held (Juba, Wau, Aweil, Torit and Kapoeta until 2002, Raga
until June 2001) and IRIN reporting on Kurmuk; Upper Nile, Unity and northern
Jonglei stay with Khartoum and its allied militias. That is an approximation:
the real lines were towns and roads, not counties. Eritrea's hold on Zalambessa
and Irob until May 2000 and Ethiopia's on Badme since February 1999 follow the
usual accounts of the war.

North Africa and the Middle East on 1 January 2000: the Western Sahara berm
(from MINURSO maps), the Golan ceasefire line of 1974 and the Cyprus Green Line
are hand-drawn approximations, a few kilometres out at best. At this scale
the Oslo patchwork of Areas A, B and C cannot be drawn: the Palestinian
Authority holds the West Bank governorates and Gaza, Israel the Jerusalem and
Jericho governorates (East Jerusalem and the Jordan Valley). The South Lebanon
Army's zone is the districts of Bint Jbeil, Marjayoun and Hasbaya (the SLA
left Jezzine in June 1999). The Kurdish administrations follow the districts
each party held after the Washington Agreement of 1998.

## Flags

Lesotho and Swaziland flags are simple drawings made by `tools/countries/make_flags.py`.
The banners of the three Congolese rebel movements (RCD-Goma, MLC, RCD-ML)
and of the RUF are original designs drawn by the same script.
The SPLM/A, Somaliland, Comoros (1996-2001, without its inscriptions),
Mauritius and Seychelles flags are simple drawings of the real ones. Puntland,
the Somali factions (USC/SNA, USC/SSA, Hiiraan, RRA, JVA, SNF) and Anjouan are
original designs in the spirit of the banners they flew. The SADR, the
Kurdistan Region (for the KDP) and Northern Cyprus flags are simple drawings
of the real ones; the South Lebanon Army and PUK flags are original designs.
