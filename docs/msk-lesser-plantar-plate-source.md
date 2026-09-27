# Lesser-MTP plantar-plate MRI reference

The [Siddle et al. 2017 primary article](https://link.springer.com/article/10.1186/s12891-017-1668-0)
and Figure 1 were inspected. Panels a/b identify an intact third-MTP plantar
plate and capsule in a control subject. The remaining panels depict tears,
absent plates and erosions at other joints. They are explicitly distinguished.

The source grants CC BY 4.0, with no contrary figure credit. The PDF's original
page-4 JPEG is 1420 × 2006 pixels, substantially larger than the 567 × 801 web
preview. Its entire encoded image stream is retained without crop, resizing,
recompression or annotation changes. Original a–h labels and arrows were
visually checked. Acquisition acknowledgements and author credits are retained.

The file is `web/reference-media/msk-open/forefoot-third-mtp-plantar-plate-siddle-fig1.jpg`.
Its SHA-256 is `798342c0beebb60fe891b22a98a94afd862830b711aef8ebc8b726b26670796c`.
The catalogue and evidence ledger record its SHA-256, source PDF hash, page,
native dimensions, licence and limitations. The full composite is labelled
mixed; only panels a/b are selected for the normal-reference candidate.

One partial candidate binds `diabetic_foot.lesser_mtp_plantar_plates.body`,
explicitly at **mtp3 only**. This does not verify complete plate extent,
attachments, margins, tendon interfaces or other digit-specific sites. The
existing site-expansion requirement remains open. Individual age, sex and side
are unknown. This is a normal anatomical adjunct, not a diabetic-foot infection
case or a newly introduced instability indication. No report scope or approval
was changed.

The Einstein 2022 article inspected in this pass supplies pathological plate
examples rather than the needed normal reference. The 2023 forefoot review has
noncommercial terms and was not imported. Neither was substituted for the
normal third-MTP example.

## Extraction and runtime verification

The convenience `pypdf` ImageFile export re-encoded this JPEG, changing decoded
values by up to 16 grayscale levels. That output was excluded. The integrated
file is byte-identical to the original page-4 `/Im0` `/DCTDecode` stream; its
1420 × 2006 dimensions, embedded a–h labels and arrows were inspected.

On an isolated local server, the actual diabetic-foot Images tab displayed the
mixed-panel caption, MRI label, source links, credit and anatomical limits.
The browser decoded 1420 × 2006 pixels. Enter opened the image, full-size mode
preserved native dimensions, and Escape restored focus. A 390-pixel mobile
viewport showed the complete figure and scrollable caption without horizontal
page overflow. Browser error logs were empty; live HTTP bytes and API metadata
matched the catalogue. The temporary tab and owned port-8805 server were closed.

The existing hallux tests now select digit 1 explicitly, rather than treating
every foot reference as hallux anatomy. A separate third-MTP test protects the
original stream hash, local site, selected normal panels and pending approval.
The focused fidelity/rights/forefoot/catalogue regression passes 159 tests.
