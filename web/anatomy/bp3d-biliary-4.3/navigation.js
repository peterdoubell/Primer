'use strict';
const query = new URLSearchParams(location.search);
const sourceReport = query.get('from');
if (['ra.biliary-duct-pathology','ra.ultrasound-gallbladder','ct.liver-mass','ct.liver-lirads','ct.liver-lirads-calculated'].includes(sourceReport)) {
  const link = document.getElementById('study-return');
  link.href = '/app/#/radiology/' + sourceReport;
  link.textContent = 'Return to reporting reference';
}
