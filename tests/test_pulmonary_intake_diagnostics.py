"""Intake status must not expose identifiers from remote source content."""
import json
from tools.anatomy_sources import pulmonary_nodule_intake as intake


def test_intake_logs_counts_without_source_identifiers(tmp_path, monkeypatch, capsys):
    private = tmp_path / 'private-intake'
    private.mkdir()
    series = [{'SeriesInstanceUID': 'sensitive-source-series-1', 'PatientID': 'sensitive-source-patient',
               'ImageCount': 429, 'FileSize': 225000000},
              {'SeriesInstanceUID': 'sensitive-source-series-2', 'PatientID': 'another-sensitive-patient',
               'ImageCount': 300, 'FileSize': 160000000}]
    (private / 'series-inventory.json').write_text(json.dumps(series))
    xml = [{'series_uid': row['SeriesInstanceUID'], 'xml_name': 'sensitive-annotation.xml',
            'nodules': [{'characteristics': {'texture': value, 'calcification': '6'}}
                        for value in ('1', '3', '5')]} for row in series]
    monkeypatch.setattr(intake, 'PRIVATE', private)
    monkeypatch.setattr(intake, 'SOURCES', {})
    monkeypatch.setattr(intake, 'analyze_xml', lambda: xml)
    intake.main()
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {'xml_files': 2, 'ct_series': 2, 'candidate_count': 2}
    assert 'sensitive' not in captured.out and not captured.err
