# Anatomical display names

The laterality value `not_applicable` describes whether side metadata applies to a structure. The existing reporting contract continues to require assessment of that structure.

Ten inventory generators had prefixed that value to 259 structure names across 12 investigations. The shared `display_structure_name` function removes the prefixed marker only when the structure explicitly has `laterality: "not_applicable"`. It preserves other names, including right and left labels and source acronyms.

The current inventory and 12 locator files have been regenerated. Each structure retains its ID, required parts, laterality, conditions, reporting references and source URLs. The locator correction changes only display names. Existing source links, match classifications, counts and filters retain their previous evidence.

Run `python tools/anatomy_sources/build_structure_source_locators.py --refresh-display-names` to refresh these names without retrieving sources or creating source matches. A second run makes zero changes.

The reviewed inverse recovers the prior inventory and scope bytes exactly. The scope changes only its inventory fingerprint, and the dated reporting reconciliation continues to be checked against its original names.
