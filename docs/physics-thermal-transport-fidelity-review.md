# Thermal contact and energy transport

The existing `phys.0.hot-cold` activity assumes equal heat capacities without
calculating energy. The `phys.2.heat` activity supplies qualitative pathway
motifs. The new `physics-thermal-lab` adds physical calculations to both actual
lesson routes; their original illustrations and activities remain available.
The heat lesson's generic particle chamber is replaced by a dimensioned steady
conducting slab. Other spatial bindings are unchanged.

## Models and physical scope

Two insulated, internally uniform bodies obey
C_A T_A′ = −G(T_A−T_B), C_B T_B′ = G(T_A−T_B).
Their temperature difference has time constant
1/[G(1/C_A+1/C_B)]. The common energy-balance temperature is capacity-weighted,
not generally the arithmetic mean. The signed transferred energy determines
both temperature changes. At G=0 no contact transfer occurs; the energy-balance
temperature is not presented as a state they will reach. Temperature curves use
seconds and Celsius; the separate ledger uses joules and conserves energy.
This is a hypothetical lumped pair, not cocoa, skin, a melting ice cube or a
cooling pizza. Latent heat and heat loss to a room remain outside this activity.

The conduction example calculates Fourier flux through a homogeneous slab
with fixed boundaries, constant conductivity and no internal generation.
The temperature profile is linear. Signed rates distinguish direction from
magnitude and stationary matter from transported energy. The square 3D slab
uses the same area and thickness; 0.1 scene unit represents one centimetre in
all three directions. Sixteen colour bands sample the exact temperature at
their centres on a fixed −20…120 °C scale. They are display bands, not physical
interfaces. The gold arrow is directional; its length does not encode watts.
The numeric rate label responds to conductivity even though conductivity does
not change the physical slab dimensions or its fixed-boundary temperatures.

The convection example solves a steady water-channel energy balance:
ṁ c_p dT/dx = h P(T_wall−T). P=0.04 m, c_p=4180 J/(kg·K), and constant wall
T and h are explicitly hypothetical assumptions. The analytical exponential
profile gives Q̇=ṁ c_p(T_out−T_in). The ledger takes inlet enthalpy as its
reference. Water flows inlet to outlet even when it loses energy to a colder
wall. The wall and inlet sliders are restricted to 5–95 °C for ambient-pressure
liquid water. No buoyancy, natural-convection circulation, turbulence or
varying fluid properties are simulated. Those remain required for the lesson's
rising-air example; this is a faithful forced-convection example.

The radiation example is a diffuse grey surface facing a large black enclosure
with view factor one, across a vacuum. Thermal absorption equals emissivity.
Emission and absorption use absolute kelvin temperatures; net outward power
is εσA(T_surface⁴−T_surroundings⁴). Emission and absorption can both be nonzero
at equal temperatures while the net exchange is zero. ε=0 models an ideal
reflector, not a measured coating. The arrows represent emitted/absorbed energy
directions; reflected radiation is excluded from these bars and explicitly
identified in the note. Solar shortwave colour, spectral dependence, finite
view factors and conductive flask supports remain outside this example.

The [OpenStax heat-transfer chapter](https://openstax.org/books/university-physics-volume-2/pages/1-6-mechanisms-of-heat-transfer)
provides the Fourier and thermal-radiation laws and the distinction between
stationary matter and bulk fluid transport. The rounded numerical Stefan–
Boltzmann constant is from [NIST CODATA](https://physics.nist.gov/cgi-bin/cuu/Value?sigma).
The calculations and SVG/3D artwork are original; no source figure is copied.
The water profile and two-body solution follow directly from the stated energy
balances rather than a fitted picture.

## Verification

`tools/check_physics_thermal_lab.js` checks 3,168 physical states, including
reversed/equal temperatures, unequal capacities, disconnected contact and
zero/full emissivity. Its independent RK4 spatial integration checks the
water profile against the energy-balance differential equation. Contact checks
use capacity-weighted conservation, both signed energy changes and numerical
time derivatives. Radiation gross powers are independently reconstructed
using SI-defining k_B, h and c rather than the implementation's rounded sigma.
Actual mounted SVG coordinates and signed bars are checked in 51 states.
Eighty-one 3D states check all slab extents, centre temperatures and rates.
Strict backend bindings reject cross-lesson scenarios and extra properties.

Actual lesson browser checks at 1440 and 390 CSS pixels exercise 37 heat states
and 18 contact states per viewport, ten additional slab control extrema per
viewport, preset/reset, fit/enlarged plots, active control visibility, SVG text
bounds and body overflow. The rotatable slab also receives keyboard rotation
and Home reset. The original activities remain reachable. Local browser checks
are not authenticated-production verification or whole-curriculum approval.

This closes the observed quantitative thermal-contact and transfer examples.
Natural convection, phase changes and the other named cases above remain
incomplete. The full mathematics, physics and clinical/commercial radiology
objective remains active; counts and equation checks do not establish it.
