# Draft technical inquiry — not sent

Recipient: Thor Andreassen, thor.andreassen@du.edu (public dataset contact)

Subject: S192803 MRI export and STL coordinate convention — Dryad zkh1893gw

Hello Dr Andreassen,

We are evaluating the public S192803 dataset as a possible anatomy reference
for an educational radiology application. Thank you for making it available.
Both downloaded archives match Dryad's published SHA-256 checksums.

Could you clarify three points?

1. S192803_MRI_Scan.mhd specifies a 1024 × 1830 × 130 MET_UCHAR grid. Its raw
   file passes the original ZIP CRC, but contains only 15,475 nonzero voxels in
   a small region overlapping the lateral tibial-cartilage mask; the rest is
   zero. Is a complete MRI volume available, or was this export intentionally
   limited to that region?
2. What is the documented transformation between the Raw MRI Scan STLs and
   MetaImage volumes? Offset + TransformMatrix × (Spacing × index) does not
   reach the native ACL STL bounds. We have not fitted or adopted an alternative.
3. Are the smoothing parameters and unsmoothed surfaces for the `_smooth.stl`
   files available? We would like to assess boundary detail without equating
   tessellation density with accuracy.

We can provide exact headers, CRCs and numerical comparisons if useful. We
have not described these files as a clinically validated image/model pair or
distributed modified anatomy.

Kind regards,
[Connected Gmail sender]

This is a prepared draft only. No external message has been sent. Explicit
permission to send through the connected Gmail account has been requested and
is pending; the account identifies the sender if permission is given.
