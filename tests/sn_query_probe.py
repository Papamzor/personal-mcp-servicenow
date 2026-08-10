"""What ServiceNow's condition parser actually receives, modelled for tests.

Asserting on the *encoded URL* is how you write a test that passes while the
query is still wrong: ``sysparm_query=nameLIKEA&B`` reads as if it carries
``A&B`` and in fact carries ``A``, with a stray ``B`` parameter alongside. Every
encoder assertion in this repo goes through these helpers instead, so it is
pinned against the decoded value rather than against a string that merely looks
right.

Two decoding steps happen on ServiceNow's side, in this order:

1. The HTTP server splits the query string on ``&`` and percent-decodes each
   parameter value. ``urllib.parse.parse_qsl`` does exactly this, including
   reading ``+`` as a space.
2. ServiceNow's encoded-query parser splits the *already decoded*
   ``sysparm_query`` on ``^`` into conditions.

The order is the whole story. Step 1 is why a raw ``&`` in a value truncates the
condition it sits in. Step 2 is why a ``^`` in a value cannot be escaped at all:
by the time the parser runs, the percent-decoding has already happened, so the
parser sees a real separator no matter how the ``^`` was transmitted.

Reproduces the 2026-08-05 probes that measured the defect, so a test failure here
means the same thing a live-instance probe would.
"""
from __future__ import annotations

from urllib.parse import parse_qsl, urlsplit


def servicenow_params(url: str) -> dict[str, str]:
    """The parameters ServiceNow's servlet layer would see, percent-decoded."""
    return dict(parse_qsl(urlsplit(url).query, keep_blank_values=True))


def servicenow_conditions(url: str) -> list[str]:
    """The decoded ``sysparm_query`` split into conditions on ``^``."""
    query = servicenow_params(url).get("sysparm_query")
    if query is None:
        return []
    return query.split("^")


def servicenow_value_after(url: str, prefix: str) -> str:
    """The one condition beginning with *prefix*, with the prefix stripped.

    Raises if the query did not resolve to exactly one such condition. That is
    not defensiveness — it is the assertion: a value that splits on ``^``
    produces two matching conditions, and a value truncated by ``&`` produces a
    condition whose tail went missing.
    """
    matches = [
        condition[len(prefix):]
        for condition in servicenow_conditions(url)
        if condition.startswith(prefix)
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one condition starting with {prefix!r}, "
            f"got {len(matches)}: {servicenow_conditions(url)!r}"
        )
    return matches[0]


def assert_no_smuggled_parameter(url: str) -> None:
    """No URL parameter appeared that the caller did not ask for.

    The signature of the ``&`` defect: a value's ``&`` ends ``sysparm_query`` and
    everything after it becomes a sibling parameter. Every parameter this codebase
    sends is a ``sysparm_*``, so anything else is smuggled out of a value.
    """
    stray = [name for name in servicenow_params(url) if not name.startswith("sysparm_")]
    assert not stray, f"value escaped into URL parameter(s): {stray!r} in {url!r}"
