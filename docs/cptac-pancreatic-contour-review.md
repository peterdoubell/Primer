# Pancreatic source contours and native raster error

Every original CLOSED_PLANAR contour from both independently acquired C3L-02112 CT series is preserved and displayed: 43 arterial-labelled and 49 venous-labelled contours. Archive SHA-256 must match the prior original geometry audit before the same open source is decoded. Source CT shape/orientation/HU scale, every physical image position, every referenced SOP and every source contour plane are checked. Simple source polygons are checked for repeated vertices and self-contact; multiple contours per plane are rejected for explicit combination review.

The review atlas shows unmarked original CT, original continuous RTSTRUCT polygon (blue), and original polygon plus derived raster boundary (amber). Even/odd membership at actual native pixel centres creates a conversion candidate; it does not redefine original annotation truth. No smoothing, supersampling, registration or cross-acquisition contour transfer is performed. Original CT is displayed with nearest pixels at physical aspect ratio in a −160 to 240 HU window. Derived arrays remain in ignored research storage, with native plane indices stored explicitly; the selected-plane arrays are not advertised as contiguous 3D masks.

The venous-labelled source has no contour on acquired native planes **534 and 535**, between annotated planes 533 and 536. These original CT images are displayed separately. Their annotation state remains **unknown**, not negative. No contour is interpolated through this gap and the other acquisition cannot supply its missing anatomy.

| Source role | Contours | Source → raster conservative bound | Raster → source conservative bound | Recorded ROI volume | Annotated polygon slabs | Selected-pixel slabs |
|---|---:|---:|---:|---:|---:|---:|
| Arterial-labelled | 43 | 0.650389 mm | 0.444246 mm | 12.411718 cm³ | 12.322059 cm³ | 12.316360 cm³ |
| Venous-labelled | 49 | 1.367897 mm | 0.425626 mm | 12.117638 cm³ | 11.476346 cm³ | 11.468800 cm³ |

Every direction is measured against all opposite boundary segments, with arclength samples at no more than 0.125 mm and a conservative half-gap allowance for unsampled points. These are planar conversion bounds, not 3D surface, inter-series anatomical, clinical tolerance or segmentation accuracy measures. The largest forward venous bound occurs on original contour 1/native plane 536 (final atlas page); the largest arterial bound occurs on contour 35/native plane 168 (page 12). Raster boundaries differ from continuous source features even though each raster section has one 4-connected foreground component and no 8-connected background holes. That 2D result does not establish 3D anatomical topology.

Slab arithmetic assigns 0.625 mm thickness to **only each annotated centre**. It is 0.722% and 5.292% below the corresponding recorded polygon ROI volumes, respectively. It is not a validated lesion volume and does not define source end caps or account for unannotated interior planes. First/last contour masks remain positive (503/834 arterial and 241/983 venous selected pixels). Neither source endpoint is zeroed, capped, extended or repaired to force volume agreement. The original source volume field, distinct area calculations and unresolved semantics are all retained.

The source annotations are location/target contours, with source ROI names retained verbatim. No whole-pancreas, ducts, neural tissue, vessel wall/lumen, tumour histology or full staging coverage is inferred from these polygons. Current source image and annotation CC BY 4.0 attribution/version evidence is recorded separately in the [original source review](cptac-pancreatic-source-review.md) and [attribution](cptac-pancreatic-source-review/ATTRIBUTION.md). Original CSV and RTSTRUCT tracking UIDs still differ; phase adequacy and source diagnosis remain unapproved. These images and derivatives are offline review evidence, not new clinical representation credit or runtime-promoted 3D models.

Representative presentation inspection on 4 October 2026 covered arterial page 1, both maximum-error pages and both unannotated-plane views. It checked legibility, physical axes and source/derived boundary distinction. All source contours have atlas panels and fingerprint coverage; independent clinical boundary interpretation of all panels remains required. The full radiology objective remains active and incomplete.

[Machine-readable per-contour measurements and atlas fingerprints](cptac-pancreatic-contour-review/contour-raster-review.json)

## arterial-labelled atlas

- [Contours 2, 1, 0](cptac-pancreatic-contour-review/arterial-labelled-contour-page01.png)
- [Contours 5, 4, 3](cptac-pancreatic-contour-review/arterial-labelled-contour-page02.png)
- [Contours 8, 7, 6](cptac-pancreatic-contour-review/arterial-labelled-contour-page03.png)
- [Contours 11, 10, 9](cptac-pancreatic-contour-review/arterial-labelled-contour-page04.png)
- [Contours 14, 13, 12](cptac-pancreatic-contour-review/arterial-labelled-contour-page05.png)
- [Contours 17, 16, 15](cptac-pancreatic-contour-review/arterial-labelled-contour-page06.png)
- [Contours 19, 18, 22](cptac-pancreatic-contour-review/arterial-labelled-contour-page07.png)
- [Contours 21, 20, 25](cptac-pancreatic-contour-review/arterial-labelled-contour-page08.png)
- [Contours 24, 23, 28](cptac-pancreatic-contour-review/arterial-labelled-contour-page09.png)
- [Contours 27, 26, 31](cptac-pancreatic-contour-review/arterial-labelled-contour-page10.png)
- [Contours 30, 29, 33](cptac-pancreatic-contour-review/arterial-labelled-contour-page11.png)
- [Contours 32, 36, 35](cptac-pancreatic-contour-review/arterial-labelled-contour-page12.png)
- [Contours 34, 39, 38](cptac-pancreatic-contour-review/arterial-labelled-contour-page13.png)
- [Contours 37, 42, 41](cptac-pancreatic-contour-review/arterial-labelled-contour-page14.png)
- [Contours 40](cptac-pancreatic-contour-review/arterial-labelled-contour-page15.png)

## venous-labelled atlas

- [Contours 48, 47, 46](cptac-pancreatic-contour-review/venous-labelled-contour-page01.png)
- [Contours 45, 44, 43](cptac-pancreatic-contour-review/venous-labelled-contour-page02.png)
- [Contours 42, 41, 40](cptac-pancreatic-contour-review/venous-labelled-contour-page03.png)
- [Contours 39, 38, 37](cptac-pancreatic-contour-review/venous-labelled-contour-page04.png)
- [Contours 36, 35, 34](cptac-pancreatic-contour-review/venous-labelled-contour-page05.png)
- [Contours 33, 32, 31](cptac-pancreatic-contour-review/venous-labelled-contour-page06.png)
- [Contours 30, 29, 28](cptac-pancreatic-contour-review/venous-labelled-contour-page07.png)
- [Contours 27, 26, 25](cptac-pancreatic-contour-review/venous-labelled-contour-page08.png)
- [Contours 24, 23, 22](cptac-pancreatic-contour-review/venous-labelled-contour-page09.png)
- [Contours 21, 20, 19](cptac-pancreatic-contour-review/venous-labelled-contour-page10.png)
- [Contours 18, 17, 16](cptac-pancreatic-contour-review/venous-labelled-contour-page11.png)
- [Contours 15, 14, 13](cptac-pancreatic-contour-review/venous-labelled-contour-page12.png)
- [Contours 12, 9, 11](cptac-pancreatic-contour-review/venous-labelled-contour-page13.png)
- [Contours 10, 0, 8](cptac-pancreatic-contour-review/venous-labelled-contour-page14.png)
- [Contours 7, 6, 5](cptac-pancreatic-contour-review/venous-labelled-contour-page15.png)
- [Contours 4, 3, 2](cptac-pancreatic-contour-review/venous-labelled-contour-page16.png)
- [Contours 1](cptac-pancreatic-contour-review/venous-labelled-contour-page17.png)
- [Unannotated acquired plane 534](cptac-pancreatic-contour-review/venous-labelled-unannotated-plane534.png)
- [Unannotated acquired plane 535](cptac-pancreatic-contour-review/venous-labelled-unannotated-plane535.png)
