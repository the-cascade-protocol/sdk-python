"""
Cascade Protocol namespace URIs and vocabulary constants.

These constants map directly to the RDF namespace prefixes used
in Turtle serialization throughout the Cascade Protocol ecosystem.

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Namespace URIs
# ---------------------------------------------------------------------------

NAMESPACES: dict[str, str] = {
    # Cascade Protocol core vocabulary (v1)
    "cascade": "https://ns.cascadeprotocol.org/core/v1#",
    # Cascade Protocol clinical vocabulary (v1)
    "clinical": "https://ns.cascadeprotocol.org/clinical/v1#",
    # Cascade Protocol health/wellness vocabulary (v1)
    "health": "https://ns.cascadeprotocol.org/health/v1#",
    # Cascade Protocol checkup vocabulary (v1)
    "checkup": "https://ns.cascadeprotocol.org/checkup/v1#",
    # Cascade Protocol POTS vocabulary (v1)
    "pots": "https://ns.cascadeprotocol.org/pots/v1#",
    # Cascade Protocol coverage/insurance vocabulary (v1)
    "coverage": "https://ns.cascadeprotocol.org/coverage/v1#",
    # HL7 FHIR namespace
    "fhir": "http://hl7.org/fhir/",
    # SNOMED CT namespace
    "sct": "http://snomed.info/sct/",
    # ICD-10-CM namespace
    "icd10": "http://hl7.org/fhir/sid/icd-10-cm/",
    # LOINC namespace
    "loinc": "http://loinc.org/rdf#",
    # RxNorm namespace
    "rxnorm": "http://www.nlm.nih.gov/research/umls/rxnorm/",
    # W3C PROV-O namespace
    "prov": "http://www.w3.org/ns/prov#",
    # XML Schema datatypes namespace
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    # Unified Code for Units of Measure namespace
    "ucum": "http://unitsofmeasure.org/",
    # FOAF namespace
    "foaf": "http://xmlns.com/foaf/0.1/",
    # vCard namespace for contact information
    "vcard": "http://www.w3.org/2006/vcard/ns#",
    # Solid Terms namespace for WebID profile discovery
    "solid": "http://www.w3.org/ns/solid/terms#",
    # Personal Information Management (PIM) namespace for Solid storage discovery
    "pim": "http://www.w3.org/ns/pim/space#",
    # Linked Data Platform namespace
    "ldp": "http://www.w3.org/ns/ldp#",
    # Dublin Core Terms namespace
    "dcterms": "http://purl.org/dc/terms/",
    # W3C DCAT 3 namespace. cascade:ExportManifest is rdfs:subClassOf
    # dcat:Dataset (core v3.4): a pod export is a published dataset with a
    # title, description, creation date and publisher, which DCAT already
    # standardises. Registered so a DCAT-aware consumer can resolve the
    # superclass; the SDK emits the dcterms: descriptive terms, not dcat: ones.
    "dcat": "http://www.w3.org/ns/dcat#",
    # W3C VoID namespace. cascade:RecordSummary is rdfs:subClassOf void:Dataset
    # and its entity-count properties are rdfs:subPropertyOf void:entities
    # (core v3.4). See RECORD_SUMMARY_COUNT_CLASSES below for the pairing.
    "void": "http://rdfs.org/ns/void#",
    # RDF namespace (used internally, not typically declared in output)
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    # RDFS namespace
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    # OWL namespace
    "owl": "http://www.w3.org/2002/07/owl#",
    # -- Draft vocabularies (v1-draft; NOT in VOCAB_VERSIONS until v1.0
    #    graduation, per D-PATH). Registered so their terms round-trip and the
    #    reverse predicate map resolves; no JSON-LD context for drafts yet. --
    # Cascade Protocol evidence vocabulary (v1-draft; grounding/assertion facets)
    "evidence": "https://ns.cascadeprotocol.org/evidence/v1#",
    # Cascade Protocol workbench vocabulary (v1-draft; investigation app, notes)
    "workbench": "https://ns.cascadeprotocol.org/workbench/v1#",
    # W3C Web Annotation namespace (notes substrate: body/target/motivation/selectors)
    "oa": "http://www.w3.org/ns/oa#",
    # W3C RDF Calendar (iCalendar) namespace (follow-up due date / status)
    "ical": "http://www.w3.org/2002/12/cal/ical#",
    # SKOS namespace (workbench:followUp is an oa:Motivation with skos:broader)
    "skos": "http://www.w3.org/2004/02/skos/core#",
}

# ---------------------------------------------------------------------------
# Type Mapping
# ---------------------------------------------------------------------------

# Mapping from data type key (Pod file paths / CLI queries) to RDF vocabulary info.
# Each entry contains:
#   rdf_type  - The rdf:type value for the record (prefixed name)
#   name_key  - The JSON/Python property holding the record's display name
#   name_pred - The Turtle predicate for the name field (prefixed name)
TYPE_MAPPING: dict[str, dict[str, str]] = {
    "medications": {
        "rdf_type": "clinical:Medication",
        "name_key": "medication_name",
        "name_pred": "clinical:drugName",
    },
    "conditions": {
        "rdf_type": "health:ConditionRecord",
        "name_key": "condition_name",
        "name_pred": "health:conditionName",
    },
    "allergies": {
        "rdf_type": "health:AllergyRecord",
        "name_key": "allergen",
        "name_pred": "health:allergen",
    },
    "lab-results": {
        "rdf_type": "health:LabResultRecord",
        "name_key": "test_name",
        "name_pred": "health:testName",
    },
    "immunizations": {
        "rdf_type": "health:ImmunizationRecord",
        "name_key": "vaccine_name",
        "name_pred": "health:vaccineName",
    },
    "vital-signs": {
        "rdf_type": "clinical:VitalSign",
        "name_key": "vital_type",
        "name_pred": "clinical:vitalType",
    },
    "supplements": {
        "rdf_type": "clinical:Supplement",
        "name_key": "supplement_name",
        "name_pred": "clinical:supplementName",
    },
    # clinical v1.15: clinical:Procedure is the class clinical:ProcedureShape
    # targets, and clinical:procedureName is the canonical name spelling. The
    # health: vocabulary defines NEITHER a procedure class NOR
    # health:procedureName, so the previous health:ProcedureRecord type ran
    # against no shape at all. health:procedureName is still READ during the
    # migration window; see health_procedure_name below.
    "procedures": {
        "rdf_type": "clinical:Procedure",
        "name_key": "procedure_name",
        "name_pred": "clinical:procedureName",
    },
    "family-history": {
        "rdf_type": "health:FamilyHistoryRecord",
        "name_key": "condition_name",
        "name_pred": "health:conditionName",
    },
    "insurance": {
        "rdf_type": "clinical:CoverageRecord",
        "name_key": "provider_name",
        "name_pred": "clinical:providerName",
    },
    "encounters": {
        "rdf_type": "clinical:Encounter",
        "name_key": "encounter_type",
        "name_pred": "clinical:encounterType",
    },
    "medication-administrations": {
        "rdf_type": "clinical:MedicationAdministration",
        "name_key": "medication_name",
        "name_pred": "clinical:drugName",
    },
    "implanted-devices": {
        "rdf_type": "clinical:ImplantedDevice",
        "name_key": "device_type",
        "name_pred": "clinical:deviceType",
    },
    "imaging-studies": {
        "rdf_type": "clinical:ImagingStudy",
        "name_key": "study_description",
        "name_pred": "clinical:studyDescription",
    },
    "claims": {
        "rdf_type": "coverage:ClaimRecord",
        "name_key": "claim_type",
        "name_pred": "coverage:claimType",
    },
    "benefit-statements": {
        "rdf_type": "coverage:BenefitStatement",
        "name_key": "adjudication_status",
        "name_pred": "coverage:adjudicationStatus",
    },
    "denial-notices": {
        "rdf_type": "coverage:DenialNotice",
        "name_key": "denied_procedure_code",
        "name_pred": "coverage:deniedProcedureCode",
    },
    "appeals": {
        "rdf_type": "coverage:AppealRecord",
        "name_key": "appeal_level",
        "name_pred": "coverage:appealLevel",
    },
    "patient-profile": {
        "rdf_type": "cascade:PatientProfile",
        "name_key": "name",
        "name_pred": "foaf:name",
    },
    "activity": {
        "rdf_type": "health:ActivitySnapshot",
        "name_key": "date",
        "name_pred": "health:date",
    },
    "sleep": {
        "rdf_type": "health:SleepSnapshot",
        "name_key": "date",
        "name_pred": "health:date",
    },
    "heart-rate": {
        "rdf_type": "clinical:VitalSign",
        "name_key": "vital_type",
        "name_pred": "clinical:vitalType",
    },
    "blood-pressure": {
        "rdf_type": "clinical:VitalSign",
        "name_key": "vital_type",
        "name_pred": "clinical:vitalType",
    },
    "clinical-social-history": {
        "rdf_type": "clinical:SocialHistoryRecord",
        "name_key": "social_history_category",
        "name_pred": "clinical:socialHistoryCategory",
    },
    "ai-extraction-activities": {
        "rdf_type": "cascade:AIExtractionActivity",
        "name_key": "extraction_model",
        "name_pred": "cascade:extractionModel",
    },
    "ai-discarded-extractions": {
        "rdf_type": "cascade:AIDiscardedExtraction",
        "name_key": "discard_reason",
        "name_pred": "cascade:discardReason",
    },
    "social-history-consents": {
        "rdf_type": "cascade:SocialHistoryConsent",
        "name_key": "consent_scope",
        "name_pred": "cascade:consentScope",
    },
    "social-history": {
        "rdf_type": "health:SocialHistoryRecord",
        "name_key": "smoking_status",
        "name_pred": "health:smokingStatus",
    },
    "advisory-application-activities": {
        "rdf_type": "cascade:AdvisoryApplicationActivity",
        "name_key": "applied_triples_count",
        "name_pred": "cascade:appliedTriplesCount",
    },
    "ai-generation-activities": {
        "rdf_type": "cascade:AIGenerationActivity",
        "name_key": "extraction_model",
        "name_pred": "cascade:extractionModel",
    },
    "proxy-agents": {
        "rdf_type": "cascade:ProxyAgent",
        "name_key": "proxy_web_id",
        "name_pred": "cascade:proxyWebID",
    },
    # -- health v2.5 -- single-day entries inside the wellness history
    #    containers. Distinct from the 7-day aggregate health:ActivitySnapshot /
    #    health:SleepSnapshot above; the vocabulary keeps the two apart and so
    #    does this SDK.
    "daily-activity": {
        "rdf_type": "health:DailyActivitySnapshot",
        "name_key": "date",
        "name_pred": "cascade:date",
    },
    "daily-sleep": {
        "rdf_type": "health:DailySleepSnapshot",
        "name_key": "date",
        "name_pred": "cascade:date",
    },
    "daily-vitals": {
        "rdf_type": "health:DailyVitalReading",
        "name_key": "date",
        "name_pred": "health:date",
    },
    # -- health v2.5 -- wellness container classes. Each is
    #    rdfs:subClassOf health:HealthProfile and carries one family of
    #    history containers.
    "activity-data": {
        "rdf_type": "health:ActivityData",
        "name_key": "date",
        "name_pred": "health:date",
    },
    "sleep-data": {
        "rdf_type": "health:SleepData",
        "name_key": "date",
        "name_pred": "health:date",
    },
    "heart-rate-data": {
        "rdf_type": "health:HeartRateData",
        "name_key": "date",
        "name_pred": "health:date",
    },
    "blood-pressure-data": {
        "rdf_type": "health:BloodPressureData",
        "name_key": "date",
        "name_pred": "health:date",
    },
    "hrv-data": {
        "rdf_type": "health:HRVData",
        "name_key": "date",
        "name_pred": "health:date",
    },
    "body-measurements": {
        "rdf_type": "health:BodyMeasurements",
        "name_key": "date",
        "name_pred": "health:date",
    },
    # -- core v3.4 -- pod export manifest --
    "export-manifest": {
        "rdf_type": "cascade:ExportManifest",
        "name_key": "title",
        "name_pred": "dcterms:title",
    },
    "record-summary": {
        "rdf_type": "cascade:RecordSummary",
        "name_key": "domain",
        "name_pred": "cascade:domain",
    },
    "interaction-scenario": {
        "rdf_type": "cascade:InteractionScenario",
        "name_key": "title",
        "name_pred": "dcterms:title",
    },
}

# ---------------------------------------------------------------------------
# Deprecated rdf:type spellings (clinical v1.13)
# ---------------------------------------------------------------------------

# Four clinical: classes were deprecated in clinical v1.13 (owl:deprecated true
# with rdfs:seeAlso pointing at the health: class listed here). They were NOT
# removed: the pod export path is still their sole emitter and existing pods
# contain them.
#
# The asymmetry this map encodes, deliberately:
#   READERS accept both spellings. Dropping the deprecated types would silently
#          lose every record in an already-written pod.
#   WRITERS emit only the health: forms. Nothing in this SDK serializes a
#          clinical: spelling for these four classes.
DEPRECATED_TYPE_ALIASES: dict[str, str] = {
    "clinical:LabResult": "health:LabResultRecord",
    "clinical:Condition": "health:ConditionRecord",
    "clinical:Allergy": "health:AllergyRecord",
    "clinical:Immunization": "health:ImmunizationRecord",
    # clinical v1.15: no vocabulary ever defined health:ProcedureRecord and no
    # shape targeted it.
    "health:ProcedureRecord": "clinical:Procedure",
}

# ---------------------------------------------------------------------------
# Record summary counts and their VoID pairing (core v3.4)
# ---------------------------------------------------------------------------

# cascade:RecordSummary is rdfs:subClassOf void:Dataset. Each entity-count
# property below is rdfs:subPropertyOf void:entities, and all but
# cascade:coverageCount name the void:class they count, so a VoID-aware
# consumer can read Cascade record counts with no Cascade-specific code.
RECORD_SUMMARY_COUNT_CLASSES: dict[str, str] = {
    "cascade:conditionCount": "https://ns.cascadeprotocol.org/health/v1#ConditionRecord",
    "cascade:medicationCount": "https://ns.cascadeprotocol.org/clinical/v1#Medication",
    "cascade:allergyCount": "https://ns.cascadeprotocol.org/health/v1#AllergyRecord",
    "cascade:labResultCount": "https://ns.cascadeprotocol.org/health/v1#LabResultRecord",
    "cascade:immunizationCount": "https://ns.cascadeprotocol.org/health/v1#ImmunizationRecord",
    "cascade:supplementCount": "https://ns.cascadeprotocol.org/clinical/v1#Supplement",
}

# Entity counts: subproperties of void:entities. cascade:coverageCount is one
# of these but names no void:class in the ontology, so it is listed here and
# absent from RECORD_SUMMARY_COUNT_CLASSES.
RECORD_SUMMARY_ENTITY_COUNTS: frozenset[str] = frozenset(
    set(RECORD_SUMMARY_COUNT_CLASSES) | {"cascade:coverageCount"}
)

# Day counts. These count DAYS COVERED, not entities, and are deliberately NOT
# subproperties of void:entities: a 30-day heart rate history holds far more
# than 30 readings. Treating them as entity counts would make the VoID reading
# of a pod wrong.
RECORD_SUMMARY_DAY_COUNTS: frozenset[str] = frozenset({
    "cascade:vitalSignDays",
    "cascade:heartRateDays",
    "cascade:bloodPressureDays",
    "cascade:activityDays",
    "cascade:sleepDays",
})

# ---------------------------------------------------------------------------
# Record Type to Mapping Key
# ---------------------------------------------------------------------------

# Mapping from record type string (e.g. 'MedicationRecord') to the
# TYPE_MAPPING key (e.g. 'medications'). Used for serialization dispatch.
TYPE_TO_MAPPING_KEY: dict[str, str] = {
    "MedicationRecord": "medications",
    "ConditionRecord": "conditions",
    "AllergyRecord": "allergies",
    "LabResultRecord": "lab-results",
    "ImmunizationRecord": "immunizations",
    "VitalSign": "vital-signs",
    "Supplement": "supplements",
    # Two accepted spellings, one mapping key. The FIRST entry is the canonical
    # record-type string the deserializer returns, exactly as for the other
    # multi-spelling entries below. "ProcedureRecord" stays canonical so the
    # Procedure dataclass and parse(..., "ProcedureRecord") are unchanged; the
    # RDF type it serializes to is clinical:Procedure either way, which is the
    # part clinical v1.15 corrects. A record-type string differing from the RDF
    # local name is already the norm here (MedicationRecord is clinical:Medication).
    "ProcedureRecord": "procedures",
    "Procedure": "procedures",
    "FamilyHistoryRecord": "family-history",
    "CoverageRecord": "insurance",
    "InsurancePlan": "insurance",
    "Encounter": "encounters",
    "MedicationAdministration": "medication-administrations",
    "ImplantedDevice": "implanted-devices",
    "ImagingStudy": "imaging-studies",
    "ClaimRecord": "claims",
    "BenefitStatement": "benefit-statements",
    "DenialNotice": "denial-notices",
    "AppealRecord": "appeals",
    "PatientProfile": "patient-profile",
    "ActivitySnapshot": "activity",
    "SleepSnapshot": "sleep",
    "ClinicalSocialHistoryRecord": "clinical-social-history",
    "AIExtractionActivity": "ai-extraction-activities",
    "AIDiscardedExtraction": "ai-discarded-extractions",
    "SocialHistoryConsent": "social-history-consents",
    "SocialHistoryRecord": "social-history",
    "AdvisoryApplicationActivity": "advisory-application-activities",
    "AIGenerationActivity": "ai-generation-activities",
    "ProxyAgent": "proxy-agents",
    # -- health v2.5 --
    "DailyActivitySnapshot": "daily-activity",
    "DailySleepSnapshot": "daily-sleep",
    "DailyVitalReading": "daily-vitals",
    "ActivityData": "activity-data",
    "SleepData": "sleep-data",
    "HeartRateData": "heart-rate-data",
    "BloodPressureData": "blood-pressure-data",
    "HRVData": "hrv-data",
    "BodyMeasurements": "body-measurements",
    # -- core v3.4 --
    "ExportManifest": "export-manifest",
    "RecordSummary": "record-summary",
    "InteractionScenario": "interaction-scenario",
}

# ---------------------------------------------------------------------------
# Wellness history containers (health v2.5)
# ---------------------------------------------------------------------------

# Each wellness container class carries one or more ordered history
# properties. The value is an rdf:List, so entry ORDER is part of the data:
# these are time series, and reading them into an unordered collection loses
# information that is in the file.
#
# The second element of each pair is the entry class the ontology declares as
# the property's rdfs:range. health:BloodPressureReading and health:HRVReading
# are NOT modelled in this SDK yet, so those two containers read with an empty
# history until they are; the reader resolves whatever registered record type
# an entry carries rather than assuming the declared range, so adding those
# classes later needs no change here.
WELLNESS_HISTORY_PROPERTIES: dict[str, list[tuple[str, str]]] = {
    "ActivityData": [("health:dailyActivityHistory", "DailyActivitySnapshot")],
    "SleepData": [("health:dailySleepHistory", "DailySleepSnapshot")],
    "HeartRateData": [
        ("health:restingHeartRateHistory", "DailyVitalReading"),
        ("health:walkingHeartRateHistory", "DailyVitalReading"),
    ],
    "BloodPressureData": [("health:bloodPressureHistory", "BloodPressureReading")],
    "HRVData": [("health:hrvHistory", "HRVReading")],
    "BodyMeasurements": [("health:bodyMassHistory", "DailyVitalReading")],
}

# ---------------------------------------------------------------------------
# Schema Version
# ---------------------------------------------------------------------------

# Current Cascade Protocol schema version.
CURRENT_SCHEMA_VERSION = "1.3"

# ---------------------------------------------------------------------------
# Property Predicates
# ---------------------------------------------------------------------------

# Mapping from Python snake_case property names to their Turtle predicates.
# Used during serialization to convert Python field values to RDF triples.
PROPERTY_PREDICATES: dict[str, str] = {
    # -- Medication predicates (clinical: vocabulary) --
    "medication_name": "clinical:drugName",
    "dose": "clinical:dosage",
    "frequency": "health:frequency",
    "route": "health:route",
    "prescriber": "health:prescriber",
    "start_date": "health:startDate",
    "end_date": "health:endDate",
    "is_active": "clinical:status",
    "rx_norm_code": "clinical:rxNormCode",
    "medication_class": "health:medicationClass",
    "affects_vital_signs": "health:affectsVitalSigns",

    # -- Condition predicates (health: vocabulary) --
    "condition_name": "health:conditionName",
    "status": "health:status",
    "onset_date": "health:onsetDate",
    "icd10_code": "health:icd10Code",
    "snomed_code": "health:snomedCode",
    "condition_class": "health:conditionClass",
    "monitored_vital_signs": "health:monitoredVitalSigns",

    # -- Allergy predicates (health: vocabulary) --
    "allergen": "health:allergen",
    "allergy_category": "health:allergyCategory",
    "reaction": "health:reaction",
    "allergy_severity": "health:allergySeverity",

    # -- Lab result predicates (health: vocabulary) --
    "test_name": "health:testName",
    "result_value": "health:resultValue",
    "result_unit": "health:resultUnit",
    "reference_range": "health:referenceRange",
    "interpretation": "health:interpretation",
    "performed_date": "health:performedDate",
    "test_code": "health:testCode",
    "lab_category": "health:labCategory",
    "specimen_type": "health:specimenType",
    "reported_date": "health:reportedDate",
    "ordering_provider": "health:orderingProvider",
    "performing_lab": "health:performingLab",

    # -- Immunization predicates (health: vocabulary) --
    "vaccine_name": "health:vaccineName",
    "administration_date": "health:administrationDate",
    "vaccine_code": "health:vaccineCode",
    "manufacturer": "health:manufacturer",
    "lot_number": "health:lotNumber",
    "dose_quantity": "health:doseQuantity",
    "site": "health:site",
    "administering_provider": "health:administeringProvider",
    "administering_location": "health:administeringLocation",

    # -- Vital sign predicates (clinical: vocabulary) --
    "vital_type": "clinical:vitalType",
    "vital_type_name": "clinical:vitalTypeName",
    "value": "clinical:value",
    "unit": "clinical:unit",
    "effective_date": "clinical:effectiveDate",
    "loinc_code": "clinical:loincCode",
    "reference_range_low": "clinical:referenceRangeLow",
    "reference_range_high": "clinical:referenceRangeHigh",

    # -- Clinical enrichment predicates --
    "provenance_class": "clinical:provenanceClass",
    "source_fhir_resource_type": "clinical:sourceFhirResourceType",
    "clinical_intent": "clinical:clinicalIntent",
    "indication": "clinical:indication",
    "course_of_therapy_type": "clinical:courseOfTherapyType",
    "as_needed": "clinical:asNeeded",
    "medication_form": "clinical:medicationForm",
    "active_ingredient": "clinical:activeIngredient",
    "ingredient_strength": "clinical:ingredientStrength",
    "refills_allowed": "clinical:refillsAllowed",
    "supply_duration_days": "clinical:supplyDurationDays",
    "prescription_category": "clinical:prescriptionCategory",
    "drug_codes": "clinical:drugCode",

    # -- Coverage predicates (clinical: and coverage: vocabularies) --
    "provider_name": "clinical:providerName",
    "member_id": "clinical:memberId",
    "group_number": "clinical:groupNumber",
    "plan_name": "clinical:planName",
    "plan_type": "clinical:planType",
    "coverage_type": "clinical:coverageType",
    "relationship": "clinical:relationship",
    "effective_period_start": "clinical:effectivePeriodStart",
    "effective_period_end": "clinical:effectivePeriodEnd",
    "payor_name": "clinical:payorName",
    "subscriber_id": "clinical:subscriberId",
    "subscriber_relationship": "coverage:subscriberRelationship",
    "subscriber_name": "coverage:subscriberName",
    "effective_start": "coverage:effectiveStart",
    "effective_end": "coverage:effectiveEnd",
    "rx_bin": "coverage:rxBin",
    "rx_pcn": "coverage:rxPcn",
    "rx_group": "coverage:rxGroup",

    # -- Patient profile predicates (cascade:, foaf:, and vcard: vocabularies) --
    "date_of_birth": "cascade:dateOfBirth",
    "biological_sex": "cascade:biologicalSex",
    "contact_phone": "vcard:hasTelephone",
    "contact_email": "vcard:hasEmail",
    "computed_age": "cascade:computedAge",
    "age_group": "cascade:ageGroup",
    "gender_identity": "cascade:genderIdentity",
    "profile_id": "cascade:profileId",
    "name": "foaf:name",
    "given_name": "foaf:givenName",
    "family_name": "foaf:familyName",
    "blood_type": "health:bloodType",

    # -- Procedure predicates --
    # clinical:procedureName is canonical (clinical v1.15). The health:
    # spelling below is what a C-CDA import path writes on records it types
    # clinical:Procedure; it is accepted for the migration window and both
    # halves are removed together when the window closes.
    "procedure_name": "clinical:procedureName",
    "health_procedure_name": "health:procedureName",
    "performer": "health:performer",
    "location": "health:location",

    # -- Family history predicates --
    # Note: `relationship` is shared with Coverage (clinical:relationship)
    "onset_age": "health:onsetAge",

    # -- Shared predicates --
    "notes": "health:notes",
    "source_record_id": "health:sourceRecordId",
    # core v3.5, the ORIGIN axis. Distinct from cascade:sourceSystem (the
    # INGESTION batch) and from clinical:sourceEHR (a display label): this is
    # the only one of the three that may be used as a reconciliation key.
    "source_identity": "cascade:sourceIdentity",
    # The INGESTION axis. Published in the JSON-LD context since core v3.0 but
    # never registered here, so it could not round-trip while the ORIGIN axis
    # above could. Not a reconciliation key; see the comment on the property.
    "source_system": "cascade:sourceSystem",
    # core v3.6: why this record's primary VALUE is absent. Meaningful only
    # when that value is in fact absent, and bound to the 15 codes of
    # http://terminology.hl7.org/CodeSystem/data-absent-reason.
    "data_absent_reason": "cascade:dataAbsentReason",
    # health v2.7 / clinical v1.15: the source's own interpretation code,
    # verbatim, for the case where it is in neither ratified value set. The
    # clinical: spelling is written on vital signs; see the serializer's
    # type-specific overrides.
    "interpretation_source_code": "health:interpretationSourceCode",

    # -- Activity snapshot predicates --
    "date": "health:date",
    "steps": "health:steps",
    "distance": "health:distance",
    "active_minutes": "health:activeMinutes",
    "calories": "health:calories",

    # -- Sleep snapshot predicates --
    "total_sleep_minutes": "health:totalSleepMinutes",
    "deep_sleep_minutes": "health:deepSleepMinutes",
    "rem_sleep_minutes": "health:remSleepMinutes",
    "light_sleep_minutes": "health:lightSleepMinutes",
    "awakenings": "health:awakenings",

    # -- Encounter predicates (clinical: vocabulary) --
    "encounter_type": "clinical:encounterType",
    "encounter_class": "clinical:encounterClass",
    "encounter_status": "clinical:encounterStatus",
    "encounter_start": "clinical:encounterStart",
    "encounter_end": "clinical:encounterEnd",
    "facility_name": "clinical:facilityName",

    # -- MedicationAdministration predicates (clinical: vocabulary) --
    "administered_date": "clinical:administeredDate",
    "administered_dose": "clinical:administeredDose",
    "administered_route": "clinical:administeredRoute",
    "administration_status": "clinical:administrationStatus",

    # -- ImplantedDevice predicates (clinical: vocabulary) --
    "device_type": "clinical:deviceType",
    "implant_date": "clinical:implantDate",
    "device_manufacturer": "clinical:deviceManufacturer",
    "udi_carrier": "clinical:udiCarrier",
    "device_status": "clinical:deviceStatus",

    # -- ImagingStudy predicates (clinical: vocabulary) --
    "imaging_modality": "clinical:imagingModality",
    "study_description": "clinical:studyDescription",
    "number_of_series": "clinical:numberOfSeries",
    "study_date": "clinical:studyDate",
    "dicom_study_uid": "clinical:dicomStudyUid",
    "retrieve_url": "clinical:retrieveUrl",

    # -- Coverage v1.3 — ClaimRecord predicates --
    "claim_date": "coverage:claimDate",
    "claim_total": "coverage:claimTotal",
    "claim_status": "coverage:claimStatus",
    "claim_type": "coverage:claimType",
    "billing_provider": "coverage:billingProvider",

    # -- Coverage v1.3 — BenefitStatement predicates --
    "adjudication_date": "coverage:adjudicationDate",
    "adjudication_status": "coverage:adjudicationStatus",
    "outcome_code": "coverage:outcomeCode",
    "denial_reason": "coverage:denialReason",
    "total_billed": "coverage:totalBilled",
    "total_allowed": "coverage:totalAllowed",
    "total_paid": "coverage:totalPaid",
    "patient_responsibility": "coverage:patientResponsibility",
    "related_claim": "coverage:relatedClaim",

    # -- Coverage v1.3 — DenialNotice predicates --
    "denied_procedure_code": "coverage:deniedProcedureCode",
    "denial_reason_code": "coverage:denialReasonCode",
    "denial_letter_date": "coverage:denialLetterDate",
    "appeal_deadline": "coverage:appealDeadline",
    "coverage_policy_reference": "coverage:coveragePolicyReference",

    # -- Coverage v1.3 — AppealRecord predicates --
    "appeal_level": "coverage:appealLevel",
    "appeal_filed_date": "coverage:appealFiledDate",
    "appeal_outcome": "coverage:appealOutcome",
    "appeal_outcome_date": "coverage:appealOutcomeDate",

    # -- Core v2.8 — FHIR passthrough predicates --
    "layer_promotion_status": "cascade:layerPromotionStatus",
    "fhir_json": "cascade:fhirJson",
    "source_record_date": "cascade:sourceRecordDate",

    # -- Core predicates (cascade: vocabulary) --
    "data_provenance": "cascade:dataProvenance",
    "schema_version": "cascade:schemaVersion",

    # -- Clinical v1.8 -- SocialHistoryRecord predicates --
    "social_history_category": "clinical:socialHistoryCategory",
    "packs_per_year": "clinical:packsPerYear",
    "substance_type": "clinical:substanceType",
    "frequency_description": "clinical:frequencyDescription",
    "social_history_consent": "clinical:socialHistoryConsent",

    # -- Core v3.0 -- AIExtractionActivity predicates --
    "extraction_confidence": "cascade:extractionConfidence",
    "extraction_model": "cascade:extractionModel",
    "source_narrative_section": "cascade:sourceNarrativeSection",
    "requires_user_review": "cascade:requiresUserReview",

    # -- Core v3.0 -- AIDiscardedExtraction predicates --
    "discard_reason": "cascade:discardReason",

    # -- Core v3.0 -- SocialHistoryConsent predicates --
    "consent_scope": "cascade:consentScope",
    "consent_granted_at": "cascade:consentGrantedAt",
    "consent_revoked_at": "cascade:consentRevokedAt",

    # -- Health v2.4 -- SocialHistoryRecord predicates (consumer-reported) --
    "smoking_status": "health:smokingStatus",
    "alcohol_use": "health:alcoholUse",
    "exercise_frequency": "health:exerciseFrequency",
    "occupational_exposure": "health:occupationalExposure",

    # -- Core v3.1-3.3 -- AIGenerationActivity predicates --
    "prompt_version": "cascade:promptVersion",
    "generation_temperature": "cascade:generationTemperature",
    "trigger": "cascade:trigger",

    # -- Core v3.1-3.3 -- AdvisoryApplicationActivity predicates --
    "applied_triples_count": "cascade:appliedTriplesCount",

    # -- Core v3.1-3.3 -- ProxyAgent predicates --
    "acts_for_patient": "cascade:actsForPatient",
    "proxy_web_id": "cascade:proxyWebID",
    "proxy_relationship": "cascade:proxyRelationship",
    "proxy_scope": "cascade:proxyScope",
    "proxy_granted_at": "cascade:proxyGrantedAt",
    "proxy_revoked_at": "cascade:proxyRevokedAt",

    # -- evidence v1-draft.0.2 (DRAFT) -- verdict-taxonomy-v2 facet predicates.
    #    The grounding outcome as orthogonal facets on an evidence:Assertion.
    "direction": "evidence:direction",
    "basis": "evidence:basis",
    "strength": "evidence:strength",
    "settled": "evidence:settled",
    "reason": "evidence:reason",
    "confidence": "evidence:confidence",

    # -- workbench v1-draft.0.4 (DRAFT) -- user filing label (organization axis).
    "user_source_label": "workbench:userSourceLabel",
    # Note: workbench:followUp is an oa:Motivation individual (a VALUE of
    # oa:motivatedBy), not a predicate. Like the cascade: provenance individuals
    # it is not registered here; the "workbench" namespace above lets it
    # round-trip as a prefixed value.

    # -- Health v2.5 -- daily snapshot predicates. These are the SINGLE-DAY
    #    forms. health:activeEnergyBurnedKcal / exerciseMinutesWeekly /
    #    standHoursDaily are the 7-day aggregate forms on
    #    health:ActivitySnapshot; the two sets are distinct and both are
    #    emitted, so they are registered separately.
    "active_energy_kcal": "health:activeEnergyKcal",
    "exercise_minutes": "health:exerciseMinutes",
    "stand_hours": "health:standHours",
    "duration_hours": "health:durationHours",
    # health:sleepQuality takes an IRI object (health:Good), not a string
    # literal — see the serializer's sleep-quality handling.
    "sleep_quality": "health:sleepQuality",
    # -- Core v3.4 -- reading-level terms emitted on history-container entries.
    #    cascade:sampleCount says how many underlying samples an aggregated
    #    reading came from; a resting heart rate derived from 142 samples is a
    #    stronger observation than one derived from 2.
    "sample_count": "cascade:sampleCount",

    # -- Core v3.4 -- pod export manifest.
    #    cascade:ExportManifest is rdfs:subClassOf dcat:Dataset, so the
    #    descriptive terms are the DCAT-standard dcterms: ones rather than
    #    Cascade-specific inventions.
    "title": "dcterms:title",
    "description": "dcterms:description",
    "created": "dcterms:created",
    "creator": "dcterms:creator",
    "patient_profile_version": "cascade:patientProfileVersion",
    "provenance_layers": "cascade:provenanceLayers",
    "clinical_summary": "cascade:clinicalSummary",
    "wellness_summary": "cascade:wellnessSummary",
    "device_sources": "cascade:deviceSources",
    "interaction_scenarios": "cascade:interactionScenarios",
    # -- Core v3.4 -- record summary (rdfs:subClassOf void:Dataset) --
    "domain": "cascade:domain",
    "condition_count": "cascade:conditionCount",
    "medication_count": "cascade:medicationCount",
    "allergy_count": "cascade:allergyCount",
    "lab_result_count": "cascade:labResultCount",
    "immunization_count": "cascade:immunizationCount",
    "coverage_count": "cascade:coverageCount",
    "supplement_count": "cascade:supplementCount",
    "vital_sign_days": "cascade:vitalSignDays",
    "heart_rate_days": "cascade:heartRateDays",
    "blood_pressure_days": "cascade:bloodPressureDays",
    "activity_days": "cascade:activityDays",
    "sleep_days": "cascade:sleepDays",
    # -- Core v3.4 -- interaction scenario (deliberately novel: no ratified
    #    vocabulary models cross-provenance correlation as a first-class thing)
    "involved_resources": "cascade:involvedResources",
    "severity": "cascade:severity",
    "requires_cross_provenance": "cascade:requiresCrossProvenance",
    # -- Core v3.4 -- device sources. cascade:sourceType describes the
    #    TRANSPORT a reading arrived through, never its trustworthiness;
    #    trustworthiness is cascade:dataProvenance.
    "source_type": "cascade:sourceType",
    "data_types": "cascade:dataTypes",
    "version": "cascade:version",
    "label": "prov:label",

    # -- Clinical v1.10-1.12 -- traversable graph edges --
    "has_encounter": "clinical:hasEncounter",
    "indication_reference": "clinical:indicationReference",
    # v1.12: a subproperty of indicationReference. The predicate is the
    # machine-readable basis: indicationReference restates a reference the
    # SOURCE carried; parsedIndicationReference records a match an importer
    # computed from a coded or free-text reason. Consumers must present them
    # differently.
    "parsed_indication_reference": "clinical:parsedIndicationReference",
    "linked_condition": "clinical:linkedCondition",
    # DEPRECATED in clinical v1.10 (owl:deprecated true). Space-separated UUIDs
    # in a single literal, which no graph query can traverse. Registered for
    # READ support only, so existing data carrying it is not silently dropped;
    # writers should use linked_condition.
    "linked_condition_ids": "clinical:linkedConditionIds",
}

# Also provide camelCase -> predicate mapping for JSON input compatibility
# (conformance fixtures use camelCase keys from the TypeScript SDK)
PROPERTY_PREDICATES_CAMEL: dict[str, str] = {
    "medicationName": "clinical:drugName",
    "dose": "clinical:dosage",
    "frequency": "health:frequency",
    "route": "health:route",
    "prescriber": "health:prescriber",
    "startDate": "health:startDate",
    "endDate": "health:endDate",
    "isActive": "clinical:status",
    "rxNormCode": "clinical:rxNormCode",
    "medicationClass": "health:medicationClass",
    "affectsVitalSigns": "health:affectsVitalSigns",
    "conditionName": "health:conditionName",
    "status": "health:status",
    "onsetDate": "health:onsetDate",
    "icd10Code": "health:icd10Code",
    "snomedCode": "health:snomedCode",
    "conditionClass": "health:conditionClass",
    "monitoredVitalSigns": "health:monitoredVitalSigns",
    "allergen": "health:allergen",
    "allergyCategory": "health:allergyCategory",
    "reaction": "health:reaction",
    "allergySeverity": "health:allergySeverity",
    "testName": "health:testName",
    "resultValue": "health:resultValue",
    "resultUnit": "health:resultUnit",
    "referenceRange": "health:referenceRange",
    "interpretation": "health:interpretation",
    "performedDate": "health:performedDate",
    "testCode": "health:testCode",
    "labCategory": "health:labCategory",
    "specimenType": "health:specimenType",
    "reportedDate": "health:reportedDate",
    "orderingProvider": "health:orderingProvider",
    "performingLab": "health:performingLab",
    "vaccineName": "health:vaccineName",
    "administrationDate": "health:administrationDate",
    "vaccineCode": "health:vaccineCode",
    "manufacturer": "health:manufacturer",
    "lotNumber": "health:lotNumber",
    "doseQuantity": "health:doseQuantity",
    "site": "health:site",
    "administeringProvider": "health:administeringProvider",
    "administeringLocation": "health:administeringLocation",
    "vitalType": "clinical:vitalType",
    "vitalTypeName": "clinical:vitalTypeName",
    "value": "clinical:value",
    "unit": "clinical:unit",
    "effectiveDate": "clinical:effectiveDate",
    "loincCode": "clinical:loincCode",
    "referenceRangeLow": "clinical:referenceRangeLow",
    "referenceRangeHigh": "clinical:referenceRangeHigh",
    "provenanceClass": "clinical:provenanceClass",
    "sourceFhirResourceType": "clinical:sourceFhirResourceType",
    "clinicalIntent": "clinical:clinicalIntent",
    "indication": "clinical:indication",
    "courseOfTherapyType": "clinical:courseOfTherapyType",
    "asNeeded": "clinical:asNeeded",
    "medicationForm": "clinical:medicationForm",
    "activeIngredient": "clinical:activeIngredient",
    "ingredientStrength": "clinical:ingredientStrength",
    "refillsAllowed": "clinical:refillsAllowed",
    "supplyDurationDays": "clinical:supplyDurationDays",
    "prescriptionCategory": "clinical:prescriptionCategory",
    "drugCodes": "clinical:drugCode",
    "providerName": "clinical:providerName",
    "memberId": "clinical:memberId",
    "groupNumber": "clinical:groupNumber",
    "planName": "clinical:planName",
    "planType": "clinical:planType",
    "coverageType": "clinical:coverageType",
    "relationship": "clinical:relationship",
    "effectivePeriodStart": "clinical:effectivePeriodStart",
    "effectivePeriodEnd": "clinical:effectivePeriodEnd",
    "payorName": "clinical:payorName",
    "subscriberId": "clinical:subscriberId",
    "subscriberRelationship": "coverage:subscriberRelationship",
    "subscriberName": "coverage:subscriberName",
    "effectiveStart": "coverage:effectiveStart",
    "effectiveEnd": "coverage:effectiveEnd",
    "rxBin": "coverage:rxBin",
    "rxPcn": "coverage:rxPcn",
    "rxGroup": "coverage:rxGroup",
    "dateOfBirth": "cascade:dateOfBirth",
    "biologicalSex": "cascade:biologicalSex",
    "contactPhone": "vcard:hasTelephone",
    "contactEmail": "vcard:hasEmail",
    "computedAge": "cascade:computedAge",
    "ageGroup": "cascade:ageGroup",
    "genderIdentity": "cascade:genderIdentity",
    "profileId": "cascade:profileId",
    "name": "foaf:name",
    "givenName": "foaf:givenName",
    "familyName": "foaf:familyName",
    "bloodType": "health:bloodType",
    "procedureName": "clinical:procedureName",
    "healthProcedureName": "health:procedureName",
    "performer": "health:performer",
    "location": "health:location",
    "onsetAge": "health:onsetAge",
    "notes": "health:notes",
    "sourceRecordId": "health:sourceRecordId",
    "sourceIdentity": "cascade:sourceIdentity",
    "sourceSystem": "cascade:sourceSystem",
    "dataAbsentReason": "cascade:dataAbsentReason",
    "interpretationSourceCode": "health:interpretationSourceCode",
    "date": "health:date",
    "steps": "health:steps",
    "distance": "health:distance",
    "activeMinutes": "health:activeMinutes",
    "calories": "health:calories",
    "totalSleepMinutes": "health:totalSleepMinutes",
    "deepSleepMinutes": "health:deepSleepMinutes",
    "remSleepMinutes": "health:remSleepMinutes",
    "lightSleepMinutes": "health:lightSleepMinutes",
    "awakenings": "health:awakenings",
    "encounterType": "clinical:encounterType",
    "encounterClass": "clinical:encounterClass",
    "encounterStatus": "clinical:encounterStatus",
    "encounterStart": "clinical:encounterStart",
    "encounterEnd": "clinical:encounterEnd",
    "facilityName": "clinical:facilityName",
    "administeredDate": "clinical:administeredDate",
    "administeredDose": "clinical:administeredDose",
    "administeredRoute": "clinical:administeredRoute",
    "administrationStatus": "clinical:administrationStatus",
    "deviceType": "clinical:deviceType",
    "implantDate": "clinical:implantDate",
    "deviceManufacturer": "clinical:deviceManufacturer",
    "udiCarrier": "clinical:udiCarrier",
    "deviceStatus": "clinical:deviceStatus",
    "imagingModality": "clinical:imagingModality",
    "studyDescription": "clinical:studyDescription",
    "numberOfSeries": "clinical:numberOfSeries",
    "studyDate": "clinical:studyDate",
    "dicomStudyUid": "clinical:dicomStudyUid",
    "retrieveUrl": "clinical:retrieveUrl",
    "claimDate": "coverage:claimDate",
    "claimTotal": "coverage:claimTotal",
    "claimStatus": "coverage:claimStatus",
    "claimType": "coverage:claimType",
    "billingProvider": "coverage:billingProvider",
    "adjudicationDate": "coverage:adjudicationDate",
    "adjudicationStatus": "coverage:adjudicationStatus",
    "outcomeCode": "coverage:outcomeCode",
    "denialReason": "coverage:denialReason",
    "totalBilled": "coverage:totalBilled",
    "totalAllowed": "coverage:totalAllowed",
    "totalPaid": "coverage:totalPaid",
    "patientResponsibility": "coverage:patientResponsibility",
    "relatedClaim": "coverage:relatedClaim",
    "deniedProcedureCode": "coverage:deniedProcedureCode",
    "denialReasonCode": "coverage:denialReasonCode",
    "denialLetterDate": "coverage:denialLetterDate",
    "appealDeadline": "coverage:appealDeadline",
    "coveragePolicyReference": "coverage:coveragePolicyReference",
    "appealLevel": "coverage:appealLevel",
    "appealFiledDate": "coverage:appealFiledDate",
    "appealOutcome": "coverage:appealOutcome",
    "appealOutcomeDate": "coverage:appealOutcomeDate",
    "layerPromotionStatus": "cascade:layerPromotionStatus",
    "fhirJson": "cascade:fhirJson",
    "sourceRecordDate": "cascade:sourceRecordDate",
    "dataProvenance": "cascade:dataProvenance",
    "schemaVersion": "cascade:schemaVersion",
    # -- Clinical v1.8 -- SocialHistoryRecord predicates --
    "socialHistoryCategory": "clinical:socialHistoryCategory",
    "packsPerYear": "clinical:packsPerYear",
    "substanceType": "clinical:substanceType",
    "frequencyDescription": "clinical:frequencyDescription",
    "socialHistoryConsent": "clinical:socialHistoryConsent",
    # -- Core v3.0 -- AIExtractionActivity predicates --
    "extractionConfidence": "cascade:extractionConfidence",
    "extractionModel": "cascade:extractionModel",
    "sourceNarrativeSection": "cascade:sourceNarrativeSection",
    "requiresUserReview": "cascade:requiresUserReview",
    # -- Core v3.0 -- AIDiscardedExtraction predicates --
    "discardReason": "cascade:discardReason",
    # -- Core v3.0 -- SocialHistoryConsent predicates --
    "consentScope": "cascade:consentScope",
    "consentGrantedAt": "cascade:consentGrantedAt",
    "consentRevokedAt": "cascade:consentRevokedAt",
    # -- Health v2.4 -- SocialHistoryRecord predicates (consumer-reported) --
    "smokingStatus": "health:smokingStatus",
    "alcoholUse": "health:alcoholUse",
    "exerciseFrequency": "health:exerciseFrequency",
    "occupationalExposure": "health:occupationalExposure",
    # -- Core v3.1-3.3 -- AIGenerationActivity predicates --
    "promptVersion": "cascade:promptVersion",
    "generationTemperature": "cascade:generationTemperature",
    "trigger": "cascade:trigger",
    # -- Core v3.1-3.3 -- AdvisoryApplicationActivity predicates --
    "appliedTriplesCount": "cascade:appliedTriplesCount",
    # -- Core v3.1-3.3 -- ProxyAgent predicates --
    "actsForPatient": "cascade:actsForPatient",
    "proxyWebID": "cascade:proxyWebID",
    "proxyRelationship": "cascade:proxyRelationship",
    "proxyScope": "cascade:proxyScope",
    "proxyGrantedAt": "cascade:proxyGrantedAt",
    "proxyRevokedAt": "cascade:proxyRevokedAt",
    # -- evidence v1-draft.0.2 (DRAFT) -- verdict-taxonomy-v2 facet predicates --
    "direction": "evidence:direction",
    "basis": "evidence:basis",
    "strength": "evidence:strength",
    "settled": "evidence:settled",
    "reason": "evidence:reason",
    "confidence": "evidence:confidence",
    # -- workbench v1-draft.0.4 (DRAFT) -- user filing label. followUp is an
    #    oa:Motivation individual, not a predicate (see the snake_case block). --
    "userSourceLabel": "workbench:userSourceLabel",
    # -- Health v2.5 -- daily snapshot predicates (single-day forms) --
    "activeEnergyKcal": "health:activeEnergyKcal",
    "exerciseMinutes": "health:exerciseMinutes",
    "standHours": "health:standHours",
    "durationHours": "health:durationHours",
    "sleepQuality": "health:sleepQuality",
    # -- Core v3.4 -- reading-level terms --
    "sampleCount": "cascade:sampleCount",
    # -- Core v3.4 -- pod export manifest --
    "title": "dcterms:title",
    "description": "dcterms:description",
    "created": "dcterms:created",
    "creator": "dcterms:creator",
    "patientProfileVersion": "cascade:patientProfileVersion",
    "provenanceLayers": "cascade:provenanceLayers",
    "clinicalSummary": "cascade:clinicalSummary",
    "wellnessSummary": "cascade:wellnessSummary",
    "deviceSources": "cascade:deviceSources",
    "interactionScenarios": "cascade:interactionScenarios",
    # -- Core v3.4 -- record summary --
    "domain": "cascade:domain",
    "conditionCount": "cascade:conditionCount",
    "medicationCount": "cascade:medicationCount",
    "allergyCount": "cascade:allergyCount",
    "labResultCount": "cascade:labResultCount",
    "immunizationCount": "cascade:immunizationCount",
    "coverageCount": "cascade:coverageCount",
    "supplementCount": "cascade:supplementCount",
    "vitalSignDays": "cascade:vitalSignDays",
    "heartRateDays": "cascade:heartRateDays",
    "bloodPressureDays": "cascade:bloodPressureDays",
    "activityDays": "cascade:activityDays",
    "sleepDays": "cascade:sleepDays",
    # -- Core v3.4 -- interaction scenario --
    "involvedResources": "cascade:involvedResources",
    "severity": "cascade:severity",
    "requiresCrossProvenance": "cascade:requiresCrossProvenance",
    # -- Core v3.4 -- device sources --
    "sourceType": "cascade:sourceType",
    "dataTypes": "cascade:dataTypes",
    "version": "cascade:version",
    "label": "prov:label",
    # -- Clinical v1.10-1.12 -- traversable graph edges --
    "hasEncounter": "clinical:hasEncounter",
    "indicationReference": "clinical:indicationReference",
    "parsedIndicationReference": "clinical:parsedIndicationReference",
    "linkedCondition": "clinical:linkedCondition",
    # DEPRECATED (clinical v1.10). Read support only.
    "linkedConditionIds": "clinical:linkedConditionIds",
}


def build_reverse_predicate_map(
    additional_mappings: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    Build a reverse mapping from full predicate URI to Python property name.

    Expands each PROPERTY_PREDICATES shorthand (e.g. 'clinical:drugName')
    to a full URI and maps it back to the snake_case property key.

    Args:
        additional_mappings: Optional extra full-URI-to-property-name entries
            (e.g. type-specific overrides for VitalSign clinical predicates).

    Returns:
        Dict mapping full predicate URI strings to Python property names.
    """
    reverse_map: dict[str, str] = {}
    for py_key, pred_shorthand in PROPERTY_PREDICATES.items():
        colon_idx = pred_shorthand.find(":")
        if colon_idx >= 0:
            ns_prefix = pred_shorthand[:colon_idx]
            local_name = pred_shorthand[colon_idx + 1:]
            ns_uri = NAMESPACES.get(ns_prefix)
            if ns_uri:
                reverse_map[f"{ns_uri}{local_name}"] = py_key
    if additional_mappings:
        reverse_map.update(additional_mappings)
    return reverse_map


def build_reverse_predicate_map_camel(
    additional_mappings: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    Build a reverse mapping from full predicate URI to camelCase JSON property name.

    Used when parsing Turtle back to camelCase dict (for conformance fixture comparison).
    """
    reverse_map: dict[str, str] = {}
    for camel_key, pred_shorthand in PROPERTY_PREDICATES_CAMEL.items():
        colon_idx = pred_shorthand.find(":")
        if colon_idx >= 0:
            ns_prefix = pred_shorthand[:colon_idx]
            local_name = pred_shorthand[colon_idx + 1:]
            ns_uri = NAMESPACES.get(ns_prefix)
            if ns_uri:
                # Only set if not already set (first mapping wins)
                full_uri = f"{ns_uri}{local_name}"
                if full_uri not in reverse_map:
                    reverse_map[full_uri] = camel_key
    if additional_mappings:
        reverse_map.update(additional_mappings)
    return reverse_map
