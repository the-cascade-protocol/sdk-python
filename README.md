# cascade-protocol

Python SDK for the [Cascade Protocol](https://cascadeprotocol.org) — a privacy-first, local-first standard for serializing personal health data as RDF/Turtle.

## Installation

```bash
pip install cascade-protocol
```

With optional extras:

```bash
pip install "cascade-protocol[pandas]"       # pandas DataFrame integration
pip install "cascade-protocol[validation]"   # SHACL validation via pyshacl
pip install "cascade-protocol[notebooks]"    # Jupyter notebook support
pip install "cascade-protocol[all]"          # Everything
```

## Quick Start

```python
from cascade_protocol import Medication, serialize, validate, Pod

# Create a medication record
med = Medication(
    id="urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
    medication_name="Metoprolol Succinate",
    is_active=True,
    dose="25mg",
    data_provenance="ClinicalGenerated",
    schema_version="1.3",
)

# Serialize to Turtle
turtle = serialize(med)
print(turtle)

# Validate structural integrity
result = validate(turtle)
print(result.is_valid, result.errors)

# Open a Cascade Pod and query records
pod = Pod.open("./my-pod")
meds = pod.query("medications")

# Convert to pandas DataFrame (requires pandas extra)
df = meds.to_dataframe()
print(df.head())

# Reconstruct models from DataFrame
restored = Medication.from_dataframe(df)
```

## Serialization Output

```turtle
@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee> a health:MedicationRecord ;
    health:medicationName "Metoprolol Succinate" ;
    health:isActive true ;
    cascade:dataProvenance cascade:ClinicalGenerated ;
    cascade:schemaVersion "1.3" ;
    health:dose "25mg" .
```

## Supported Data Types

| Class | RDF Type | Description |
|---|---|---|
| `Medication` | `health:MedicationRecord` | Prescription and OTC drugs |
| `Condition` | `health:ConditionRecord` | Medical diagnoses |
| `Allergy` | `health:AllergyRecord` | Allergies and intolerances |
| `LabResult` | `health:LabResultRecord` | Laboratory test results |
| `VitalSign` | `clinical:VitalSign` | Vital sign measurements |
| `Immunization` | `health:ImmunizationRecord` | Vaccine records |
| `Procedure` | `health:ProcedureRecord` | Clinical procedures |
| `FamilyHistory` | `health:FamilyHistoryRecord` | Family health history |
| `Coverage` | `coverage:InsurancePlan` | Insurance coverage |
| `PatientProfile` | `cascade:PatientProfile` | Patient demographics |
| `ActivitySnapshot` | `health:ActivitySnapshot` | Daily activity data |
| `SleepSnapshot` | `health:SleepSnapshot` | Nightly sleep data |

## Pod API

```python
from cascade_protocol import Pod

pod = Pod.open("./my-pod")

# Query by data type
meds = pod.query("medications")
vitals = pod.query("vital-signs")
profile = pod.query("patient-profile")

# Iterate records
for med in meds:
    print(med.medication_name, med.dose)

# DataFrame conversion
df = meds.to_dataframe()
```

## Parsing Turtle

```python
from cascade_protocol.deserializer import parse, parse_one

# Parse multiple records
meds = parse(turtle_string, "MedicationRecord")

# Parse a single record
med = parse_one(turtle_string, "MedicationRecord")
```

## Namespaces

```python
from cascade_protocol.vocabularies import NAMESPACES, CURRENT_SCHEMA_VERSION

print(NAMESPACES["cascade"])   # https://ns.cascadeprotocol.org/core/v1#
print(NAMESPACES["health"])    # https://ns.cascadeprotocol.org/health/v1#
print(CURRENT_SCHEMA_VERSION)  # 1.3
```

## Privacy & Security

- Zero network calls during normal operation
- All processing is local
- No telemetry or analytics
- Data never leaves your machine

## License

Apache 2.0 — see [LICENSE](LICENSE).

## Links

- [Cascade Protocol Specification](https://cascadeprotocol.org/docs/spec)
- [Protocol Schema Reference](https://cascadeprotocol.org/docs/cascade-protocol-schemas)
- [Conformance Test Suite](https://github.com/cascade-protocol/conformance)
