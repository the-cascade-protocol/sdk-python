"""
ImagingStudy data model for the Cascade Protocol.

Metadata record for a diagnostic imaging study (CT, MRI, X-ray, ultrasound).
Records that imaging exists and its key characteristics without requiring
access to DICOM images. Useful for clinical timeline, pre-procedure review,
and agent reasoning about imaging history.

RDF type: ``clinical:ImagingStudy``
Vocabulary: https://ns.cascadeprotocol.org/clinical/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class ImagingStudy(CascadeRecord):
    """
    An imaging study record in the Cascade Protocol.

    Required fields: ``study_description``, ``data_provenance``, ``schema_version``.

    Serializes as ``clinical:ImagingStudy`` in Turtle.
    """

    type: str = field(default="ImagingStudy", init=True)

    study_description: str = ""
    """
    Human-readable study description.
    Maps to ``clinical:studyDescription`` in Turtle serialization.
    """

    imaging_modality: str | None = None
    """
    Imaging modality: CT, MR, DX, US, NM.
    Maps to ``clinical:imagingModality`` in Turtle serialization.
    """

    study_date: str | None = None
    """
    Date of the study (ISO 8601).
    Maps to ``clinical:studyDate`` in Turtle serialization.
    """

    number_of_series: int | None = None
    """
    Number of series in the study.
    Maps to ``clinical:numberOfSeries`` in Turtle serialization.
    """

    dicom_study_uid: str | None = None
    """
    DICOM Study Instance UID.
    Maps to ``clinical:dicomStudyUid`` in Turtle serialization.
    """

    retrieve_url: str | None = None
    """
    URL to the DICOM server for retrieval, if available.
    Maps to ``clinical:retrieveUrl`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["ImagingStudy"]:  # type: ignore[name-defined]
        """Reconstruct a list of ImagingStudy records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
