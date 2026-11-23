"""Offline salivary tools accept their documented package, not arbitrary I/O paths."""
import pytest

from tools.anatomy_sources import salivary_package_paths as paths


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    checkout = tmp_path / "independent-checkout"
    package = checkout / "web/anatomy/zanatomy-salivary"
    package.mkdir(parents=True)
    monkeypatch.setattr(paths, "PACKAGE_ROOT", package)
    monkeypatch.chdir(checkout)
    return package


def test_relative_and_absolute_documented_invocations_use_this_checkout(checkout):
    assert paths.package_directory("web/anatomy/zanatomy-salivary") == checkout
    assert paths.package_directory(checkout) == checkout
    assert len(paths.MESH_FILES) == 18 and len(set(paths.PACKAGE_MEMBERS)) == 26
    assert all(paths.package_member(name).parent == checkout for name in paths.PACKAGE_MEMBERS)


def test_other_output_directory_is_rejected_without_creating_it(checkout, tmp_path):
    other = tmp_path / "other-output"
    with pytest.raises(ValueError, match="isolated checkout"):
        paths.package_directory(other)
    assert not other.exists()


def test_manifest_cannot_select_an_unlisted_file(checkout):
    with pytest.raises(ValueError, match="Unrecognised"):
        paths.package_member("unlisted.mesh.gz")
    assert list(checkout.iterdir()) == []


def test_a_known_name_cannot_redirect_io_to_a_benign_external_file(checkout, tmp_path):
    outside = tmp_path / "benign.txt"
    outside.write_text("unchanged")
    (checkout / "source.json").symlink_to(outside)
    with pytest.raises(ValueError, match="symbolic links"):
        paths.package_member("source.json")
    assert outside.read_text() == "unchanged"


def test_package_directory_itself_cannot_be_a_symbolic_link(checkout, tmp_path, monkeypatch):
    link = tmp_path / "linked-package"
    link.symlink_to(checkout, target_is_directory=True)
    monkeypatch.setattr(paths, "PACKAGE_ROOT", link)
    with pytest.raises(ValueError, match="symbolic links"):
        paths.package_directory(link)
    with pytest.raises(ValueError, match="symbolic links"):
        paths.package_member("surfaces.json")
