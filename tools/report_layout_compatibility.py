"""Recover the exact report builder from before the Arial 12 pt copy layout (2026-11-15).

Only these three literals are restored, and only from the exact new bytes.
"""
import hashlib

PATH = 'web/radiology-structured.js'
BEFORE = '8445df128aa282ae71ff3439f05e32fe2510e337a9999d5e262b8180d1227a50'
AFTER = '814b3b3c171f98c6f0dfd2e693a4bfbb1a8a75d20a96f11f6c1d01f2426a523a'
LITERALS = (
    (b"/^(Clinical history|Comparison|Protocol|Technique|Findings|Impression|Recommendation):$/",
     b"/^(Clinical history|Comparison|Impression|Recommendation):$/"),
    (b"font-family:Arial,sans-serif;font-size:12pt;line-height:1.4", b"font-family:Arial,sans-serif;line-height:1.4"),
    (b"case 'main': return '<u>' + content + '</u>';", b"case 'main': return '<strong><u>' + content + '</u></strong>';"),
)


def before_report_layout_bytes(path, raw):
    if str(path) != PATH or hashlib.sha256(raw).hexdigest() != AFTER:
        return raw
    restored = raw
    for current, previous in LITERALS:
        if restored.count(current) != 1:
            raise ValueError('Report layout inverse literal is not unique')
        restored = restored.replace(current, previous, 1)
    if hashlib.sha256(restored).hexdigest() != BEFORE:
        raise ValueError('Report layout changed unrelated builder bytes')
    return restored
