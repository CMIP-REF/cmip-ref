from pathlib import Path

import pytest

from cmip_ref.datasets.utils import validate_path


@pytest.mark.parametrize(
    "raw, expected",
    [
        [
            "/data/file.csv",
            Path("/data/file.csv"),
        ]
    ],
)
def test_validate_prefix(raw, expected, mocker):
    mocker.patch.object(Path, "exists", return_value=True)

    assert validate_path(raw) == expected


def test_validate_prefix_with_relative_path(mocker):
    mocker.patch.object(Path, "exists", return_value=True)
    raw_path = "data/subfolder/file.csv"

    with pytest.raises(ValueError):
        validate_path(raw_path)


def test_validate_prefix_missing(mocker):
    mocker.patch.object(Path, "exists", return_value=False)

    raw_path = "/other_dir/file.csv"
    with pytest.raises(FileNotFoundError):
        validate_path(raw_path)
