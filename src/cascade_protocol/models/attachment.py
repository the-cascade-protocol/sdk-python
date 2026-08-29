"""
Attachment metadata for the Cascade Protocol (core v3.7).

A ``cascade:Attachment`` describes a binary document stored alongside a Pod's
RDF: its media type, its content digest, and the pod-relative location of the
bytes. Attached to the record it renders with ``cascade:hasAttachment``.

RDF type: ``cascade:Attachment`` (``rdfs:subClassOf prov:Entity``)
Vocabulary: https://ns.cascadeprotocol.org/core/v1#

Modelling, and why:

FHIR R4 permits an attachment's bytes either inline as base64 (``Attachment.data``)
or by reference (``Attachment.url``). Core v3.7 takes the second, for a reason
specific to Pods rather than to messages: Turtle files here are parse-critical,
read in full by every consumer to answer any question, so an unbounded base64
literal is paid for by every reader including the ones that will never open the
attachment. The bytes live under ``attachments/{algorithm}/{digest}`` and the
Turtle carries only this small metadata node.

THE FILE'S NAME IS ITS DIGEST, which is what makes the arrangement checkable
rather than merely tidy: a consumer hashes what it read and compares it with
where it read it from, so nothing has to be trusted to keep name and content in
agreement.

THE ALGORITHM IS NAMED, AND IT IS NOT FHIR'S. ``Attachment.hash`` fixes SHA-1 in
the specification, and a collision-capable digest in a content-addressed store is
a mechanism by which one document silently replaces another. The algorithm is
carried explicitly in :attr:`Attachment.hash_algorithm`, named by its token in the
IANA Named Information Hash Algorithm Registry (RFC 6920). New implementations
MUST write ``"sha-256"``.

NOT a :class:`~cascade_protocol.models.common.CascadeRecord`. An attachment is
not a health record: it carries no ``cascade:dataProvenance`` and no
``cascade:schemaVersion``, and ``cascade:AttachmentShape`` requires neither.
Subclassing ``CascadeRecord`` would give every attachment two required fields
the vocabulary does not define for it.

IDENTIFIED BY IRI, not by a blank node. ``cascade:HasAttachmentEdgeShape``
asserts ``sh:nodeKind sh:IRI`` on the object of ``cascade:hasAttachment``,
precisely so that the record and the attachment can live in DIFFERENT files —
which is how a Pod partitioned by record type actually stores them.

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Attachment:
    """
    Metadata for a binary document stored alongside a Pod's RDF (core v3.7).

    ``cascade:AttachmentShape`` requires exactly the three facts without which
    an attachment node cannot do its job, all at ``sh:Violation``:
    :attr:`attachment_path` (without it there is nothing to open),
    :attr:`content_hash` (without it nothing distinguishes the right bytes from
    any other bytes at that path) and :attr:`hash_algorithm` (without it the
    digest cannot be recomputed and so cannot be checked, which makes the hash
    decorative).

    :attr:`media_type`'s PRESENCE is only a warning — stored bytes with no
    stated type are awkward to render but not lost — while its FORM is a
    violation.
    """

    id: str = ""
    """
    RDF subject IRI. Required: the edge shape asserts ``sh:nodeKind sh:IRI`` so
    that the attachment can live in a different file from the record that points
    at it.
    """

    type: str = field(default="Attachment", init=True)

    attachment_path: str = ""
    """
    Location of the bytes, as a path relative to the Pod root, for example
    ``"attachments/sha-256/8dd3c6b5..."``.

    FHIR alignment: ``Attachment.url``. Constrained to "/"-separated segments
    each beginning with an alphanumeric, in the character set pod-structure.md
    requires of Pod filenames. That form excludes an absolute path, a URL and
    any ``".."`` segment by construction: the first two break when a Pod is
    copied, and the third lets an attachment reference read a file outside the
    Pod.

    Maps to ``cascade:attachmentPath`` in Turtle serialization.
    """

    content_hash: str = ""
    """
    Digest of the attachment bytes, LOWERCASE HEXADECIMAL, with no algorithm
    prefix and no separator.

    Lowercase hex rather than the base64 FHIR uses for ``Attachment.hash``,
    because this value is also a filename: base64's alphabet includes ``"/"``
    and its case-sensitivity is unsafe on a case-insensitive filesystem. A
    single canonical spelling also means two Pods holding the same document
    hold the same string, which is the whole point of addressing by content.

    Maps to ``cascade:contentHash`` in Turtle serialization.
    """

    hash_algorithm: str = ""
    """
    Algorithm :attr:`content_hash` was computed with, named by its token in the
    IANA Named Information Hash Algorithm Registry (RFC 6920): ``"sha-256"``,
    ``"sha-512"``. New implementations MUST write ``"sha-256"``.

    Stated rather than assumed. An unlabelled digest cannot be verified by a
    consumer that does not already know how it was produced, and cannot be
    migrated when an algorithm weakens without rewriting every reference.

    NOT enumerated by the shape, and not enumerated here: the registry grows,
    and an enum would have to be revised to accept a stronger hash, which is the
    wrong direction for a property whose purpose is to let the algorithm be
    replaced.

    Maps to ``cascade:hashAlgorithm`` in Turtle serialization.
    """

    attachment_media_type: str | None = None
    """
    IANA media type of the bytes, for example ``"application/pdf"`` or
    ``"text/html"``. Registered names and syntax are RFC 6838.

    FHIR alignment: ``Attachment.contentType``.

    Spelled with the ``attachment_`` prefix the vocabulary uses rather than a
    bare ``media_type``, for the reason :attr:`attachment_title` records.

    Maps to ``cascade:attachmentMediaType`` in Turtle serialization.
    """

    byte_size: int | None = None
    """
    Size of the attachment in bytes. FHIR alignment: ``Attachment.size``.

    Recorded so a consumer can decide whether to read a file before opening it,
    and so a truncated copy is detectable without rehashing.

    Maps to ``cascade:byteSize`` in Turtle serialization.
    """

    attachment_title: str | None = None
    """
    Label to show in place of the bytes, verbatim from the source. FHIR
    alignment: ``Attachment.title``. Without it the only thing a reader can
    display for an attachment is a digest.

    NOT spelled ``title``: this SDK's predicate registry is keyed on the Python
    field name, and ``title`` is already bound to ``dcterms:title`` by
    ``cascade:ExportManifest``. Reusing it here would either silently emit an
    attachment label as a Dublin Core dataset title or force a type-specific
    override to undo the collision. The vocabulary's own spelling avoids both.

    Maps to ``cascade:attachmentTitle`` in Turtle serialization.
    """
