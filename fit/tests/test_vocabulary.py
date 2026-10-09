from tiergen.core.events import AppEvent, ConnEvent, FiveTuple, SensorFlowId
from tiergen.core.ir import Choice, Endpoint
from tiergen.core.program import Program, ResolvedAction, ResolvedBehaviour
from tiergen.core.records import Peer
from tiergen.fit import label, vocabulary
from tiergen.fit.ingest import candidates_of

WS, WEB = "10.0.0.2", "10.0.0.80"


def _program() -> Program:
    browse = ResolvedBehaviour(
        "browse",
        ("idle", "home", "news"),
        (1.0, 0.0, 0.0),
        ((0.0, 0.5, 0.5), (1.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
        (),
        None,
        {
            "idle": None,
            "home": ResolvedAction("http.get", "web", {"path": "/"}, None),
            "news": ResolvedAction(
                "http.get", "web", {"path": Choice(("/news", "/sport"), (0.5, 0.5))}, None
            ),
        },
    )
    return Program(
        scenario="s",
        instance="lab/ws[0]",
        group="lab",
        kind="ws",
        platform="linux",
        hostname="lab-ws-0",
        seed=1,
        start="2026-10-05T08:00:00+02:00",
        duration_s=600,
        behaviours=(browse,),
        impls={"http.get": {"http.httpx": 1.0}},
        services=(),
        peers={"web": (Peer("lab/web[0]", WEB, (Endpoint("http", 80, "tcp"),)),)},
        routes=(),
        schedule=(),
        forwards=False,
        credentials=None,
    )


def conn(native: str, orig: str, port: int, at: float) -> ConnEvent:
    return ConnEvent(
        SensorFlowId("zeek", "p", native),
        FiveTuple(orig, 40000, WEB, port, "tcp"),
        at,
        None,
        None,
        None,
        None,
        None,
        "closed",
        {},
    )


def app(native: str, uri: str) -> AppEvent:
    return AppEvent(SensorFlowId("zeek", "p", native), 0, 0.0, "http", {"uri": uri}, {})


def test_the_vocabulary_places_connections_by_peer_port_and_path() -> None:
    vocab = vocabulary([_program()], {"lab/ws[0]": {"lan": WS}, "lab/web[0]": {"lan": WEB}})
    assert vocab.instance_of == {WS: "lab/ws[0]"}
    assert [c.state for c in candidates_of(vocab, "ws", "browse")] == ["home", "news"]
    home = vocab.match(conn("a", WS, 80, 1.0), [app("a", "/")])
    news = vocab.match(conn("b", WS, 80, 2.0), [app("b", "/sport")])
    assert not isinstance(home, str)
    assert not isinstance(news, str)
    assert (home.state, news.state) == ("home", "news")
    assert vocab.match(conn("c", WS, 80, 3.0), []) == "ambiguous"
    assert vocab.match(conn("d", WS, 22, 4.0), []) == "no action"
    assert vocab.match(conn("e", "10.0.0.1", 80, 5.0), []) == "unknown originator"


def test_labelling_makes_one_stream_per_instance_and_counts_the_rest() -> None:
    vocab = vocabulary([_program()], {"lab/ws[0]": {"lan": WS}, "lab/web[0]": {"lan": WEB}})
    events = [
        conn("a", WS, 80, 10.0),
        app("a", "/"),
        conn("b", WS, 80, 20.0),
        app("b", "/news"),
        conn("b2", WS, 80, 20.0),  # the same connection seen at a second capture point
        app("b2", "/news"),
        conn("c", WS, 80, 30.0),
        conn("d", "10.0.0.1", 80, 40.0),
    ]
    labelled = label(events, vocab)
    assert labelled.connections == 4
    assert labelled.unmapped.by_reason == {"ambiguous": 1, "unknown originator": 1}
    assert labelled.unmapped.originators == {"10.0.0.1": 1}
    [stream] = labelled.streams[("ws", "browse")]
    assert stream.host == "lab/ws[0]"
    assert stream.marks == ("home", "news")
    assert stream.times == (10.0, 20.0)
    assert labelled.app_coverage == 0.5
