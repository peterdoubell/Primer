"""Keep frontend failure states factual, visible, and retryable."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_reassurance_banner_is_confined_to_actual_error_cards():
    source = (ROOT / "web" / "app.js").read_text()
    card = source[source.index("function errCard("):source.index("function pagehead(")]
    assert source.count("'DON’T PANIC'") == 1
    assert "'DON’T PANIC'" in card
    assert "'aria-hidden': 'true'" in card


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_error_cards_preserve_diagnostics_and_retry_without_guessing():
    script = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('web/app.js', 'utf8');
const snippet = source.slice(source.indexOf('const SAID ='), source.indexOf('function pagehead('));
const warnings = [];
let retries = 0;
function element(tag, attrs, ...children) {
  return {tag, attrs, children, append(...items) { this.children.push(...items); }};
}
const context = {
  navigator: {onLine: true},
  console: {warn(...args) {warnings.push(args);}},
  el: element,
  btn: (attrs, ...children) => element('button', attrs, ...children),
};
vm.createContext(context);
vm.runInContext(snippet, context);
function text(node) {
  return typeof node === 'string' ? node : (node.children || []).map(text).join(' ');
}
const unknown = context.errCard({error: '<unsafe>internal detail'}, () => {retries++;});
unknown.children.find(x => x.tag === 'button').attrs.onclick();
const jsError = context.errCard(new Error('renderer exception'));
const known = context.errCard({error: 'no such node'});
const temporary = context.errCard({error: 'article temporarily unavailable'});
context.navigator.onLine = false;
const offline = context.errCard(new Error('fetch failed'));
console.log(JSON.stringify({
  unknown: text(unknown), jsError: text(jsError), known: text(known),
  temporary: text(temporary), offline: text(offline), warnings, retries,
  role: unknown.attrs.role,
  heading: unknown.children.find(x => x.tag === 'h3'),
  noRetryButtons: jsError.children.filter(x => x.tag === 'button').length,
}));
"""
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True,
        timeout=10, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    cards = json.loads(result.stdout)
    assert cards["role"] == "alert"
    assert "DON’T PANIC" in cards["unknown"]
    assert cards["heading"]["children"] == ["Unable to load content"]
    assert "aria-hidden" not in cards["heading"]["attrs"]
    assert cards["retries"] == 1
    assert cards["noRetryButtons"] == 0
    assert "This content could not be loaded right now." in cards["unknown"]
    assert "Reopen this page to try again." in cards["jsError"]
    assert "That lesson is not among these pages." in cards["known"]
    assert "Wikipedia is temporarily unavailable." in cards["temporary"]
    assert "Your browser reports that it is offline." in cards["offline"]
    for name in ("unknown", "jsError", "known", "temporary", "offline"):
        assert "safely written" not in cards[name]
        assert "everything" not in cards[name].lower()
        assert "likely the network" not in cards[name]
        assert "internal detail" not in cards[name]
        assert "renderer exception" not in cards[name]
    assert ["[primer]", "<unsafe>internal detail"] in cards["warnings"]
    assert ["[primer]", "renderer exception"] in cards["warnings"]
