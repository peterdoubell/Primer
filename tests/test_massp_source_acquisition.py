import hashlib

from tools.anatomy_sources.acquire_massp_lifespan import selected, verified


def test_source_selection_excludes_std_maps_and_unrelated_or_unpinned_names():
    assert selected('proba_ahead-massp2_avg-gpi_hem-l_decade-18to80_n97.nii.gz')
    assert selected('massp_2p0-label-list.txt')
    for name in ('proba_ahead-massp2_std-gpi_hem-l_decade-18to80_n97.nii.gz',
                 'proba_ahead-massp2_avg-ic_hem-l_decade-18to80_n105.nii.gz',
                 '../proba_ahead-massp2_avg-gpi_hem-l_decade-18to80_n97.nii.gz',
                 'proba_ahead-massp2_avg-amg_hem-l_decade-18to80_n97.nii.gz'):
        assert not selected(name)


def test_source_cache_requires_both_publisher_length_and_checksum(tmp_path):
    path = tmp_path / 'source.nii.gz'
    original = b'source-voxel-data'
    entry = {'size': len(original), 'computed_md5': hashlib.md5(original).hexdigest()}
    assert not verified(path, entry)
    path.write_bytes(original)
    assert verified(path, entry)
    path.write_bytes(original + b'padding')
    assert not verified(path, entry)
    path.write_bytes(b'X' * len(original))
    assert not verified(path, entry)
