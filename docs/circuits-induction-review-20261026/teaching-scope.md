# Current teaching integration

The two lessons retain their original assessments, prerequisites, media IDs and illustrations. Only authored teaching and learning outcomes are added to their curriculum objects. `original-lessons.json` and the preservation test recover the original complete physics curriculum fingerprint.

Sources inspected on 2026-10-26:

- [OpenStax: Kirchhoff’s rules](https://openstax.org/books/university-physics-volume-2/pages/10-3-kirchhoffs-rules): conservation-based circuit analysis.
- [OpenStax: mutual inductance](https://openstax.org/books/university-physics-volume-2/pages/14-1-mutual-inductance): linked flux and induced emf between circuits.
- [Partovi and Morris, Electrodynamics of a Magnet Moving through a Conducting Pipe](https://arxiv.org/abs/physics/0406085): the paper treats an infinitely long conducting shell with finite magnet geometry and broader electromagnetic behavior. The current finite-length pipe implementation is a separately derived low-speed resistive-current approximation, not a reproduction of that paper’s full boundary-value solution. The historical numerical benchmark alone does not validate its full control domain.

Current evidence separately checks circuit/field laws, finite-wall quadrature, nineteen trajectory boundary cases and authenticated mounting at two viewport widths. The reader smoke proof checks served teaching content and station reachability; it does not establish complete speech or graphical correspondence. Those checks, primary-source review for the remaining station constants, strict historical compatibility and the full regression suite remain release requirements. No whole-physics or whole-goal completion is claimed.

## Additional source findings, 2026-10-26

[NPL conductivity calibration documentation](https://www.npl.co.uk/products-services/magnetics/ac-and-dc-conductivity) identifies 58 MS/m with 100% IACS. This supports the reference-conductivity preset, not any arbitrary actual copper sample.

[Incept1D’s own Paschen model documentation](https://chombo-discharge.github.io/Incept1D/examples/paschen.html) reproduces the A=15 and B=365 conventional air-like coefficients and gives a fitted E/p range of 100–800 V/(cm Torr). It explicitly excludes attachment in this reduced model and distinguishes algebraic verification from real-air validation. The current station already discloses attachment omission, but needs an explicit reduced-field validity readout for both imposed state and predicted threshold before release. The source also treats secondary emission as a cathode/surface parameter, which should be reflected in the control label. This finding remains open; it is not a completed source approval.

### Reduced-field finding implemented

The current core reports imposed and threshold reduced fields in V/(cm Torr), classifies them separately against 100–800, and records the threshold classification at every plotted gap. The reader exposes both values and extrapolation status in visible text, the quantity ledger and dynamic narration. The control identifies cathode secondary emission. The existing attachment-free and non-calibrated-air limitations remain explicit. An independent unit-conversion test covers 162 combinations and every sampled threshold-curve point. This verifies implementation of the stated model domain, not physical validation of real-air discharge.

## Electrostatic derivation and constants

[Fitzpatrick’s University of Texas dielectric-interface derivation](https://farside.ph.utexas.edu/teaching/jk1/lectures/node42.html) supplies the planar image-charge solution and interface polarization density. Setting the source-side relative permittivity to one gives the current station’s contrast factor. The finite fixed-charge spherical shell is an additional derivation: its exterior source field equals that of its central charge, and the image potential is harmonic over the shell interior. The spherical mean-value property therefore gives the integrated interaction and force without treating the physical shell as a polarizable conductor. The condition that the shell does not cross the interface is essential. The independent surface-force integration checks this extension; it is not a claim that the source describes an actual rubbed balloon.

The numerical vacuum permittivity matches the [NIST 2022 CODATA value](https://www.physics.nist.gov/cgi-bin/cuu/Value?eqep0=). The constants are numerical recommended values; vacuum permittivity and permeability are not claimed to be exact SI-defining constants.
