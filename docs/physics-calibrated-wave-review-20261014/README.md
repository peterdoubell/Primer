# Calibrated ramp, sound and travelling-wave models

Three existing lesson artefacts now expose their physical coordinates. This is a targeted fidelity improvement, not approval of the whole physics curriculum or the radiology objective.

- `phys.1.machines`: the existing frictionless, quasistatic ramp relation F=Wh/L is plotted in metres and newtons. Every point and selected marker uses that scale; raising the 100 N load through 1 m retains 100 J of work. The separate 3D lever remains a different simple-machine example.
- `phys.1.sound`: the trace is pressure perturbation at one point over 0–10 ms, with arbitrary pressure units. Relative intensity uses amplitude squared in the declared fixed linear medium; it is not a watt-per-square-metre prediction.
- `phys.2.waves`: the graph shows y(x,t)=A sin[2πf(x/12−t)] across 0–12 m, with y in centimetres. A new 0–2 s snapshot control exposes rightward propagation at 12 m/s. The material points oscillate transversely. Different horizontal and vertical scales are explicit, so the drawn slope is not a physical string angle. Reflections, dispersion and nonlinear dynamics are outside the model.

The relations follow [OpenStax work](https://openstax.org/books/university-physics-volume-1/pages/7-1-work) and [mathematics of waves](https://openstax.org/books/university-physics-volume-1/pages/16-2-mathematics-of-waves). Wave traces use at least 64 segments per cycle. For amplitude at most 10 units/cm, the second-derivative interpolation bound plus vertical coordinate rounding is below 0.013 units/cm. Sample points are independently compared with the analytical field using explicit rounding bounds for both coordinates.

The existing physics checker now verifies 45,556 equation/geometry assertions over 17 targeted scenarios, including full ramp curves, pressure traces, travelling-wave snapshots and exact restoration after complete periods. Periodic time endpoints are tested as equal shapes; the control smoke test also exercises an interior time.

Authenticated isolated reader checks cover all three lesson routes at 1440 and 390 pixels: 44 authored, native keyboard endpoint, interior-time and reset states. Every SVG text bound, text-pair overlap and page overflow check passed. Served renderer bytes match the recorded SHA-256. Images show the actual lesson diagrams and routes. This is local evidence; production release remains pending.

The exact inverse restores only the bounded renderer changes for historical comparisons. Original clinical, source and QFT reviews remain historical, and current waveform behavior has its own equation and reader evidence. Unrecorded byte changes are rejected.
