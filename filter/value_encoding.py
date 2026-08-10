"""Per-value encoding boundary for ServiceNow encoded queries (v4.4.1).

One half of a two-part contract. The other half is
``http_layer/url_builder.encode_query_string``, and they only work together.

    producer  ->  encode_query_value(value)        THIS module: escapes one
                                                   caller value, refuses '^'
    assembly  ->  "field" + operator + value       structure added around it
    transport ->  encode_query_string(whole)       normalises, and no longer
                                                   treats '&' as an operator

Before v4.4.1 nothing escaped values on most paths, and the transport kept ``&``
in its safe-set — so it decoded any escaping a call site *had* applied and then
passed the raw ``&`` through, ending ``sysparm_query`` and truncating the
condition. Both halves had to change together: escaping here alone is undone by a
transport that treats ``&`` as safe, and dropping ``&`` there alone does nothing
for the paths that never escaped anything.

Why the safe-set here is not ``safe=''``
----------------------------------------
``= < > ( ) : @ !`` were measured (2026-08-05) to survive intact inside a value:
ServiceNow splits ``field=value`` on the first ``=`` only, and the rest are
ordinary characters to its condition parser. Leaving them unescaped keeps a
``javascript:gs.daysAgoStart(14)`` operand byte-identical to what shipped before.

It also carries the invariant the transport's idempotency depends on. That
function stays idempotent by decoding before re-encoding, which is only safe
while decoding cannot resurrect a structural character. Because this safe-set is
the transport's minus ``^`` — and ``^`` is refused rather than escaped — a
producer never emits a ``%XY`` for anything the transport leaves raw. Widening
either set breaks it, so the relationship is pinned by a test.

Why ``^`` is refused rather than escaped
----------------------------------------
``^`` is the condition separator and encoded-query syntax has no escape for it.
Correct end-to-end encoding still hands ServiceNow a *decoded* value containing
``^``, and its parser splits there. No encoder can carry it, so a value
containing one is refused: the alternative is running a broader query than the
caller asked for and reporting its rows as matches.

``^OR`` inside a filter value is the documented exception, and it is resolved
*before* this function is reached — ``_build_query_condition``'s structural
handlers claim such values as caller-supplied query fragments (an LLM writing
``{"priority": "1^ORpriority=2"}`` means the OR). Only a *terminal* value —
one that is about to be pasted after ``field=`` or after an operator — is
encoded here, so the refusal never fires on the structural path.
"""
from __future__ import annotations

from urllib.parse import quote

from constants import QUERY_VALUE_CARET_ERROR
from http_layer.errors import ErrorCode

#: Characters left unescaped inside a value: the transport's operator safe-set
#: minus ``^`` (refused) and minus ``&`` (must become ``%26`` or it separates
#: URL parameters). Measured harmless inside a value — see the module docstring.
QUERY_VALUE_SAFE = "=<>():@!"

#: The one character encoded-query syntax cannot carry inside a value.
QUERY_VALUE_FORBIDDEN = "^"

#: Values are echoed back in the refusal message; cap the echo so a long
#: description does not dominate the error.
_MESSAGE_VALUE_LIMIT = 80


class QueryValueError(ValueError):
    """A caller value cannot be carried by ServiceNow's encoded-query syntax.

    Raised at the point the value would be pasted into a query, so the request
    is never sent. Carries ``to_error_dict()`` in the same shape and vocabulary
    as ``ServiceNowRequestError`` (``VALIDATION``) — consumers already map that
    shape, and ``read_helpers.is_read_failure`` already recognises it, so a
    refusal travels back to the client through the paths that exist.
    """

    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        self.code = ErrorCode.VALIDATION
        super().__init__(message)

    @classmethod
    def refused(cls, value: str, template: str) -> "QueryValueError":
        """Build a refusal from a message template in ``constants``.

        Keeps the value echo (and its length cap) in one place, so a second
        refusal reason cannot drift from the first in how it reports the value.
        """
        return cls(
            value,
            template.format(value=_truncate(value), char=QUERY_VALUE_FORBIDDEN),
        )

    def to_error_dict(self) -> dict:
        """The §3.1 failure shape. Consumers return this straight to the client."""
        return {"error": {"code": self.code, "message": self.message}}


def _truncate(value: str) -> str:
    if len(value) <= _MESSAGE_VALUE_LIMIT:
        return value
    return value[:_MESSAGE_VALUE_LIMIT] + "..."


def encode_query_value(value: str) -> str:
    """Escape one caller-supplied value for use inside a ``sysparm_query``.

    Args:
        value: A terminal value — the operand of a single condition. Not a
            query fragment: a caller-built ``priority=1^ORpriority=2`` must not
            be passed here, it would be refused.

    Returns:
        The value with everything but ``QUERY_VALUE_SAFE`` percent-encoded.
        Non-string input is returned unchanged, so an ``int`` filter value from
        a JSON boundary still interpolates instead of raising ``TypeError``.

    Raises:
        QueryValueError: *value* contains ``^``.
    """
    if not isinstance(value, str):
        return value
    if QUERY_VALUE_FORBIDDEN in value:
        raise QueryValueError.refused(value, QUERY_VALUE_CARET_ERROR)
    return quote(value, safe=QUERY_VALUE_SAFE)
