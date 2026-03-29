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
    # Linked Data Platform namespace
    "ldp": "http://www.w3.org/ns/ldp#",
    # Dublin Core Terms namespace
    "dcterms": "http://purl.org/dc/terms/",
    # RDF namespace (used internally, not typically declared in output)
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    # RDFS namespace
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    # OWL namespace
    "owl": "http://www.w3.org/2002/07/owl#",
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
        "rdf_type": "health:MedicationRecord",
        "name_key": "medication_name",
        "name_pred": "health:medicationName",
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
    "procedures": {
        "rdf_type": "health:ProcedureRecord",
        "name_key": "procedure_name",
        "name_pred": "health:procedureName",
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
        "name_pred": "health:medicationName",
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
}

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
    "ProcedureRecord": "procedures",
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
    # -- Medication predicates (health: vocabulary) --
    "medication_name": "health:medicationName",
    "dose": "health:dose",
    "frequency": "health:frequency",
    "route": "health:route",
    "prescriber": "health:prescriber",
    "start_date": "health:startDate",
    "end_date": "health:endDate",
    "is_active": "health:isActive",
    "rx_norm_code": "health:rxNormCode",
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

    # -- Patient profile predicates (cascade: and foaf: vocabularies) --
    "date_of_birth": "cascade:dateOfBirth",
    "biological_sex": "cascade:biologicalSex",
    "computed_age": "cascade:computedAge",
    "age_group": "cascade:ageGroup",
    "gender_identity": "cascade:genderIdentity",
    "profile_id": "cascade:profileId",
    "name": "foaf:name",
    "given_name": "foaf:givenName",
    "family_name": "foaf:familyName",
    "blood_type": "health:bloodType",

    # -- Procedure predicates --
    "procedure_name": "health:procedureName",
    "performer": "health:performer",
    "location": "health:location",

    # -- Family history predicates --
    # Note: `relationship` is shared with Coverage (clinical:relationship)
    "onset_age": "health:onsetAge",

    # -- Shared predicates --
    "notes": "health:notes",
    "source_record_id": "health:sourceRecordId",

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
}

# Also provide camelCase -> predicate mapping for JSON input compatibility
# (conformance fixtures use camelCase keys from the TypeScript SDK)
PROPERTY_PREDICATES_CAMEL: dict[str, str] = {
    "medicationName": "health:medicationName",
    "dose": "health:dose",
    "frequency": "health:frequency",
    "route": "health:route",
    "prescriber": "health:prescriber",
    "startDate": "health:startDate",
    "endDate": "health:endDate",
    "isActive": "health:isActive",
    "rxNormCode": "health:rxNormCode",
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
    "computedAge": "cascade:computedAge",
    "ageGroup": "cascade:ageGroup",
    "genderIdentity": "cascade:genderIdentity",
    "profileId": "cascade:profileId",
    "name": "foaf:name",
    "givenName": "foaf:givenName",
    "familyName": "foaf:familyName",
    "bloodType": "health:bloodType",
    "procedureName": "health:procedureName",
    "performer": "health:performer",
    "location": "health:location",
    "onsetAge": "health:onsetAge",
    "notes": "health:notes",
    "sourceRecordId": "health:sourceRecordId",
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
}


def build_reverse_predicate_map(
    additional_mappings: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    Build a reverse mapping from full predicate URI to Python property name.

    Expands each PROPERTY_PREDICATES shorthand (e.g. 'health:medicationName')
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
