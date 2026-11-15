'use strict';
// Dimensionless linear plane wave with sound speed c = 1 and bulk modulus K = 1.
function sampleParcel(restX,time,amplitude,wavelength) {
  if (![restX,time,amplitude,wavelength].every(Number.isFinite))
    throw new RangeError('Wave inputs must be finite numbers.');
  if (Math.abs(restX)>1000 || Math.abs(time)>1000 || wavelength<.5 || wavelength>2 || amplitude < 0 || amplitude > wavelength/100)
    throw new RangeError('Use positions and times within ±1000, wavelength 0.5–2, and displacement at most 1% of it.');
  const k=2*Math.PI/wavelength;
  const phase=k*(restX-time);
  const displacement=amplitude*Math.cos(phase);
  return {
    restX,
    x:restX+displacement,
    displacement,
    velocity:k*amplitude*Math.sin(phase),
    pressure:k*amplitude*Math.sin(phase)
  };
}
if(typeof module!=='undefined')module.exports={sampleParcel};
