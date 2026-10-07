from pathlib import Path

from tiergen.backends.sensor._base import read_zeek_log

ZEEK = Path(__file__).parents[2] / "zeek" / "tests" / "samples"


def test_the_tab_separated_form_is_typed_by_its_header() -> None:
    records = list(read_zeek_log(ZEEK / "conn.log"))
    assert len(records) == 6
    web = next(r for r in records if r["conn_state"] == "SF")
    assert web["id.orig_h"] == "10.20.0.2"
    assert web["id.resp_p"] == 80
    assert web["proto"] == "tcp"
    assert isinstance(web["ts"], float)
    assert web["duration"] == 0.000905
    assert (web["orig_bytes"], web["resp_bytes"], web["orig_pkts"]) == (142, 325, 6)
    assert web["local_orig"] is True
    assert web["tunnel_parents"] is None  # the unset field
    rejected = next(r for r in records if r["conn_state"] == "REJ")
    assert rejected["service"] is None
    quiet = next(r for r in records if r["conn_state"] == "OTH")
    assert quiet["duration"] is None  # the unset field, in a numeric column


def test_the_json_form_reads_the_same() -> None:
    assert list(read_zeek_log(ZEEK / "conn.json.log")) == list(read_zeek_log(ZEEK / "conn.log"))


def test_sets_and_empties(tmp_path: Path) -> None:
    log = tmp_path / "x.log"
    log.write_text(
        "#separator \\x09\n#set_separator\t,\n#empty_field\t(empty)\n#unset_field\t-\n"
        "#fields\tts\ttags\tnames\n#types\ttime\tset[string]\tvector[string]\n"
        "1.5\ta,b\t(empty)\n2.5\t-\tx\n"
    )
    assert list(read_zeek_log(log)) == [
        {"ts": 1.5, "tags": ["a", "b"], "names": []},
        {"ts": 2.5, "tags": None, "names": ["x"]},
    ]
