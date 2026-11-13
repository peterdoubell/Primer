# Offline reporting material in the Vercel bundle

The Python deployment excludes the plain reporting catalogue, historical catalogue snapshots and offline fidelity inventories and audits. The runtime uses the gzip catalogue. The files remain available in Git for authoring, tests and fidelity review.

The plain catalogue is 79,348,349 bytes and the gzip decompresses to identical bytes. The reader loaded all 98 forms with only the gzip present. A comparison using the Vercel builder's file matcher omitted another 227,670,255 bytes of offline material. It added no files. The preview build measures the deployed bundle separately because its Git input already omits some files.

These exclusions name the offline reports individually and retain the runtime's separately referenced scope-review evidence. The historical configuration inverse remains pinned to the exact bytes.
