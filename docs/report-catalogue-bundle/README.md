# Report catalogue bundle

Vercel excludes the plain descriptor reporting catalogue. The hosted reader already loads the gzip copy when it is present. The plain catalogue remains available to authoring and tests in the repository.

The plain file is 79,348,349 bytes. The gzip file is 3,875,305 bytes and decompresses to the same SHA-256 `decc8effb8b98dbaf39075404885a4b1b68dab920f5b12d9ec51e5150752f84c`. The deployment exclusion removes the duplicate plain file from the Python function input. A packed-only runtime check and historical compatibility tests verify the change.
