#!/usr/bin/env node
'use strict';

// Execute the shipped picture handlers against representative reader markup.
// These small DOM doubles cover semantics/events; the CSS failure was also
// reproduced in Chromium with the real #article figure img rule.
const assert = require('node:assert/strict');

class Element {
  constructor(tag, attrs = {}, children = []) {
    this.tagName = tag.toUpperCase(); this.attrs = {...attrs};
    this.children = []; this.parentElement = null; this.dataset = {};
    this.style = {}; this.hidden = false; this.complete = false; this.naturalWidth = 0; this.isConnected = true; this.currentSrc = '';
    this.listeners = {};
    const classes = new Set((attrs.class || '').split(/\s+/));
    this.classList = {contains: value => classes.has(value), add: value => classes.add(value), remove: value => classes.delete(value)};
    for (const [key, value] of Object.entries(attrs)) if (key.startsWith('on') && typeof value === 'function') this.listeners[key.slice(2)] = [value];
    children.forEach(child => this.append(child));
  }
  append(child) {
    if (child == null) return;
    if (child instanceof Element) child.parentElement = this;
    this.children.push(child);
  }
  get textContent() { return this.children.map(child => child instanceof Element ? child.textContent : String(child)).join(''); }
  getAttribute(key) { return Object.hasOwn(this.attrs, key) ? this.attrs[key] : null; }
  hasAttribute(key) { return Object.hasOwn(this.attrs, key); }
  setAttribute(key, value) { this.attrs[key] = String(value); }
  removeAttribute(key) { delete this.attrs[key]; }
  remove() { const parent = this.parentElement; if (parent) parent.children.splice(parent.children.indexOf(this), 1); this.parentElement = null; }
  matches(selector) {
    return selector.split(',').some(value => {
      const part = value.trim();
      return part.startsWith('.') ? this.classList.contains(part.slice(1)) : this.tagName === part.toUpperCase();
    });
  }
  closest(selector) {
    for (let node = this; node; node = node.parentElement) if (node.matches(selector)) return node;
    return null;
  }
  querySelectorAll(selector) {
    return this.children.flatMap(child => child instanceof Element
      ? [...(child.matches(selector) ? [child] : []), ...child.querySelectorAll(selector)] : []);
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  addEventListener(type, handler) { (this.listeners[type] ||= []).push(handler); }
  fire(type, extra = {}) {
    const event = {target: this, prevented: false, preventDefault() { this.prevented = true; }, propagationStopped: false, stopPropagation() { this.propagationStopped = true; }, ...extra};
    (this.listeners[type] || []).forEach(handler => handler(event));
    return event;
  }
  insertAdjacentElement(position, sibling) {
    assert.equal(position, 'afterend');
    const parent = this.parentElement;
    parent.children.splice(parent.children.indexOf(this) + 1, 0, sibling);
    sibling.parentElement = parent;
  }
}

const el = (tag, attrs, ...children) => new Element(tag, attrs, children);
const opened = [];
// Registering top-level browser listeners is inert in this isolated executable.
// The real exported handlers receive only the DOM/host operations they use.
globalThis.window = { addEventListener() {} };
globalThis.document = { addEventListener() {} };
const { attachPictureHandlers, pictureCaptionElement } = require('../web/app.js');
const context = {
  pictureCaptionElement,
  attachPictureHandlers: art => attachPictureHandlers(art, {
    createElement: el, baseURL: 'http://localhost/',
    openPicture: (image, opener) => opened.push({ image, opener }),
  }),
};

// Genetics supplies image-only anchors with alt="" but a useful figcaption.
const image = el('img', {alt: ''});
const anchor = el('a', {href: '#'}, image);
const art = el('article', {}, el('figure', {}, anchor,
  el('figcaption', {}, 'DNA carries hereditary information.')));
context.attachPictureHandlers(art);
assert.equal(anchor.getAttribute('aria-label'), 'Open picture: DNA carries hereditary information.');
assert.equal(anchor.getAttribute('role'), 'button');
assert.equal(anchor.getAttribute('tabindex'), '0');
art.fire('keydown', {target: anchor, key: 'Enter'});
assert.equal(opened.length, 0, 'native anchor Enter must not open a second dialog');
art.fire('click', {target: anchor});
assert.equal(opened.length, 1);
art.fire('keydown', {target: anchor, key: ' '});
assert.equal(opened.length, 2, 'Space must activate an image-only anchor');

// Sanitized anchors without href have no native Enter activation.
const noHrefImage = el('img', {alt: 'Chromosome pairs'});
const noHref = el('a', {}, noHrefImage);
const noHrefArt = el('article', {}, noHref);
context.attachPictureHandlers(noHrefArt);
noHrefArt.fire('keydown', {target: noHref, key: 'Enter'});
assert.equal(opened.length, 3);
assert.equal(opened[2].image, noHrefImage);

// A failed bare image must lose its display box even under figure display:block.
const failed = el('img', {alt: 'A chromosome map'});
failed.complete = true;
failed.currentSrc = 'http://localhost/broken.png';
const failedArt = el('article', {}, el('figure', {}, failed));
context.attachPictureHandlers(failedArt);
assert(failed.hidden);
assert.equal(failed.style.display, 'none');
assert.match(failedArt.querySelector('.image-load-note').textContent, /A chromosome map/);
assert.equal(failedArt.querySelector('.picture-fallback'), null);
failed.fire('error');
assert.equal(failedArt.querySelectorAll('.image-load-note').length, 1, 'failure note is idempotent');
failedArt.querySelector('button').fire('click');
assert.equal(failed.getAttribute('loading'), 'eager', 'hidden retry must actually fetch');
failed.naturalWidth = 800; failed.fire('load');
assert.equal(failed.hidden, false);
assert.equal(failedArt.querySelector('.image-load-note'), null);

// A failed thumbnail can use the actual larger asset, without a placeholder.
const responsive = el('img', {alt:'Vessel', src:'/app/small.webp', srcset:'/app/small.webp 800w, /app/large.webp 1600w'});
responsive.currentSrc = 'http://localhost/app/small.webp';
const responsiveArt = el('article', {}, responsive);
context.attachPictureHandlers(responsiveArt);
responsive.fire('error');
assert.equal(responsive.getAttribute('src'), '/app/large.webp');
assert.equal(responsiveArt.querySelector('.image-load-note'), null);
responsive.naturalWidth = 1600; responsive.fire('load');
assert.equal(responsive.hidden, false);

const pending = el('img', {alt:'Not fetched yet',src:'/app/pending.webp'});
pending.isConnected = false; pending.complete = true;
const pendingArt = el('article', {}, pending);
context.attachPictureHandlers(pendingArt);
assert.equal(pending.hidden, false, 'detached image is not a failed fetch');

// An image failure must not erase a healthy sibling or shared link text.
const first = el('img', {alt: 'Before replication'});
const second = el('img', {alt: 'After replication'});
const shared = el('a', {href: '#'}, first, second);
const sharedArt = el('article', {}, el('figure', {}, shared, el('figcaption', {}, 'Comparison')));
context.attachPictureHandlers(sharedArt);
first.fire('error');
assert(first.hidden);
assert.equal(shared.hidden, false);
assert.equal(second.hidden, false);
assert.match(sharedArt.querySelector('.image-load-note').textContent, /Before replication/);
assert.equal(context.pictureCaptionElement(second), null, 'shared caption is not an individual description');

// External picture links and curriculum wikilinks retain their navigation.
for (const attrs of [{href: 'https://example.com/image'}, {href: '#/read/DNA', class: 'primer-wikilink'}]) {
  const linkedImage = el('img', {alt: 'DNA'});
  const link = el('a', attrs, linkedImage);
  const linkedArt = el('article', {}, link);
  context.attachPictureHandlers(linkedArt);
  assert.equal(link.getAttribute('role'), null);
  assert.equal(linkedArt.fire('click', {target: linkedImage}).prevented, false);
}
assert.equal(opened.length, 3);
console.log('Verified reader picture names, keyboard activation, failure states and link preservation');

const atlasImage = el('img', {alt: 'Annotated ligament anatomy'});
const atlas = el('section', {class: 'rad-structure-atlas'}, el('figure', {class: 'rad-anatomy-illustration'},
  atlasImage, el('figcaption', {}, el('p', {}, 'Source caption.'),
    el('p', {}, 'Identified in this figure: ligament.'), el('p', {}, 'Original authors, CC BY 4.0.'))));
context.attachPictureHandlers(atlas);
assert.equal(atlasImage.getAttribute('aria-label'),
  'Open picture: Source caption.\nIdentified in this figure: ligament.\nOriginal authors, CC BY 4.0.',
  'Detached clinical atlas captions preserve paragraph boundaries');

// The same source renderer is used in the gallery and reporting steps. A source
// example must keep its licensing, limitations and white paper background there.
const { walkthroughFigure, sourceAtlasFigure } = require('../web/app.js');
const sourceRows = JSON.parse(require('node:fs').readFileSync(require('node:path').join(__dirname, '../data/radiology/radiology-open-images.json'), 'utf8'));
const sourceAsset = sourceRows['ra.ct-bowel-wall'].find(a => a.figure_number === 20);
assert.ok(sourceAsset);
const sourceFigure = walkthroughFigure(sourceAsset, { sourceRenderer: asset => sourceAtlasFigure(asset, {
  createElement: (tag, props, ...children) => { const node = el(tag, props, ...children); node.dataset = {...(props?.dataset || {})}; return node; },
  sourceLink: (title, url) => el('a', {href: url}, title),
}) });
assert.ok(sourceFigure.classList.contains('rad-walk-figure'));
const sourcePicture = sourceFigure.querySelector('img');
assert.equal(sourcePicture.dataset.fullSrc, sourceAsset.src);
assert.equal(sourcePicture.dataset.paperBackground, 'white');
assert.equal(sourcePicture.getAttribute('width'), sourceAsset.width);
assert.ok(sourceFigure.textContent.includes(sourceAsset.limits));
assert.ok(sourceFigure.textContent.includes(sourceAsset.attribution));
assert.ok(sourceFigure.textContent.includes('CC BY 2.0'));
assert.ok(sourceFigure.querySelectorAll('a').some(a => a.getAttribute('href') === sourceAsset.figure_url));

// Repainting the same source-step host must not stack picture dialogs. A nested
// host also owns its click/keyboard event instead of opening via the outer host.
const onceImage = el('img', {src: '/app/source-original.png', alt: 'Original source'});
const onceHost = el('section', {}, el('figure', {}, onceImage));
const onceOuter = el('article', {}, onceHost);
context.attachPictureHandlers(onceHost);
context.attachPictureHandlers(onceHost);
context.attachPictureHandlers(onceOuter);
const beforeRepeatedClick = opened.length;
const onceClick = onceHost.fire('click', {target: onceImage});
assert.equal(opened.length, beforeRepeatedClick + 1);
assert.equal(onceClick.propagationStopped, true);
const beforeRepeatedKey = opened.length;
const onceKey = onceHost.fire('keydown', {target: onceImage, key: 'Enter'});
assert.equal(opened.length, beforeRepeatedKey + 1);
assert.equal(onceKey.propagationStopped, true);
