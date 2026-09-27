# Muscle investigation source-view correction

27 September 2026. Both `ra.mri-muscle-injury` and `ra.mri-muscle-disease`
inherited a generic long-bone spatial schematic despite requiring named
muscles, tendons, aponeuroses, fascia and regional distribution assessment.

Both investigations now offer six registered Z-Anatomy source groups. They
start with the muscle layer selected and regional clipping disabled, so stored
muscle objects are not truncated to a joint window. Reset restores the same
muscle/uncropped state. Layer availability is checked before loading, and the
configuration permits this mode only for supported limb source groups.
Existing other views retain their previous defaults.

These are the available source groups, not an exhaustive inventory of every
muscle in the examined region. The interface preserves adult right-sided,
contralateral, tendon/aponeurosis/fascia and internal-architecture limitations.
It does not simulate oedema, tears, fatty replacement or denervation. Existing
site-expansion requirements and scope blockers remain unchanged. No source mesh
was modified and no anatomical completeness or clinical review was approved.

185 relevant tests passed. Browser verification checked all six actually
rendered muscle groups, uncropped initial state, reset after layer/crop changes,
the non-traumatic disease route, mobile width without overflow and no console
errors. [Region evidence](msk-muscle-region-review/regions.json),
[desktop proof](msk-muscle-region-review/browser-desktop.png) and
[mobile proof](msk-muscle-region-review/browser-mobile.png) preserve results.
The temporary server/tab were closed and viewport reset.

The [current audit](msk-verification-muscle-regions-2026-09-27.json) and review
queue retain the entire 5,229-requirement scope with clinical/commercial
readiness false. Pending presentation-dependency hashes were refreshed for the
viewer/configuration change without carrying forward any clinical approval.

## Regional configuration checks

The catalogue now rejects empty/non-list source collections, missing or
non-text anatomy limits, unsupported display modes and conflicting whole-foot
framing plus uncropped-muscle settings. These configurations cannot silently
present a different anatomical extent from their label. Valid configurations
and source geometry are unchanged. Thirty-seven relevant tests passed,
including six malformed-configuration cases. All eleven existing BodyParts3D
regions retain an available default layer; this inventory check is not a new
browser or clinical validation of those regions.
