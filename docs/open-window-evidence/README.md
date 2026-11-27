# Who supplies the account in “The Open Window”?

An additional server-marked sequence for `lang.5.narratology`. The module’s
original sequence remains first. Its existing standalone narrative-order
activity remains linked unchanged. This sequence instead works from an actual
story: attributing speech, comparing an earlier claim with later narration,
weighing the closing comment, then distinguishing third-person voice from
local access to a character’s thought.

The four checked steps use matching, structural comparison and prediction;
the final prediction transfers to a previously unused sentence from the
opening. Introductory and worked-example beats, hints, mistake-specific
feedback and explanations use the existing learning-game player and server
marking. Answers and explanations stay in the authored server model until
submission. Completion records study and preserves the mastery boundary.

The source is Saki, *Beasts and Super-Beasts* (John Lane, 1914), “The Open
Window”, printed pages 50–55. The original literary text is public domain.
`source-wikisource-10921512.txt` preserves the exact attributed Wikisource
revision; `source.json` pins its SHA-256, ten literal character-range excerpts,
and the independently checked 1914 scan (PDF pages 64–69). The transcription’s
punctuation is retained in the quoted excerpts. The exercise does not use
Wikisource’s audio or editorial metadata as literary evidence.

The interpretation is deliberately bounded. Vera’s claim is distinguished
from the narrator reporting it; the return scene undermines her account.
The final comment gives reason to doubt her dog-phobia explanation. The
transfer describes one sentence’s mental access, rather than asserting that
the entire story maintains a single focaliser. The content remains authored
and awaiting subject review.

Checks:

```sh
python -m pytest tests/test_open_window_sequence.py tests/test_learning_games.py -q
python tools/learning_games_report.py --check
python tools/learning_games_inventory.py --check
```

Normal entry: open Narratology and Critical Theory, choose its Play stop,
then choose **Whose account? The Open Window** in the activity picker.
