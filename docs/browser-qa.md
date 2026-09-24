# Browser QA evidence

Run browser checks against an isolated loopback Primer server. Checks that create
a test learner or record reviews require a disposable database. Supply the server
origin explicitly for mutating checks; public and production hosts are rejected.

The following tools create a new private directory under the operating system's
temporary directory for every run:

- `check_spatial_browser.cjs`
- `check_review_game_browser.cjs`
- `check_module_media_browser.cjs`
- `check_mobile_navigation.cjs`
- `check_legacy_browser.cjs`
- `check_learning_pathways.cjs`
- `check_detailed_anatomy.cjs`
- `check_content_resilience.cjs`
- `check_concept_browser.cjs`

They print `EVIDENCE_DIRECTORY=<absolute path>` before starting the browser. Read
that line to find screenshots and result reports. No command-line value controls
the output path, so an existing directory or its files cannot be selected for
overwrite or cleanup. The former output-directory argument in slot 3 is ignored.
Existing optional filters remain in slot 4; use `-` for the unused slot 3.

```sh
node tools/check_learning_pathways.cjs http://127.0.0.1:8793
node tools/check_module_media_browser.cjs http://127.0.0.1:8793 - --photos-only
node tools/check_concept_browser.cjs http://127.0.0.1:8793 - arts.1.beat
node --test tests/qa-browser.test.cjs
```

If Playwright is not installed locally, provide its node_modules directory through
`NODE_PATH`. QA wrappers should parse the printed directory rather than assume
the old output argument names a created directory. Preserve the resulting
evidence separately if it must survive operating-system temporary-file cleanup.
