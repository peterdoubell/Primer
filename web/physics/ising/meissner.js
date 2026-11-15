'use strict';

(() => {
  // x is position divided by half-thickness. ratio is half-thickness / lambda.
  function londonField(x, ratio) {
    if (!Number.isFinite(x) || Math.abs(x) > 1 || !Number.isFinite(ratio) || ratio < 0.25 || ratio > 20) {
      throw new RangeError('Position or penetration-depth ratio is outside the model');
    }
    return Math.cosh(x * ratio) / Math.cosh(ratio);
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {londonField};
    return;
  }

  const slider = document.getElementById('penetration-ratio');
  const history = document.getElementById('field-history');
  const canvas = document.getElementById('magnetic-field');
  const context = canvas.getContext('2d');
  const blue = '#a2d2f1', orange = '#f6ba81';
  const left = 64, right = 614, top = 25, bottom = 257;
  const plotX = position => left + (right - left) * (position + 1) / 2;
  const plotY = field => bottom - (bottom - top) * field;

  function draw() {
    const ratio = Number(slider.value);
    const trapped = history.value === 'field-cooled' ? 1 : 0;
    const center = londonField(0, ratio);
    document.getElementById('penetration-value').textContent = ratio.toFixed(2);
    document.getElementById('field-values').textContent = `Centre field relative to applied field. Superconductor ${center.toPrecision(4)}. Ideal conductor ${trapped}.`;
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.font = '18px system-ui';
    for (const value of [0, .25, .5, .75, 1]) {
      const y = plotY(value);
      context.fillStyle = '#374952';
      context.fillRect(left, y, right - left, 1);
      context.fillStyle = '#e4eff5';
      context.fillText(String(value), 8, y + 6);
    }
    context.lineWidth = 3;
    context.strokeStyle = orange;
    context.setLineDash([10, 6]);
    context.beginPath();
    context.moveTo(left, plotY(trapped));
    context.lineTo(right, plotY(trapped));
    context.stroke();
    context.setLineDash([]);
    context.strokeStyle = blue;
    context.beginPath();
    for (let step = 0; step <= 400; step++) {
      const x = step / 200 - 1;
      const y = plotY(londonField(x, ratio));
      if (step === 0) context.moveTo(plotX(x), y);
      else context.lineTo(plotX(x), y);
    }
    context.stroke();
    context.fillText('−1', left - 8, 285);
    context.fillText('0', plotX(0) - 4, 285);
    context.fillText('+1', right - 19, 285);
    context.fillText('Position / half-thickness', 230, 314);
  }

  slider.addEventListener('input', draw);
  history.addEventListener('change', draw);
  draw();
})();
