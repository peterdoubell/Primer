# Original JPEG stream restoration

The convenience PDF image exporter was found to recompress some embedded JPEGs.
A source audit checked 24 whole-figure JPEG entries against their recorded PDF
page and uniquely matching image dimensions. Direct `/DCTDecode` streams were
compared with the actual saved bytes and decoded pixels.

Fourteen figures were restored to their exact original encoded streams: one
shoulder schematic, two wrist schematics, five knee MRI figures, two hip figures
and four ankle figures. Native dimensions, panel arrangements and annotations
are unchanged. Re-encoding had introduced maximum channel differences of 3–21
levels. This restoration removes that additional loss; it does not create new
anatomical detail or confer clinical approval.

Five entries already matched their original streams and were unchanged. Five
cases remain held: the CMYK triceps figure needs PDF colour-semantics review,
and four other entries lack a unique dimension-matched direct JPEG object.
They were not automatically replaced. Cropped panels and non-JPEG source
objects were outside this bounded pass.

All 14 restored originals were visually inspected together to confirm the same
figures, embedded labels, arrows and panel arrangements. Source hashes, old and
new image hashes, PDF pages and object identifiers are preserved in
[the audit](msk-original-jpeg-review/audit.json). The catalogue and every matching
evidence record now refer to the original bytes. Clinical reviews remain pending
and anatomical scope and figure counts are unchanged.

Reproduce with `tools/anatomy_sources/audit_pdf_jpeg_sources.py`, supplying the
recorded source-PDF map and an output directory. The script stages candidates
only; it refuses automatic treatment of masks, explicit PDF decode transforms,
CMYK colour semantics or ambiguous image matches. Original source PDFs and
superseded exports remain in `/tmp/primer-msk-sources/pdf-jpeg-audit/` and their
previous acquisition folders.

## Verification

The repeat audit now finds 19 byte-identical originals and the same five held
cases. The two restored ICC-based diagrams use the explicitly inspected IEC
61966-2.1 sRGB profile, SHA-256
`2b3aa1645779a9e634744faf9b01e9102b0c9b88fd6deced7934df86b949af7e`.
The audit holds unfamiliar PDF colour profiles rather than assuming DeviceRGB.

All 14 original images were opened through their actual shoulder, wrist, knee,
hip and ankle reporting pages on an isolated server. Every browser image decoded
at the expected native dimensions and opened/closed with the keyboard. HTTP
responses matched the restored hashes; browser error logs were empty. Source
diagram colours were inspected in the viewer. The owned tab and port-8806
server were stopped. Final source and HTTP checks are beside the initial audit.

The focused fidelity, rights, figure and reporting regression passed 201 tests.
There is no change to the 5,202-target scope or clinical approval: the goal
remains unproven, with 131 unverified candidates and 5,071 missing requirements.
