# LyNoS station examples in the source locator

The CT mediastinum and lung cancer readers link to their corresponding structure tables. Fifteen directly matched primary station codes provide links from 30 requirement rows to 39 original Pat9 node IDs. Each link selects the exact source mask on CT or its 3D surface. Primary, secondary and tertiary terms retain the authors’ wording.

The tables disclose masks 12, 14 and 26 with source codes that differ from the inventory, mask 19 with its code/side discrepancy, and undefined mask 21. Their full source annotations remain accessible in the general Pat9 viewer. Full station region boundaries remain a separate outstanding representation requirement. The source locator continues to grant no structure coverage or clinical approval.

Existing structure names, Stanford atlas matches and Radiology Assistant matches are retained. Regenerate only the reviewed station links with `python tools/anatomy_sources/lynos_station_locators.py`. The full locator generator invokes the same refresher after its external-source tables are built. The operation is idempotent and retains independently maintained display names.

The original crosswalk is recorded in `pat9-primary-station-crosswalk.json`. Each match is checked against the current original mask ID and literal primary code before publication. The source terms describe individual node masks under the authors’ IASLC 2009 scheme. [LyNoS publisher record](https://zenodo.org/records/10102261)
