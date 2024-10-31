# ruff: noqa: S603, S607
"""
Fetch test data

This is required to run the local test suite.

This script requires a local installation of esgpull.

Run the following commands to setup a new esgf installation if you haven't done so already.
You should only need to do this once.

```
uv run esgpull self install
uv run esgpull config api.index_node esgf-node.llnl.gov
```

It is up to you where you install esgpull.
For most users, installing it in a default location will make sense
because sharing your ESGF data across projects will be fine.
For some users (e.g. those on shared systems),
you may want to use a more specific location.

Changes to this file will trigger the CI to redownload the test-data.
"""

import subprocess


def queue_esgf_download(  # noqa: PLR0913
    source_id: str,
    experiment_id: str,
    member_id: str,
    frequency: str,
    variables: list[str],
    search_id: str,
    project: str = "CMIP6",
    mip_era: str = "CMIP6",
) -> str:
    """
    Add the tracking of a given search to the esgpull queue.

    Returns
    -------
    str
        The search tag used to track the download

    """
    search_tag = f"{mip_era}_{source_id}_{member_id}_{experiment_id}_{frequency}_{search_id}"
    variable_id_comma_separated = ",".join(variables)

    subprocess.check_call(
        [
            "esgpull",
            "add",
            "--tag",
            search_tag,
            "--track",
            "--distrib",
            "true",
            f"project:{project}",
            f"mip_era:{mip_era}",
            f"source_id:{source_id}",
            f"member_id:{member_id}",
            f"frequency:{frequency}",
            f"experiment_id:{experiment_id}",
            f"variable_id:{variable_id_comma_separated}",
        ]
    )

    subprocess.run(
        [
            "esgpull",
            "update",
            "-y",
            "--tag",
            search_tag,
        ],
        input=b"y",
        check=False,
    )

    return search_tag


def download_esgf(allow_disable_ssl: bool = False) -> None:
    """
    Queue up and download the ESGF data.

    Parameters
    ----------
    allow_disable_ssl
        Some ESGF nodes have SSL issues.

        Set this to true to allow the download to attempt to download without SSL.
    """
    try:
        subprocess.check_call(
            [
                "esgpull",
                "download",
            ]
        )
    except subprocess.CalledProcessError:
        if not allow_disable_ssl:
            raise

        subprocess.check_call(
            [
                "esgpull",
                "retry",
            ]
        )
        subprocess.check_call(
            [
                "esgpull",
                "download",
                "--disable-ssl",
            ]
        )


def main():  # noqa: D103
    search_tags = []

    source_id = "ACCESS-ESM1-5"
    member_id = "r1i1p1f1"
    experiment_id = "ssp126"

    for frequency, variables, search_id in (
        ("mon", ["tas", "rsut", "rlut", "rsdt"], "gregory-data"),
        ("fx", ["areacella"], "areacella"),
    ):
        search_tag = queue_esgf_download(
            source_id=source_id,
            member_id=member_id,
            experiment_id=experiment_id,
            frequency=frequency,
            variables=variables,
            search_id=search_id,
        )
        search_tags.append(search_tag)

    download_esgf(allow_disable_ssl=True)


if __name__ == "__main__":
    main()
