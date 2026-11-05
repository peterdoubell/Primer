"""Remove only the exact module-mission shell additions for historical checks."""
import hashlib
BEFORE = 'bfb3fcf886d87cb6c3f85e4b97acfea2c225172273c4f68698ca615b5724b0f1'
AFTER = '528c7b9793bc601214767509642a9307b5645d1c9bb8b2c5447d83850f927d92'
ADDITIONS = [b'  <link rel="stylesheet" href="/app/module-mission.css">\n', b'  <script src="/app/module-mission.js"></script>\n']

def previous_shell_bytes(relative, raw):
    if relative != 'web/index.html' or hashlib.sha256(raw).hexdigest() != AFTER:
        return raw
    restored = raw
    for addition in ADDITIONS:
        if restored.count(addition) != 1:
            raise ValueError('Module mission shell addition is not unique')
        restored = restored.replace(addition, b'', 1)
    if hashlib.sha256(restored).hexdigest() != BEFORE:
        raise ValueError('Module mission inverse changed unrelated shell bytes')
    return restored
