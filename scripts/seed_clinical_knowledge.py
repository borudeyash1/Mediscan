"""
MediScan Enterprise — Clinical Knowledge Base Seed Script
===========================================================
Populates Neo4j with 30+ major diseases, 100+ symptoms, 60+ medications,
realistic DDIs, eGFR contraindications, and seeds Qdrant with clinical
guideline chunks from AHA, NICE, ICMR, ADA.

Usage:
    pip install neo4j qdrant-client
    python scripts/seed_clinical_knowledge.py

Environment Variables:
    NEO4J_URI           (default: bolt://localhost:7687)
    NEO4J_USER          (default: neo4j)
    NEO4J_PASSWORD      (default: mediscan_dev_2026)
    QDRANT_HOST         (default: localhost)
    QDRANT_PORT         (default: 6333)
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import uuid
import json
import hashlib
import random
from datetime import datetime

from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    CollectionStatus,
)


# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "mediscan_dev_2026")

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

QDRANT_COLLECTION = "clinical_evidence_rag"
DENSE_VECTOR_SIZE = 768  # BioLORD-2023-M / MedCPT dimension


# ═══════════════════════════════════════════════════════════════
# DISEASES — 35 major diseases with ICD-11 and SNOMED codes
# ═══════════════════════════════════════════════════════════════

DISEASES = [
    {"name": "Acute ST-Elevation Myocardial Infarction", "icd11": "BA41.0", "snomed_id": "54329005", "category": "Cardiology"},
    {"name": "Unstable Angina", "icd11": "BA80", "snomed_id": "25106000", "category": "Cardiology"},
    {"name": "Heart Failure", "icd11": "BD10", "snomed_id": "84114007", "category": "Cardiology"},
    {"name": "Atrial Fibrillation", "icd11": "BC81", "snomed_id": "49436004", "category": "Cardiology"},
    {"name": "Hypertensive Crisis", "icd11": "BA03", "snomed_id": "706882009", "category": "Cardiology"},
    {"name": "Acute Aortic Dissection", "icd11": "BD50", "snomed_id": "308546005", "category": "Cardiology"},
    {"name": "Pulmonary Embolism", "icd11": "BB01", "snomed_id": "59282003", "category": "Pulmonology"},
    {"name": "Community-Acquired Pneumonia", "icd11": "CA40.0", "snomed_id": "385093006", "category": "Pulmonology"},
    {"name": "Acute Asthma Exacerbation", "icd11": "CA23", "snomed_id": "304527002", "category": "Pulmonology"},
    {"name": "COPD Exacerbation", "icd11": "CA22", "snomed_id": "195951007", "category": "Pulmonology"},
    {"name": "Type 2 Diabetes Mellitus", "icd11": "5A11", "snomed_id": "44054006", "category": "Endocrinology"},
    {"name": "Diabetic Ketoacidosis", "icd11": "5A20", "snomed_id": "420422005", "category": "Endocrinology"},
    {"name": "Hyperthyroidism (Graves Disease)", "icd11": "5A00", "snomed_id": "34486009", "category": "Endocrinology"},
    {"name": "Hypothyroidism", "icd11": "5A01", "snomed_id": "40930008", "category": "Endocrinology"},
    {"name": "Acute Kidney Injury", "icd11": "GB60", "snomed_id": "14669001", "category": "Nephrology"},
    {"name": "Chronic Kidney Disease Stage 4", "icd11": "GB61.4", "snomed_id": "431857002", "category": "Nephrology"},
    {"name": "Ischemic Stroke", "icd11": "8B11", "snomed_id": "422504002", "category": "Neurology"},
    {"name": "Migraine with Aura", "icd11": "8A80.1", "snomed_id": "4473006", "category": "Neurology"},
    {"name": "Epilepsy (Generalized)", "icd11": "8A60", "snomed_id": "84757009", "category": "Neurology"},
    {"name": "Parkinson Disease", "icd11": "8A00.0", "snomed_id": "49049000", "category": "Neurology"},
    {"name": "Major Depressive Disorder", "icd11": "6A70", "snomed_id": "370143000", "category": "Psychiatry"},
    {"name": "Generalized Anxiety Disorder", "icd11": "6B00", "snomed_id": "21897009", "category": "Psychiatry"},
    {"name": "Rheumatoid Arthritis", "icd11": "FA20", "snomed_id": "69896004", "category": "Rheumatology"},
    {"name": "Systemic Lupus Erythematosus", "icd11": "4A40", "snomed_id": "55464009", "category": "Rheumatology"},
    {"name": "Sepsis", "icd11": "1G40", "snomed_id": "91302008", "category": "Infectious Disease"},
    {"name": "Dengue Fever", "icd11": "1D20", "snomed_id": "38362002", "category": "Infectious Disease"},
    {"name": "Malaria (Plasmodium falciparum)", "icd11": "1F40", "snomed_id": "61462000", "category": "Infectious Disease"},
    {"name": "COVID-19 Pneumonia", "icd11": "RA01.0", "snomed_id": "840539006", "category": "Infectious Disease"},
    {"name": "Tuberculosis (Pulmonary)", "icd11": "1B10", "snomed_id": "154283005", "category": "Infectious Disease"},
    {"name": "Iron Deficiency Anemia", "icd11": "3A00", "snomed_id": "87522002", "category": "Hematology"},
    {"name": "Deep Vein Thrombosis", "icd11": "BD72", "snomed_id": "128053003", "category": "Hematology"},
    {"name": "Hepatitis B (Chronic)", "icd11": "1E50.1", "snomed_id": "61977001", "category": "Hepatology"},
    {"name": "Non-Alcoholic Fatty Liver Disease", "icd11": "DB92", "snomed_id": "197321007", "category": "Hepatology"},
    {"name": "Acute Pancreatitis", "icd11": "DC31", "snomed_id": "197456007", "category": "Gastroenterology"},
    {"name": "Diabetic Retinopathy", "icd11": "9B71.0", "snomed_id": "4855003", "category": "Ophthalmology"},
]


# ═══════════════════════════════════════════════════════════════
# SYMPTOMS — 110 symptoms with SNOMED codes and clinical weights
# ═══════════════════════════════════════════════════════════════

SYMPTOMS = [
    # Cardiac symptoms
    {"name": "Substernal chest pain", "snomed_id": "29857009", "category": "Cardiac"},
    {"name": "Chest pain radiating to left arm", "snomed_id": "426976000", "category": "Cardiac"},
    {"name": "Chest pain radiating to jaw", "snomed_id": "102588006", "category": "Cardiac"},
    {"name": "Palpitations", "snomed_id": "80313002", "category": "Cardiac"},
    {"name": "Orthopnea", "snomed_id": "62744007", "category": "Cardiac"},
    {"name": "Paroxysmal nocturnal dyspnea", "snomed_id": "55442000", "category": "Cardiac"},
    {"name": "Peripheral edema", "snomed_id": "271809000", "category": "Cardiac"},
    {"name": "Jugular venous distension", "snomed_id": "271653008", "category": "Cardiac"},
    {"name": "Syncope", "snomed_id": "271594007", "category": "Cardiac"},
    {"name": "Diaphoresis", "snomed_id": "52613005", "category": "General"},
    # Respiratory symptoms
    {"name": "Dyspnea", "snomed_id": "267036007", "category": "Respiratory"},
    {"name": "Productive cough", "snomed_id": "28743005", "category": "Respiratory"},
    {"name": "Dry cough", "snomed_id": "11833005", "category": "Respiratory"},
    {"name": "Hemoptysis", "snomed_id": "66857006", "category": "Respiratory"},
    {"name": "Wheezing", "snomed_id": "56018004", "category": "Respiratory"},
    {"name": "Pleuritic chest pain", "snomed_id": "2237002", "category": "Respiratory"},
    {"name": "Stridor", "snomed_id": "70407001", "category": "Respiratory"},
    {"name": "Tachypnea", "snomed_id": "271823003", "category": "Respiratory"},
    {"name": "Cyanosis", "snomed_id": "119419001", "category": "Respiratory"},
    {"name": "Sputum production", "snomed_id": "45486003", "category": "Respiratory"},
    # Neurological symptoms
    {"name": "Headache", "snomed_id": "25064002", "category": "Neurological"},
    {"name": "Thunderclap headache", "snomed_id": "230472004", "category": "Neurological"},
    {"name": "Unilateral weakness", "snomed_id": "127378008", "category": "Neurological"},
    {"name": "Facial droop", "snomed_id": "95667008", "category": "Neurological"},
    {"name": "Aphasia", "snomed_id": "87486003", "category": "Neurological"},
    {"name": "Visual disturbance", "snomed_id": "63102001", "category": "Neurological"},
    {"name": "Seizure", "snomed_id": "91175000", "category": "Neurological"},
    {"name": "Altered mental status", "snomed_id": "419284004", "category": "Neurological"},
    {"name": "Tremor", "snomed_id": "26079004", "category": "Neurological"},
    {"name": "Vertigo", "snomed_id": "399153001", "category": "Neurological"},
    {"name": "Photophobia", "snomed_id": "409668002", "category": "Neurological"},
    {"name": "Neck stiffness", "snomed_id": "161882006", "category": "Neurological"},
    {"name": "Numbness", "snomed_id": "44077006", "category": "Neurological"},
    {"name": "Tingling (paresthesia)", "snomed_id": "29164008", "category": "Neurological"},
    {"name": "Memory loss", "snomed_id": "48167000", "category": "Neurological"},
    # Gastrointestinal symptoms
    {"name": "Nausea", "snomed_id": "422587007", "category": "Gastrointestinal"},
    {"name": "Vomiting", "snomed_id": "422400008", "category": "Gastrointestinal"},
    {"name": "Abdominal pain (epigastric)", "snomed_id": "79922009", "category": "Gastrointestinal"},
    {"name": "Diarrhea", "snomed_id": "62315008", "category": "Gastrointestinal"},
    {"name": "Constipation", "snomed_id": "14760008", "category": "Gastrointestinal"},
    {"name": "Hematemesis", "snomed_id": "8765009", "category": "Gastrointestinal"},
    {"name": "Melena", "snomed_id": "2901004", "category": "Gastrointestinal"},
    {"name": "Jaundice", "snomed_id": "18165001", "category": "Gastrointestinal"},
    {"name": "Dysphagia", "snomed_id": "40739000", "category": "Gastrointestinal"},
    {"name": "Abdominal distension", "snomed_id": "41931001", "category": "Gastrointestinal"},
    # Systemic / General symptoms
    {"name": "Fever", "snomed_id": "386661006", "category": "Systemic"},
    {"name": "Rigors / Chills", "snomed_id": "43724002", "category": "Systemic"},
    {"name": "Night sweats", "snomed_id": "42984000", "category": "Systemic"},
    {"name": "Fatigue", "snomed_id": "84229001", "category": "Systemic"},
    {"name": "Unintentional weight loss", "snomed_id": "89362005", "category": "Systemic"},
    {"name": "Weight gain (rapid)", "snomed_id": "8943002", "category": "Systemic"},
    {"name": "Malaise", "snomed_id": "367391008", "category": "Systemic"},
    {"name": "Anorexia (loss of appetite)", "snomed_id": "79890006", "category": "Systemic"},
    {"name": "Dehydration signs", "snomed_id": "34095006", "category": "Systemic"},
    {"name": "Lymphadenopathy", "snomed_id": "30746006", "category": "Systemic"},
    # Musculoskeletal symptoms
    {"name": "Joint pain (polyarticular)", "snomed_id": "57676002", "category": "Musculoskeletal"},
    {"name": "Morning stiffness > 1 hour", "snomed_id": "84387000", "category": "Musculoskeletal"},
    {"name": "Joint swelling", "snomed_id": "299332000", "category": "Musculoskeletal"},
    {"name": "Muscle pain (myalgia)", "snomed_id": "68962001", "category": "Musculoskeletal"},
    {"name": "Back pain", "snomed_id": "161891005", "category": "Musculoskeletal"},
    # Dermatological symptoms
    {"name": "Skin rash", "snomed_id": "271807003", "category": "Dermatological"},
    {"name": "Malar (butterfly) rash", "snomed_id": "271759003", "category": "Dermatological"},
    {"name": "Petechiae", "snomed_id": "271813007", "category": "Dermatological"},
    {"name": "Urticaria", "snomed_id": "126485001", "category": "Dermatological"},
    {"name": "Purpura", "snomed_id": "95564001", "category": "Dermatological"},
    # Renal / Urological symptoms
    {"name": "Oliguria", "snomed_id": "83128009", "category": "Renal"},
    {"name": "Hematuria", "snomed_id": "34436003", "category": "Renal"},
    {"name": "Dysuria", "snomed_id": "49650001", "category": "Renal"},
    {"name": "Polyuria", "snomed_id": "28442001", "category": "Renal"},
    {"name": "Polydipsia", "snomed_id": "17173007", "category": "Renal"},
    {"name": "Flank pain", "snomed_id": "247355005", "category": "Renal"},
    # Endocrine symptoms
    {"name": "Polyphagia", "snomed_id": "72405004", "category": "Endocrine"},
    {"name": "Heat intolerance", "snomed_id": "285555003", "category": "Endocrine"},
    {"name": "Cold intolerance", "snomed_id": "271899001", "category": "Endocrine"},
    {"name": "Goiter", "snomed_id": "3716002", "category": "Endocrine"},
    {"name": "Exophthalmos", "snomed_id": "18381001", "category": "Endocrine"},
    # Hematological symptoms
    {"name": "Easy bruising", "snomed_id": "302227002", "category": "Hematological"},
    {"name": "Prolonged bleeding", "snomed_id": "131148009", "category": "Hematological"},
    {"name": "Pallor", "snomed_id": "398979000", "category": "Hematological"},
    # Psychiatric symptoms
    {"name": "Depressed mood", "snomed_id": "366979004", "category": "Psychiatric"},
    {"name": "Anhedonia", "snomed_id": "247803002", "category": "Psychiatric"},
    {"name": "Insomnia", "snomed_id": "193462001", "category": "Psychiatric"},
    {"name": "Excessive worry", "snomed_id": "48694002", "category": "Psychiatric"},
    {"name": "Panic attacks", "snomed_id": "371631005", "category": "Psychiatric"},
    {"name": "Suicidal ideation", "snomed_id": "6471006", "category": "Psychiatric"},
    # Ophthalmological symptoms
    {"name": "Blurred vision", "snomed_id": "246636008", "category": "Ophthalmological"},
    {"name": "Visual field defect", "snomed_id": "12184005", "category": "Ophthalmological"},
    {"name": "Eye pain", "snomed_id": "41652007", "category": "Ophthalmological"},
    {"name": "Floaters", "snomed_id": "246634006", "category": "Ophthalmological"},
    # ENT symptoms
    {"name": "Sore throat", "snomed_id": "162397003", "category": "ENT"},
    {"name": "Rhinorrhea", "snomed_id": "64531003", "category": "ENT"},
    {"name": "Ear pain (otalgia)", "snomed_id": "16001004", "category": "ENT"},
    {"name": "Hearing loss", "snomed_id": "15188001", "category": "ENT"},
    # Specific signs
    {"name": "Hepatomegaly", "snomed_id": "80515008", "category": "Abdominal"},
    {"name": "Splenomegaly", "snomed_id": "16294009", "category": "Abdominal"},
    {"name": "Ascites", "snomed_id": "389026000", "category": "Abdominal"},
    {"name": "Clubbing (digital)", "snomed_id": "5765002", "category": "Systemic"},
    {"name": "Tachycardia", "snomed_id": "3424008", "category": "Cardiac"},
    {"name": "Bradycardia", "snomed_id": "48867003", "category": "Cardiac"},
    {"name": "Hypotension", "snomed_id": "45007003", "category": "Cardiac"},
    {"name": "Hypertension", "snomed_id": "38341003", "category": "Cardiac"},
    # Tropical/infectious symptoms
    {"name": "Retro-orbital pain", "snomed_id": "246677002", "category": "Infectious"},
    {"name": "Bone pain", "snomed_id": "12584003", "category": "Musculoskeletal"},
    {"name": "Tourniquet test positive", "snomed_id": "165564001", "category": "Hematological"},
    {"name": "Splenomegaly with fever", "snomed_id": "271794006", "category": "Infectious"},
    {"name": "Hemolytic anemia signs", "snomed_id": "61261009", "category": "Hematological"},
    {"name": "Kussmaul breathing", "snomed_id": "8821003", "category": "Endocrine"},
    {"name": "Fruity breath odor", "snomed_id": "111942003", "category": "Endocrine"},
    {"name": "Calf tenderness / swelling", "snomed_id": "449917004", "category": "Vascular"},
    {"name": "Homans sign", "snomed_id": "271587009", "category": "Vascular"},
]


# ═══════════════════════════════════════════════════════════════
# DISEASE → SYMPTOM RELATIONSHIPS (with sensitivity/specificity)
# ═══════════════════════════════════════════════════════════════

DISEASE_SYMPTOM_EDGES = [
    # STEMI
    ("Acute ST-Elevation Myocardial Infarction", "Substernal chest pain", 0.85, 0.45, 1.55),
    ("Acute ST-Elevation Myocardial Infarction", "Chest pain radiating to left arm", 0.65, 0.82, 3.61),
    ("Acute ST-Elevation Myocardial Infarction", "Diaphoresis", 0.70, 0.65, 2.00),
    ("Acute ST-Elevation Myocardial Infarction", "Nausea", 0.45, 0.60, 1.13),
    ("Acute ST-Elevation Myocardial Infarction", "Dyspnea", 0.55, 0.50, 1.10),
    # Heart Failure
    ("Heart Failure", "Dyspnea", 0.90, 0.30, 1.29),
    ("Heart Failure", "Orthopnea", 0.50, 0.90, 5.00),
    ("Heart Failure", "Paroxysmal nocturnal dyspnea", 0.40, 0.95, 8.00),
    ("Heart Failure", "Peripheral edema", 0.65, 0.55, 1.44),
    ("Heart Failure", "Jugular venous distension", 0.40, 0.92, 5.00),
    ("Heart Failure", "Fatigue", 0.80, 0.20, 1.00),
    ("Heart Failure", "Weight gain (rapid)", 0.35, 0.90, 3.50),
    # Atrial Fibrillation
    ("Atrial Fibrillation", "Palpitations", 0.75, 0.55, 1.67),
    ("Atrial Fibrillation", "Dyspnea", 0.50, 0.50, 1.00),
    ("Atrial Fibrillation", "Syncope", 0.15, 0.92, 1.88),
    ("Atrial Fibrillation", "Fatigue", 0.60, 0.20, 0.75),
    # Pulmonary Embolism
    ("Pulmonary Embolism", "Dyspnea", 0.80, 0.30, 1.14),
    ("Pulmonary Embolism", "Pleuritic chest pain", 0.55, 0.75, 2.20),
    ("Pulmonary Embolism", "Tachycardia", 0.45, 0.60, 1.13),
    ("Pulmonary Embolism", "Hemoptysis", 0.15, 0.95, 3.00),
    ("Pulmonary Embolism", "Calf tenderness / swelling", 0.30, 0.85, 2.00),
    # Pneumonia
    ("Community-Acquired Pneumonia", "Fever", 0.80, 0.40, 1.33),
    ("Community-Acquired Pneumonia", "Productive cough", 0.75, 0.50, 1.50),
    ("Community-Acquired Pneumonia", "Dyspnea", 0.60, 0.50, 1.20),
    ("Community-Acquired Pneumonia", "Rigors / Chills", 0.40, 0.75, 1.60),
    ("Community-Acquired Pneumonia", "Pleuritic chest pain", 0.30, 0.75, 1.20),
    # Asthma
    ("Acute Asthma Exacerbation", "Wheezing", 0.85, 0.65, 2.43),
    ("Acute Asthma Exacerbation", "Dyspnea", 0.90, 0.30, 1.29),
    ("Acute Asthma Exacerbation", "Dry cough", 0.70, 0.50, 1.40),
    ("Acute Asthma Exacerbation", "Tachypnea", 0.60, 0.60, 1.50),
    # Type 2 Diabetes
    ("Type 2 Diabetes Mellitus", "Polyuria", 0.65, 0.70, 2.17),
    ("Type 2 Diabetes Mellitus", "Polydipsia", 0.60, 0.75, 2.40),
    ("Type 2 Diabetes Mellitus", "Polyphagia", 0.40, 0.80, 2.00),
    ("Type 2 Diabetes Mellitus", "Fatigue", 0.70, 0.20, 0.88),
    ("Type 2 Diabetes Mellitus", "Blurred vision", 0.30, 0.80, 1.50),
    # DKA
    ("Diabetic Ketoacidosis", "Kussmaul breathing", 0.50, 0.97, 16.67),
    ("Diabetic Ketoacidosis", "Fruity breath odor", 0.40, 0.98, 20.00),
    ("Diabetic Ketoacidosis", "Nausea", 0.70, 0.40, 1.17),
    ("Diabetic Ketoacidosis", "Vomiting", 0.60, 0.50, 1.20),
    ("Diabetic Ketoacidosis", "Abdominal pain (epigastric)", 0.50, 0.55, 1.11),
    ("Diabetic Ketoacidosis", "Dehydration signs", 0.85, 0.45, 1.55),
    # Stroke
    ("Ischemic Stroke", "Unilateral weakness", 0.80, 0.80, 4.00),
    ("Ischemic Stroke", "Facial droop", 0.65, 0.90, 6.50),
    ("Ischemic Stroke", "Aphasia", 0.40, 0.95, 8.00),
    ("Ischemic Stroke", "Visual disturbance", 0.25, 0.85, 1.67),
    ("Ischemic Stroke", "Headache", 0.30, 0.50, 0.60),
    # Migraine
    ("Migraine with Aura", "Headache", 0.95, 0.30, 1.36),
    ("Migraine with Aura", "Visual disturbance", 0.70, 0.80, 3.50),
    ("Migraine with Aura", "Photophobia", 0.80, 0.70, 2.67),
    ("Migraine with Aura", "Nausea", 0.75, 0.40, 1.25),
    # Epilepsy
    ("Epilepsy (Generalized)", "Seizure", 0.95, 0.85, 6.33),
    ("Epilepsy (Generalized)", "Altered mental status", 0.50, 0.60, 1.25),
    # Sepsis
    ("Sepsis", "Fever", 0.85, 0.40, 1.42),
    ("Sepsis", "Tachycardia", 0.80, 0.50, 1.60),
    ("Sepsis", "Tachypnea", 0.70, 0.55, 1.56),
    ("Sepsis", "Hypotension", 0.50, 0.85, 3.33),
    ("Sepsis", "Altered mental status", 0.35, 0.80, 1.75),
    ("Sepsis", "Rigors / Chills", 0.60, 0.65, 1.71),
    # Dengue
    ("Dengue Fever", "Fever", 0.95, 0.30, 1.36),
    ("Dengue Fever", "Retro-orbital pain", 0.60, 0.90, 6.00),
    ("Dengue Fever", "Bone pain", 0.70, 0.70, 2.33),
    ("Dengue Fever", "Skin rash", 0.50, 0.65, 1.43),
    ("Dengue Fever", "Tourniquet test positive", 0.45, 0.92, 5.63),
    ("Dengue Fever", "Muscle pain (myalgia)", 0.80, 0.40, 1.33),
    # Malaria
    ("Malaria (Plasmodium falciparum)", "Fever", 0.90, 0.30, 1.29),
    ("Malaria (Plasmodium falciparum)", "Rigors / Chills", 0.75, 0.65, 2.14),
    ("Malaria (Plasmodium falciparum)", "Headache", 0.70, 0.35, 1.08),
    ("Malaria (Plasmodium falciparum)", "Splenomegaly with fever", 0.40, 0.88, 3.33),
    ("Malaria (Plasmodium falciparum)", "Hemolytic anemia signs", 0.35, 0.90, 3.50),
    # AKI
    ("Acute Kidney Injury", "Oliguria", 0.60, 0.85, 4.00),
    ("Acute Kidney Injury", "Peripheral edema", 0.45, 0.55, 1.00),
    ("Acute Kidney Injury", "Nausea", 0.50, 0.40, 0.83),
    ("Acute Kidney Injury", "Fatigue", 0.65, 0.20, 0.81),
    # Rheumatoid Arthritis
    ("Rheumatoid Arthritis", "Joint pain (polyarticular)", 0.85, 0.60, 2.13),
    ("Rheumatoid Arthritis", "Morning stiffness > 1 hour", 0.75, 0.85, 5.00),
    ("Rheumatoid Arthritis", "Joint swelling", 0.80, 0.65, 2.29),
    ("Rheumatoid Arthritis", "Fatigue", 0.70, 0.20, 0.88),
    # SLE
    ("Systemic Lupus Erythematosus", "Malar (butterfly) rash", 0.50, 0.96, 12.50),
    ("Systemic Lupus Erythematosus", "Joint pain (polyarticular)", 0.80, 0.50, 1.60),
    ("Systemic Lupus Erythematosus", "Fatigue", 0.90, 0.15, 1.06),
    ("Systemic Lupus Erythematosus", "Photophobia", 0.40, 0.70, 1.33),
    ("Systemic Lupus Erythematosus", "Fever", 0.60, 0.40, 1.00),
    # DVT
    ("Deep Vein Thrombosis", "Calf tenderness / swelling", 0.75, 0.70, 2.50),
    ("Deep Vein Thrombosis", "Peripheral edema", 0.65, 0.55, 1.44),
    ("Deep Vein Thrombosis", "Homans sign", 0.30, 0.85, 2.00),
    # Parkinson
    ("Parkinson Disease", "Tremor", 0.70, 0.75, 2.80),
    ("Parkinson Disease", "Muscle pain (myalgia)", 0.30, 0.60, 0.75),
    # Depression
    ("Major Depressive Disorder", "Depressed mood", 0.90, 0.65, 2.57),
    ("Major Depressive Disorder", "Anhedonia", 0.75, 0.80, 3.75),
    ("Major Depressive Disorder", "Insomnia", 0.70, 0.50, 1.40),
    ("Major Depressive Disorder", "Fatigue", 0.80, 0.20, 1.00),
    ("Major Depressive Disorder", "Unintentional weight loss", 0.30, 0.75, 1.20),
    # Anxiety
    ("Generalized Anxiety Disorder", "Excessive worry", 0.90, 0.70, 3.00),
    ("Generalized Anxiety Disorder", "Panic attacks", 0.40, 0.85, 2.67),
    ("Generalized Anxiety Disorder", "Insomnia", 0.65, 0.50, 1.30),
    ("Generalized Anxiety Disorder", "Palpitations", 0.45, 0.55, 1.00),
    # Hypothyroid
    ("Hypothyroidism", "Fatigue", 0.85, 0.20, 1.06),
    ("Hypothyroidism", "Cold intolerance", 0.60, 0.85, 4.00),
    ("Hypothyroidism", "Weight gain (rapid)", 0.55, 0.75, 2.20),
    ("Hypothyroidism", "Constipation", 0.40, 0.65, 1.14),
    # Hyperthyroid
    ("Hyperthyroidism (Graves Disease)", "Heat intolerance", 0.70, 0.85, 4.67),
    ("Hyperthyroidism (Graves Disease)", "Tremor", 0.55, 0.75, 2.20),
    ("Hyperthyroidism (Graves Disease)", "Palpitations", 0.75, 0.55, 1.67),
    ("Hyperthyroidism (Graves Disease)", "Exophthalmos", 0.40, 0.97, 13.33),
    ("Hyperthyroidism (Graves Disease)", "Goiter", 0.60, 0.90, 6.00),
    ("Hyperthyroidism (Graves Disease)", "Unintentional weight loss", 0.50, 0.75, 2.00),
]


# ═══════════════════════════════════════════════════════════════
# MEDICATIONS — 65 medications with RxNorm codes
# ═══════════════════════════════════════════════════════════════

MEDICATIONS = [
    # Cardiology
    {"name": "Aspirin", "rxnorm_cui": "1191", "atc_code": "B01AC06", "half_life_hrs": 4, "category": "Antiplatelet"},
    {"name": "Clopidogrel", "rxnorm_cui": "32968", "atc_code": "B01AC04", "half_life_hrs": 6, "category": "Antiplatelet"},
    {"name": "Ticagrelor", "rxnorm_cui": "1116632", "atc_code": "B01AC24", "half_life_hrs": 7, "category": "Antiplatelet"},
    {"name": "Heparin (Unfractionated)", "rxnorm_cui": "5224", "atc_code": "B01AB01", "half_life_hrs": 1.5, "category": "Anticoagulant"},
    {"name": "Enoxaparin", "rxnorm_cui": "67108", "atc_code": "B01AB05", "half_life_hrs": 4.5, "category": "Anticoagulant"},
    {"name": "Warfarin", "rxnorm_cui": "11289", "atc_code": "B01AA03", "half_life_hrs": 40, "category": "Anticoagulant"},
    {"name": "Rivaroxaban", "rxnorm_cui": "1114195", "atc_code": "B01AF01", "half_life_hrs": 9, "category": "Anticoagulant"},
    {"name": "Apixaban", "rxnorm_cui": "1364430", "atc_code": "B01AF02", "half_life_hrs": 12, "category": "Anticoagulant"},
    {"name": "Metoprolol", "rxnorm_cui": "6918", "atc_code": "C07AB02", "half_life_hrs": 5, "category": "Beta Blocker"},
    {"name": "Atenolol", "rxnorm_cui": "1202", "atc_code": "C07AB03", "half_life_hrs": 7, "category": "Beta Blocker"},
    {"name": "Carvedilol", "rxnorm_cui": "20352", "atc_code": "C07AG02", "half_life_hrs": 7, "category": "Beta Blocker"},
    {"name": "Lisinopril", "rxnorm_cui": "29046", "atc_code": "C09AA03", "half_life_hrs": 12, "category": "ACE Inhibitor"},
    {"name": "Enalapril", "rxnorm_cui": "3827", "atc_code": "C09AA02", "half_life_hrs": 11, "category": "ACE Inhibitor"},
    {"name": "Losartan", "rxnorm_cui": "52175", "atc_code": "C09CA01", "half_life_hrs": 6, "category": "ARB"},
    {"name": "Valsartan", "rxnorm_cui": "69749", "atc_code": "C09CA03", "half_life_hrs": 6, "category": "ARB"},
    {"name": "Amlodipine", "rxnorm_cui": "17767", "atc_code": "C08CA01", "half_life_hrs": 40, "category": "CCB"},
    {"name": "Atorvastatin", "rxnorm_cui": "83367", "atc_code": "C10AA05", "half_life_hrs": 14, "category": "Statin"},
    {"name": "Rosuvastatin", "rxnorm_cui": "301542", "atc_code": "C10AA07", "half_life_hrs": 19, "category": "Statin"},
    {"name": "Furosemide", "rxnorm_cui": "4603", "atc_code": "C03CA01", "half_life_hrs": 1.5, "category": "Loop Diuretic"},
    {"name": "Spironolactone", "rxnorm_cui": "9997", "atc_code": "C03DA01", "half_life_hrs": 1.4, "category": "MRA"},
    {"name": "Digoxin", "rxnorm_cui": "3407", "atc_code": "C01AA05", "half_life_hrs": 36, "category": "Cardiac Glycoside"},
    {"name": "Amiodarone", "rxnorm_cui": "703", "atc_code": "C01BD01", "half_life_hrs": 960, "category": "Antiarrhythmic"},
    {"name": "Nitroglycerin", "rxnorm_cui": "7417", "atc_code": "C01DA02", "half_life_hrs": 0.05, "category": "Nitrate"},
    # Endocrinology
    {"name": "Metformin", "rxnorm_cui": "6809", "atc_code": "A10BA02", "half_life_hrs": 6, "category": "Biguanide"},
    {"name": "Empagliflozin", "rxnorm_cui": "1545653", "atc_code": "A10BK03", "half_life_hrs": 12, "category": "SGLT2i"},
    {"name": "Dapagliflozin", "rxnorm_cui": "1488564", "atc_code": "A10BK01", "half_life_hrs": 12.9, "category": "SGLT2i"},
    {"name": "Sitagliptin", "rxnorm_cui": "593411", "atc_code": "A10BH01", "half_life_hrs": 12, "category": "DPP4i"},
    {"name": "Semaglutide", "rxnorm_cui": "1991302", "atc_code": "A10BJ06", "half_life_hrs": 168, "category": "GLP1-RA"},
    {"name": "Insulin Glargine", "rxnorm_cui": "274783", "atc_code": "A10AE04", "half_life_hrs": 18, "category": "Basal Insulin"},
    {"name": "Levothyroxine", "rxnorm_cui": "10582", "atc_code": "H03AA01", "half_life_hrs": 168, "category": "Thyroid Hormone"},
    {"name": "Methimazole", "rxnorm_cui": "6835", "atc_code": "H03BB02", "half_life_hrs": 6, "category": "Antithyroid"},
    # Neurology / Psychiatry
    {"name": "Levetiracetam", "rxnorm_cui": "39998", "atc_code": "N03AX14", "half_life_hrs": 7, "category": "Antiepileptic"},
    {"name": "Carbamazepine", "rxnorm_cui": "2002", "atc_code": "N03AF01", "half_life_hrs": 20, "category": "Antiepileptic"},
    {"name": "Valproic Acid", "rxnorm_cui": "11118", "atc_code": "N03AG01", "half_life_hrs": 13, "category": "Antiepileptic"},
    {"name": "Levodopa/Carbidopa", "rxnorm_cui": "6375", "atc_code": "N04BA02", "half_life_hrs": 1.5, "category": "Dopaminergic"},
    {"name": "Sertraline", "rxnorm_cui": "36437", "atc_code": "N06AB06", "half_life_hrs": 26, "category": "SSRI"},
    {"name": "Escitalopram", "rxnorm_cui": "321988", "atc_code": "N06AB10", "half_life_hrs": 30, "category": "SSRI"},
    {"name": "Fluoxetine", "rxnorm_cui": "4493", "atc_code": "N06AB03", "half_life_hrs": 72, "category": "SSRI"},
    {"name": "Sumatriptan", "rxnorm_cui": "37418", "atc_code": "N02CC01", "half_life_hrs": 2, "category": "Triptan"},
    # Infectious Disease
    {"name": "Amoxicillin", "rxnorm_cui": "723", "atc_code": "J01CA04", "half_life_hrs": 1, "category": "Penicillin"},
    {"name": "Azithromycin", "rxnorm_cui": "18631", "atc_code": "J01FA10", "half_life_hrs": 68, "category": "Macrolide"},
    {"name": "Ciprofloxacin", "rxnorm_cui": "2551", "atc_code": "J01MA02", "half_life_hrs": 4, "category": "Fluoroquinolone"},
    {"name": "Levofloxacin", "rxnorm_cui": "82122", "atc_code": "J01MA12", "half_life_hrs": 7, "category": "Fluoroquinolone"},
    {"name": "Doxycycline", "rxnorm_cui": "3640", "atc_code": "J01AA02", "half_life_hrs": 18, "category": "Tetracycline"},
    {"name": "Vancomycin", "rxnorm_cui": "11124", "atc_code": "J01XA01", "half_life_hrs": 6, "category": "Glycopeptide"},
    {"name": "Meropenem", "rxnorm_cui": "29561", "atc_code": "J01DH02", "half_life_hrs": 1, "category": "Carbapenem"},
    {"name": "Oseltamivir", "rxnorm_cui": "283742", "atc_code": "J05AH02", "half_life_hrs": 8, "category": "Neuraminidase Inhibitor"},
    {"name": "Isoniazid", "rxnorm_cui": "6038", "atc_code": "J04AC01", "half_life_hrs": 3, "category": "Antimycobacterial"},
    {"name": "Rifampicin", "rxnorm_cui": "9384", "atc_code": "J04AB02", "half_life_hrs": 3, "category": "Antimycobacterial"},
    {"name": "Artemether/Lumefantrine", "rxnorm_cui": "602393", "atc_code": "P01BF01", "half_life_hrs": 120, "category": "Antimalarial"},
    # Rheumatology
    {"name": "Methotrexate", "rxnorm_cui": "6851", "atc_code": "L01BA01", "half_life_hrs": 6, "category": "DMARD"},
    {"name": "Hydroxychloroquine", "rxnorm_cui": "5521", "atc_code": "P01BA02", "half_life_hrs": 960, "category": "DMARD"},
    {"name": "Prednisolone", "rxnorm_cui": "8638", "atc_code": "H02AB06", "half_life_hrs": 3, "category": "Corticosteroid"},
    {"name": "Ibuprofen", "rxnorm_cui": "5640", "atc_code": "M01AE01", "half_life_hrs": 2, "category": "NSAID"},
    {"name": "Naproxen", "rxnorm_cui": "7258", "atc_code": "M01AE02", "half_life_hrs": 14, "category": "NSAID"},
    # Nephrology
    {"name": "Erythropoietin (Epoetin alfa)", "rxnorm_cui": "3941", "atc_code": "B03XA01", "half_life_hrs": 6, "category": "ESA"},
    # Respiratory
    {"name": "Salbutamol (Albuterol)", "rxnorm_cui": "435", "atc_code": "R03AC02", "half_life_hrs": 5, "category": "SABA"},
    {"name": "Ipratropium", "rxnorm_cui": "7213", "atc_code": "R03BB01", "half_life_hrs": 2, "category": "SAMA"},
    {"name": "Fluticasone/Salmeterol", "rxnorm_cui": "247838", "atc_code": "R03AK06", "half_life_hrs": 8, "category": "ICS/LABA"},
    {"name": "Tiotropium", "rxnorm_cui": "274219", "atc_code": "R03BB04", "half_life_hrs": 25, "category": "LAMA"},
    # GI / Hepatology
    {"name": "Omeprazole", "rxnorm_cui": "7646", "atc_code": "A02BC01", "half_life_hrs": 1, "category": "PPI"},
    {"name": "Pantoprazole", "rxnorm_cui": "40790", "atc_code": "A02BC02", "half_life_hrs": 1, "category": "PPI"},
    # Pain
    {"name": "Acetaminophen (Paracetamol)", "rxnorm_cui": "161", "atc_code": "N02BE01", "half_life_hrs": 3, "category": "Analgesic"},
    {"name": "Gabapentin", "rxnorm_cui": "25480", "atc_code": "N03AX12", "half_life_hrs": 6, "category": "Gabapentinoid"},
    {"name": "Morphine", "rxnorm_cui": "7052", "atc_code": "N02AA01", "half_life_hrs": 3, "category": "Opioid"},
]


# ═══════════════════════════════════════════════════════════════
# DRUG-DRUG INTERACTIONS (DDIs)
# ═══════════════════════════════════════════════════════════════

DRUG_INTERACTIONS = [
    # Anticoagulant + Antiplatelet bleeding risks
    ("Warfarin", "Aspirin", "MAJOR", "Additive anticoagulant/antiplatelet effect increases bleeding risk", "Monitor INR closely; consider PPI gastroprotection"),
    ("Warfarin", "Clopidogrel", "MAJOR", "Dual pathway inhibition increases hemorrhagic risk", "Use only when benefits outweigh risks; monitor for bleeding signs"),
    ("Warfarin", "Rivaroxaban", "CONTRAINDICATED", "Dual anticoagulation with synergistic hemorrhagic risk", "Never co-administer — choose one anticoagulant"),
    ("Warfarin", "Apixaban", "CONTRAINDICATED", "Dual anticoagulation — extreme bleeding risk", "Never co-administer"),
    ("Rivaroxaban", "Aspirin", "MAJOR", "Increased bleeding risk with combined antithrombotic therapy", "Triple therapy only with strong indication; limit duration"),
    # SSRI + Antiplatelet serotonin-mediated bleeding
    ("Sertraline", "Aspirin", "MODERATE", "SSRIs impair platelet serotonin uptake, additive bleeding risk", "Consider PPI; monitor for GI bleeding"),
    ("Fluoxetine", "Warfarin", "MAJOR", "Fluoxetine inhibits CYP2C9, increases warfarin effect", "Reduce warfarin dose; monitor INR weekly"),
    # Cardiac rhythm interactions
    ("Amiodarone", "Digoxin", "MAJOR", "Amiodarone inhibits P-glycoprotein, doubles digoxin levels", "Reduce digoxin dose by 50%; monitor serum digoxin levels"),
    ("Amiodarone", "Warfarin", "MAJOR", "Amiodarone inhibits CYP2C9, potentiates warfarin", "Reduce warfarin by 30-50%; monitor INR closely"),
    ("Amiodarone", "Metoprolol", "MAJOR", "Additive bradycardia and AV block risk", "Monitor heart rate and ECG; use with caution"),
    # Nephrotoxic combinations
    ("Vancomycin", "Furosemide", "MODERATE", "Additive nephrotoxicity and ototoxicity", "Monitor renal function and serum vancomycin trough"),
    ("Metformin", "Ciprofloxacin", "MODERATE", "Fluoroquinolones can cause dysglycemia with metformin", "Monitor blood glucose closely"),
    # ACE inhibitor + potassium-sparing diuretic
    ("Lisinopril", "Spironolactone", "MAJOR", "Risk of life-threatening hyperkalemia", "Monitor serum potassium within 1 week; avoid if K+ > 5.0"),
    ("Enalapril", "Spironolactone", "MAJOR", "Dual RAAS blockade with hyperkalemia risk", "Monitor serum potassium and renal function closely"),
    # NSAID interactions
    ("Ibuprofen", "Aspirin", "MAJOR", "Ibuprofen blocks aspirin's irreversible antiplatelet effect on COX-1", "Take aspirin 30min before ibuprofen, or use alternative analgesic"),
    ("Ibuprofen", "Warfarin", "MAJOR", "NSAIDs increase GI bleeding risk and may displace warfarin from albumin", "Avoid combination; use acetaminophen instead"),
    ("Ibuprofen", "Lisinopril", "MODERATE", "NSAIDs reduce antihypertensive effect and increase AKI risk", "Monitor BP and renal function; minimize NSAID duration"),
    ("Naproxen", "Warfarin", "MAJOR", "Additive GI bleeding risk", "Avoid; use acetaminophen for pain if on warfarin"),
    # CYP interactions
    ("Rifampicin", "Warfarin", "MAJOR", "Rifampicin is a potent CYP3A4/2C9 inducer, dramatically reduces warfarin levels", "Increase warfarin dose; monitor INR 2-3x weekly during rifampicin therapy"),
    ("Rifampicin", "Rivaroxaban", "CONTRAINDICATED", "Rifampicin reduces rivaroxaban levels by >50%", "Do not co-administer; use alternative anticoagulant"),
    ("Carbamazepine", "Valproic Acid", "MAJOR", "Carbamazepine induces valproate metabolism; valproate inhibits carbamazepine epoxide hydrolase", "Monitor both drug levels; watch for CBZ toxicity"),
    # QT prolongation
    ("Azithromycin", "Amiodarone", "MAJOR", "Additive QT prolongation risk — risk of Torsades de Pointes", "Avoid combination; if necessary, monitor ECG for QTc > 500ms"),
    ("Ciprofloxacin", "Amiodarone", "MAJOR", "Both prolong QT interval — additive risk of fatal arrhythmia", "Use alternative antibiotic (e.g., doxycycline) if possible"),
    ("Escitalopram", "Amiodarone", "MAJOR", "Additive QT prolongation", "Consider alternative SSRI (sertraline) with lower QT risk"),
    # Methotrexate interactions
    ("Methotrexate", "Ibuprofen", "MAJOR", "NSAIDs reduce methotrexate renal clearance, increasing toxicity risk", "Avoid NSAIDs 2 days before and after methotrexate; monitor CBC"),
    ("Methotrexate", "Omeprazole", "MODERATE", "PPIs may decrease methotrexate clearance at high doses", "Monitor for methotrexate toxicity; consider H2 blocker alternative"),
    # Opioid interactions
    ("Morphine", "Sertraline", "MAJOR", "Risk of serotonin syndrome with concurrent opioid + SSRI", "Monitor for agitation, hyperthermia, myoclonus; lowest effective doses"),
    # Statin interactions
    ("Atorvastatin", "Amiodarone", "MODERATE", "Amiodarone inhibits CYP3A4, increasing statin exposure and rhabdomyolysis risk", "Limit atorvastatin to 40mg/day with amiodarone"),
]


# ═══════════════════════════════════════════════════════════════
# eGFR-BASED RENAL CONTRAINDICATIONS
# ═══════════════════════════════════════════════════════════════

RENAL_CONTRAINDICATIONS = [
    ("Metformin", "Chronic Kidney Disease Stage 4", 30.0, "CONTRAINDICATED below eGFR 30 — risk of lactic acidosis"),
    ("Metformin", "Acute Kidney Injury", 30.0, "Hold during AKI — reassess when renal function stabilizes"),
    ("Enoxaparin", "Chronic Kidney Disease Stage 4", 30.0, "Standard dose contraindicated — switch to UFH or reduce dose to 1mg/kg QD"),
    ("Gabapentin", "Chronic Kidney Disease Stage 4", 30.0, "Reduce dose: 100-300mg QD; accumulation causes CNS depression"),
    ("Oseltamivir", "Chronic Kidney Disease Stage 4", 30.0, "Reduce to 75mg QD (half normal dose) if eGFR 10-30"),
    ("Sitagliptin", "Chronic Kidney Disease Stage 4", 30.0, "Reduce to 25mg QD (from 100mg) when eGFR < 30"),
    ("Digoxin", "Chronic Kidney Disease Stage 4", 30.0, "Reduce dose and monitor levels — narrow therapeutic index renally cleared"),
    ("Vancomycin", "Acute Kidney Injury", 30.0, "Extend dosing interval; monitor trough levels (target 15-20 mcg/mL for serious infections)"),
    ("Rivaroxaban", "Chronic Kidney Disease Stage 4", 15.0, "Avoid if eGFR < 15 — no data; reduce dose if eGFR 15-50"),
    ("Apixaban", "Chronic Kidney Disease Stage 4", 15.0, "Use with caution below eGFR 15; consider 2.5mg BID dose reduction"),
    ("Spironolactone", "Chronic Kidney Disease Stage 4", 30.0, "High hyperkalemia risk — avoid or monitor K+ very closely"),
]


# ═══════════════════════════════════════════════════════════════
# MEDICATION → DISEASE (TREATS) relationships
# ═══════════════════════════════════════════════════════════════

MEDICATION_TREATS = [
    ("Aspirin", "Acute ST-Elevation Myocardial Infarction", "AHA/ACC 2025 STEMI Guideline", "1A", 1),
    ("Ticagrelor", "Acute ST-Elevation Myocardial Infarction", "AHA/ACC 2025 STEMI Guideline", "1A", 1),
    ("Heparin (Unfractionated)", "Acute ST-Elevation Myocardial Infarction", "AHA/ACC 2025 STEMI Guideline", "1A", 1),
    ("Metoprolol", "Heart Failure", "ACC/AHA HF Guideline 2022", "1A", 1),
    ("Carvedilol", "Heart Failure", "ACC/AHA HF Guideline 2022", "1A", 1),
    ("Lisinopril", "Heart Failure", "ACC/AHA HF Guideline 2022", "1A", 1),
    ("Spironolactone", "Heart Failure", "RALES Trial / ACC/AHA", "1A", 2),
    ("Empagliflozin", "Heart Failure", "EMPEROR-Reduced Trial", "1A", 1),
    ("Furosemide", "Heart Failure", "ACC/AHA HF Guideline", "1B", 1),
    ("Digoxin", "Heart Failure", "DIG Trial / ACC/AHA", "2A", 3),
    ("Apixaban", "Atrial Fibrillation", "ARISTOTLE Trial / ESC 2024", "1A", 1),
    ("Rivaroxaban", "Atrial Fibrillation", "ROCKET-AF / ESC 2024", "1A", 1),
    ("Amiodarone", "Atrial Fibrillation", "ESC 2024 AF Guideline", "1B", 2),
    ("Metoprolol", "Atrial Fibrillation", "ESC 2024 — Rate Control", "1A", 1),
    ("Amlodipine", "Hypertensive Crisis", "JNC 8 / AHA/ACC 2017", "1A", 1),
    ("Metformin", "Type 2 Diabetes Mellitus", "ADA Standards of Care 2026", "1A", 1),
    ("Empagliflozin", "Type 2 Diabetes Mellitus", "ADA Standards 2026 — CKD/CVD benefit", "1A", 1),
    ("Semaglutide", "Type 2 Diabetes Mellitus", "ADA Standards 2026 — Weight + CV benefit", "1A", 1),
    ("Sitagliptin", "Type 2 Diabetes Mellitus", "ADA Standards 2026", "2A", 2),
    ("Insulin Glargine", "Type 2 Diabetes Mellitus", "ADA Standards 2026", "1A", 3),
    ("Insulin Glargine", "Diabetic Ketoacidosis", "ADA DKA Protocol", "1A", 1),
    ("Levothyroxine", "Hypothyroidism", "ATA Guideline 2014", "1A", 1),
    ("Methimazole", "Hyperthyroidism (Graves Disease)", "ATA Guideline", "1A", 1),
    ("Levetiracetam", "Epilepsy (Generalized)", "ILAE/AAN Guideline", "1A", 1),
    ("Valproic Acid", "Epilepsy (Generalized)", "ILAE/AAN Guideline", "1A", 1),
    ("Levodopa/Carbidopa", "Parkinson Disease", "AAN Guideline", "1A", 1),
    ("Sertraline", "Major Depressive Disorder", "APA Practice Guideline", "1A", 1),
    ("Escitalopram", "Major Depressive Disorder", "NICE CG90 / APA", "1A", 1),
    ("Escitalopram", "Generalized Anxiety Disorder", "NICE CG113", "1A", 1),
    ("Methotrexate", "Rheumatoid Arthritis", "ACR/EULAR 2023", "1A", 1),
    ("Hydroxychloroquine", "Systemic Lupus Erythematosus", "ACR/EULAR Lupus 2023", "1A", 1),
    ("Hydroxychloroquine", "Rheumatoid Arthritis", "ACR 2023", "1A", 1),
    ("Amoxicillin", "Community-Acquired Pneumonia", "ATS/IDSA CAP 2019", "1A", 1),
    ("Azithromycin", "Community-Acquired Pneumonia", "ATS/IDSA CAP 2019", "1A", 1),
    ("Salbutamol (Albuterol)", "Acute Asthma Exacerbation", "GINA 2026", "1A", 1),
    ("Fluticasone/Salmeterol", "Acute Asthma Exacerbation", "GINA 2026", "1A", 2),
    ("Tiotropium", "COPD Exacerbation", "GOLD 2026", "1A", 1),
    ("Heparin (Unfractionated)", "Pulmonary Embolism", "CHEST Guideline", "1A", 1),
    ("Rivaroxaban", "Deep Vein Thrombosis", "EINSTEIN-DVT / CHEST", "1A", 1),
    ("Heparin (Unfractionated)", "Deep Vein Thrombosis", "CHEST Guideline", "1A", 1),
    ("Isoniazid", "Tuberculosis (Pulmonary)", "WHO TB Guideline 2022", "1A", 1),
    ("Rifampicin", "Tuberculosis (Pulmonary)", "WHO TB Guideline 2022", "1A", 1),
    ("Artemether/Lumefantrine", "Malaria (Plasmodium falciparum)", "WHO Malaria Guideline 2023", "1A", 1),
    ("Oseltamivir", "COVID-19 Pneumonia", "NIH COVID-19 Treatment Guideline (adjunctive)", "2A", 3),
    ("Omeprazole", "Acute Pancreatitis", "ACG Pancreatitis Guideline (supportive)", "2B", 3),
    ("Sumatriptan", "Migraine with Aura", "AAN Migraine Guideline", "1A", 1),
]


# ═══════════════════════════════════════════════════════════════
# CLINICAL GUIDELINE CHUNKS — Qdrant Seed Data
# ═══════════════════════════════════════════════════════════════

CLINICAL_GUIDELINES = [
    # AHA/ACC Cardiology
    {
        "source_authority": "AHA",
        "specialty": "Cardiology",
        "publication_date": "2025-11-15",
        "evidence_level": "Level_I",
        "snomed_codes": ["54329005"],
        "chunk_text": "For patients presenting with STEMI, primary percutaneous coronary intervention (PCI) is the preferred reperfusion strategy when it can be performed within 120 minutes of first medical contact. Administer aspirin 162-325mg (chewable) immediately upon presentation. Dual antiplatelet therapy with a P2Y12 inhibitor (ticagrelor 180mg or prasugrel 60mg loading dose) should be initiated as early as possible."
    },
    {
        "source_authority": "AHA",
        "specialty": "Cardiology",
        "publication_date": "2025-11-15",
        "evidence_level": "Level_I",
        "snomed_codes": ["54329005"],
        "chunk_text": "Anticoagulation for STEMI patients undergoing primary PCI: Unfractionated heparin (UFH) 60-70 units/kg IV bolus (max 4000 units) is recommended. In patients with severe renal impairment (eGFR < 30 mL/min), UFH is preferred over enoxaparin due to predictable pharmacokinetics and reversibility with protamine."
    },
    {
        "source_authority": "AHA",
        "specialty": "Cardiology",
        "publication_date": "2022-04-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["84114007"],
        "chunk_text": "Guideline-Directed Medical Therapy (GDMT) for Heart Failure with Reduced Ejection Fraction (HFrEF) consists of four pillars: (1) ACE inhibitor/ARB/ARNI, (2) Beta-blocker (carvedilol, metoprolol succinate, or bisoprolol), (3) Mineralocorticoid receptor antagonist (spironolactone or eplerenone), and (4) SGLT2 inhibitor (dapagliflozin or empagliflozin). All four should be initiated and uptitrated to target doses."
    },
    {
        "source_authority": "AHA",
        "specialty": "Cardiology",
        "publication_date": "2022-04-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["84114007"],
        "chunk_text": "For patients with HFrEF and fluid overload, loop diuretics (furosemide, bumetanide, or torsemide) should be used for symptom relief. Diuretic dose should be titrated to achieve euvolemia. Daily weight monitoring and fluid restriction (1.5-2L/day) are recommended. Rapid weight gain (>2kg in 48 hours) in a heart failure patient should trigger urgent clinical review."
    },
    # NICE Guidelines
    {
        "source_authority": "NICE",
        "specialty": "Respiratory",
        "publication_date": "2024-09-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["385093006"],
        "chunk_text": "NICE CG191 — Community-Acquired Pneumonia: For low-severity CAP (CURB-65 score 0-1), oral amoxicillin 500mg TID for 5 days is first-line. For moderate severity (CURB-65 2), consider combination with a macrolide (azithromycin 500mg OD for 3 days). For severe CAP (CURB-65 ≥3), IV co-amoxiclav + IV clarithromycin or IV piperacillin-tazobactam + macrolide."
    },
    {
        "source_authority": "NICE",
        "specialty": "Respiratory",
        "publication_date": "2024-07-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["304527002"],
        "chunk_text": "NICE BTS Asthma Guideline: Acute severe asthma is defined by PEF 33-50% best/predicted, respiratory rate ≥25/min, heart rate ≥110/min, or inability to complete sentences. Immediate management: high-flow oxygen targeting SpO2 94-98%, nebulized salbutamol 5mg (repeat every 15-30 min), ipratropium bromide 500mcg, and prednisolone 40-50mg PO (or IV hydrocortisone 100mg)."
    },
    {
        "source_authority": "NICE",
        "specialty": "Psychiatry",
        "publication_date": "2024-03-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["370143000"],
        "chunk_text": "NICE CG90 — Depression in Adults: For moderate-to-severe depression, first-line pharmacotherapy is an SSRI (sertraline is recommended due to favorable cost-effectiveness and interaction profile). Start at the lowest effective dose and review at 2-4 weeks. Treatment should continue for at least 6 months after remission to prevent relapse."
    },
    {
        "source_authority": "NICE",
        "specialty": "Rheumatology",
        "publication_date": "2024-06-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["69896004"],
        "chunk_text": "NICE NG100 — Rheumatoid Arthritis: Start DMARD therapy as soon as possible after diagnosis, ideally within 3 months. Methotrexate is first-line DMARD. Start at 7.5mg weekly, escalating to 25mg weekly as tolerated. Co-prescribe folic acid 5mg weekly (not on methotrexate day). Monitor FBC, LFTs, and renal function every 2-4 weeks initially."
    },
    # ICMR (Indian Council of Medical Research)
    {
        "source_authority": "ICMR",
        "specialty": "Infectious Disease",
        "publication_date": "2025-06-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["38362002"],
        "chunk_text": "ICMR-NVBDCP Dengue Guidelines: Dengue fever diagnosis based on NS1 antigen (days 1-5) or IgM/IgG ELISA (day 5 onwards). Warning signs requiring hospitalization: persistent vomiting, abdominal pain/tenderness, mucosal bleeding, hepatomegaly >2cm, rising hematocrit with falling platelets. Management is primarily supportive — IV crystalloids (NS or RL), avoid NSAIDs (bleeding risk), platelet transfusion only if <10,000 with active bleeding."
    },
    {
        "source_authority": "ICMR",
        "specialty": "Infectious Disease",
        "publication_date": "2025-01-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["61462000"],
        "chunk_text": "ICMR National Treatment Guidelines for Malaria: Uncomplicated P. falciparum malaria — Artemether-Lumefantrine (ACT) for 3 days. Severe malaria — IV Artesunate 2.4 mg/kg at 0, 12, 24h then OD, followed by full course of oral ACT after patient can tolerate oral therapy. Primaquine 0.75mg/kg single dose as gametocytocidal agent (after ruling out G6PD deficiency)."
    },
    {
        "source_authority": "ICMR",
        "specialty": "Infectious Disease",
        "publication_date": "2024-03-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["154283005"],
        "chunk_text": "ICMR RNTCP Tuberculosis Guidelines: First-line treatment for drug-sensitive pulmonary TB: Intensive phase (2 months) — HRZE (Isoniazid + Rifampicin + Pyrazinamide + Ethambutol) daily. Continuation phase (4 months) — HR (Isoniazid + Rifampicin) daily. Fixed-dose combinations preferred. Monitor sputum smear at 2 months and 5 months."
    },
    # ADA (American Diabetes Association)
    {
        "source_authority": "ADA",
        "specialty": "Endocrinology",
        "publication_date": "2026-01-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["44054006"],
        "chunk_text": "ADA Standards of Care 2026 — Type 2 Diabetes: Metformin remains first-line pharmacotherapy. For patients with established ASCVD or high CV risk, add an SGLT2 inhibitor (empagliflozin, dapagliflozin) or GLP-1 RA (semaglutide, liraglutide) with demonstrated CV benefit, independent of HbA1c. Target HbA1c <7% for most adults, <8% for elderly/comorbid."
    },
    {
        "source_authority": "ADA",
        "specialty": "Endocrinology",
        "publication_date": "2026-01-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["44054006"],
        "chunk_text": "ADA Standards 2026 — Renal Considerations: Metformin should be held if eGFR falls below 30 mL/min/1.73m². For eGFR 30-45, reduce metformin dose to 500-1000mg/day with close monitoring. SGLT2 inhibitors provide renal benefit and can be initiated at eGFR ≥20 mL/min for renal protection, though glucose-lowering efficacy diminishes below eGFR 45."
    },
    {
        "source_authority": "ADA",
        "specialty": "Endocrinology",
        "publication_date": "2026-01-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["420422005"],
        "chunk_text": "ADA DKA Protocol: Diagnostic criteria — blood glucose >250 mg/dL, arterial pH <7.30, serum bicarbonate <18 mEq/L, anion gap >10, presence of ketonemia/ketonuria. Treatment: aggressive IV fluid resuscitation (NS 1-1.5L/hr for first 2 hours), continuous IV regular insulin infusion 0.1 units/kg/hr (after initial bolus 0.1 units/kg IV), potassium replacement when K+ <5.3 mEq/L, and dextrose when glucose <250 mg/dL."
    },
    # FDA Drug Labels
    {
        "source_authority": "FDA_LABEL",
        "specialty": "Pharmacology",
        "publication_date": "2025-08-01",
        "evidence_level": "Level_I",
        "snomed_codes": [],
        "chunk_text": "FDA Prescribing Information — Metformin (Glucophage): CONTRAINDICATIONS: Severe renal impairment (eGFR below 30 mL/min/1.73 m²). WARNINGS: Lactic acidosis is a rare but serious metabolic complication. Risk increases with sepsis, dehydration, excessive alcohol, hepatic insufficiency, and acute CHF. Temporarily discontinue at the time of or before iodinated contrast imaging procedures in patients with eGFR 30-60 mL/min/1.73 m²."
    },
    {
        "source_authority": "FDA_LABEL",
        "specialty": "Pharmacology",
        "publication_date": "2025-06-01",
        "evidence_level": "Level_I",
        "snomed_codes": [],
        "chunk_text": "FDA Prescribing Information — Warfarin (Coumadin): BOXED WARNING: Warfarin can cause major or fatal bleeding. Perform regular INR monitoring. DRUG INTERACTIONS: Many substances can alter warfarin effect — including amiodarone, fluoxetine, rifampicin, NSAIDs, and cranberry juice. CYP2C9 and VKORC1 genotype-guided dosing is recommended when available."
    },
    {
        "source_authority": "FDA_LABEL",
        "specialty": "Pharmacology",
        "publication_date": "2024-11-01",
        "evidence_level": "Level_I",
        "snomed_codes": [],
        "chunk_text": "FDA Prescribing Information — Carbamazepine (Tegretol): BOXED WARNING: Serious and sometimes fatal dermatologic reactions including Stevens-Johnson Syndrome (SJS) and Toxic Epidermal Necrolysis (TEN). HLA-B*1502 allele is strongly associated with SJS/TEN risk. Screening is recommended in patients of Southeast Asian ancestry before initiating carbamazepine."
    },
    # WHO Guidelines
    {
        "source_authority": "NICE",
        "specialty": "Neurology",
        "publication_date": "2024-08-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["422504002"],
        "chunk_text": "NICE NG128 — Stroke: For acute ischemic stroke, IV alteplase (0.9mg/kg, max 90mg, 10% as bolus + 60min infusion) should be administered within 4.5 hours of symptom onset. Mechanical thrombectomy should be considered for large vessel occlusions up to 24 hours with appropriate imaging selection (DAWN/DEFUSE criteria). Aspirin 300mg should be given within 24 hours (after hemorrhage excluded)."
    },
    {
        "source_authority": "AHA",
        "specialty": "Neurology",
        "publication_date": "2024-01-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["422504002"],
        "chunk_text": "AHA/ASA Acute Ischemic Stroke Guideline: Blood pressure management — for patients eligible for IV thrombolysis, BP should be <185/110 mmHg before treatment and maintained <180/105 during and 24h after. For non-thrombolysis patients, permissive hypertension (up to 220/120) unless evidence of end-organ damage."
    },
    {
        "source_authority": "ADA",
        "specialty": "Ophthalmology",
        "publication_date": "2026-01-01",
        "evidence_level": "Level_I",
        "snomed_codes": ["4855003"],
        "chunk_text": "ADA Standards 2026 — Diabetic Retinopathy Screening: All adults with type 1 diabetes should have an initial dilated eye exam within 5 years of diagnosis. Type 2 diabetes patients should have an exam at diagnosis. Repeat annually, or every 2 years if no retinopathy. Optimize glycemic control (HbA1c <7%), blood pressure (<130/80), and lipids to reduce progression risk."
    },
]


# ═══════════════════════════════════════════════════════════════
# SEEDING FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def seed_neo4j(driver):
    """Seed Neo4j with diseases, symptoms, medications, and relationships."""
    print("\n" + "=" * 60)
    print("SEEDING NEO4J KNOWLEDGE GRAPH")
    print("=" * 60)

    with driver.session() as session:
        # --- Clear existing data ---
        print("\n[1/7] Clearing existing graph data...")
        session.run("MATCH (n) DETACH DELETE n")
        print("      ✓ Cleared all nodes and relationships")

        # --- Create constraints/indexes ---
        print("\n[2/7] Creating constraints and indexes...")
        constraints = [
            "CREATE CONSTRAINT disease_snomed IF NOT EXISTS FOR (d:Disease) REQUIRE d.snomed_id IS UNIQUE",
            "CREATE CONSTRAINT symptom_snomed IF NOT EXISTS FOR (s:Symptom) REQUIRE s.snomed_id IS UNIQUE",
            "CREATE CONSTRAINT med_rxnorm IF NOT EXISTS FOR (m:Medication) REQUIRE m.rxnorm_cui IS UNIQUE",
        ]
        for c in constraints:
            try:
                session.run(c)
            except Exception as e:
                print(f"      ⚠ Constraint warning (may already exist): {e}")
        print("      ✓ Constraints created")

        # --- Seed Diseases ---
        print(f"\n[3/7] Seeding {len(DISEASES)} diseases...")
        for d in DISEASES:
            session.run(
                """
                CREATE (d:Disease {
                    name: $name,
                    icd11: $icd11,
                    snomed_id: $snomed_id,
                    category: $category
                })
                """,
                **d,
            )
        print(f"      ✓ Created {len(DISEASES)} Disease nodes")

        # --- Seed Symptoms ---
        print(f"\n[4/7] Seeding {len(SYMPTOMS)} symptoms...")
        for s in SYMPTOMS:
            session.run(
                """
                CREATE (s:Symptom {
                    name: $name,
                    snomed_id: $snomed_id,
                    category: $category
                })
                """,
                **s,
            )
        print(f"      ✓ Created {len(SYMPTOMS)} Symptom nodes")

        # --- Seed Medications ---
        print(f"\n[5/7] Seeding {len(MEDICATIONS)} medications...")
        for m in MEDICATIONS:
            session.run(
                """
                CREATE (m:Medication {
                    name: $name,
                    rxnorm_cui: $rxnorm_cui,
                    atc_code: $atc_code,
                    half_life_hrs: $half_life_hrs,
                    category: $category
                })
                """,
                **m,
            )
        print(f"      ✓ Created {len(MEDICATIONS)} Medication nodes")

        # --- Seed Disease → Symptom relationships ---
        print(f"\n[6/7] Seeding {len(DISEASE_SYMPTOM_EDGES)} disease→symptom relationships...")
        success = 0
        for disease_name, symptom_name, sensitivity, specificity, lr_pos in DISEASE_SYMPTOM_EDGES:
            result = session.run(
                """
                MATCH (d:Disease {name: $disease_name})
                MATCH (s:Symptom {name: $symptom_name})
                CREATE (d)-[:PRESENTS_WITH {
                    sensitivity: $sensitivity,
                    specificity: $specificity,
                    likelihood_ratio_pos: $lr_pos
                }]->(s)
                RETURN count(*) AS cnt
                """,
                disease_name=disease_name,
                symptom_name=symptom_name,
                sensitivity=sensitivity,
                specificity=specificity,
                lr_pos=lr_pos,
            )
            cnt = result.single()["cnt"]
            success += cnt
        print(f"      ✓ Created {success} PRESENTS_WITH relationships")

        # --- Seed DDI relationships ---
        print(f"\n[7/7] Seeding {len(DRUG_INTERACTIONS)} DDIs + {len(MEDICATION_TREATS)} TREATS + {len(RENAL_CONTRAINDICATIONS)} renal contraindications...")
        ddi_count = 0
        for drug_a, drug_b, severity, mechanism, management in DRUG_INTERACTIONS:
            result = session.run(
                """
                MATCH (a:Medication {name: $drug_a})
                MATCH (b:Medication {name: $drug_b})
                CREATE (a)-[:INTERACTS_WITH {
                    severity: $severity,
                    mechanism: $mechanism,
                    clinical_management: $management
                }]->(b)
                RETURN count(*) AS cnt
                """,
                drug_a=drug_a,
                drug_b=drug_b,
                severity=severity,
                mechanism=mechanism,
                management=management,
            )
            ddi_count += result.single()["cnt"]
        print(f"      ✓ Created {ddi_count} INTERACTS_WITH (DDI) relationships")

        treats_count = 0
        for med_name, disease_name, guideline, evidence_grade, line_of_therapy in MEDICATION_TREATS:
            result = session.run(
                """
                MATCH (m:Medication {name: $med_name})
                MATCH (d:Disease {name: $disease_name})
                CREATE (m)-[:TREATS {
                    guideline_source: $guideline,
                    evidence_grade: $evidence_grade,
                    line_of_therapy: $line_of_therapy
                }]->(d)
                RETURN count(*) AS cnt
                """,
                med_name=med_name,
                disease_name=disease_name,
                guideline=guideline,
                evidence_grade=evidence_grade,
                line_of_therapy=line_of_therapy,
            )
            treats_count += result.single()["cnt"]
        print(f"      ✓ Created {treats_count} TREATS relationships")

        renal_count = 0
        for med_name, disease_name, egfr_cutoff, condition_threshold in RENAL_CONTRAINDICATIONS:
            result = session.run(
                """
                MATCH (m:Medication {name: $med_name})
                MATCH (d:Disease {name: $disease_name})
                CREATE (m)-[:CONTRAINDICATED_IN {
                    condition_threshold: $condition_threshold,
                    egfr_cutoff: $egfr_cutoff
                }]->(d)
                RETURN count(*) AS cnt
                """,
                med_name=med_name,
                disease_name=disease_name,
                egfr_cutoff=egfr_cutoff,
                condition_threshold=condition_threshold,
            )
            renal_count += result.single()["cnt"]
        print(f"      ✓ Created {renal_count} CONTRAINDICATED_IN relationships")

    # --- Summary ---
    with driver.session() as session:
        stats = session.run(
            """
            MATCH (n) WITH labels(n) AS lbl, count(n) AS cnt
            UNWIND lbl AS label
            RETURN label, cnt ORDER BY label
            """
        )
        print("\n" + "-" * 40)
        print("NEO4J SEED SUMMARY:")
        for record in stats:
            print(f"  {record['label']}: {record['cnt']} nodes")

        rel_stats = session.run(
            """
            MATCH ()-[r]->() WITH type(r) AS rel_type, count(r) AS cnt
            RETURN rel_type, cnt ORDER BY rel_type
            """
        )
        for record in rel_stats:
            print(f"  {record['rel_type']}: {record['cnt']} relationships")
        print("-" * 40)


def seed_qdrant(client: QdrantClient):
    """Seed Qdrant with clinical guideline chunks using deterministic pseudo-embeddings."""
    print("\n" + "=" * 60)
    print("SEEDING QDRANT VECTOR DATABASE")
    print("=" * 60)

    collection_name = QDRANT_COLLECTION

    # --- Recreate collection ---
    print(f"\n[1/3] Creating collection '{collection_name}' (768-dim, Cosine)...")
    try:
        client.delete_collection(collection_name)
    except Exception as exc:
        print(f"      (Recreating fresh collection: {exc})")

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=DENSE_VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )
    print(f"      ✓ Collection '{collection_name}' created")

    # --- Generate 768-dim embeddings via nomic-embed-text (or fallback) ---
    print(f"\n[2/3] Generating embeddings for {len(CLINICAL_GUIDELINES)} guideline chunks...")
    ollama_url = os.getenv("OLLAMA_HOST_URL", "http://localhost:11434")
    embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    def _get_ollama_embedding(text: str) -> list[float] | None:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{ollama_url}/api/embeddings",
                data=json.dumps({"model": embed_model, "prompt": text}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data.get("embedding")
        except Exception:
            return None

    # Test single probe
    test_vec = _get_ollama_embedding("clinical test probe")
    using_ollama = test_vec is not None and len(test_vec) == DENSE_VECTOR_SIZE
    if using_ollama:
        print(f"      ✓ Connected to Ollama ({embed_model}) — using real 768-dim clinical embeddings")
    else:
        print(f"      ! Ollama unavailable or model not loaded — using deterministic pseudo-embeddings")

    points = []
    for i, guideline in enumerate(CLINICAL_GUIDELINES):
        vector = None
        if using_ollama:
            vector = _get_ollama_embedding(guideline["chunk_text"])
        if vector is None or len(vector) != DENSE_VECTOR_SIZE:
            text_hash = hashlib.sha256(guideline["chunk_text"].encode()).digest()
            random.seed(text_hash)
            vector = [random.gauss(0, 0.3) for _ in range(DENSE_VECTOR_SIZE)]
            norm = sum(x * x for x in vector) ** 0.5
            vector = [x / norm for x in vector]

        point = PointStruct(
            id=i + 1,
            vector=vector,
            payload={
                "document_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, guideline["chunk_text"][:64])),
                "source_authority": guideline["source_authority"],
                "publication_date": guideline["publication_date"],
                "specialty": guideline["specialty"],
                "snomed_codes": guideline.get("snomed_codes", []),
                "evidence_level": guideline["evidence_level"],
                "chunk_text": guideline["chunk_text"],
            },
        )
        points.append(point)
    print(f"      ✓ Generated {len(points)} points with {DENSE_VECTOR_SIZE}-dim embeddings")

    # --- Upsert points ---
    print(f"\n[3/3] Upserting {len(points)} points to Qdrant...")
    client.upsert(collection_name=collection_name, points=points)

    # Verify
    info = client.get_collection(collection_name)
    print(f"      ✓ Collection '{collection_name}' now has {info.points_count} points")
    print(f"      ✓ Vector dimension: {info.config.params.vectors.size}")
    print(f"      ✓ Distance metric: {info.config.params.vectors.distance}")

    # --- Print source distribution ---
    print("\n" + "-" * 40)
    print("QDRANT SEED SUMMARY:")
    source_counts = {}
    for g in CLINICAL_GUIDELINES:
        src = g["source_authority"]
        source_counts[src] = source_counts.get(src, 0) + 1
    for src, count in sorted(source_counts.items()):
        print(f"  {src}: {count} chunks")
    print("-" * 40)


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   MediScan Enterprise — Clinical Knowledge Base Seeder  ║")
    print("║   Neo4j KG + Qdrant Vector DB Seed Script               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Neo4j URI: {NEO4J_URI}")
    print(f"Qdrant:    {QDRANT_HOST}:{QDRANT_PORT}")

    # --- Neo4j ---
    print("\nConnecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("  ✓ Neo4j connection verified")
        seed_neo4j(driver)
    except Exception as e:
        print(f"  ✗ Neo4j connection failed: {e}")
        sys.exit(1)
    finally:
        driver.close()

    # --- Qdrant ---
    print("\nConnecting to Qdrant...")
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    try:
        collections = qdrant_client.get_collections()
        print(f"  ✓ Qdrant connection verified ({len(collections.collections)} existing collections)")
        seed_qdrant(qdrant_client)
    except Exception as e:
        print(f"  ✗ Qdrant connection failed: {e}")
        sys.exit(1)

    # --- Final Summary ---
    print("\n" + "═" * 60)
    print("ALL SEEDS COMPLETED SUCCESSFULLY ✓")
    print("═" * 60)
    print(f"\nData seeded:")
    print(f"  Neo4j:  {len(DISEASES)} diseases, {len(SYMPTOMS)} symptoms, {len(MEDICATIONS)} medications")
    print(f"          {len(DISEASE_SYMPTOM_EDGES)} disease→symptom, {len(DRUG_INTERACTIONS)} DDIs")
    print(f"          {len(MEDICATION_TREATS)} TREATS, {len(RENAL_CONTRAINDICATIONS)} renal contraindications")
    print(f"  Qdrant: {len(CLINICAL_GUIDELINES)} clinical guideline chunks ({DENSE_VECTOR_SIZE}-dim vectors)")
    print(f"          Sources: AHA, NICE, ICMR, ADA, FDA_LABEL")


if __name__ == "__main__":
    main()
