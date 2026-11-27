"""Reproduce independent pixel references from direct complex groove sums.

Authoring-only: requires NumPy and SciPy; neither is imported by the activity.
Checks the committed fixture by default. Use --write to regenerate it.
"""
from pathlib import Path
import json
import argparse
import numpy as np
from scipy.integrate import quad

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'tests/fixtures/grating-spectrometer-reference.json'


def reproduce():
    examples = []
    cases = [({}, [108, 118, 119, 120, 131]),
             ({'grooves': 1600}, [108, 119, 131]),
             ({'density': 100, 'grooves': 3000, 'focalMm': 100, 'pixelUm': 50}, [11, 12]),
             ({'order': 2, 'grooves': 600, 'pixelUm': 25}, [19, 23, 28])]
    for changed, bins in cases:
        s = dict(density=600, grooves=600, order=1, focalMm=300, pixelUm=5, **{})
        s.update(changed)
        d = .001 / s['density']; f = .001 * s['focalMm']; width = s['pixelUm'] * 1e-6
        wavelengths = np.array([5889.950, 5895.924]) * 1e-10
        centre = np.arcsin(s['order'] * wavelengths / d).mean()
        grooves = np.arange(s['grooves'])
        for i in bins:
            left = -.0006 + i * width; right = left + width
            components = []
            for wavelength in wavelengths:
                def intensity(x):
                    theta = centre + np.arctan(x / f)
                    amplitudes = np.exp(2j * np.pi * grooves * d * np.sin(theta) / wavelength)
                    return float(abs(amplitudes.mean()) ** 2)
                # Explicit subdivisions keep narrow peaks from falling between
                # the initial quadrature samples in a much wider pixel.
                edges = np.linspace(left, right, 65)
                integral = sum(quad(intensity, a, b, epsabs=1e-15, epsrel=1e-10)[0]
                               for a, b in zip(edges, edges[1:]))
                components.append(integral / width)
            examples.append(dict(settings=s, index=i, left=left, right=right,
                                 components=components, total=sum(components) / 2))
    return dict(method='Direct sum of N complex groove amplitudes; independent SciPy adaptive quadrature in 64 subintervals per pixel; air wavelengths transcribed from NIST R56', pixels=examples)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Regenerate the committed reference fixture')
    args = parser.parse_args()
    result = reproduce()
    if args.write:
        TARGET.write_text(json.dumps(result, indent=2) + '\n')
    else:
        saved = json.loads(TARGET.read_text())
        assert len(saved['pixels']) == len(result['pixels'])
        for before, after in zip(saved['pixels'], result['pixels']):
            assert before['settings'] == after['settings'] and before['index'] == after['index']
            assert max(abs(a-b) for a,b in zip(before['components'], after['components'])) < 1e-10
        print('13 independent raw-phasor pixel integrals reproduced')
