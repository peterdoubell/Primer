/* A local, deliberately paced image sequence for Reproduction and Growth. */
(function () {
  'use strict';

  const ASSET_ROOT = '/app/reference-media/prenatal-development/';
  const MANIFEST = ASSET_ROOT + 'sequence.json';
  let serial = 0;

  function element(tag, attributes = {}, text) {
    const result = document.createElement(tag);
    for (const [name, value] of Object.entries(attributes)) result.setAttribute(name, value);
    if (text !== undefined) result.textContent = text;
    return result;
  }

  function checkedManifest(data) {
    if (!data || !Array.isArray(data.frames) || !data.frames.length || data.frames.length > 250) {
      throw new Error('The sequence contains no usable frames.');
    }
    const ids = new Set();
    let previousDay = -1;
    for (const frame of data.frames) {
      if (!frame || typeof frame.id !== 'string' || ids.has(frame.id) ||
          !Number.isInteger(frame.developmentalDay) || frame.developmentalDay <= previousDay ||
          frame.developmentalDay < 0 || frame.developmentalDay > 83 ||
          frame.gestationalDays !== frame.developmentalDay + 14 ||
          !/^\/app\/reference-media\/prenatal-development\/[a-z0-9-]+\.webp$/.test(frame.src || '') ||
          ['label', 'ageLabel', 'alt', 'caption'].some(key => typeof frame[key] !== 'string' || !frame[key].trim())) {
        throw new Error('The sequence has an invalid frame.');
      }
      ids.add(frame.id);
      previousDay = frame.developmentalDay;
    }
    if (data.gif !== ASSET_ROOT + 'prenatal-development.gif') throw new Error('The animation link is invalid.');
    return data;
  }

  function render(item, hooks) {
    const prefix = 'prenatal-sequence-' + (++serial);
    const root = element('section', { class: 'card lesson-model prenatal-sequence',
      'data-renderer': 'prenatal-sequence', 'aria-labelledby': prefix + '-title' });
    const title = element('h3', { id: prefix + '-title' }, item.title);
    const heading = element('div', { class: 'model-heading-row' });
    heading.append(title);
    const instructions = element('p', { class: 'model-instructions' }, item.instructions);
    const status = element('p', { class: 'model-status prenatal-status', role: 'status',
      'aria-live': 'polite', 'aria-atomic': 'true' }, 'Loading the development sequence…');
    const content = element('div', { class: 'prenatal-content' });
    content.hidden = true;
    const figure = element('figure', { class: 'prenatal-figure' });
    const stage = element('div', { class: 'prenatal-stage', 'aria-busy': 'true' });
    const imageHost = element('div', { class: 'prenatal-image-host' });
    const imageMessage = element('p', { class: 'prenatal-image-message' }, 'Loading frame…');
    stage.append(imageHost, imageMessage);
    const caption = element('figcaption', { id: prefix + '-caption', class: 'prenatal-caption' });
    figure.append(stage, caption);
    const age = element('p', { class: 'prenatal-age', id: prefix + '-age' });
    const position = element('span', { class: 'prenatal-position' });
    const controls = element('div', { class: 'model-controls prenatal-controls' });
    const rangeLabel = element('label', { for: prefix + '-frame' }, 'Explore development');
    const slider = element('input', { id: prefix + '-frame', type: 'range', min: '0', max: '0',
      step: '1', value: '0', 'aria-describedby': prefix + '-timing' });
    const row = element('div', { class: 'model-button-row prenatal-buttons' });
    function button(text, action) {
      const result = element('button', { type: 'button', class: 'btn ghost small' }, text);
      result.addEventListener('click', action);
      return result;
    }
    const previous = button('Previous frame', () => select(index - 1, true));
    const play = button('Play sequence', togglePlayback);
    play.setAttribute('aria-pressed', 'false');
    const next = button('Next frame', () => select(index + 1, true));
    row.append(previous, play, next, position);
    const timing = element('p', { id: prefix + '-timing', class: 'prenatal-detail' },
      'Day numbers count from fertilisation. Pregnancy age includes the preceding two weeks. ' +
      'Frames sample different time intervals; playback is not real-time growth.');
    const motion = element('p', { class: 'prenatal-detail' });
    const note = element('p', { class: 'prenatal-detail' });
    const links = element('div', { class: 'prenatal-links' });
    const fullImage = element('a', { target: '_blank', rel: 'noopener noreferrer' }, 'View this frame');
    const gifLink = element('a', { download: 'prenatal-development.gif' }, 'Download GIF');
    const viewGif = element('a', { target: '_blank', rel: 'noopener noreferrer' }, 'View GIF');
    links.append(fullImage, gifLink, viewGif);
    const sources = element('div', { class: 'prenatal-sources' });
    const retry = button('Retry sequence', load);
    retry.hidden = true;
    const retryImage = button('Retry frame', () => select(index, true));
    retryImage.hidden = true;
    controls.append(rangeLabel, slider, row);
    content.append(age, figure, controls, retryImage, timing, motion, note, links, sources);
    root.append(heading, instructions, status, retry, content);

    let frames = [], index = 0, playing = false, timer = null, disposed = false;
    let request = null, imageVersion = 0, imageReady = false, imageFailed = false;
    let wasConnected = root.isConnected;
    const preference = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
    function motionText() {
      motion.textContent = preference && preference.matches
        ? 'Reduced motion is enabled. Playback uses slower, discrete frames; you can also step through at your own pace.'
        : 'Use the slider or arrow keys to inspect one frame at a time, or play the sequence.';
    }
    function updateControls() {
      previous.disabled = index === 0;
      next.disabled = index >= frames.length - 1;
      play.disabled = !frames.length || imageFailed;
      play.textContent = playing ? 'Pause sequence' : index === frames.length - 1 ? 'Replay sequence' : 'Play sequence';
      play.setAttribute('aria-pressed', String(playing));
    }
    function stop() {
      playing = false;
      clearTimeout(timer);
      timer = null;
      updateControls();
    }
    function schedule() {
      clearTimeout(timer);
      if (!playing || !imageReady || disposed) return;
      const requested = Number(frames[index].durationMs);
      const duration = Math.max(preference && preference.matches ? 2000 : 500,
        Math.min(Number.isFinite(requested) ? requested : 1200, 10000));
      timer = setTimeout(() => {
        if (!root.isConnected || document.hidden) { stop(); return; }
        if (index === frames.length - 1) {
          stop();
          status.textContent = 'End of the first-trimester sequence.';
        } else select(index + 1, false);
      }, duration);
    }
    function selectedText(frame) {
      return frame.label + ' after fertilisation · Pregnancy age ' + frame.ageLabel;
    }
    function select(value, manual) {
      if (disposed || !frames.length) return;
      if (manual) stop();
      clearTimeout(timer);
      const number = Number(value);
      index = Number.isFinite(number) ? Math.max(0, Math.min(frames.length - 1, Math.round(number))) : index;
      const frame = frames[index], version = ++imageVersion;
      slider.value = String(index);
      slider.setAttribute('style', '--range-fill: ' + (frames.length > 1 ? index / (frames.length - 1) * 100 : 0) + '%');
      slider.setAttribute('aria-valuetext', selectedText(frame) + ', frame ' + (index + 1) + ' of ' + frames.length);
      age.textContent = selectedText(frame);
      position.textContent = (index + 1) + ' / ' + frames.length;
      caption.textContent = frame.caption;
      fullImage.setAttribute('href', frame.src);
      imageReady = false;
      imageFailed = false;
      stage.setAttribute('aria-busy', 'true');
      imageMessage.hidden = false;
      imageMessage.textContent = 'Loading frame…';
      retryImage.hidden = true;
      const picture = element('img', { alt: frame.alt, width: '1024', height: '1024',
        decoding: 'async', 'aria-describedby': prefix + '-caption' });
      picture.hidden = true;
      picture.addEventListener('load', () => {
        if (disposed || version !== imageVersion) return;
        imageReady = true;
        picture.hidden = false;
        imageMessage.hidden = true;
        stage.setAttribute('aria-busy', 'false');
        schedule();
      });
      picture.addEventListener('error', () => {
        if (disposed || version !== imageVersion) return;
        imageFailed = true;
        stop();
        stage.setAttribute('aria-busy', 'false');
        imageMessage.textContent = 'This frame could not be loaded.';
        retryImage.hidden = false;
        status.textContent = 'Frame unavailable. Retry this frame or choose another with the slider.';
      });
      imageHost.replaceChildren(picture);
      picture.setAttribute('src', frame.src);
      updateControls();
      if (manual) status.textContent = 'Frame ' + (index + 1) + ' of ' + frames.length + '. ' + selectedText(frame) + '.';
    }
    function togglePlayback() {
      if (disposed || !frames.length || imageFailed) return;
      if (playing) { stop(); status.textContent = 'Sequence paused.'; return; }
      if (index === frames.length - 1) select(0, false);
      playing = true;
      updateControls();
      status.textContent = 'Playing the development sequence.';
      schedule();
    }
    slider.addEventListener('input', () => select(slider.value, true));
    function onVisibility() {
      if (document.hidden && playing) { stop(); status.textContent = 'Sequence paused while this page is hidden.'; }
    }
    function onMotionChange() { stop(); motionText(); }
    document.addEventListener('visibilitychange', onVisibility);
    if (preference && preference.addEventListener) preference.addEventListener('change', onMotionChange);
    motionText();
    const observer = new MutationObserver(() => {
      if (root.isConnected) wasConnected = true;
      else if (wasConnected) root.dispose();
    });
    observer.observe(document.body, { childList: true, subtree: true });
    root.dispose = () => {
      if (disposed) return;
      disposed = true;
      stop();
      if (request) request.abort();
      observer.disconnect();
      document.removeEventListener('visibilitychange', onVisibility);
      if (preference && preference.removeEventListener) preference.removeEventListener('change', onMotionChange);
    };

    async function load() {
      if (disposed) return;
      retry.hidden = true;
      status.textContent = 'Loading the development sequence…';
      if (request) request.abort();
      const currentRequest = new AbortController();
      request = currentRequest;
      try {
        const response = await fetch(MANIFEST, { signal: currentRequest.signal, credentials: 'same-origin' });
        if (!response.ok) throw new Error('Sequence unavailable');
        const data = checkedManifest(await response.json());
        if (disposed || request !== currentRequest) return;
        frames = data.frames;
        slider.max = String(frames.length - 1);
        note.textContent = data.note || 'AI-generated educational reconstructions; not clinical images. Magnification varies; not to scale.';
        gifLink.setAttribute('href', data.gif);
        viewGif.setAttribute('href', data.gif);
        sources.replaceChildren();
        if (Array.isArray(data.sources)) {
          for (const source of data.sources) {
            if (typeof source.title !== 'string' || !/^https:\/\//.test(source.url || '')) continue;
            sources.append(element('a', { href: source.url, target: '_blank', rel: 'noopener noreferrer' }, source.title));
          }
        }
        content.hidden = false;
        status.textContent = frames.length + ' frames ready. Playback starts only when you choose Play.';
        select(0, false);
      } catch (error) {
        if (disposed || request !== currentRequest || error.name === 'AbortError') return;
        status.textContent = 'The development sequence is unavailable. The rest of this lesson is ready to use.';
        retry.hidden = false;
      }
    }
    if (hooks && typeof hooks.speakButton === 'function') {
      heading.prepend(hooks.speakButton(() => [item.title, item.instructions, age.textContent,
        caption.textContent, timing.textContent, note.textContent].join(' '), 'Read this sequence aloud'));
    }
    load();
    return root;
  }

  window.PrimerPrenatalSequence = Object.freeze({ render });
}());
