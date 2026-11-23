import { repeatGates, prediction } from './model.mjs';
self.onmessage = event => {
  try {
    const { state } = event.data;
    self.postMessage({ simulated: repeatGates(state), predicted: prediction(state) });
  } catch {
    self.postMessage({ error: 'This comparison could not be calculated. Try the gate again.' });
  }
};
