import pytest
from tools.simple_report_sheet_compatibility import ROOT,before_simple_asset
@pytest.mark.parametrize('name',['radiology-structured.js','radiology-structured.css'])
def test_sheet_inverse_is_exact_and_rejects_drift(name):
 path='web/'+name;raw=(ROOT/path).read_bytes();old=before_simple_asset(path,raw)
 assert old!=raw and before_simple_asset(path,old)==old
 with pytest.raises(ValueError,match='Unreviewed'):before_simple_asset(path,raw+b' ')
