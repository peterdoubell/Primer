'use strict';

(function () {
  const domain = Object.freeze({ a: [-1, 4], x: [-3, 3], width: [0, 20] });

  function requireRange(value, [minimum, maximum], name) {
    if (!Number.isFinite(value) || value < minimum || value > maximum) {
      throw new RangeError(name + ' is outside its supported domain');
    }
  }

  function cubic(a, x) {
    requireRange(a, domain.a, 'a');
    requireRange(x, domain.x, 'x');
    const value = x ** 3 - 3 * a * x;
    const derivative = 3 * (x ** 2 - a);
    const secondDerivative = 6 * x;
    let stationary, intervals, classification;
    if (a < 0) {
      stationary = [];
      intervals = [{ from: null, to: null, sign: 1 }];
      classification = 'none';
    } else if (a === 0) {
      stationary = [{ x: 0, y: 0, kind: 'stationary inflection' }];
      intervals = [{ from: null, to: 0, sign: 1 }, { from: 0, to: null, sign: 1 }];
      classification = 'flat';
    } else {
      const root = Math.sqrt(a);
      stationary = [
        { x: -root, y: 2 * a * root, kind: 'local maximum' },
        { x: root, y: -2 * a * root, kind: 'local minimum' },
      ];
      intervals = [
        { from: null, to: -root, sign: 1 },
        { from: -root, to: root, sign: -1 },
        { from: root, to: null, sign: 1 },
      ];
      classification = 'two';
    }
    return { a, x, value, derivative, secondDerivative, stationary, intervals, classification };
  }

  function pen(width) {
    requireRange(width, domain.width, 'width');
    const length = 20 - width;
    return {
      width, length, perimeter: 2 * (width + length), area: width * length,
      derivative: 20 - 2 * width, secondDerivative: -2,
      maximumWidth: 10, maximumArea: 100, areaShortfall: (width - 10) ** 2,
    };
  }

  const api = Object.freeze({ domain, cubic, pen });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof globalThis !== 'undefined') globalThis.PrimerDerivativeSigns = api;
})();
