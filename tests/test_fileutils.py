import pytest
from pathlib import Path
from shutil import rmtree

from futilities import fileutils

@pytest.fixture
def tmp_dir():
    tmp_dir_path = Path.cwd() / 'tmp'
    tmp_dir_path.mkdir()
    yield tmp_dir_path
    if tmp_dir_path.exists():
        rmtree(tmp_dir_path)

@pytest.fixture
def dummy_filetree(tmp_dir):
    [(tmp_dir / x).mkdir(parents=True) for x in ['a/a/a', 'b/b', 'c']]
    (tmp_dir / 'b/b/test.txt').touch()
    yield tmp_dir


def test_remove_empty_dirs(dummy_filetree):
    assert dummy_filetree.exists(), 'fixture failed to create filetree'
    fileutils.remove_empty_dirs(dummy_filetree)
    assert (dummy_filetree / 'b/b/test.txt').exists(), 'txt file was deleted'
    assert not (dummy_filetree / 'a/a/a').exists(), 'empty dir was not deleted'
    (dummy_filetree / 'b/b/test.txt').unlink()
    fileutils.remove_empty_dirs(dummy_filetree, remove_parent_dir=True)
    assert not dummy_filetree.exists(), 'parent directory was not deleted'




