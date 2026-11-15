'use strict';
const sourceReport = new URLSearchParams(location.search).get('from');
if (['ra.biliary-duct-pathology','ra.ultrasound-gallbladder'].includes(sourceReport)) {
  const link = document.getElementById('study-return');
  link.href = '/app/#/radiology/' + sourceReport;
  link.textContent = 'Return to reporting reference';
}
