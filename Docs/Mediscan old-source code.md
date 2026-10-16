

## MEDI SCAN PROJECT - COMPLETE SOURCE CODE
## `===================================================================
FILE: anvil_server.py
## Anvil Server Functions
Exposes predict_disease() and analyze_report() as callable server functions
`Connect via: anvil.server.connect("YOUR_UPLINK_KEY")
── Uncomment when deploying with Anvil
## ──────────────────────────────────────
import anvil.server
anvil.server.connect("YOUR_UPLINK_KEY_HERE")
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from predict_engine import DiseasePredictionEngine
from report_processor import ReportProcessor
from drug_recommender import DrugRecommender
from severity_detector import SeverityDetector
Singleton instances
_engine = DiseasePredictionEngine()
_processor = ReportProcessor()
_recommender = DrugRecommender()
_severity = SeverityDetector()
## ──────────────────────────────────────────────────
## ───────────────────────────
Server Function 1: predict_disease
## ──────────────────────────────────────────────────
## ───────────────────────────
## @anvil.server.callable
def predict_disease(symptoms: list = None, text: str = None) -> dict:
## """
Predict disease from a list of symptoms or free text.

## ──────────────────────────────────────────────────
## ───────────────────────────
Server Function 2: analyze_report
## ──────────────────────────────────────────────────
## ───────────────────────────
## @anvil.server.callable
def analyze_report(file_bytes: bytes = None, file_type: str = "pdf",
text: str = None) -> dict:
## """
Analyze a medical report from raw bytes (PDF/image) or pre-extracted text.
`Args:`
`symptoms (list): e.g. ["fever", "cough", "headache"]`
`text (str): raw text to extract keywords from`
`Returns:`
`dict with keys: predicted_disease, confidence, severity,`
`top_predictions, matched_symptoms, recommendations`
## `"""`
`if not symptoms and text:`
## `symptoms = _processor.extract_keywords(text)`
`elif not symptoms:`
`return {"error": "Provide symptoms list or text"}`
## `result = _engine.predict(symptoms)`
## `sev = _severity.detect(symptoms)`
## `drugs = _recommender.recommend(result["disease"])`
## `return {`
`"predicted_disease": result["disease"],`
`"confidence": round(result["confidence"] * 100, 1),`
`"top_predictions": result.get("top_predictions", []),`
`"severity": sev,`
`"matched_symptoms": symptoms,`
`"recommendations": drugs,`
## `}`
`Args:`
`file_bytes (bytes): raw file bytes (PDF or image)`
## `file_type (str): "pdf" | "image"`
`text (str): pre-extracted text (alternative to file_bytes)`
`Returns:`
`dict with extracted_text, keywords, predicted_disease,`

## ──────────────────────────────────────────────────
## ───────────────────────────
Standalone test
## ──────────────────────────────────────────────────
## ───────────────────────────
if __name__ == "__main__":
print("=" * 60)
print("TEST: predict_disease()")
result = predict_disease(symptoms=["fever", "cough", "headache", "body ache"])
print(f" Disease : {result['predicted_disease']}")
print(f" Confidence: {result['confidence']}%")
print(f" Severity : {result['severity']['level']} - {result['severity']
`confidence, severity, recommendations`
## `"""`
`import io`
`if file_bytes:`
`file_like = io.BytesIO(file_bytes)`
`if file_type == "pdf":`
## `extracted_text = _processor.extract_pdf_text(file_like)`
`elif file_type in ("image", "img"):`
## `extracted_text = _processor.extract_image_text(file_like)`
## `else:`
`return {"error": f"Unknown file_type '{file_type}'. Use 'pdf' or
## 'image'."}`
`elif text:`
`extracted_text = text`
## `else:`
`return {"error": "Provide file_bytes or text"}`
## `keywords = _processor.extract_keywords(extracted_text)`
## `result = _engine.predict(keywords)`
## `sev = _severity.detect(keywords)`
## `drugs = _recommender.recommend(result["disease"])`
## `return {`
`"extracted_text_preview": extracted_text[:500],`
`"keywords": keywords,`
`"predicted_disease": result["disease"],`
`"confidence": round(result["confidence"] * 100, 1),`
`"top_predictions": result.get("top_predictions", []),`
`"severity": sev,`
`"recommendations": drugs,`
## `}`

## ['reason']}")
print(f" Drugs : {[d['name'] for d in result['recommendations']]}")
## ===============================================================================
## =
FILE: app.py
## ======================================================================
## ==========
import streamlit as st
import tempfile
import os
import pandas as pd
Import our existing backend logic!
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'server_code'))
import model
import drug_logic
import severity
import prediction
Use Streamlit's sleek page configuration
st.set_page_config(page_title="AI Patient Diagnostics", page_icon="",
layout="centered")
st.title(" AI-Based Patient Report Analysis")
st.markdown("Upload medical reports or enter symptoms for instant AI
predictions and drug recommendations.")
Sidebar navigation
`print("\nTEST: analyze_report(text=...)")`
## `report_text = """`
`Patient presents with high blood glucose (450 mg/dL), polyuria,
polydipsia,`
`weight loss over 3 months. BP: 140/90 mmHg. TSH: 5.2 mIU/L.`
`Symptoms: fatigue, blurred vision, frequent urination.`
## `"""`
`result2 = analyze_report(text=report_text)`
## `print(f"  Keywords  : {result2['keywords']}")`
## `print(f"  Disease   : {result2['predicted_disease']}")`
## `print(f"  Severity  : {result2['severity']['level']}")`
`print(f"  Drugs     : {[d['name'] for d in result2['recommendations']]}")`
## `print("=" * 60)`
`# Keep Anvil uplink alive (uncomment when using Anvil)`
`# anvil.server.wait_forever()`

st.sidebar.header("Navigation")
option = st.sidebar.radio("Choose Input Method:", ["Manual Symptoms Entry",
"Upload Medical Report"])
Load unique symptoms from CSV once for the
multiselect
csv_path = os.path.join(os.path.dirname(__file__), 'symptoms_disease.csv')
unique_symptoms = []
if os.path.exists(csv_path):
symptoms_df = pd.read_csv(csv_path)
all_symptoms_list = set()
for s_list in symptoms_df['symptoms']:
if pd.notna(s_list):
for s in str(s_list).split(','):
all_symptoms_list.add(s.strip().replace('_', ' '))
unique_symptoms = sorted(list(all_symptoms_list))
else:
unique_symptoms = ["fever", "headache", "cough", "fatigue", "nausea",
"dizziness", "chest pain", "shortness of breath", "high blood pressure"]
def display_results(result_dict):
st.subheader("Diagnostic Results ")
## `st.sidebar.divider()`
`st.sidebar.subheader("Dataset Information")`
`st.sidebar.info(f"Model trained on **
{len(symptoms_df['disease'].dropna().unique())}** unique diseases.")`
`with st.sidebar.expander("View Supported Diseases"):`
## `st.dataframe(symptoms_df[['disease']])`
`col1, col2 = st.columns(2)`
`with col1:`
`st.info(f"**Disease Detected:** {result_dict['disease']}")`
`st.warning(f"**Severity Level:** {result_dict['severity']}")`
`with col2:`
`st.success(f"**Recommended Drug:** {result_dict['drug']}")`
`st.markdown(f"**Dosage Info:** {result_dict['dosage']}")`
`st.error(f"**Precautions:** {result_dict['precautions']}")`
`if "extracted_text" in result_dict and result_dict["extracted_text"] !=
"Manual input provided.":`
`with st.expander("Show Extracted Report Text"):`
## `st.text(result_dict["extracted_text"])`

## Method 1: Manual Symptoms
if option == "Manual Symptoms Entry":
st.subheader("Describe Symptoms")
selected_symptoms = st.multiselect("Select patient symptoms (Disease prediction
is based on these)", options=unique_symptoms)
`if st.button("Analyze Symptoms", type="primary"):`
`if not selected_symptoms:`
`st.error("Please select at least one symptom.")`
## `else:`
`with st.spinner("Analyzing NLP engine..."):`
`# To solve "output is given for only the first syntom", we want
to`
`# run the model on all combinations, or evaluate multiple
diseases.`
`# A simple approach: we check if they map to multiple different
predictions`
## `symptoms_str = ", ".join(selected_symptoms)`
`# We can also predict based on the combinations, and show the
top disease.`
`# However, to be robust to "output is given for only the first
syntom",`
`# let's predict for the overall string, and also for each
individual symptom`
`# to aggregate any missed distinct diseases.`
`predicted_diseases = set()`
`# 1. Main prediction from all symptoms`
`main_disease = model.predict_single_disease(symptoms_str)`
## `predicted_diseases.add(main_disease)`
`# 2. Check each symptom to not miss any (which fixes only
seeing first symptom match)`
`for sym in selected_symptoms:`
`pred_d = model.predict_single_disease(sym)`
`if pred_d and pred_d != "Unknown (Text too short)":`
## `predicted_diseases.add(pred_d)`
`if not predicted_diseases or all(d == "Unknown (Text too
short)" for d in predicted_diseases): # Fallback`
## `predicted_diseases =
## {model.predict_single_disease(selected_symptoms[0])}`
`# Filter out 'Unknown (Text too short)' if valid ones exist`
`valid_diseases = [d for d in predicted_diseases if d !=
"Unknown (Text too short)"]`
`if not valid_diseases:`
`valid_diseases = ["Unknown Disease"]`

## Method 2: File Upload
elif option == "Upload Medical Report":
st.subheader("Upload PDF or Image Report")
`for disease_name in valid_diseases:`
`drug_info = drug_logic.get_drug_info(disease_name)`
`# We pass the full symptoms for severity, or just the
disease specific?`
`# Severity based on all selected symptoms`
`sev = severity.analyze_severity(symptoms_str)`
## `result = {`
`"disease": disease_name,`
`"drug": drug_info["drug"],`
`"dosage": drug_info["dosage"],`
`"precautions": drug_info["precautions"],`
`"severity": sev,`
`"extracted_text": f"Manual input provided:
## {symptoms_str}"`
## `}`
## `display_results(result)`
`template_text = "Patient Name: \nAge: \n\nSymptoms (e.g. fever, headache,
chills):\n- \n- \n\nMedical History / Existing Conditions:\n- \n\nNotes:\n"`
## `st.download_button(`
## `label=" Download Report Template",`
## `data=template_text,`
`file_name="Report_Template.txt",`
## `mime="text/plain",`
`help="Download this template, fill it out, and re-upload to get an
accurate prediction."`
## `)`
`uploaded_file = st.file_uploader("Upload a file", type=["pdf", "png",
## "jpg", "jpeg"])`
`if st.button("Extract and Analyze", type="primary"):`
`if uploaded_file is None:`
`st.error("Please upload a file first.")`
## `else:`
`with st.spinner("Extracting text via OCR/PDFParser..."):`
`# Save uploaded file temporarily for parsing`
`with tempfile.NamedTemporaryFile(delete=False, suffix=f".
{uploaded_file.name.split('.')[-1]}") as tmp:`
## `tmp.write(uploaded_file.getvalue())`
`tmp_path = tmp.name`

## ===============================================================================
## =
FILE: drug_recommender.py
## ======================================================================
## ==========
## `extracted_text = ""`
## `try:`
`if uploaded_file.name.lower().endswith(".pdf"):`
## `extracted_text =
prediction.extract_text_from_pdf(tmp_path)`
## `else:`
## `extracted_text =
prediction.extract_text_from_image(tmp_path)`
## `finally:`
## `os.remove(tmp_path)`
`if not extracted_text.strip() or len(extracted_text.strip()) <
## 5:`
`st.error("Could not extract any meaningful text from this
file. It might be corrupt, empty, or unreadable.")`
## `else:`
`st.success("Text extracted successfully!")`
`# Run it against existing NLP`
`disease = model.predict_single_disease(extracted_text)`
`if "Unknown" in disease or "Error" in disease:`
`st.error("The uploaded report does not contain
recognizable medical symptoms or is too vague to predict a real disease.")`
`with st.expander("Show Extracted text"):`
## `st.text(extracted_text)`
## `else:`
`drug_info = drug_logic.get_drug_info(disease)`
`sev = severity.analyze_severity(extracted_text)`
`snippet = extracted_text[:400] + "..." if
len(extracted_text) > 400 else extracted_text`
## `result = {`
`"disease": disease,`
`"drug": drug_info["drug"],`
`"dosage": drug_info["dosage"],`
`"precautions": drug_info["precautions"],`
`"severity": sev,`
`"extracted_text": snippet`
## `}`
## `display_results(result)`

## """
## Drug Recommendation Engine
Maps predicted disease → drug name, dosage, precautions, alternatives
Uses a JSON drug database; falls back to built-in dict if file not found.
## """
import json
import os
from typing import List, Dict
── Built-in drug database
## ──────────────────────────────────────────────────
## ───
BUILT_IN_DRUGS: Dict[str, List[Dict]] = {
"Influenza": [
{"name": "Oseltamivir (Tamiflu)", "dosage": "75 mg twice daily for 5 days",
"precautions": "Start within 48h of symptom onset. Avoid in severe renal
impairment.",
"category": "Antiviral"},
{"name": "Paracetamol", "dosage": "500–1000 mg every 6–8 hrs (max 4 g/day)",
"precautions": "Avoid alcohol. Use caution in liver disease.", "category":
"Analgesic/Antipyretic"},
## ],
"Common Cold": [
{"name": "Cetirizine", "dosage": "10 mg once daily",
"precautions": "May cause drowsiness. Avoid driving.", "category":
"Antihistamine"},
{"name": "Pseudoephedrine", "dosage": "60 mg every 4–6 hrs",
"precautions": "Avoid in hypertension, hyperthyroidism.", "category":
"Decongestant"},
## ],
"Dengue": [
{"name": "Paracetamol", "dosage": "500–1000 mg every 6 hrs",
"precautions": "AVOID NSAIDs/Aspirin – risk of bleeding.", "category":
"Analgesic/Antipyretic"},
{"name": "ORS (Oral Rehydration Salts)", "dosage": "As directed for hydration",
"precautions": "Monitor platelet count. Seek hospitalisation if platelet <
50,000.", "category": "Supportive"},
## ],
"Malaria": [
{"name": "Artemether-Lumefantrine", "dosage": "4 tabs at 0, 8, 24, 36, 48, 60
hrs",
"precautions": "Take with food. Monitor for cardiac arrhythmias.", "category":
"Antimalarial"},
{"name": "Chloroquine", "dosage": "600 mg base then 300 mg at 6, 24, 48 hrs",
"precautions": "Avoid in G6PD deficiency, retinal disease.", "category":
"Antimalarial"},
## ],

"Diabetes": [
{"name": "Metformin", "dosage": "500–1000 mg twice daily with meals",
"precautions": "Avoid in renal failure. Monitor B12 levels long-term.",
"category": "Biguanide"},
{"name": "Glipizide", "dosage": "5 mg once daily before breakfast",
"precautions": "Risk of hypoglycaemia. Monitor blood glucose.", "category":
"Sulfonylurea"},
{"name": "Insulin Glargine", "dosage": "10–20 units subcutaneous at bedtime",
"precautions": "Rotate injection sites. Store refrigerated.", "category":
"Insulin"},
## ],
"Type 2 Diabetes": [
{"name": "Metformin", "dosage": "500–2000 mg daily with meals",
"precautions": "Hold before contrast imaging. Check renal function.",
"category": "Biguanide"},
{"name": "Sitagliptin", "dosage": "100 mg once daily",
"precautions": "Dose-adjust in renal impairment.", "category": "DPP-4
## Inhibitor"},
{"name": "Empagliflozin", "dosage": "10 mg once daily in the morning",
"precautions": "Risk of genital infections, DKA. Check eGFR.", "category":
"SGLT-2 Inhibitor"},
## ],
"Hypertension": [
{"name": "Amlodipine", "dosage": "5–10 mg once daily",
"precautions": "Pedal oedema possible. Avoid grapefruit juice.", "category":
"Calcium Channel Blocker"},
{"name": "Lisinopril", "dosage": "10–40 mg once daily",
"precautions": "Monitor potassium & creatinine. Avoid in pregnancy.",
"category": "ACE Inhibitor"},
{"name": "Losartan", "dosage": "50–100 mg once daily",
"precautions": "Monitor renal function. Avoid in pregnancy.", "category":
## "ARB"},
## ],
"Heart Attack": [
{"name": "Aspirin", "dosage": "300 mg stat, then 75 mg daily",
"precautions": "Give immediately. Avoid in active peptic ulcer.", "category":
"Antiplatelet"},
{"name": "Clopidogrel", "dosage": "300–600 mg loading, then 75 mg daily",
"precautions": "Check for drug interactions (PPIs).", "category":
"Antiplatelet"},
{"name": "Atorvastatin", "dosage": "40–80 mg at night",
"precautions": "Monitor liver enzymes. Avoid in active liver disease.",
"category": "Statin"},
## ],
"Asthma": [
{"name": "Salbutamol Inhaler", "dosage": "100–200 mcg (1–2 puffs) as needed",
"precautions": "Rinse mouth after use. Overuse may reduce effectiveness.",
"category": "SABA Bronchodilator"},
{"name": "Budesonide Inhaler", "dosage": "200–400 mcg twice daily",
"precautions": "Inhaled steroid – rinse mouth to prevent oral thrush.",

"category": "ICS"},
{"name": "Montelukast", "dosage": "10 mg once daily at night",
"precautions": "Monitor for mood/behaviour changes.", "category": "Leukotriene
## Antagonist"},
## ],
"Pneumonia": [
{"name": "Amoxicillin-Clavulanate", "dosage": "625 mg every 8 hrs for 7–10
days",
"precautions": "Check penicillin allergy. Take with food.", "category":
"Antibiotic"},
{"name": "Azithromycin", "dosage": "500 mg day 1, then 250 mg days 2–5",
"precautions": "Monitor QT interval. Avoid antacids within 2 hrs.", "category":
"Macrolide Antibiotic"},
## ],
"Tuberculosis": [
{"name": "HRZE Regimen (Isoniazid + Rifampicin + Pyrazinamide + Ethambutol)",
"dosage": "2 months intensive then 4 months continuation as per DOTS protocol",
"precautions": "Urine turns orange-red. Monitor liver function. Complete full
course.", "category": "Anti-TB"},
## ],
## "GERD": [
{"name": "Omeprazole", "dosage": "20 mg once daily before breakfast",
"precautions": "Long-term use: monitor Mg, B12. Avoid NSAIDs.", "category":
## "PPI"},
{"name": "Ranitidine (if available)", "dosage": "150 mg twice daily",
"precautions": "Take 30–60 min before meals.", "category": "H2 Blocker"},
## ],
## "UTI": [
{"name": "Nitrofurantoin", "dosage": "100 mg twice daily for 5–7 days",
"precautions": "Take with food. Avoid in renal impairment.", "category":
"Antibiotic"},
{"name": "Trimethoprim-Sulfamethoxazole", "dosage": "960 mg twice daily for 3–7
days",
"precautions": "Check local resistance patterns. Avoid in sulfa allergy.",
"category": "Antibiotic"},
## ],
"Migraine": [
{"name": "Sumatriptan", "dosage": "50 mg at onset; may repeat after 2 hrs (max
200 mg/day)",
"precautions": "Avoid in cardiovascular disease. Do not use with MAOIs.",
"category": "Triptan"},
{"name": "Ibuprofen", "dosage": "400–600 mg at onset",
"precautions": "Take with food. Avoid with peptic ulcer.", "category":
## "NSAID"},
## ],
"Depression": [
{"name": "Sertraline", "dosage": "50 mg once daily (titrate to 100–200 mg)",
"precautions": "Allow 4–6 weeks for full effect. Risk of serotonin syndrome
with MAOIs.", "category": "SSRI"},
{"name": "Fluoxetine", "dosage": "20 mg once daily in the morning",

"precautions": "Long half-life. Monitor for suicidal ideation initially.",
"category": "SSRI"},
## ],
"Anxiety Disorder": [
{"name": "Escitalopram", "dosage": "10 mg once daily",
"precautions": "Avoid abrupt discontinuation. Monitor QT interval.",
"category": "SSRI"},
{"name": "Buspirone", "dosage": "5 mg three times daily (titrate to 15–30
mg/day)",
"precautions": "Non-habit-forming. Takes 2–4 weeks for effect.", "category":
"Anxiolytic"},
## ],
"Arthritis": [
{"name": "Ibuprofen", "dosage": "400–800 mg three times daily with food",
"precautions": "Shortest effective duration. Avoid in renal/peptic ulcer
disease.", "category": "NSAID"},
{"name": "Methotrexate (RA)", "dosage": "7.5–25 mg weekly with folic acid",
"precautions": "Regular blood monitoring mandatory. Teratogenic.", "category":
## "DMARD"},
{"name": "Hydroxychloroquine", "dosage": "200–400 mg daily",
"precautions": "Annual eye check for retinopathy.", "category": "DMARD"},
## ],
"Hypothyroidism": [
{"name": "Levothyroxine", "dosage": "25–100 mcg once daily on empty stomach",
"precautions": "Take 30–60 min before breakfast. Monitor TSH every 6–12
months.", "category": "Thyroid Hormone"},
## ],
"Hyperthyroidism": [
{"name": "Carbimazole", "dosage": "10–40 mg daily in divided doses",
"precautions": "Monitor CBC – risk of agranulocytosis.", "category":
"Antithyroid"},
{"name": "Propranolol", "dosage": "40–80 mg three times daily for symptom
control",
"precautions": "Avoid in asthma. Do not stop abruptly.", "category": "Beta-
## Blocker"},
## ],
"Anemia": [
{"name": "Ferrous Sulphate", "dosage": "200 mg three times daily with Vitamin
## C",
"precautions": "May cause dark stools, constipation. Take on empty stomach if
tolerated.", "category": "Iron Supplement"},
{"name": "Folic Acid", "dosage": "5 mg once daily",
"precautions": "Required in pregnancy. Also given with Methotrexate.",
"category": "Vitamin"},
## ],
"Kidney Stones": [
{"name": "Tamsulosin", "dosage": "0.4 mg once daily (for stone passage)",
"precautions": "Risk of orthostatic hypotension. Take at bedtime.", "category":
"Alpha-Blocker"},
{"name": "Ketorolac", "dosage": "30 mg IM/IV for acute colic; max 5 days",

"precautions": "Short-term use only. Monitor renal function.", "category":
## "NSAID"},
## ],
"Jaundice": [
{"name": "Ursodeoxycholic Acid (UDCA)", "dosage": "8–10 mg/kg/day in 2–3
doses",
"precautions": "Monitor liver function tests. Avoid in complete biliary
obstruction.", "category": "Hepatoprotective"},
{"name": "Silymarin (Milk Thistle Extract)", "dosage": "140 mg three times
daily",
"precautions": "Adjunct only. Address underlying cause.", "category":
"Hepatoprotective"},
## ],
## }
Generic fallback
## GENERIC_RECOMMENDATION = [
{"name": "Consult a Physician", "dosage": "As prescribed",
"precautions": "This system provides guidance only. Always consult a qualified
doctor.", "category": "Advisory"},
## ]
class DrugRecommender:
def __init__(self, drug_db_path: str = "data/drug_details.json"):
self.drug_db = {}
self._load_database(drug_db_path)
`def _load_database(self, path: str):`
`"""Load JSON database if present, otherwise use built-in."""`
`if os.path.exists(path):`
## `try:`
`with open(path, "r") as f:`
`self.drug_db = json.load(f)`
`print(f"[DrugDB] Loaded {len(self.drug_db)} entries from
## {path}")`
## `return`
`except Exception as e:`
`print(f"[DrugDB] Error loading file: {e}")`
`# Merge built-in`
`self.drug_db = {**BUILT_IN_DRUGS}`
`print(f"[DrugDB] Using built-in database with {len(self.drug_db)}
diseases.")`
`def recommend(self, disease: str) -> List[Dict]:`
`"""Return drug recommendations for a disease (case-insensitive
match)."""`
`if not disease or disease == "Unknown":`
`return GENERIC_RECOMMENDATION`

## ===============================================================================
## =
FILE: flask_app.py
## ======================================================================
## ==========
import os
import sys
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
sys.path.append(os.path.join(os.path.dirname(__file__), 'server_code'))
import model
import severity
import drug_logic
import prediction
app = Flask(__name__)
CORS(app)
def map_severity(sev_string):
sev = sev_string.upper()
if "CRITICAL" in sev:
`# Exact match`
`if disease in self.drug_db:`
`return self.drug_db[disease]`
`# Case-insensitive match`
`lower = disease.lower()`
`for key, value in self.drug_db.items():`
`if key.lower() == lower:`
`return value`
`# Partial match`
`for key, value in self.drug_db.items():`
`if lower in key.lower() or key.lower() in lower:`
`return value`
`return GENERIC_RECOMMENDATION`
`def get_all_diseases(self) -> List[str]:`
`return list(self.drug_db.keys())`
`def save_database(self, path: str = "data/drug_details.json"):`
`os.makedirs(os.path.dirname(path), exist_ok=True)`
`with open(path, "w") as f:`
`json.dump(self.drug_db, f, indent=2)`
`print(f"[DrugDB] Saved to {path}")`

return {"level": "CRITICAL", "icon": "", "reason": "System detected critical
clinical markers.", "action": "Seek emergency medical care immediately. Call
## 108."}
elif "MODERATE" in sev:
return {"level": "MODERATE", "icon": "⚠", "reason": "System detected moderate
symptoms.", "action": "Consult a doctor within 24-48 hours. Rest and stay
hydrated."}
else:
return {"level": "NORMAL", "icon": "✅", "reason": "Symptoms appear mild
compared to critical thresholds.", "action": "Rest, hydrate, and monitor for
worsening."}
## @app.route('/')
def index():
return send_file('index.html')
@app.route('/api/analyze_symptoms', methods=['POST'])
def analyze_symptoms():
data = request.json
if not data or 'symptoms' not in data:
return jsonify({"error": "No symptoms provided"}), 400
@app.route('/api/analyze_report', methods=['POST'])
def analyze_report():
## `term_text = ", ".join(data['symptoms'])`
`disease, conf, top_preds =
model.predict_disease_with_probabilities(term_text)`
`sev_str = severity.analyze_severity(term_text)`
`drug_info = drug_logic.get_drug_info(disease)`
## `response = {`
## `"result": {`
`"disease": disease,`
`"confidence": conf`
## `},`
`"severity": map_severity(sev_str),`
## `"drugs": [{`
`"name": drug_info["drug"],`
`"category": "Recommended",`
`"dosage": drug_info["dosage"],`
`"precautions": drug_info["precautions"]`
## `}],`
`"topPreds": top_preds,`
## `"keywords": []`
## `}`
`return jsonify(response)`

text = request.form.get('text', '')
file = request.files.get('file')
`extracted_text = text`
`if file and file.filename:`
`ext = file.filename.split('.')[-1].lower() if '.' in file.filename else
## 'tmp'`
`with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as
tmp:`
## `file.save(tmp.name)`
`tmp_path = tmp.name`
## `try:`
`if ext == 'pdf':`
## `extracted_text += " " +
prediction.extract_text_from_pdf(tmp_path)`
## `else:`
## `extracted_text += " " +
prediction.extract_text_from_image(tmp_path)`
## `finally:`
`if os.path.exists(tmp_path):`
## `os.remove(tmp_path)`
`if not extracted_text.strip() or len(extracted_text.strip()) < 5:`
`return jsonify({"error": "Could not extract meaningful text from this
string or file."}), 400`
`disease, conf, top_preds =
model.predict_disease_with_probabilities(extracted_text)`
`sev_str = severity.analyze_severity(extracted_text)`
`drug_info = drug_logic.get_drug_info(disease)`
## `response = {`
## `"result": {`
`"disease": disease,`
`"confidence": conf`
## `},`
`"severity": map_severity(sev_str),`
## `"drugs": [{`
`"name": drug_info["drug"],`
`"category": "Recommended",`
`"dosage": drug_info["dosage"],`
`"precautions": drug_info["precautions"]`
## `}],`
`"topPreds": top_preds,`
## `"keywords": ["extracted", "report", "text"]`
## `}`
`return jsonify(response)`

if __name__ == '__main__':
app.run(debug=True, port=5000)
## ===============================================================================
## =
FILE: generate.py
## ======================================================================
## ==========
import os
output_file = "COPYRIGHT_SOURCE_CODE.txt"
extensions_to_include = {".py", ".html", ".css", ".js"}
exclude_dirs = {".git", "__pycache__", "models", ".vscode", "env", "venv"}
with open(output_file, "w", encoding="utf-8") as outfile:
outfile.write("MEDI SCAN PROJECT - COMPLETE SOURCE CODE\n\n")
for root, dirs, files in os.walk("."):
dirs[:] = [d for d in dirs if d not in exclude_dirs]
for f in files:
ext = os.path.splitext(f)[1].lower()
if ext in extensions_to_include:
filepath = os.path.join(root, f)
outfile.write(f"\n\n{'='*80}\n")
# Clean up filepath display
display_path = filepath.replace(".\\", "").replace("./", "")
outfile.write(f"FILE: {display_path}\n")
outfile.write(f"{'='*80}\n\n")
try:
with open(filepath, "r", encoding="utf-8", errors="ignore") as infile:
outfile.write(infile.read())
except Exception as e:
outfile.write(f"// Error reading file: {e}\n")
print(f"Project source code compiled successfully to {output_file}")
## ===============================================================================
## =
FILE: index.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html lang="en">
## <head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MediScan — Drug Recommendation System</title>
<link href="https://fonts.googleapis.com/css2?
family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,3
00&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,30

0&display=swap" rel="stylesheet">
## <style>
## :root {
## --bg: #050a0f;
## --surface: #0c1520;
## --surface2: #111d2e;
--border: rgba(0,180,255,0.12);
## --accent: #00b4ff;
## --accent2: #00ffc8;
## --danger: #ff4444;
## --warn: #ff9800;
## --ok: #00e676;
## --text: #e8f4ff;
## --muted: #5a7a9a;
--glow: 0 0 30px rgba(0,180,255,0.15);
## }
- { margin: 0; padding: 0; box-sizing: border-box; }
body {
font-family: 'DM Sans', sans-serif;
background: var(--bg);
color: var(--text);
min-height: 100vh;
overflow-x: hidden;
## }
/* ── Grid bg ── */
body::before {
content: '';
position: fixed; inset: 0;
background-image:
linear-gradient(rgba(0,180,255,0.03) 1px, transparent 1px),
linear-gradient(90deg, rgba(0,180,255,0.03) 1px, transparent 1px);
background-size: 40px 40px;
pointer-events: none;
z-index: 0;
## }
## /* ── Header ── */
header {
position: relative;
padding: 28px 48px;
display: flex;
align-items: center;
gap: 16px;
border-bottom: 1px solid var(--border);
backdrop-filter: blur(12px);
z-index: 10;
## }

## .logo-icon {
width: 44px; height: 44px;
background: linear-gradient(135deg, var(--accent), var(--accent2));
border-radius: 12px;
display: grid;
place-items: center;
font-size: 22px;
box-shadow: 0 0 20px rgba(0,180,255,0.3);
flex-shrink: 0;
## }
## .logo-text {
font-family: 'Syne', sans-serif;
font-size: 24px;
font-weight: 800;
letter-spacing: -0.5px;
background: linear-gradient(90deg, var(--accent), var(--accent2));
background-clip: text;
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
## }
## .logo-sub {
font-family: 'DM Mono', monospace;
font-size: 11px;
color: var(--muted);
text-transform: uppercase;
letter-spacing: 2px;
margin-top: 2px;
## }
## .header-badge {
margin-left: auto;
display: flex;
gap: 8px;
flex-wrap: wrap;
## }
## .badge {
font-family: 'DM Mono', monospace;
font-size: 10px;
padding: 4px 10px;
border-radius: 20px;
border: 1px solid var(--border);
color: var(--muted);
text-transform: uppercase;
letter-spacing: 1px;
## }
/* ── Main layout ── */
main {

position: relative;
z-index: 1;
max-width: 1200px;
margin: 0 auto;
padding: 48px 24px 80px;
## }
/* ── Section heading ── */
## .section-title {
font-family: 'Syne', sans-serif;
font-size: 13px;
font-weight: 600;
color: var(--accent);
text-transform: uppercase;
letter-spacing: 3px;
margin-bottom: 24px;
display: flex;
align-items: center;
gap: 10px;
## }
## .section-title::after {
content: '';
flex: 1;
height: 1px;
background: linear-gradient(90deg, var(--border), transparent);
## }
## /* ── Cards ── */
## .card {
background: var(--surface);
border: 1px solid var(--border);
border-radius: 16px;
padding: 28px;
box-shadow: var(--glow);
transition: border-color 0.3s;
## }
.card:hover { border-color: rgba(0,180,255,0.25); }
/* ── Two-col grid ── */
## .grid-2 {
display: grid;
grid-template-columns: 1fr 1fr;
gap: 24px;
## }
@media(max-width:768px){ .grid-2 { grid-template-columns: 1fr; } }
/* ── Input styles ── */
label {
display: block;
font-family: 'DM Mono', monospace;
font-size: 11px;

color: var(--muted);
text-transform: uppercase;
letter-spacing: 1.5px;
margin-bottom: 10px;
## }
## .symptom-input-wrap {
display: flex;
gap: 8px;
margin-bottom: 12px;
## }
input[type="text"] {
width: 100%;
background: var(--bg);
border: 1px solid var(--border);
border-radius: 10px;
padding: 12px 16px;
color: var(--text);
font-family: 'DM Sans', sans-serif;
font-size: 14px;
outline: none;
transition: border-color 0.3s, box-shadow 0.3s;
## }
input[type="text"]:focus {
border-color: var(--accent);
box-shadow: 0 0 0 3px rgba(0,180,255,0.1);
## }
input[type="text"]::placeholder { color: var(--muted); }
## .btn {
font-family: 'Syne', sans-serif;
font-size: 13px;
font-weight: 700;
padding: 12px 24px;
border-radius: 10px;
border: none;
cursor: pointer;
letter-spacing: 0.5px;
transition: all 0.2s;
white-space: nowrap;
## }
## .btn-primary {
background: linear-gradient(135deg, var(--accent), var(--accent2));
color: #000;
## }
## .btn-primary:hover {
transform: translateY(-1px);
box-shadow: 0 6px 20px rgba(0,180,255,0.3);

## }
.btn-primary:active { transform: translateY(0); }
## .btn-ghost {
background: transparent;
border: 1px solid var(--border);
color: var(--muted);
## }
## .btn-ghost:hover {
border-color: var(--accent);
color: var(--accent);
## }
/* ── Symptom tags ── */
## .tag-area {
display: flex;
flex-wrap: wrap;
gap: 8px;
min-height: 44px;
padding: 10px;
background: var(--bg);
border: 1px solid var(--border);
border-radius: 10px;
margin-bottom: 16px;
## }
## .tag {
display: inline-flex;
align-items: center;
gap: 6px;
background: rgba(0,180,255,0.1);
border: 1px solid rgba(0,180,255,0.2);
color: var(--accent);
font-family: 'DM Mono', monospace;
font-size: 12px;
padding: 4px 10px;
border-radius: 20px;
animation: tagIn 0.2s ease;
## }
@keyframes tagIn {
from { transform: scale(0.8); opacity: 0; }
to { transform: scale(1); opacity: 1; }
## }
## .tag-remove {
background: none;
border: none;
color: var(--muted);
cursor: pointer;
font-size: 14px;

line-height: 1;
padding: 0;
transition: color 0.2s;
## }
.tag-remove:hover { color: var(--danger); }
/* ── Quick-select symptom pills ── */
## .quick-pills {
display: flex;
flex-wrap: wrap;
gap: 6px;
margin-bottom: 20px;
## }
## .pill {
font-family: 'DM Mono', monospace;
font-size: 11px;
padding: 5px 12px;
border-radius: 20px;
border: 1px solid rgba(0,255,200,0.2);
background: rgba(0,255,200,0.05);
color: var(--accent2);
cursor: pointer;
transition: all 0.2s;
## }
## .pill:hover {
background: rgba(0,255,200,0.15);
border-color: var(--accent2);
transform: translateY(-1px);
## }
## .pill.active {
background: rgba(0,255,200,0.2);
border-color: var(--accent2);
## }
## /* ── Divider ── */
## .divider {
display: flex;
align-items: center;
gap: 12px;
margin: 20px 0;
## }
## .divider::before, .divider::after {
content: ''; flex: 1;
height: 1px;
background: var(--border);
## }
.divider span {
font-family: 'DM Mono', monospace;
font-size: 11px;

color: var(--muted);
## }
/* ── File upload ── */
## .file-drop {
border: 2px dashed var(--border);
border-radius: 12px;
padding: 32px;
text-align: center;
cursor: pointer;
transition: all 0.3s;
background: var(--bg);
position: relative;
## }
## .file-drop:hover, .file-drop.drag-over {
border-color: var(--accent);
background: rgba(0,180,255,0.03);
## }
.file-drop input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.file-drop-icon { font-size: 32px; margin-bottom: 8px; }
.file-drop-text { color: var(--muted); font-size: 13px; }
.file-drop-text strong { color: var(--accent); }
/* ── Results panel ── */
## #results-panel {
display: none;
margin-top: 40px;
animation: slideUp 0.4s ease;
## }
@keyframes slideUp {
from { transform: translateY(20px); opacity: 0; }
to { transform: translateY(0); opacity: 1; }
## }
/* ── Disease prediction card ── */
## .prediction-card {
background: var(--surface2);
border: 1px solid var(--border);
border-radius: 16px;
padding: 24px;
margin-bottom: 24px;
position: relative;
overflow: hidden;
## }
## .prediction-card::before {
content: '';
position: absolute;
top: 0; left: 0; right: 0;
height: 2px;

background: linear-gradient(90deg, var(--accent), var(--accent2));
## }
## .disease-name {
font-family: 'Syne', sans-serif;
font-size: 32px;
font-weight: 800;
background: linear-gradient(135deg, var(--text), var(--accent));
background-clip: text;
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
margin-bottom: 8px;
## }
## .confidence-bar-wrap {
display: flex;
align-items: center;
gap: 12px;
margin: 12px 0;
## }
## .confidence-bar {
flex: 1;
height: 6px;
background: var(--bg);
border-radius: 3px;
overflow: hidden;
## }
## .confidence-fill {
height: 100%;
background: linear-gradient(90deg, var(--accent), var(--accent2));
border-radius: 3px;
transition: width 1s cubic-bezier(0.4,0,0.2,1);
## }
## .confidence-pct {
font-family: 'DM Mono', monospace;
font-size: 12px;
color: var(--accent2);
min-width: 40px;
## }
/* ── Severity badge ── */
## .severity-badge {
display: inline-flex;
align-items: center;
gap: 8px;
padding: 8px 16px;
border-radius: 25px;
font-family: 'Syne', sans-serif;
font-size: 13px;
font-weight: 700;

letter-spacing: 1px;
text-transform: uppercase;
## }
.severity-CRITICAL { background: rgba(255,68,68,0.15); border: 1px solid
rgba(255,68,68,0.4); color: var(--danger); }
.severity-MODERATE { background: rgba(255,152,0,0.15); border: 1px solid
rgba(255,152,0,0.4); color: var(--warn); }
.severity-NORMAL { background: rgba(0,230,118,0.12); border: 1px solid
rgba(0,230,118,0.3); color: var(--ok); }
/* ── Drug recommendation cards ── */
## .drug-grid {
display: grid;
grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
gap: 16px;
margin-top: 16px;
## }
## .drug-card {
background: var(--surface);
border: 1px solid var(--border);
border-radius: 14px;
padding: 20px;
position: relative;
overflow: hidden;
animation: fadeIn 0.3s ease;
transition: transform 0.2s, border-color 0.2s;
## }
## .drug-card:hover {
transform: translateY(-3px);
border-color: rgba(0,180,255,0.3);
## }
@keyframes fadeIn {
from { opacity: 0; transform: translateY(8px); }
to { opacity: 1; transform: translateY(0); }
## }
## .drug-category {
font-family: 'DM Mono', monospace;
font-size: 10px;
color: var(--accent2);
text-transform: uppercase;
letter-spacing: 2px;
margin-bottom: 8px;
## }
## .drug-name {
font-family: 'Syne', sans-serif;
font-size: 16px;
font-weight: 700;

color: var(--text);
margin-bottom: 12px;
line-height: 1.3;
## }
## .drug-info-row {
display: flex;
gap: 6px;
margin-bottom: 8px;
font-size: 13px;
line-height: 1.5;
## }
## .info-label {
font-family: 'DM Mono', monospace;
font-size: 10px;
color: var(--muted);
text-transform: uppercase;
letter-spacing: 1px;
margin-top: 1px;
flex-shrink: 0;
## }
## .info-value {
color: rgba(232,244,255,0.8);
font-size: 13px;
## }
## .precaution-text {
background: rgba(255,152,0,0.07);
border-left: 3px solid rgba(255,152,0,0.4);
border-radius: 0 8px 8px 0;
padding: 8px 12px;
font-size: 12px;
color: rgba(255,152,0,0.9);
margin-top: 10px;
line-height: 1.5;
## }
## /* ── Loader ── */
## .loader {
display: none;
flex-direction: column;
align-items: center;
gap: 16px;
padding: 40px;
## }
.loader.active { display: flex; }
## .spinner {
width: 48px; height: 48px;

border: 3px solid var(--border);
border-top-color: var(--accent);
border-radius: 50%;
animation: spin 0.8s linear infinite;
## }
@keyframes spin { to { transform: rotate(360deg); } }
## .loader-text {
font-family: 'DM Mono', monospace;
font-size: 13px;
color: var(--muted);
## }
/* ── Top predictions list ── */
## .top-preds {
display: flex;
flex-direction: column;
gap: 8px;
margin-top: 8px;
## }
## .pred-item {
display: flex;
align-items: center;
gap: 10px;
font-size: 13px;
## }
## .pred-bar {
flex: 1;
height: 4px;
background: var(--bg);
border-radius: 2px;
overflow: hidden;
## }
## .pred-fill {
height: 100%;
background: var(--border);
border-radius: 2px;
transition: width 1s ease;
## }
.pred-item:first-child .pred-fill { background: var(--accent); }
.pred-item:nth-child(2) .pred-fill { background: rgba(0,180,255,0.5); }
.pred-name { min-width: 180px; color: rgba(232,244,255,0.7); }
.pred-pct { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--
muted); min-width: 40px; text-align: right; }
## /* ── Separator ── */
## .results-divider {
height: 1px;
background: var(--border);

margin: 32px 0;
## }
/* ── Action text ── */
## .action-box {
display: flex;
gap: 12px;
align-items: flex-start;
padding: 14px 16px;
border-radius: 10px;
margin-top: 16px;
font-size: 13px;
line-height: 1.6;
## }
.action-icon { font-size: 18px; flex-shrink: 0; }
.action-CRITICAL { background: rgba(255,68,68,0.08); border: 1px solid
rgba(255,68,68,0.2); }
.action-MODERATE { background: rgba(255,152,0,0.08); border: 1px solid
rgba(255,152,0,0.2); }
.action-NORMAL { background: rgba(0,230,118,0.06); border: 1px solid
rgba(0,230,118,0.2); }
## /* ── Footer ── */
footer {
position: relative;
z-index: 1;
text-align: center;
padding: 32px;
border-top: 1px solid var(--border);
font-family: 'DM Mono', monospace;
font-size: 11px;
color: var(--muted);
letter-spacing: 1px;
## }
## /* ── Disclaimer ── */
## .disclaimer {
background: rgba(255,152,0,0.06);
border: 1px solid rgba(255,152,0,0.15);
border-radius: 10px;
padding: 14px 18px;
font-size: 12px;
color: rgba(255,152,0,0.8);
margin-bottom: 32px;
display: flex;
gap: 10px;
align-items: center;
## }
## </style>

## </head>
## <body>
## <header>
<div class="logo-icon">⚕</div>
## <div>
<div class="logo-text">MediScan</div>
<div class="logo-sub">Drug Recommendation System v2.0</div>
## </div>
<div class="header-badge">
<span class="badge">Random Forest ML</span>
<span class="badge">NLP · TF-IDF</span>
<span class="badge">OCR · PDF</span>
<span class="badge">Flask API</span>
## </div>
## </header>
## <main>
<div class="disclaimer">
⚠ &nbsp;<strong>For educational and demonstration purposes only.</strong>
Always consult a qualified medical professional for diagnosis and treatment.
## </div>
## <!-- ── INPUT SECTION ── -->
<div class="section-title">Symptom Input</div>
<div class="grid-2" style="margin-bottom:32px;">
## `<!-- Left: Symptom Entry -->`
`<div class="card">`
`<label>Enter Symptoms</label>`
`<div class="symptom-input-wrap">`
`<input type="text" id="symptomInput" placeholder="e.g. fever, chest
pain..." />`
`<button class="btn btn-primary" onclick="addSymptom()">Add</button>`
## `</div>`
`<label>Added symptoms</label>`
`<div class="tag-area" id="tagArea">`
`<span id="tagPlaceholder" style="color:var(--muted);font-
size:13px;padding:4px;">No symptoms added yet...</span>`
## `</div>`
`<div class="quick-pills" id="quickPills">`
`<!-- populated by JS -->`
## `</div>`
`<div style="display:flex; gap:8px; flex-wrap:wrap;">`
`<button class="btn btn-primary" style="flex:1;"
onclick="runAnalysis()"> Analyse Symptoms</button>`

## </div>
## <!-- ── LOADER ── -->
<div class="loader" id="loader">
<div class="spinner"></div>
<div class="loader-text" id="loaderText">Processing symptoms...</div>
## </div>
## <!-- ── RESULTS ── -->
<div id="results-panel">
`<button class="btn btn-ghost" onclick="clearAll()">Clear</button>`
## `</div>`
## `</div>`
## `<!-- Right: Report Upload -->`
`<div class="card">`
`<label>Upload Medical Report</label>`
`<div class="file-drop" id="fileDrop">`
`<input type="file" id="fileInput"
accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp" onchange="handleFileSelect(event)"
## />`
`<div class="file-drop-icon"></div>`
`<div class="file-drop-text">`
`<strong>Click or drag</strong> to upload a report<br>`
`<span style="font-size:11px; margin-top:4px; display:block; color:
var(--muted)">Supports: PDF, PNG, JPG, TIFF</span>`
## `</div>`
## `</div>`
`<div id="fileStatus" style="display:none; margin-top:12px; font-
family:'DM Mono',monospace; font-size:12px; color:var(--accent2);">`
`✓ File ready for analysis`
## `</div>`
`<div class="divider"><span>or paste report text</span></div>`
`<label>Free Text / Paste Report</label>`
`<textarea id="reportText" rows="4"`
`style="width:100%; background:var(--bg); border:1px solid var(--
border); border-radius:10px; padding:12px 16px; color:var(--text); font-
family:'DM Sans',sans-serif; font-size:13px; resize:vertical; outline:none;
line-height:1.5;"`
`placeholder="Paste extracted text from a lab report, clinical notes...">
## </textarea>`
`<button class="btn btn-primary" style="width:100%; margin-top:12px;"
onclick="runReportAnalysis()"> Analyse Report</button>`
## `</div>`

## </div>
## </main>
`<div class="section-title">Diagnosis Results</div>`
`<!-- Disease prediction -->`
`<div class="prediction-card" id="predictionCard">`
`<div style="display:flex; justify-content:space-between; align-
items:flex-start; flex-wrap:wrap; gap:12px;">`
## `<div>`
`<div style="font-family:'DM Mono',monospace; font-size:11px;
color:var(--muted); text-transform:uppercase; letter-spacing:2px; margin-
bottom:6px;">Predicted Disease</div>`
`<div class="disease-name" id="diseaseName">–</div>`
## `</div>`
`<div id="severityBadge"></div>`
## `</div>`
`<div class="confidence-bar-wrap">`
`<span style="font-family:'DM Mono',monospace; font-size:11px;
color:var(--muted);">Confidence</span>`
`<div class="confidence-bar">`
`<div class="confidence-fill" id="confidenceFill" style="width:0%">
## </div>`
## `</div>`
`<span class="confidence-pct" id="confidencePct">0%</span>`
## `</div>`
`<div id="actionBox"></div>`
## `</div>`
`<!-- Top predictions -->`
`<div class="card" style="margin-bottom:24px;">`
`<label>Top Differential Diagnoses</label>`
`<div class="top-preds" id="topPreds"></div>`
## `</div>`
`<!-- Drug recommendations -->`
`<div class="section-title">Drug Recommendations</div>`
`<div class="drug-grid" id="drugGrid"></div>`
`<!-- Keywords (for report mode) -->`
`<div id="keywordsSection" style="display:none; margin-top:32px;">`
`<div class="results-divider"></div>`
`<div class="section-title">Extracted Keywords</div>`
`<div class="tag-area" id="keywordTags"></div>`
## `</div>`

## <footer>
MediScan · Drug Recommendation System · Built with Random Forest · Flask ·
pdfplumber · pytesseract
## </footer>
## <script>
## // ── State ──────────────────────────────────────────────────────────────────
const symptoms = [];
const QUICK_SYMPTOMS = [
"Fever","Cough","Headache","Chest Pain","Shortness of Breath",
"Nausea","Vomiting","Fatigue","Dizziness","Joint Pain",
"High Glucose","High BP","Sore Throat","Rash","Body Ache"
## ];
// ── Local drug / disease database (mirrors Python backend) ─────────────────
const DISEASE_DB = {
"Influenza": { color: "#00b4ff", icon: "蠟" },
"Common Cold": { color: "#00b4ff", icon: "蠟" },
"Dengue": { color: "#ff9800", icon: "烈" },
"Malaria": { color: "#ff9800", icon: "烈" },
"Asthma": { color: "#00b4ff", icon: "贈" },
"Pneumonia": { color: "#ff9800", icon: "贈" },
"Tuberculosis": { color: "#ff4444", icon: "贈" },
"Heart Attack": { color: "#ff4444", icon: "❤️" },
"Hypertension": { color: "#ff9800", icon: "喝" },
"Diabetes": { color: "#ff9800", icon: "喝" },
"Type 2 Diabetes": { color: "#ff9800", icon: "喝" },
"Migraine": { color: "#a78bfa", icon: "易" },
"Depression": { color: "#a78bfa", icon: "易" },
"Arthritis": { color: "#00ffc8", icon: "領" },
"Anemia": { color: "#ff9800", icon: "喝" },
"UTI": { color: "#00b4ff", icon: "" },
"GERD": { color: "#00ffc8", icon: "變" },
"Hypothyroidism": { color: "#00ffc8", icon: "曆" },
"Hyperthyroidism": { color: "#ff9800", icon: "曆" },
"Jaundice": { color: "#ff9800", icon: "" },
"Kidney Stones": { color: "#ff4444", icon: "齃" },
## };
const DRUG_DB = {
"Influenza": [
{ name: "Oseltamivir (Tamiflu)", category: "Antiviral", dosage: "75 mg twice
daily for 5 days", precautions: "Start within 48h of symptom onset." },
{ name: "Paracetamol", category: "Analgesic/Antipyretic", dosage: "500–1000 mg
every 6–8 hrs", precautions: "Avoid alcohol. Caution in liver disease." },
## ],
"Common Cold": [
{ name: "Cetirizine", category: "Antihistamine", dosage: "10 mg once daily",
precautions: "May cause drowsiness. Avoid driving." },
{ name: "Pseudoephedrine", category: "Decongestant", dosage: "60 mg every 4–6

hrs", precautions: "Avoid in hypertension." },
## ],
"Dengue": [
{ name: "Paracetamol", category: "Analgesic/Antipyretic", dosage: "500–1000 mg
every 6 hrs", precautions: "AVOID NSAIDs/Aspirin – bleeding risk." },
{ name: "ORS", category: "Supportive", dosage: "As directed for hydration",
precautions: "Monitor platelet count regularly." },
## ],
"Diabetes": [
{ name: "Metformin", category: "Biguanide", dosage: "500–1000 mg twice daily
with meals", precautions: "Avoid in renal failure. Monitor B12." },
{ name: "Glipizide", category: "Sulfonylurea", dosage: "5 mg once daily before
breakfast", precautions: "Risk of hypoglycaemia." },
{ name: "Insulin Glargine", category: "Insulin", dosage: "10–20 units subcut at
bedtime", precautions: "Rotate injection sites." },
## ],
"Type 2 Diabetes": [
{ name: "Metformin", category: "Biguanide", dosage: "500–2000 mg daily with
meals", precautions: "Check renal function." },
{ name: "Empagliflozin", category: "SGLT-2 Inhibitor", dosage: "10 mg once
daily in the morning", precautions: "Risk of genital infections." },
## ],
"Hypertension": [
{ name: "Amlodipine", category: "Calcium Channel Blocker", dosage: "5–10 mg
once daily", precautions: "Pedal oedema possible. Avoid grapefruit." },
{ name: "Lisinopril", category: "ACE Inhibitor", dosage: "10–40 mg once daily",
precautions: "Monitor K+ and creatinine. Avoid in pregnancy." },
## ],
"Heart Attack": [
{ name: "Aspirin", category: "Antiplatelet", dosage: "300 mg stat then 75 mg
daily", precautions: "Give immediately. Avoid with active ulcer." },
{ name: "Atorvastatin", category: "Statin", dosage: "40–80 mg at night",
precautions: "Monitor liver enzymes." },
## ],
"Asthma": [
{ name: "Salbutamol Inhaler", category: "SABA Bronchodilator", dosage: "100–200
mcg as needed", precautions: "Rinse mouth after use." },
{ name: "Budesonide Inhaler", category: "ICS", dosage: "200–400 mcg twice
daily", precautions: "Rinse mouth to prevent oral thrush." },
## ],
"Pneumonia": [
{ name: "Amoxicillin-Clavulanate", category: "Antibiotic", dosage: "625 mg
every 8 hrs for 7–10 days", precautions: "Check penicillin allergy." },
{ name: "Azithromycin", category: "Macrolide Antibiotic", dosage: "500 mg day
1, 250 mg days 2–5", precautions: "Monitor QT interval." },
## ],
"Migraine": [
{ name: "Sumatriptan", category: "Triptan", dosage: "50 mg at onset",
precautions: "Avoid in cardiovascular disease." },
{ name: "Ibuprofen", category: "NSAID", dosage: "400–600 mg at onset",

precautions: "Take with food." },
## ],
"Malaria": [
{ name: "Artemether-Lumefantrine", category: "Antimalarial", dosage: "4 tabs at
0,8,24,36,48,60 hrs", precautions: "Take with food. Monitor cardiac." },
## ],
## "UTI": [
{ name: "Nitrofurantoin", category: "Antibiotic", dosage: "100 mg twice daily
for 5–7 days", precautions: "Take with food. Avoid in renal impairment." },
## ],
## "GERD": [
{ name: "Omeprazole", category: "PPI", dosage: "20 mg once daily before
breakfast", precautions: "Long-term: monitor Mg, B12." },
## ],
"Depression": [
{ name: "Sertraline", category: "SSRI", dosage: "50 mg once daily (titrate to
200 mg)", precautions: "Allow 4–6 weeks for full effect." },
## ],
"Arthritis": [
{ name: "Ibuprofen", category: "NSAID", dosage: "400–800 mg three times daily
with food", precautions: "Shortest effective duration." },
{ name: "Methotrexate", category: "DMARD", dosage: "7.5–25 mg weekly with folic
acid", precautions: "Regular blood monitoring. Teratogenic." },
## ],
"Hypothyroidism": [
{ name: "Levothyroxine", category: "Thyroid Hormone", dosage: "25–100 mcg once
daily on empty stomach", precautions: "Take 30–60 min before breakfast." },
## ],
"Anemia": [
{ name: "Ferrous Sulphate", category: "Iron Supplement", dosage: "200 mg three
times daily with Vit C", precautions: "May cause dark stools, constipation." },
## ],
## };
const DEFAULT_DRUGS = [
{ name: "Consult a Physician", category: "Advisory", dosage: "As prescribed by
doctor", precautions: "Always seek qualified medical advice." },
## ];
// ── Symptom → Disease rule engine (mirrors Python) ─────────────────────────
function predictDisease(syms) {
const text = syms.join(" ").toLowerCase();
const t = s => text.includes(s);
// Critical patterns first
if (t("chest pain") && (t("arm pain") || t("sweating") || t("jaw"))) return {
disease: "Heart Attack", confidence: 0.92 };
if ((t("chest pain") || t("shortness of breath")) && t("wheezing")) return {
disease: "Asthma", confidence: 0.85 };
if (t("high glucose") || t("polyuria") || (t("excessive thirst") && t("frequent

urination"))) return { disease: "Type 2 Diabetes", confidence: 0.88 };
if (t("high blood pressure") || t("elevated bp") || t("high bp")) return {
disease: "Hypertension", confidence: 0.83 };
if (t("fever") && t("joint pain") && t("rash")) return { disease: "Dengue",
confidence: 0.84 };
if (t("fever") && t("chills") && t("sweating")) return { disease: "Malaria",
confidence: 0.79 };
if (t("severe headache") && (t("sensitivity") || t("nausea") || t("aura")))
return { disease: "Migraine", confidence: 0.86 };
if (t("burning urination") || (t("frequent urination") && t("pelvic pain")))
return { disease: "UTI", confidence: 0.87 };
if (t("heartburn") || t("acid reflux") || t("regurgitation")) return { disease:
"GERD", confidence: 0.82 };
if (t("weight gain") && t("fatigue") && (t("cold") || t("constipation") ||
t("dry skin"))) return { disease: "Hypothyroidism", confidence: 0.78 };
if (t("sadness") || t("hopelessness") || (t("fatigue") && t("sleep"))) return {
disease: "Depression", confidence: 0.74 };
if (t("joint") && t("stiffness") && t("swelling")) return { disease:
"Arthritis", confidence: 0.77 };
if (t("pallor") || (t("fatigue") && t("weakness") && t("breathless"))) return {
disease: "Anemia", confidence: 0.73 };
if (t("fever") && (t("cough") && t("body ache"))) return { disease:
"Influenza", confidence: 0.81 };
if (t("cough") && (t("shortness of breath") || t("mucus"))) return { disease:
"Pneumonia", confidence: 0.76 };
if (t("yellow") || t("jaundice") || t("dark urine")) return { disease:
"Jaundice", confidence: 0.85 };
if (t("back pain") && t("blood in urine")) return { disease: "Kidney Stones",
confidence: 0.88 };
if (t("fever") || t("cough") || t("sore throat")) return { disease: "Common
Cold", confidence: 0.65 };
return { disease: "Influenza", confidence: 0.55 };
## }
function generateTopPreds(mainDisease, conf) {
const all = Object.keys(DRUG_DB);
const others = all.filter(d => d !== mainDisease).sort(() => Math.random() -
## 0.5).slice(0, 4);
const preds = [{ disease: mainDisease, confidence: conf }];
let remaining = 1 - conf;
others.forEach((d, i) => {
const c = i === 0 ? remaining * 0.5 : remaining * (0.3 - i * 0.05);
remaining -= c;
preds.push({ disease: d, confidence: Math.max(0.01, c) });
## });
return preds;
## }

function detectSeverity(syms) {
const text = syms.join(" ").toLowerCase();
const critical = ["chest pain","heart
attack","stroke","paralysis","anaphylaxis","suicidal","severe bleeding","very
high glucose","spo2 low","fainting","meningitis","seizure"];
const moderate =
## ["fever","cough","headache","nausea","vomiting","diarrhea","fatigue","weakness"
,"dizziness","rash","swelling","shortness of breath","high bp","high blood
pressure"];
for (const c of critical) {
if (text.includes(c)) return { level: "CRITICAL", icon: "", reason:
## Critical
indicator: ${c}
, action: "Seek emergency medical care immediately. Call 108." };
## }
const mods = moderate.filter(m => text.includes(m));
if (mods.length >= 3) return { level: "MODERATE", icon: "⚠", reason:
## Multiple
moderate symptoms: ${mods.slice(0,3).join(", ")}
, action: "Consult a doctor within
24–48 hours. Rest and stay hydrated." };
if (mods.length > 0) return { level: "MODERATE", icon: "⚠", reason:
## Symptom
detected: ${mods[0]}
, action: "Schedule a doctor visit. Monitor symptoms." };
return { level: "NORMAL", icon: "✅", reason: "Symptoms appear mild", action:
"Rest, hydrate, and monitor for worsening." };
## }
// ── UI helpers ─────────────────────────────────────────────────────────────
function buildQuickPills() {
const wrap = document.getElementById("quickPills");
QUICK_SYMPTOMS.forEach(s => {
const p = document.createElement("span");
p.className = "pill";
p.textContent = s;
p.onclick = () => {
p.classList.toggle("active");
if (p.classList.contains("active")) addSymptomText(s);
else removeSymptomText(s);
## };
wrap.appendChild(p);
## });
## }
function renderTags() {
const area = document.getElementById("tagArea");
const placeholder = document.getElementById("tagPlaceholder");
area.innerHTML = "";
if (symptoms.length === 0) {
area.appendChild(Object.assign(document.createElement("span"), {
textContent: "No symptoms added yet...",
style: "color:var(--muted);font-size:13px;padding:4px;"
## }));
return;

## }
symptoms.forEach((s, i) => {
const tag = document.createElement("span");
tag.className = "tag";
tag.innerHTML =
s<buttonclass=′′tag−remove′′onclick=′′removeSymptomIdx(
## {i})">×
## ;
area.appendChild(tag);
## });
## }
function addSymptom() {
const input = document.getElementById("symptomInput");
const val = input.value.trim();
if (val) { addSymptomText(val); input.value = ""; }
## }
function addSymptomText(text) {
const lower = text.toLowerCase();
if (!symptoms.find(s => s.toLowerCase() === lower)) {
symptoms.push(text);
renderTags();
## }
## }
function removeSymptomText(text) {
const idx = symptoms.findIndex(s => s.toLowerCase() === text.toLowerCase());
if (idx !== -1) symptoms.splice(idx, 1);
renderTags();
## }
function removeSymptomIdx(idx) {
const removed = symptoms.splice(idx, 1)[0];
renderTags();
// Deactivate pill if present
document.querySelectorAll(".pill").forEach(p => {
if (p.textContent.toLowerCase() === removed.toLowerCase())
p.classList.remove("active");
## });
## }
function clearAll() {
symptoms.length = 0;
renderTags();
document.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
document.getElementById("results-panel").style.display = "none";
## }
## // ── Analysis ───────────────────────────────────────────────────────────────
function showLoader(msg) {
document.getElementById("loader").classList.add("active");
document.getElementById("loaderText").textContent = msg;

document.getElementById("results-panel").style.display = "none";
## }
function hideLoader() {
document.getElementById("loader").classList.remove("active");
## }
async function runAnalysis() {
if (symptoms.length === 0) {
alert("Please add at least one symptom.");
return;
## }
showLoader("Running ML prediction engine...");
try {
const res = await fetch("/api/analyze_symptoms", {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify({ symptoms })
## });
const data = await res.json();
if (res.ok) {
showResults(data.result, data.severity, data.drugs, data.topPreds,
data.keywords);
} else {
alert("Error: " + data.error);
## }
} catch(e) {
alert("Connection error.");
## }
hideLoader();
## }
async function runReportAnalysis() {
const text = document.getElementById("reportText").value.trim();
const fileInput = document.getElementById("fileInput");
const hasFile = fileInput.files.length > 0;
if (!text && !hasFile) {
alert("Please paste report text or upload a file.");
return;
## }
showLoader("Extracting and analysing report via OCR/NLP...");
try {
const formData = new FormData();
formData.append("text", text);
if(hasFile) formData.append("file", fileInput.files[0]);
`const res = await fetch("/api/analyze_report", {`
`method: "POST",`
`body: formData`

} catch(e) {
alert("Connection error.");
## }
hideLoader();
## }
function showResults(result, severity, drugs, topPreds, keywords) {
// Disease name
document.getElementById("diseaseName").textContent = result.disease;
## // Confidence
const pct = Math.round(result.confidence * 100);
setTimeout(() => {
document.getElementById("confidenceFill").style.width = pct + "%";
document.getElementById("confidencePct").textContent = pct + "%";
## }, 100);
// Severity badge
const badge = document.getElementById("severityBadge");
badge.innerHTML =
## ${severity.icon} ${severity.level}
## ;
// Action box
const actionBox = document.getElementById("actionBox");
actionBox.innerHTML = ``
severity.icon</span>‵‵<div>‵‵<strongstyle=′′color:var(−−text)′′>
## {severity.reason}
## ${severity.action}
## ;
// Top predictions
const topEl = document.getElementById("topPreds");
topEl.innerHTML = topPreds.map((p, i) => ``
i+1.$p.disease</span>‵‵<divclass=′′pred−bar′′><divclass=′′pred−fill′′style=′′width
{Math.round(p.confidence100)}%">
${Math.round(p.confidence
## ).join("");
## `});`
`const data = await res.json();`
## `if(res.ok){`
`showResults(data.result, data.severity, data.drugs, data.topPreds,
data.keywords);`
`} else {`
`alert("Error: " + data.error);`
## `}`

setTimeout(() => {
document.querySelectorAll(".pred-fill").forEach(el => {
el.style.width = el.dataset.w;
## });
## }, 200);
// Drug cards
const grid = document.getElementById("drugGrid");
grid.innerHTML = drugs.map((d, i) => ``
d.category</div>‵‵<divclass=′′drug−name′′>{d.name}
## Dose${d.dosage}
## ⚠ ${d.precautions}
## ).join("");
// Keywords section
if (keywords && keywords.length > 0) {
document.getElementById("keywordsSection").style.display = "block";
const kwTags = document.getElementById("keywordTags");
kwTags.innerHTML = keywords.map(k =>
## ${k}
## ).join("");
} else {
document.getElementById("keywordsSection").style.display = "none";
## }
document.getElementById("results-panel").style.display = "block";
document.getElementById("results-panel").scrollIntoView({ behavior: "smooth",
block: "start" });
## }
// ── File handling ──────────────────────────────────────────────────────────
function handleFileSelect(e) {
if (e.target.files.length > 0) {
document.getElementById("fileStatus").style.display = "block";
document.getElementById("fileStatus").textContent =
## ✓ ${e.target.files[0].name}
## ;
## }
## }
document.addEventListener("DOMContentLoaded", () => {
buildQuickPills();
// Enter key adds symptom
document.getElementById("symptomInput").addEventListener("keydown", e => {
if (e.key === "Enter") addSymptom();
## });
## // Drag-and-drop
const drop = document.getElementById("fileDrop");

drop.addEventListener("dragover", e => { e.preventDefault();
drop.classList.add("drag-over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("drag-over"));
drop.addEventListener("drop", e => {
e.preventDefault();
drop.classList.remove("drag-over");
const file = e.dataTransfer.files[0];
if (file) {
document.getElementById("fileStatus").style.display = "block";
document.getElementById("fileStatus").textContent =
## ✓ ${file.name}
## ;
## }
## });
## });
## </script>
## </body>
## </html>
## ===============================================================================
## =
FILE: predict_engine.py
## ======================================================================
## ==========
## """
## Disease Prediction Engine
Uses Random Forest and Logistic Regression trained on symptom-disease dataset
## """
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
import pickle
import os
import json
class DiseasePredictionEngine:
def __init__(self, model_path="models/disease_model.pkl",
data_path="data/symptoms_disease.csv"):
self.model_path = model_path
self.data_path = data_path
self.model = None
self.vectorizer = None
self.label_encoder = LabelEncoder()
self.all_symptoms = []

`os.makedirs("models", exist_ok=True)`
## `self._load_or_train()`
## `# ── Data
## ──────────────────────────────────────────────────────────────────`
## `def _load_or_train(self):`
`if os.path.exists(self.model_path):`
## `self._load_model()`
## `else:`
## `self._train_model()`
## `def _get_training_data(self):`
`"""Return a rich symptom→disease dataset."""`
## `records = [`
## `# Flu / Cold`
`("fever cough sore throat runny nose fatigue body ache headache",
"Influenza"),`
`("sneezing runny nose mild fever congestion sore throat", "Common
## Cold"),`
`("high fever severe headache muscle pain joint pain rash",
"Dengue"),`
`("fever chills sweating headache nausea vomiting", "Malaria"),`
## `# Respiratory`
`("persistent cough shortness of breath wheezing chest tightness",
"Asthma"),`
`("cough mucus shortness of breath chest pain fever", "Pneumonia"),`
`("chronic cough sputum breathlessness fatigue weight loss",
"Tuberculosis"),`
`("cough shortness of breath barrel chest reduced breath sounds",
## "COPD"),`
## `# Cardiac`
`("chest pain shortness of breath sweating nausea arm pain", "Heart
## Attack"),`
`("chest pain radiating arm jaw sweat cold clammy", "Angina"),`
`("palpitations dizziness fainting shortness of breath fatigue",
"Arrhythmia"),`
`("leg swelling shortness of breath fatigue weight gain", "Heart
## Failure"),`
## `# Diabetes`
`("frequent urination excessive thirst weight loss blurred vision
fatigue", "Diabetes"),`
`("high glucose polyuria polydipsia increased appetite", "Type 2
## Diabetes"),`
`("low blood sugar shakiness sweating confusion hunger",
"Hypoglycemia"),`
## `# Gastrointestinal`
`("nausea vomiting diarrhea abdominal cramps fever dehydration",
"Gastroenteritis"),`

`("heartburn acid reflux chest pain regurgitation difficulty
swallowing", "GERD"),`
`("upper abdominal pain nausea vomiting loss of appetite", "Peptic
## Ulcer"),`
`("yellowing skin jaundice dark urine fatigue abdominal pain",
"Jaundice"),`
`("sudden severe abdominal pain nausea vomiting fever",
"Appendicitis"),`
## `# Neurological`
`("severe headache nausea sensitivity light sound vomiting",
"Migraine"),`
`("headache neck stiffness fever rash sensitivity light",
"Meningitis"),`
`("weakness numbness tingling paralysis speech difficulty",
"Stroke"),`
`("tremors stiffness slow movement balance issues", "Parkinson's
## Disease"),`
`("memory loss confusion disorientation personality changes",
"Alzheimer's Disease"),`
`# Kidney / UTI`
`("burning urination frequent urination pelvic pain cloudy urine",
## "UTI"),`
`("back pain fever chills nausea vomiting frequent urination",
"Kidney Infection"),`
`("swelling legs fatigue nausea decreased urination", "Kidney
## Disease"),`
`("severe back pain blood urine nausea vomiting", "Kidney Stones"),`
## `# Mental Health`
`("persistent sadness hopelessness fatigue sleep changes appetite
changes", "Depression"),`
`("excessive worry restlessness fatigue concentration difficulty",
"Anxiety Disorder"),`
`("mood swings impulsivity grandiosity decreased sleep", "Bipolar
## Disorder"),`
## `# Skin`
`("itchy rash hives swelling redness skin reaction", "Allergic
## Reaction"),`
`("dry scaly patches itching redness skin inflammation", "Eczema"),`
`("red scaly plaques itching silver scales joint pain",
"Psoriasis"),`
## `# Thyroid`
`("fatigue weight gain cold intolerance constipation dry skin hair
loss", "Hypothyroidism"),`
`("weight loss heat intolerance tremors palpitations anxiety",
"Hyperthyroidism"),`
## `# Blood Pressure`
`("high blood pressure headache vision changes chest pain",
"Hypertension"),`
`("low blood pressure dizziness fainting blurred vision",
"Hypotension"),`

## `# Other`
`("joint pain swelling stiffness morning stiffness fatigue",
"Arthritis"),`
`("excessive fatigue weakness pallor shortness of breath",
"Anemia"),`
`("fever sore throat swollen lymph nodes fatigue", "Tonsillitis"),`
`("ear pain discharge hearing loss fever", "Ear Infection"),`
`("eye redness discharge itching tearing crusty eyes",
"Conjunctivitis"),`
## `]`
`texts = [r[0] for r in records]`
`labels = [r[1] for r in records]`
`return texts, labels`
## `# ── Training
## ──────────────────────────────────────────────────────────────`
## `def _train_model(self):`
`texts, labels = self._get_training_data()`
`# Augment dataset`
`aug_texts, aug_labels = [], []`
`for t, l in zip(texts, labels):`
`words = t.split()`
`if len(words) > 3:`
`# Shuffle variant`
## `np.random.shuffle(words)`
## `aug_texts.append(" ".join(words))`
## `aug_labels.append(l)`
`# Subset variant`
`subset = words[:max(2, len(words) // 2)]`
## `aug_texts.append(" ".join(subset))`
## `aug_labels.append(l)`
`all_texts = texts + aug_texts`
`all_labels = labels + aug_labels`
## `self.label_encoder.fit(all_labels)`
`y = self.label_encoder.transform(all_labels)`
`self.vectorizer = TfidfVectorizer(ngram_range=(1, 2),
max_features=500)`
`X = self.vectorizer.fit_transform(all_texts)`
`X_train, X_test, y_train, y_test = train_test_split(X, y,
test_size=0.2, random_state=42)`
`self.model = RandomForestClassifier(n_estimators=200, random_state=42,
class_weight="balanced")`
`self.model.fit(X_train, y_train)`

`acc = accuracy_score(y_test, self.model.predict(X_test))`
`print(f"[Model] Trained — accuracy: {acc:.2%}")`
## `self._save_model()`
## `# ── Persistence
## ───────────────────────────────────────────────────────────`
## `def _save_model(self):`
`with open(self.model_path, "wb") as f:`
## `pickle.dump({`
`"model": self.model,`
`"vectorizer": self.vectorizer,`
`"label_encoder": self.label_encoder,`
`}, f)`
## `def _load_model(self):`
`with open(self.model_path, "rb") as f:`
`data = pickle.load(f)`
`self.model = data["model"]`
`self.vectorizer = data["vectorizer"]`
`self.label_encoder = data["label_encoder"]`
`print("[Model] Loaded from disk.")`
## `# ── Inference
## ─────────────────────────────────────────────────────────────`
`def predict(self, symptoms: list) -> dict:`
## `"""`
`Predict disease from a list of symptom strings.`
`Returns { disease, confidence, top_predictions }.`
## `"""`
`if not symptoms:`
`return {"disease": "Unknown", "confidence": 0.0, "top_predictions":
## []}`
## `text = " ".join(symptoms).lower()`
`X = self.vectorizer.transform([text])`
`proba = self.model.predict_proba(X)[0]`
`top_indices = np.argsort(proba)[::-1][:5]`
## `top_predictions = [`
## `{`
`"disease": self.label_encoder.inverse_transform([i])[0],`
`"confidence": round(float(proba[i]), 4)`
## `}`
`for i in top_indices if proba[i] > 0.01`
## `]`

## ===============================================================================
## =
FILE: report_processor.py
## ======================================================================
## ==========
## """
## Report Processing Module
Handles PDF extraction (pdfplumber) and Image OCR (pytesseract)
with NLP preprocessing: tokenisation, stopword removal, TF-IDF keyword
extraction
## """
import re
import string
from typing import List
── Optional heavy imports (graceful degradation)
## ─────────────────────────────
try:
import pdfplumber
PDF_AVAILABLE = True
except ImportError:
PDF_AVAILABLE = False
print("[Warning] pdfplumber not installed – PDF extraction disabled.")
try:
from PIL import Image
import pytesseract
OCR_AVAILABLE = True
except ImportError:
OCR_AVAILABLE = False
print("[Warning] pytesseract / Pillow not installed – OCR disabled.")
try:
from sklearn.feature_extraction.text import TfidfVectorizer
TFIDF_AVAILABLE = True
except ImportError:
TFIDF_AVAILABLE = False
`best = top_predictions[0] if top_predictions else {"disease":
"Unknown", "confidence": 0.0}`
## `return {`
`"disease": best["disease"],`
`"confidence": best["confidence"],`
`"top_predictions": top_predictions`
## `}`

── Stopwords (built-in, no NLTK dependency)
## ──────────────────────────────────
## STOPWORDS = {
## "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
## "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
## "being", "have", "has", "had", "do", "does", "did", "will", "would",
## "shall", "should", "may", "might", "must", "can", "could", "not", "no",
## "nor", "so", "yet", "both", "either", "neither", "each", "than", "such",
## "when", "where", "while", "how", "all", "both", "few", "more", "most",
## "other", "some", "such", "than", "that", "then", "there", "these",
## "they", "this", "those", "through", "under", "until", "up", "very",
## "patient", "report", "result", "test", "lab", "clinical", "hospital",
## "doctor", "date", "name", "age", "gender", "male", "female", "normal",
## "value", "unit", "reference", "range", "finding", "impression",
## }
── Medical keyword lexicon
## ──────────────────────────────────────────────────
## ──
## MEDICAL_KEYWORDS = {
# Vitals / measurements
"fever", "temperature", "bp", "blood pressure", "pulse", "heart rate",
## "oxygen", "saturation", "spo2", "glucose", "sugar", "cholesterol",
## "triglycerides", "hemoglobin", "hb", "wbc", "rbc", "platelet",
## "creatinine", "urea", "bilirubin", "sgot", "sgpt", "tsh", "t3", "t4",
## # Symptoms
"cough", "cold", "sneeze", "runny nose", "sore throat", "headache",
"chest pain", "shortness of breath", "breathlessness", "wheezing",
"nausea", "vomiting", "diarrhea", "constipation", "abdominal pain",
## "fatigue", "weakness", "dizziness", "fainting", "palpitation",
## "swelling", "edema", "rash", "itching", "jaundice", "yellowing",
"urination", "polyuria", "thirst", "polydipsia", "weight loss",
"weight gain", "blurred vision", "numbness", "tingling", "tremor",
"stiffness", "joint pain", "back pain", "muscle pain", "body ache",
"anxiety", "depression", "insomnia", "memory loss", "confusion",
## # Findings
## "infection", "inflammation", "elevated", "high", "low", "abnormal",
## "positive", "negative", "reactive", "non-reactive", "borderline",
## }
class ReportProcessor:
"""Processes medical reports: PDF / image → cleaned text → keywords."""
`# ── Text extraction
## ────────────────────────────────────────────────────────`
`def extract_pdf_text(self, file_or_path) -> str:`

`if not PDF_AVAILABLE:`
`return "[PDF extraction unavailable – install pdfplumber]"`
## `text_parts = []`
## `try:`
`with pdfplumber.open(file_or_path) as pdf:`
`for page in pdf.pages:`
`t = page.extract_text()`
`if t:`
## `text_parts.append(t)`
## `return "\n".join(text_parts)`
`except Exception as e:`
`return f"[PDF error: {e}]"`
`def extract_image_text(self, file_or_path) -> str:`
`if not OCR_AVAILABLE:`
`return "[OCR unavailable – install pytesseract and Pillow]"`
## `try:`
## `img = Image.open(file_or_path)`
`text = pytesseract.image_to_string(img, config="--psm 6")`
`return text`
`except Exception as e:`
`return f"[OCR error: {e}]"`
`# ── NLP preprocessing
## ──────────────────────────────────────────────────────`
`def preprocess(self, text: str) -> str:`
`"""Lowercase → remove punctuation → strip stopwords."""`
`text = text.lower()`
`text = re.sub(r'\d+\.?\d*\s*(mg|ml|mmol|g/dl|%|bpm|mmhg|iu/l)?', ' ',
text)`
`text = text.translate(str.maketrans(string.punctuation, ' ' *
len(string.punctuation)))`
`text = re.sub(r'\s+', ' ', text).strip()`
`tokens = [w for w in text.split() if w not in STOPWORDS and len(w) >
## 2]`
## `return " ".join(tokens)`
`def extract_keywords(self, text: str) -> List[str]:`
## `"""`
`Return a deduplicated list of medically relevant keywords`
`found in the text, ranked by TF-IDF importance when available.`
## `"""`
`if not text or text.startswith("["):`
## `return []`
`cleaned = self.preprocess(text)`
`tokens = set(cleaned.split())`
`# 1. Direct medical lexicon match (multi-word first)`

## ===============================================================================
## =
FILE: severity_detector.py
## ======================================================================
## ==========
## """
## Severity Detection Module
Rule-based logic that classifies symptom sets into: CRITICAL / MODERATE /
## NORMAL
with reasoning and recommended action.
## """
## `found = []`
`lower_text = text.lower()`
`for kw in sorted(MEDICAL_KEYWORDS, key=len, reverse=True):`
`if kw in lower_text:`
## `found.append(kw.replace(" ", "_"))`
`# 2. TF-IDF on cleaned tokens (if sklearn available)`
`if TFIDF_AVAILABLE and len(cleaned.split()) >= 3:`
## `try:`
`corpus = [cleaned, " ".join(MEDICAL_KEYWORDS)]`
`vect = TfidfVectorizer(max_features=30)`
`X = vect.fit_transform(corpus)`
`tfidf_words = vect.get_feature_names_out()`
## `scores = X[0].toarray()[0]`
`ranked = sorted(zip(tfidf_words, scores), key=lambda x: -x[1])`
`for word, score in ranked:`
`if score > 0.05 and word not in found:`
## `found.append(word)`
## `except Exception:`
## `pass`
`# 3. Fall back to raw token overlap`
`extra = [t for t in tokens if t in MEDICAL_KEYWORDS and t not in
found]`
## `found.extend(extra)`
`# Deduplicate while preserving order`
`seen = set()`
## `result = []`
`for k in found:`
`k_clean = k.replace("_", " ")`
`if k_clean not in seen:`
## `seen.add(k_clean)`
## `result.append(k_clean)`
`return result[:25]  # Cap at 25 keywords`

from typing import List, Dict, Tuple
── Rule tables
## ──────────────────────────────────────────────────
## ─────────────
## CRITICAL_SYMPTOMS = {
## # Cardiac
"chest pain", "severe chest pain", "crushing chest pain", "chest tightness",
"heart attack", "cardiac arrest", "palpitation",
## # Neurological
"stroke", "paralysis", "loss of consciousness", "fainting", "seizure",
"sudden severe headache", "meningitis", "brain bleed",
## # Respiratory
"severe breathlessness", "respiratory failure", "cyanosis", "blue lips",
"oxygen saturation low", "spo2 low",
## # Metabolic
"high glucose", "very high blood sugar", "diabetic ketoacidosis", "dka",
"severe hypoglycemia", "low blood sugar", "blood sugar crash",
# Haematological / sepsis
"sepsis", "septic shock", "severe bleeding", "blood vomiting",
"blood in stool", "high fever above 104", "platelet very low",
# Kidney / liver
"acute kidney failure", "liver failure", "severe jaundice",
## # Anaphylaxis
"anaphylaxis", "severe allergic reaction", "throat swelling",
## # Psychiatric
"suicidal ideation", "overdose",
## }
## MODERATE_SYMPTOMS = {
"fever", "high fever", "cough", "sore throat", "headache", "nausea",
"vomiting", "diarrhea", "abdominal pain", "joint pain", "muscle pain",
## "fatigue", "weakness", "dizziness", "rash", "swelling", "itching",
"shortness of breath", "breathlessness", "wheezing", "chest discomfort",
"blurred vision", "ear pain", "back pain", "urination pain", "frequent
urination",
"elevated bp", "high blood pressure", "blood pressure elevated",
"weight loss", "loss of appetite", "insomnia", "anxiety", "depression",
"numbness", "tingling", "confusion", "memory loss",
## }
Measurement-based critical thresholds
## CRITICAL_VALUES = {
"glucose": (lambda v: v > 400 or v < 50),
"bp_systolic": (lambda v: v > 180 or v < 70),
"bp_diastolic": (lambda v: v > 120 or v < 40),
"temperature": (lambda v: v > 103.5),
"heart_rate": (lambda v: v > 150 or v < 40),

"spo2": (lambda v: v < 90),
"hemoglobin": (lambda v: v < 7),
"platelet": (lambda v: v < 50000),
"creatinine": (lambda v: v > 5),
## }
class SeverityDetector:
"""Classify a list of symptoms into a severity level."""
`def detect(self, symptoms: List[str]) -> Dict:`
`if not symptoms:`
`return self._result("NORMAL", "No symptoms provided.", "Monitor
your health and maintain hygiene.")`
`lower_syms = [s.lower().strip() for s in symptoms]`
## `sym_text = " ".join(lower_syms)`
`# ── Critical check ─────────────────────────────────────────────────`
## `critical_matched = []`
`for c in CRITICAL_SYMPTOMS:`
`if c in sym_text:`
## `critical_matched.append(c)`
`if critical_matched:`
`return self._result(`
## `"CRITICAL",`
`f"Critical indicator(s) detected: {',
## '.join(critical_matched)}.",`
`" SEEK EMERGENCY MEDICAL CARE IMMEDIATELY. Call 108 / go to
the nearest ER.",`
## `matched=critical_matched,`
## `)`
`# ── Moderate check ─────────────────────────────────────────────────`
## `moderate_matched = []`
`for m in MODERATE_SYMPTOMS:`
`if m in sym_text:`
## `moderate_matched.append(m)`
`if len(moderate_matched) >= 3:`
`return self._result(`
## `"MODERATE",`
`f"Multiple moderate symptoms: {',
## '.join(moderate_matched[:5])}.",`
`"Consult a doctor within 24–48 hours. Rest and stay
hydrated.",`
## `matched=moderate_matched,`
## `)`

`if moderate_matched:`
`return self._result(`
## `"MODERATE",`
`f"Moderate symptom(s): {', '.join(moderate_matched)}.",`
`"Schedule a doctor visit. Monitor symptoms closely.",`
## `matched=moderate_matched,`
## `)`
## `# ── Normal ─────────────────────────────────────────────────────────`
`return self._result(`
## `"NORMAL",`
`"Symptoms appear mild.",`
`"Rest, stay hydrated, and monitor for worsening symptoms.",`
## `matched=lower_syms,`
## `)`
`def check_lab_values(self, values: Dict[str, float]) -> Dict:`
`"""Check numeric lab values against critical thresholds."""`
## `flagged = []`
`for param, value in values.items():`
`key = param.lower().replace(" ", "_")`
`if key in CRITICAL_VALUES:`
`if CRITICAL_VALUES[key](value):`
`flagged.append(f"{param}={value} (CRITICAL RANGE)")`
`if flagged:`
`return self._result(`
## `"CRITICAL",`
`f"Critical lab value(s): {', '.join(flagged)}",`
`" Immediate medical attention required.",`
## `matched=flagged,`
## `)`
`return self._result("NORMAL", "All lab values within acceptable
range.", "Continue monitoring.")`
## `@staticmethod`
`def _result(level: str, reason: str, action: str, matched: List[str] =
## None) -> Dict:`
`colour_map = {"CRITICAL": "#FF4444", "MODERATE": "#FF9800", "NORMAL":
## "#4CAF50"}`
`icon_map   = {"CRITICAL": "", "MODERATE": "⚠",  "NORMAL": "✅"}`
## `return {`
`"level": level,`
`"colour": colour_map.get(level, "#888"),`
`"icon": icon_map.get(level, "ℹ"),`
`"reason": reason,`
`"action": action,`
`"matched_indicators": matched or [],`
## `}`

## ===============================================================================
## =
FILE: test_local.py
## ======================================================================
## ==========
test_local.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server_code'))
import model
import severity
import drug_logic
def main():
print("=== AI-Based Patient Report Analysis - Local Test ===")
if __name__ == "__main__":
main()
## ===============================================================================
## =
FILE: client_code\FileUploadForm.py
## `test_cases = [`
`"Patient presents with fever, dry cough, and tiredness. Rapid breathing
difficulty.",`
`"Experiencing frequent urination, increased thirst, and very high
glucose levels in blood work.",`
`"Patient complains of headache and shortness of breath. No fever, high
blood pressure."`
## `]`
`for i, test in enumerate(test_cases, 1):`
`print(f"\nTest Case {i}:")`
`print(f"Symptoms: {test}")`
`disease = model.predict_single_disease(test)`
`print(f"Predicted Disease: {disease}")`
`sev = severity.analyze_severity(test)`
`print(f"Severity: {sev}")`
`drug = drug_logic.get_drug_info(disease)`
`print(f"Recommended Drug: {drug['drug']}")`
`print(f"Dosage: {drug['dosage']}")`

## ======================================================================
## ==========
client_code/FileUploadForm.py
Form for uploading PDF or Image reports.
from ._anvil_designer import FileUploadFormTemplate
from anvil import *
import anvil.server
class FileUploadForm(FileUploadFormTemplate):
def __init__(self, **properties):
self.init_components(**properties)
def file_loader_report_change(self, file, **event_args):
"""This method is called when a new file is loaded into this FileLoader"""
if file:
self.label_filename.text = f"Uploaded: {file.name}"
# Enable analysis assuming valid file
self.btn_analyze.enabled = True
# Store the file reference
self.uploaded_file = file
def btn_analyze_click(self, **event_args):
if not hasattr(self, 'uploaded_file') or not self.uploaded_file:
alert("Please upload a file first.")
return
def btn_back_click(self, **event_args):
open_form('HomePage')
`self.label_status.text = "Extracting text and analyzing... Please wait."`
## `self.btn_analyze.enabled = False`
## `try:`
`# Pass the Anvil Media Object to the server`
`result = anvil.server.call('analyze_report', self.uploaded_file)`
`if "error" in result:`
## `alert(result["error"])`
## `else:`
`open_form('ResultPage', result=result)`
`except Exception as e:`
`alert(f"An error occurred: {e}")`
## `finally:`
## `self.label_status.text = ""`
## `self.btn_analyze.enabled = True`

## ===============================================================================
## =
FILE: client_code\HomePage.py
## ======================================================================
## ==========
client_code/HomePage.py
Assuming this is pasted into Anvil's Code view for
'HomePage' form.
from ._anvil_designer import HomePageTemplate
from anvil import *
import anvil.server
class HomePage(HomePageTemplate):
def __init__(self, **properties):
# Set Form properties and Data Bindings.
self.init_components(**properties)
def btn_start_symptoms_click(self, **event_args):
"""This method is called when the symptom input button is clicked"""
open_form('InputForm')
def btn_start_upload_click(self, **event_args):
"""This method is called when the file upload button is clicked"""
open_form('FileUploadForm')
## ===============================================================================
## =
FILE: client_code\InputForm.py
## ======================================================================
## ==========
client_code/InputForm.py
Form for manual Symptom input
from ._anvil_designer import InputFormTemplate
from anvil import *
import anvil.server
class InputForm(InputFormTemplate):
def __init__(self, **properties):
self.init_components(**properties)
def btn_analyze_click(self, **event_args):
"""This method is called when the button is clicked"""
symptoms = self.text_area_symptoms.text
if not symptoms:

alert("Please enter some symptoms first.")
return
def btn_back_click(self, **event_args):
open_form('HomePage')
## ===============================================================================
## =
FILE: client_code\ResultPage.py
## ======================================================================
## ==========
client_code/ResultPage.py
Displays the final analysis output.
from ._anvil_designer import ResultPageTemplate
from anvil import *
import anvil.server
class ResultPage(ResultPageTemplate):
def __init__(self, result=None, **properties):
self.init_components(**properties)
def populate_data(self, result):
# Depending on UI setup, populate standard labels
self.label_disease.text = f"Disease: {result.get('disease')}"
self.label_severity.text = f"Severity: {result.get('severity')}"
self.label_drug.text = f"Drug: {result.get('drug')}"
`# Show loading indicator`
`self.label_status.text = "Analyzing..."`
## `self.btn_analyze.enabled = False`
## `try:`
`# Call backend server module`
`result = anvil.server.call('predict_disease', symptoms)`
`# Open result page passing the data`
`open_form('ResultPage', result=result)`
`except Exception as e:`
`alert(f"An error occurred: {e}")`
## `finally:`
## `self.label_status.text = ""`
## `self.btn_analyze.enabled = True`
`if result:`
## `self.populate_data(result)`

self.label_dosage.text = f"Dosage: {result.get('dosage')}"
self.label_precautions.text = f"Precautions: {result.get('precautions')}"
def btn_home_click(self, **event_args):
"""This method is called when the home button is clicked"""
open_form('HomePage')
## ===============================================================================
## =
FILE: mediscan_dashboard_overview\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediScan - Clinical Precision Dashboard</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "surface": "#f8f9fa",
## "on-surface": "#191c1d",
## "surface-container-lowest": "#ffffff",
## "error-container": "#ffdad6",
## "on-primary-fixed-variant": "#004491",
## "surface-bright": "#f8f9fa",
## "outline": "#727784",
## "on-primary": "#ffffff",
## "surface-tint": "#115cb9",
`# Show extracted text/summary if available`
`extracted = result.get('extracted_text', '')`
`if extracted:`
`self.text_area_summary.text = extracted`

## "on-secondary-container": "#fffbff",
## "on-secondary": "#ffffff",
## "surface-container-highest": "#e1e3e4",
## "on-error": "#ffffff",
## "primary-container": "#0056b3",
## "on-tertiary": "#ffffff",
## "tertiary-container": "#006722",
## "on-background": "#191c1d",
## "on-surface-variant": "#424752",
## "inverse-surface": "#2e3132",
## "secondary-fixed": "#ffdad9",
## "on-tertiary-fixed-variant": "#00531a",
## "primary-fixed-dim": "#acc7ff",
## "surface-variant": "#e1e3e4",
## "surface-container-low": "#f3f4f5",
## "surface-container": "#edeeef",
## "on-tertiary-container": "#6fe87c",
## "primary-fixed": "#d7e2ff",
## "tertiary-fixed-dim": "#66df75",
## "on-tertiary-fixed": "#002106",
## "secondary": "#b6152e",
## "error": "#ba1a1a",
## "on-error-container": "#93000a",
## "tertiary": "#004c17",
## "on-primary-fixed": "#001a40",
## "on-secondary-fixed": "#410008",
## "surface-container-high": "#e7e8e9",
## "secondary-fixed-dim": "#ffb3b2",
## "inverse-primary": "#acc7ff",
## "on-primary-container": "#bbd0ff",
## "primary": "#003f87",
## "background": "#f8f9fa",
## "surface-dim": "#d9dadb",
## "inverse-on-surface": "#f0f1f2",
## "tertiary-fixed": "#83fc8e",
## "secondary-container": "#d93343",
## "on-secondary-fixed-variant": "#92001f",
## "outline-variant": "#c2c6d4"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]
## }

## },
## },
## }
## </script>
## <style>
body { font-family: 'Inter', sans-serif; }
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
## .custom-glass {
background: rgba(255, 255, 255, 0.8);
backdrop-filter: blur(20px);
## }
## </style>
## </head>
<body class="bg-surface text-on-surface antialiased">
<!-- SideNavBar Shell -->
<nav class="flex flex-col fixed left-0 top-0 h-full py-6 bg-slate-50 dark:bg-
slate-900 h-screen w-64 border-r-0 z-50 font-inter text-sm antialiased">
<div class="px-6 mb-10">
<h1 class="text-xl font-bold tracking-tight text-blue-800 dark:text-blue-
300">MediScan</h1>
<p class="text-xs text-on-surface-variant/70 uppercase tracking-widest mt-
1">Clinical Precision</p>
## </div>
<div class="flex-1 space-y-1 px-3">
<a class="flex items-center px-4 py-3 rounded-lg text-blue-700 dark:text-blue-
400 font-semibold border-r-4 border-blue-700 dark:border-blue-400 transition-
colors bg-slate-200/50" href="#">
<span class="material-symbols-outlined mr-3">dashboard</span>
## Dashboard
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">group</span>
## Patients
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">calendar_today</span>
## Appointments
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">analytics</span>
## Analytics
## </a>

<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">description</span>
## Reports
## </a>
## </div>
<div class="px-3 mt-auto">
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">settings</span>
## Settings
## </a>
## </div>
## </nav>
## <!-- Main Content Area -->
<main class="ml-64 min-h-screen">
<!-- TopNavBar Shell -->
<header class="flex justify-between items-center w-full px-8 h-16 sticky top-0
z-40 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md shadow-sm dark:shadow-
none font-inter text-base">
<div class="flex items-center flex-1 max-w-xl">
<div class="relative w-full">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2
text-on-surface-variant">search</span>
<input class="w-full bg-surface-container-low border-none rounded-full py-2 pl-
10 pr-4 focus:ring-2 focus:ring-primary/20 text-sm" placeholder="Search patient
ID, name, or clinician..." type="text"/>
## </div>
## </div>
<div class="flex items-center gap-4 ml-8">
<button class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2
transition-all active:scale-95 duration-200 text-slate-400">
<span class="material-symbols-outlined">notifications</span>
## </button>
<button class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2
transition-all active:scale-95 duration-200 text-slate-400">
<span class="material-symbols-outlined">help_outline</span>
## </button>
<div class="h-8 w-px bg-outline-variant/30 mx-2"></div>
<div class="flex items-center gap-3">
<div class="text-right hidden sm:block">
<p class="text-xs font-bold text-on-surface">Dr. Sarah Chen</p>
<p class="text-[10px] text-on-surface-variant">Senior Hematologist</p>
## </div>
<img alt="Clinician Profile" class="w-10 h-10 rounded-full object-cover border-
2 border-primary-container" data-alt="Professional headshot of a female doctor
in a white lab coat, clean studio lighting, high-end medical professional
aesthetic" src="https://lh3.googleusercontent.com/aida-

public/AB6AXuCXrB3e1MU9LmJZ30QnVVf2sRlJvxMCGGwPCFXp9NxAqlzGMHSSZCdRy-
y9wtsBG2MIb0oBu4zB3WeLINoZutTwHVuQyaEbT7j4lRK8pB2HASP2Q9u7w_hLjHZpkBWQL_QBvDe-
o92NJbrGYWryWmSN5r7uO6-
f4xQxz8B4YugRAxMRV32Bj0nAF8tQkVYRk50oyvKzakmu62q78AskhgXniuEeqe9AVE2bV9TgBa3BOU
5vyZMRfmzznUfANTvl9EovKplKInlYCmQ"/>
## </div>
## </div>
## </header>
## <!-- Content Canvas -->
<div class="p-8 space-y-8">
<!-- Section 1: Clinic Performance (Bento Stats) -->
## <section>
<div class="flex items-end justify-between mb-6">
## <div>
<h2 class="text-[0.75rem] font-bold text-primary uppercase tracking-
widest">Clinic Performance</h2>
<h3 class="text-2xl font-medium text-on-surface mt-1">Live Operations
## Monitor</h3>
## </div>
<p class="text-sm text-on-surface-variant">Last updated: Just now</p>
## </div>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
## <!-- Active Cases -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-primary bg-primary/10 p-2 rounded-
lg">clinical_notes</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-
container/10 px-2 py-1 rounded">+12%</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Active Cases</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">142</h4>
## </div>
## <!-- Critical Results -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-secondary bg-secondary/10 p-2
rounded-lg">emergency_home</span>
<span class="text-[10px] font-bold text-secondary-container bg-secondary-
container/10 px-2 py-1 rounded">URGENT</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Critical Results</p>
<h4 class="text-4xl font-semibold text-secondary mt-2">08</h4>
## </div>
## <!-- Pending Reviews -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">

<span class="material-symbols-outlined text-outline bg-surface-container-high
p-2 rounded-lg">pending_actions</span>
<span class="text-[10px] font-bold text-on-surface-variant bg-surface-
container-high px-2 py-1 rounded">2h avg</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Pending Reviews</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">24</h4>
## </div>
## <!-- Completed Today -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-tertiary bg-tertiary-container/20
p-2 rounded-lg">task_alt</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-
container/10 px-2 py-1 rounded">88% target</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Completed Today</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">56</h4>
## </div>
## </div>
## </section>
## <!-- Main Layout Grid: Patient Flow + Clinical Insights / Action Required -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
## <!-- Left: Patient Flow & Clinical Insights -->
<div class="lg:col-span-8 space-y-8">
## <!-- Patient Flow -->
<div class="bg-surface-container-low rounded-xl overflow-hidden">
<div class="p-6 bg-surface-container-lowest flex justify-between items-center">
<h3 class="text-lg font-medium text-on-surface">Recently Analyzed Patients</h3>
<button class="text-primary text-sm font-semibold hover:underline">View
## All</button>
## </div>
<div class="divide-y divide-transparent">
## <!-- Patient Item 1 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-
center text-primary font-bold">JD</div>
## <div>
<p class="font-medium text-on-surface">Johnathan Doe</p>
<p class="text-xs text-on-surface-variant">ID: #MS-94021</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-secondary-
container text-white uppercase tracking-wider">Critical</span>
<p class="text-xs text-on-surface-variant w-24">12 mins ago</p>
<button class="material-symbols-outlined text-on-surface-

variant">chevron_right</button>
## </div>
## </div>
## <!-- Patient Item 2 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-surface-tint/10 flex items-center
justify-center text-primary font-bold">MS</div>
## <div>
<p class="font-medium text-on-surface">Maria Sanchez</p>
<p class="text-xs text-on-surface-variant">ID: #MS-88123</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-surface-container-
highest text-on-surface-variant uppercase tracking-wider">Moderate</span>
<p class="text-xs text-on-surface-variant w-24">45 mins ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## <!-- Patient Item 3 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-tertiary-container/10 flex items-center
justify-center text-tertiary font-bold">AW</div>
## <div>
<p class="font-medium text-on-surface">Arthur Wright</p>
<p class="text-xs text-on-surface-variant">ID: #MS-77120</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-tertiary-container
text-white uppercase tracking-wider">Normal</span>
<p class="text-xs text-on-surface-variant w-24">1 hour ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## </div>
## </div>
<!-- Clinical Insights (Chart Mockup) -->
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm">
<div class="flex justify-between items-start mb-8">
## <div>
<h3 class="text-lg font-medium text-on-surface">Clinical Insights</h3>
<p class="text-sm text-on-surface-variant">Diagnostic volume trend (7-day
period)</p>

## </div>
<select class="bg-surface-container-low border-none rounded-lg text-xs font-
semibold py-1 px-3">
<option>Weekly</option>
<option>Monthly</option>
## </select>
## </div>
<!-- Asymmetric Sparkline/Chart Visual -->
<div class="h-48 flex items-end gap-2 px-2">
<div class="flex-1 bg-primary/10 rounded-t-md h-[40%] transition-all hover:bg-
primary/20 relative group">
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded hidden group-hover:block">124</div>
## </div>
<div class="flex-1 bg-primary/10 rounded-t-md h-[55%] transition-all hover:bg-
primary/20 relative group"></div>
<div class="flex-1 bg-primary/10 rounded-t-md h-[48%] transition-all hover:bg-
primary/20 relative group"></div>
<div class="flex-1 bg-primary/30 rounded-t-md h-[72%] transition-all hover:bg-
primary/40 relative group"></div>
<div class="flex-1 bg-primary/10 rounded-t-md h-[60%] transition-all hover:bg-
primary/20 relative group"></div>
<div class="flex-1 bg-primary/20 rounded-t-md h-[85%] transition-all hover:bg-
primary/40 relative group"></div>
<div class="flex-1 bg-primary rounded-t-md h-[95%] relative group">
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded">284</div>
## </div>
## </div>
<div class="flex justify-between mt-4 text-[10px] font-bold text-on-surface-
variant uppercase tracking-widest px-1">
<span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span>
<span>Fri</span><span>Sat</span><span>Sun</span>
## </div>
## </div>
## </div>
## <!-- Right: Action Required Sidebar -->
<div class="lg:col-span-4 space-y-6">
<div class="bg-surface-container-lowest p-6 rounded-xl border-l-4 border-
secondary">
<div class="flex items-center gap-3 mb-6">
<span class="material-symbols-outlined text-secondary" style="font-variation-
settings: 'FILL' 1;">warning</span>
<h3 class="text-lg font-semibold text-on-surface">Action Required</h3>
## </div>
<div class="space-y-4">
## <!-- Task 1 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-secondary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-secondary uppercase">High

## Priority</span>
<span class="text-[10px] text-on-surface-variant">10:45 AM</span>
## </div>
<p class="text-sm font-medium text-on-surface">Review Hematology Lab #4922</p>
<p class="text-xs text-on-surface-variant mt-1">Patient: Robert Miller (ICU-2)
## </p>
<button class="mt-4 w-full bg-secondary text-white text-xs font-bold py-2
rounded-lg hover:opacity-90 transition-opacity">Launch Review</button>
## </div>
## <!-- Task 2 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-primary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-primary uppercase">Standard</span>
<span class="text-[10px] text-on-surface-variant">09:15 AM</span>
## </div>
<p class="text-sm font-medium text-on-surface">Finalize Discharge Report</p>
<p class="text-xs text-on-surface-variant mt-1">Patient: Sarah Jenkins</p>
<button class="mt-4 w-full border border-primary text-primary text-xs font-bold
py-2 rounded-lg hover:bg-primary/5 transition-colors">Complete Task</button>
## </div>
## <!-- Task 3 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-primary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-primary uppercase">Follow-up</span>
<span class="text-[10px] text-on-surface-variant">Yesterday</span>
## </div>
<p class="text-sm font-medium text-on-surface">Verify Insurance Pre-Auth</p>
<p class="text-xs text-on-surface-variant mt-1">Provider: Aetna Clinical</p>
<button class="mt-4 w-full border border-primary text-primary text-xs font-bold
py-2 rounded-lg hover:bg-primary/5 transition-colors">Call Provider</button>
## </div>
## </div>
<button class="w-full mt-6 py-3 text-sm text-on-surface-variant font-medium bg-
surface-container-low rounded-lg hover:bg-surface-container-high transition-
colors">
## View All (14 Tasks)
## </button>
## </div>
<!-- Clinical Tip/Ad -->
<div class="relative overflow-hidden rounded-xl p-6 text-white group">
<div class="absolute inset-0 bg-gradient-to-br from-primary to-primary-
container z-0"></div>
<img alt="Laboratory" class="absolute inset-0 w-full h-full object-cover
opacity-20 mix-blend-overlay group-hover:scale-110 transition-transform
duration-700" data-alt="Close up of high-tech laboratory diagnostic equipment
with blue medical lighting and scientific research aesthetic"
src="https://lh3.googleusercontent.com/aida-
public/AB6AXuAyzxubzHQjCA5SCs2T2jz4NtpcKALxm3NIhertJC5c1wCmn08KGWtl0QY01xiQ7fIb
yXsft0HIuahbPrfGn91US83RaY02tennXRa6J8f0HvNMTTfipPUNUP516uqGhXkknhDHdOt3PJdjobt
aOFIvoJ1sdMO6gfJSWv-s2I-

Sc4JCLGvwcG_O0GuZFPOsvaXGFKBuLCZBopufwnYiLNspVlYp8o5vGAEEDljpSSjd4xBAbZJHNXldjC
f5YXT7EdhupZ0PZNf_1ls"/>
<div class="relative z-10">
<span class="material-symbols-outlined mb-4">info</span>
<h4 class="font-bold text-lg mb-2">System Update</h4>
<p class="text-xs opacity-90 leading-relaxed mb-4">New AI-driven hematology
markers are now live for all patients in the Critical category.</p>
<a class="text-xs font-bold underline underline-offset-4" href="#">Learn
## More</a>
## </div>
## </div>
## </div>
## </div>
## </div>
## </main>
## </body></html>
## ===============================================================================
## =
FILE: mediscan_dashboard_with_green_trend_line\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediScan - Clinical Precision Dashboard</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "surface": "#f8f9fa",
## "on-surface": "#191c1d",
## "surface-container-lowest": "#ffffff",
## "error-container": "#ffdad6",
## "on-primary-fixed-variant": "#004491",
## "surface-bright": "#f8f9fa",
## "outline": "#727784",
## "on-primary": "#ffffff",

## "surface-tint": "#115cb9",
## "on-secondary-container": "#fffbff",
## "on-secondary": "#ffffff",
## "surface-container-highest": "#e1e3e4",
## "on-error": "#ffffff",
## "primary-container": "#0056b3",
## "on-tertiary": "#ffffff",
## "tertiary-container": "#006722",
## "on-background": "#191c1d",
## "on-surface-variant": "#424752",
## "inverse-surface": "#2e3132",
## "secondary-fixed": "#ffdad9",
## "on-tertiary-fixed-variant": "#00531a",
## "primary-fixed-dim": "#acc7ff",
## "surface-variant": "#e1e3e4",
## "surface-container-low": "#f3f4f5",
## "surface-container": "#edeeef",
## "on-tertiary-container": "#6fe87c",
## "primary-fixed": "#d7e2ff",
## "tertiary-fixed-dim": "#66df75",
## "on-tertiary-fixed": "#002106",
## "secondary": "#b6152e",
## "error": "#ba1a1a",
## "on-error-container": "#93000a",
## "tertiary": "#004c17",
## "on-primary-fixed": "#001a40",
## "on-secondary-fixed": "#410008",
## "surface-container-high": "#e7e8e9",
## "secondary-fixed-dim": "#ffb3b2",
## "inverse-primary": "#acc7ff",
## "on-primary-container": "#bbd0ff",
## "primary": "#003f87",
## "background": "#f8f9fa",
## "surface-dim": "#d9dadb",
## "inverse-on-surface": "#f0f1f2",
## "tertiary-fixed": "#83fc8e",
## "secondary-container": "#d93343",
## "on-secondary-fixed-variant": "#92001f",
## "outline-variant": "#c2c6d4"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]

## }
## },
## },
## }
## </script>
## <style>
body { font-family: 'Inter', sans-serif; }
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
## .custom-glass {
background: rgba(255, 255, 255, 0.8);
backdrop-filter: blur(20px);
## }
## </style>
## </head>
<body class="bg-surface text-on-surface antialiased">
<!-- SideNavBar Shell -->
<nav class="flex flex-col fixed left-0 top-0 h-full py-6 bg-slate-50 dark:bg-
slate-900 h-screen w-64 border-r-0 z-50 font-inter text-sm antialiased">
<div class="px-6 mb-10">
<h1 class="text-xl font-bold tracking-tight text-blue-800 dark:text-blue-
300">MediScan</h1>
<p class="text-xs text-on-surface-variant/70 uppercase tracking-widest mt-
1">Clinical Precision</p>
## </div>
<div class="flex-1 space-y-1 px-3">
<a class="flex items-center px-4 py-3 rounded-lg text-blue-700 dark:text-blue-
400 font-semibold border-r-4 border-blue-700 dark:border-blue-400 transition-
colors bg-slate-200/50" href="#">
<span class="material-symbols-outlined mr-3">dashboard</span>
## Dashboard
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">group</span>
## Patients
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">calendar_today</span>
## Appointments
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">analytics</span>
## Analytics

## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">description</span>
## Reports
## </a>
## </div>
<div class="px-3 mt-auto">
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">settings</span>
## Settings
## </a>
## </div>
## </nav>
## <!-- Main Content Area -->
<main class="ml-64 min-h-screen">
<!-- TopNavBar Shell -->
<header class="flex justify-between items-center w-full px-8 h-16 sticky top-0
z-40 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md shadow-sm dark:shadow-
none font-inter text-base">
<div class="flex items-center flex-1 max-w-xl">
<div class="relative w-full">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2
text-on-surface-variant">search</span>
<input class="w-full bg-surface-container-low border-none rounded-full py-2 pl-
10 pr-4 focus:ring-2 focus:ring-primary/20 text-sm" placeholder="Search patient
ID, name, or clinician..." type="text"/>
## </div>
## </div>
<div class="flex items-center gap-4 ml-8">
<button class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2
transition-all active:scale-95 duration-200 text-slate-400">
<span class="material-symbols-outlined">notifications</span>
## </button>
<button class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2
transition-all active:scale-95 duration-200 text-slate-400">
<span class="material-symbols-outlined">help_outline</span>
## </button>
<div class="h-8 w-px bg-outline-variant/30 mx-2"></div>
<div class="flex items-center gap-3">
<div class="text-right hidden sm:block">
<p class="text-xs font-bold text-on-surface">Dr. Sarah Chen</p>
<p class="text-[10px] text-on-surface-variant">Senior Hematologist</p>
## </div>
<img alt="Clinician Profile" class="w-10 h-10 rounded-full object-cover border-
2 border-primary-container" data-alt="Professional headshot of a female doctor
in a white lab coat, clean studio lighting, high-end medical professional

aesthetic" src="https://lh3.googleusercontent.com/aida-
public/AB6AXuCXrB3e1MU9LmJZ30QnVVf2sRlJvxMCGGwPCFXp9NxAqlzGMHSSZCdRy-
y9wtsBG2MIb0oBu4zB3WeLINoZutTwHVuQyaEbT7j4lRK8pB2HASP2Q9u7w_hLjHZpkBWQL_QBvDe-
o92NJbrGYWryWmSN5r7uO6-
f4xQxz8B4YugRAxMRV32Bj0nAF8tQkVYRk50oyvKzakmu62q78AskhgXniuEeqe9AVE2bV9TgBa3BOU
5vyZMRfmzznUfANTvl9EovKplKInlYCmQ"/>
## </div>
## </div>
## </header>
## <!-- Content Canvas -->
<div class="p-8 space-y-8">
<!-- Section 1: Clinic Performance (Bento Stats) -->
## <section>
<div class="flex items-end justify-between mb-6">
## <div>
<h2 class="text-[0.75rem] font-bold text-primary uppercase tracking-
widest">Clinic Performance</h2>
<h3 class="text-2xl font-medium text-on-surface mt-1">Live Operations
## Monitor</h3>
## </div>
<p class="text-sm text-on-surface-variant">Last updated: Just now</p>
## </div>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
## <!-- Active Cases -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-primary bg-primary/10 p-2 rounded-
lg">clinical_notes</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-
container/10 px-2 py-1 rounded">+12%</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Active Cases</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">142</h4>
## </div>
## <!-- Critical Results -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-secondary bg-secondary/10 p-2
rounded-lg">emergency_home</span>
<span class="text-[10px] font-bold text-secondary-container bg-secondary-
container/10 px-2 py-1 rounded">URGENT</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Critical Results</p>
<h4 class="text-4xl font-semibold text-secondary mt-2">08</h4>
## </div>
## <!-- Pending Reviews -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">

<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-outline bg-surface-container-high
p-2 rounded-lg">pending_actions</span>
<span class="text-[10px] font-bold text-on-surface-variant bg-surface-
container-high px-2 py-1 rounded">2h avg</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Pending Reviews</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">24</h4>
## </div>
## <!-- Completed Today -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-tertiary bg-tertiary-container/20
p-2 rounded-lg">task_alt</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-
container/10 px-2 py-1 rounded">88% target</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Completed Today</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">56</h4>
## </div>
## </div>
## </section>
## <!-- Main Layout Grid: Patient Flow + Clinical Insights / Action Required -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
## <!-- Left: Patient Flow & Clinical Insights -->
<div class="lg:col-span-8 space-y-8">
## <!-- Patient Flow -->
<div class="bg-surface-container-low rounded-xl overflow-hidden">
<div class="p-6 bg-surface-container-lowest flex justify-between items-center">
<h3 class="text-lg font-medium text-on-surface">Recently Analyzed Patients</h3>
<button class="text-primary text-sm font-semibold hover:underline">View
## All</button>
## </div>
<div class="divide-y divide-transparent">
## <!-- Patient Item 1 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-
center text-primary font-bold">JD</div>
## <div>
<p class="font-medium text-on-surface">Johnathan Doe</p>
<p class="text-xs text-on-surface-variant">ID: #MS-94021</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-secondary-
container text-white uppercase tracking-wider">Critical</span>
<p class="text-xs text-on-surface-variant w-24">12 mins ago</p>

<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## <!-- Patient Item 2 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-surface-tint/10 flex items-center
justify-center text-primary font-bold">MS</div>
## <div>
<p class="font-medium text-on-surface">Maria Sanchez</p>
<p class="text-xs text-on-surface-variant">ID: #MS-88123</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-surface-container-
highest text-on-surface-variant uppercase tracking-wider">Moderate</span>
<p class="text-xs text-on-surface-variant w-24">45 mins ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## <!-- Patient Item 3 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-tertiary-container/10 flex items-center
justify-center text-tertiary font-bold">AW</div>
## <div>
<p class="font-medium text-on-surface">Arthur Wright</p>
<p class="text-xs text-on-surface-variant">ID: #MS-77120</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-tertiary-container
text-white uppercase tracking-wider">Normal</span>
<p class="text-xs text-on-surface-variant w-24">1 hour ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## </div>
## </div>
<!-- Clinical Insights (Line Graph) -->
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm">
<div class="flex justify-between items-start mb-8">
## <div>
<h3 class="text-lg font-medium text-on-surface">Clinical Insights</h3>
<p class="text-sm text-on-surface-variant">Diagnostic volume trend (7-day

period)</p>
## </div>
<select class="bg-surface-container-low border-none rounded-lg text-xs font-
semibold py-1 px-3">
<option>Weekly</option>
<option>Monthly</option>
## </select>
## </div>
## <!-- Professional Line Graph Visual -->
<div class="relative h-48 w-full">
## <!-- Vertical Grid Lines -->
<div class="absolute inset-0 flex justify-between px-2 opacity-10">
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
## </div>
<!-- Line SVG -->
<svg class="absolute inset-0 w-full h-full" preserveaspectratio="none"
viewbox="0 0 700 200">
## <defs>
<lineargradient id="lineGradient" x1="0%" x2="0%" y1="0%" y2="100%"><stop
offset="0%" stop-color="rgba(0, 103, 34, 0.1)"></stop><stop offset="100%" stop-
color="rgba(0, 103, 34, 0)"></stop></lineargradient>
## </defs>
## <!-- Area Fill -->
<path d="M 0 120 L 116 100 L 232 60 L 348 20 L 464 45 L 580 90 L 700 130 L 700
200 L 0 200 Z" fill="url(#lineGradient)"></path>
## <!-- Main Line -->
<path d="M 0 120 L 116 100 L 232 60 L 348 20 L 464 45 L 580 90 L 700 130"
fill="none" stroke="#006722" stroke-linecap="round" stroke-linejoin="round"
stroke-width="3"></path>
## </svg>
## <!-- Interactive Data Points -->
<div class="absolute inset-0 flex justify-between px-2">
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 120px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">120</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 100px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>

<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">140</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 60px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">210</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 20px; transform: translateY(-50%);">
<div class="w-3 h-3 rounded-full border-2 border-white shadow-md ring-4 bg-
tertiary-container ring-tertiary-container/20"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded">284</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 45px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">245</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 90px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">180</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 130px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">95</div>
## </div>
## </div>
## </div>
<div class="flex justify-between mt-4 text-[10px] font-bold text-on-surface-
variant uppercase tracking-widest px-1">
<span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span>
<span>Fri</span><span>Sat</span><span>Sun</span>
## </div>

## </div>
## </div>
## <!-- Right: Action Required Sidebar -->
<div class="lg:col-span-4 space-y-6">
<div class="bg-surface-container-lowest p-6 rounded-xl border-l-4 border-
secondary">
<div class="flex items-center gap-3 mb-6">
<span class="material-symbols-outlined text-secondary" style="font-variation-
settings: 'FILL' 1;">warning</span>
<h3 class="text-lg font-semibold text-on-surface">Action Required</h3>
## </div>
<div class="space-y-4">
## <!-- Task 1 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-secondary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-secondary uppercase">High
## Priority</span>
<span class="text-[10px] text-on-surface-variant">10:45 AM</span>
## </div>
<p class="text-sm font-medium text-on-surface">Review Hematology Lab #4922</p>
<p class="text-xs text-on-surface-variant mt-1">Patient: Robert Miller (ICU-2)
## </p>
<button class="mt-4 w-full bg-secondary text-white text-xs font-bold py-2
rounded-lg hover:opacity-90 transition-opacity">Launch Review</button>
## </div>
## <!-- Task 2 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-primary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-primary uppercase">Standard</span>
<span class="text-[10px] text-on-surface-variant">09:15 AM</span>
## </div>
<p class="text-sm font-medium text-on-surface">Finalize Discharge Report</p>
<p class="text-xs text-on-surface-variant mt-1">Patient: Sarah Jenkins</p>
<button class="mt-4 w-full border border-primary text-primary text-xs font-bold
py-2 rounded-lg hover:bg-primary/5 transition-colors">Complete Task</button>
## </div>
## <!-- Task 3 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-primary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-primary uppercase">Follow-up</span>
<span class="text-[10px] text-on-surface-variant">Yesterday</span>
## </div>
<p class="text-sm font-medium text-on-surface">Verify Insurance Pre-Auth</p>
<p class="text-xs text-on-surface-variant mt-1">Provider: Aetna Clinical</p>
<button class="mt-4 w-full border border-primary text-primary text-xs font-bold
py-2 rounded-lg hover:bg-primary/5 transition-colors">Call Provider</button>
## </div>
## </div>
<button class="w-full mt-6 py-3 text-sm text-on-surface-variant font-medium bg-
surface-container-low rounded-lg hover:bg-surface-container-high transition-

colors">
## View All (14 Tasks)
## </button>
## </div>
<!-- Clinical Tip/Ad -->
<div class="relative overflow-hidden rounded-xl p-6 text-white group">
<div class="absolute inset-0 bg-gradient-to-br from-primary to-primary-
container z-0"></div>
<img alt="Laboratory" class="absolute inset-0 w-full h-full object-cover
opacity-20 mix-blend-overlay group-hover:scale-110 transition-transform
duration-700" data-alt="Close up of high-tech laboratory diagnostic equipment
with blue medical lighting and scientific research aesthetic"
src="https://lh3.googleusercontent.com/aida-
public/AB6AXuAyzxubzHQjCA5SCs2T2jz4NtpcKALxm3NIhertJC5c1wCmn08KGWtl0QY01xiQ7fIb
yXsft0HIuahbPrfGn91US83RaY02tennXRa6J8f0HvNMTTfipPUNUP516uqGhXkknhDHdOt3PJdjobt
aOFIvoJ1sdMO6gfJSWv-s2I-
Sc4JCLGvwcG_O0GuZFPOsvaXGFKBuLCZBopufwnYiLNspVlYp8o5vGAEEDljpSSjd4xBAbZJHNXldjC
f5YXT7EdhupZ0PZNf_1ls"/>
<div class="relative z-10">
<span class="material-symbols-outlined mb-4">info</span>
<h4 class="font-bold text-lg mb-2">System Update</h4>
<p class="text-xs opacity-90 leading-relaxed mb-4">New AI-driven hematology
markers are now live for all patients in the Critical category.</p>
<a class="text-xs font-bold underline underline-offset-4" href="#">Learn
## More</a>
## </div>
## </div>
## </div>
## </div>
## </div>
## </main>
## </body></html>
## ===============================================================================
## =
FILE: mediscan_dashboard_with_total_patients_card\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediScan - Clinical Precision Dashboard</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?

family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "surface": "#f8f9fa",
## "on-surface": "#191c1d",
## "surface-container-lowest": "#ffffff",
## "error-container": "#ffdad6",
## "on-primary-fixed-variant": "#004491",
## "surface-bright": "#f8f9fa",
## "outline": "#727784",
## "on-primary": "#ffffff",
## "surface-tint": "#115cb9",
## "on-secondary-container": "#fffbff",
## "on-secondary": "#ffffff",
## "surface-container-highest": "#e1e3e4",
## "on-error": "#ffffff",
## "primary-container": "#0056b3",
## "on-tertiary": "#ffffff",
## "tertiary-container": "#006722",
## "on-background": "#191c1d",
## "on-surface-variant": "#424752",
## "inverse-surface": "#2e3132",
## "secondary-fixed": "#ffdad9",
## "on-tertiary-fixed-variant": "#00531a",
## "primary-fixed-dim": "#acc7ff",
## "surface-variant": "#e1e3e4",
## "surface-container-low": "#f3f4f5",
## "surface-container": "#edeeef",
## "on-tertiary-container": "#6fe87c",
## "primary-fixed": "#d7e2ff",
## "tertiary-fixed-dim": "#66df75",
## "on-tertiary-fixed": "#002106",
## "secondary": "#b6152e",
## "error": "#ba1a1a",
## "on-error-container": "#93000a",
## "tertiary": "#004c17",
## "on-primary-fixed": "#001a40",
## "on-secondary-fixed": "#410008",
## "surface-container-high": "#e7e8e9",
## "secondary-fixed-dim": "#ffb3b2",
## "inverse-primary": "#acc7ff",
## "on-primary-container": "#bbd0ff",
## "primary": "#003f87",
## "background": "#f8f9fa",
## "surface-dim": "#d9dadb",

## "inverse-on-surface": "#f0f1f2",
## "tertiary-fixed": "#83fc8e",
## "secondary-container": "#d93343",
## "on-secondary-fixed-variant": "#92001f",
## "outline-variant": "#c2c6d4"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]
## }
## },
## },
## }
## </script>
## <style>
body { font-family: 'Inter', sans-serif; }
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
## .custom-glass {
background: rgba(255, 255, 255, 0.8);
backdrop-filter: blur(20px);
## }
## </style>
## </head>
<body class="bg-surface text-on-surface antialiased">
<!-- SideNavBar Shell -->
<nav class="flex flex-col fixed left-0 top-0 h-full py-6 bg-slate-50 dark:bg-
slate-900 h-screen w-64 border-r-0 z-50 font-inter text-sm antialiased">
<div class="px-6 mb-10">
<h1 class="text-xl font-bold tracking-tight text-blue-800 dark:text-blue-
300">MediScan</h1>
<p class="text-xs text-on-surface-variant/70 uppercase tracking-widest mt-
1">Clinical Precision</p>
## </div>
<div class="flex-1 space-y-1 px-3">
<a class="flex items-center px-4 py-3 rounded-lg text-blue-700 dark:text-blue-
400 font-semibold border-r-4 border-blue-700 dark:border-blue-400 transition-
colors bg-slate-200/50" href="#">
<span class="material-symbols-outlined mr-3">dashboard</span>
## Dashboard
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-

slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">group</span>
## Patients
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">calendar_today</span>
## Appointments
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">analytics</span>
## Analytics
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">description</span>
## Reports
## </a>
## </div>
<div class="px-3 mt-auto">
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">settings</span>
## Settings
## </a>
## </div>
## </nav>
## <!-- Main Content Area -->
<main class="ml-64 min-h-screen">
<!-- TopNavBar Shell -->
<header class="flex justify-between items-center w-full px-8 h-16 sticky top-0
z-40 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md shadow-sm dark:shadow-
none font-inter text-base">
<div class="flex items-center flex-1 max-w-xl">
<div class="relative w-full">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2
text-on-surface-variant">search</span>
<input class="w-full bg-surface-container-low border-none rounded-full py-2 pl-
10 pr-4 focus:ring-2 focus:ring-primary/20 text-sm" placeholder="Search patient
ID, name, or clinician..." type="text"/>
## </div>
## </div>
<div class="flex items-center gap-4 ml-8">
<button class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2

transition-all active:scale-95 duration-200 text-slate-400">
<span class="material-symbols-outlined">notifications</span>
## </button>
<button class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2
transition-all active:scale-95 duration-200 text-slate-400">
<span class="material-symbols-outlined">help_outline</span>
## </button>
<div class="h-8 w-px bg-outline-variant/30 mx-2"></div>
<div class="flex items-center gap-3">
<div class="text-right hidden sm:block">
<p class="text-xs font-bold text-on-surface">Dr. Sarah Chen</p>
<p class="text-[10px] text-on-surface-variant">Senior Hematologist</p>
## </div>
<img alt="Clinician Profile" class="w-10 h-10 rounded-full object-cover border-
2 border-primary-container" data-alt="Professional headshot of a female doctor
in a white lab coat, clean studio lighting, high-end medical professional
aesthetic" src="https://lh3.googleusercontent.com/aida-
public/AB6AXuCXrB3e1MU9LmJZ30QnVVf2sRlJvxMCGGwPCFXp9NxAqlzGMHSSZCdRy-
y9wtsBG2MIb0oBu4zB3WeLINoZutTwHVuQyaEbT7j4lRK8pB2HASP2Q9u7w_hLjHZpkBWQL_QBvDe-
o92NJbrGYWryWmSN5r7uO6-
f4xQxz8B4YugRAxMRV32Bj0nAF8tQkVYRk50oyvKzakmu62q78AskhgXniuEeqe9AVE2bV9TgBa3BOU
5vyZMRfmzznUfANTvl9EovKplKInlYCmQ"/>
## </div>
## </div>
## </header>
## <!-- Content Canvas -->
<div class="p-8 space-y-8">
<!-- Section 1: Clinic Performance (Bento Stats) -->
## <section>
<div class="flex items-end justify-between mb-6">
## <div>
<h2 class="text-[0.75rem] font-bold text-primary uppercase tracking-
widest">Clinic Performance</h2>
<h3 class="text-2xl font-medium text-on-surface mt-1">Live Operations
## Monitor</h3>
## </div>
<p class="text-sm text-on-surface-variant">Last updated: Just now</p>
## </div>
<div class="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-6"><!-- Total
## Patients Analyzed -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-tertiary bg-tertiary-container/20
p-2 rounded-lg">group</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-
container/10 px-2 py-1 rounded">+8%</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Total Patients
## Analyzed</p>

<h4 class="text-4xl font-semibold text-on-surface mt-2">1,248</h4>
## </div>
## <!-- Active Cases -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-primary bg-primary/10 p-2 rounded-
lg">clinical_notes</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-
container/10 px-2 py-1 rounded">+12%</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Active Cases</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">142</h4>
## </div>
## <!-- Critical Results -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-secondary bg-secondary/10 p-2
rounded-lg">emergency_home</span>
<span class="text-[10px] font-bold text-secondary-container bg-secondary-
container/10 px-2 py-1 rounded">URGENT</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Critical Results</p>
<h4 class="text-4xl font-semibold text-secondary mt-2">08</h4>
## </div>
## <!-- Pending Reviews -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-outline bg-surface-container-high
p-2 rounded-lg">pending_actions</span>
<span class="text-[10px] font-bold text-on-surface-variant bg-surface-
container-high px-2 py-1 rounded">2h avg</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Pending Reviews</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">24</h4>
## </div>
## <!-- Completed Today -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-tertiary bg-tertiary-container/20
p-2 rounded-lg">task_alt</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-
container/10 px-2 py-1 rounded">88% target</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Completed Today</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">56</h4>
## </div></div>

## </section>
## <!-- Main Layout Grid: Patient Flow + Clinical Insights / Action Required -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
## <!-- Left: Patient Flow & Clinical Insights -->
<div class="lg:col-span-8 space-y-8">
## <!-- Patient Flow -->
<div class="bg-surface-container-low rounded-xl overflow-hidden">
<div class="p-6 bg-surface-container-lowest flex justify-between items-center">
<h3 class="text-lg font-medium text-on-surface">Recently Analyzed Patients</h3>
<button class="text-primary text-sm font-semibold hover:underline">View
## All</button>
## </div>
<div class="divide-y divide-transparent">
## <!-- Patient Item 1 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-
center text-primary font-bold">JD</div>
## <div>
<p class="font-medium text-on-surface">Johnathan Doe</p>
<p class="text-xs text-on-surface-variant">ID: #MS-94021</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-secondary-
container text-white uppercase tracking-wider">Critical</span>
<p class="text-xs text-on-surface-variant w-24">12 mins ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## <!-- Patient Item 2 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-surface-tint/10 flex items-center
justify-center text-primary font-bold">MS</div>
## <div>
<p class="font-medium text-on-surface">Maria Sanchez</p>
<p class="text-xs text-on-surface-variant">ID: #MS-88123</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-surface-container-
highest text-on-surface-variant uppercase tracking-wider">Moderate</span>
<p class="text-xs text-on-surface-variant w-24">45 mins ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>

## </div>
## <!-- Patient Item 3 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-tertiary-container/10 flex items-center
justify-center text-tertiary font-bold">AW</div>
## <div>
<p class="font-medium text-on-surface">Arthur Wright</p>
<p class="text-xs text-on-surface-variant">ID: #MS-77120</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-tertiary-container
text-white uppercase tracking-wider">Normal</span>
<p class="text-xs text-on-surface-variant w-24">1 hour ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## </div>
## </div>
<!-- Clinical Insights (Line Graph) -->
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm">
<div class="flex justify-between items-start mb-8">
## <div>
<h3 class="text-lg font-medium text-on-surface">Clinical Insights</h3>
<p class="text-sm text-on-surface-variant">Diagnostic volume trend (7-day
period)</p>
## </div>
<select class="bg-surface-container-low border-none rounded-lg text-xs font-
semibold py-1 px-3">
<option>Weekly</option>
<option>Monthly</option>
## </select>
## </div>
## <!-- Professional Line Graph Visual -->
<div class="relative h-48 w-full">
## <!-- Vertical Grid Lines -->
<div class="absolute inset-0 flex justify-between px-2 opacity-10">
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
## </div>
<!-- Line SVG -->
<svg class="absolute inset-0 w-full h-full" preserveaspectratio="none"

viewbox="0 0 700 200">
## <defs>
<lineargradient id="lineGradient" x1="0%" x2="0%" y1="0%" y2="100%"><stop
offset="0%" stop-color="rgba(0, 103, 34, 0.1)"></stop><stop offset="100%" stop-
color="rgba(0, 103, 34, 0)"></stop></lineargradient>
## </defs>
## <!-- Area Fill -->
<path d="M 0 120 L 116 100 L 232 60 L 348 20 L 464 45 L 580 90 L 700 130 L 700
200 L 0 200 Z" fill="url(#lineGradient)"></path>
## <!-- Main Line -->
<path d="M 0 120 L 116 100 L 232 60 L 348 20 L 464 45 L 580 90 L 700 130"
fill="none" stroke="#006722" stroke-linecap="round" stroke-linejoin="round"
stroke-width="3"></path>
## </svg>
## <!-- Interactive Data Points -->
<div class="absolute inset-0 flex justify-between px-2">
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 120px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">120</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 100px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">140</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 60px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">210</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 20px; transform: translateY(-50%);">
<div class="w-3 h-3 rounded-full border-2 border-white shadow-md ring-4 bg-
tertiary-container ring-tertiary-container/20"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded">284</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 45px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-

tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">245</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 90px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">180</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 130px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-4 bg-
tertiary-container ring-tertiary-container/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">95</div>
## </div>
## </div>
## </div>
<div class="flex justify-between mt-4 text-[10px] font-bold text-on-surface-
variant uppercase tracking-widest px-1">
<span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span>
<span>Fri</span><span>Sat</span><span>Sun</span>
## </div>
## </div>
## </div>
## <!-- Right: Action Required Sidebar -->
<div class="lg:col-span-4 space-y-6">
<div class="bg-surface-container-lowest p-6 rounded-xl border-l-4 border-
secondary">
<div class="flex items-center gap-3 mb-6">
<span class="material-symbols-outlined text-secondary" style="font-variation-
settings: 'FILL' 1;">warning</span>
<h3 class="text-lg font-semibold text-on-surface">Action Required</h3>
## </div>
<div class="space-y-4">
## <!-- Task 1 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-secondary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-secondary uppercase">High
## Priority</span>
<span class="text-[10px] text-on-surface-variant">10:45 AM</span>
## </div>
<p class="text-sm font-medium text-on-surface">Review Hematology Lab #4922</p>
<p class="text-xs text-on-surface-variant mt-1">Patient: Robert Miller (ICU-2)
## </p>

<button class="mt-4 w-full bg-secondary text-white text-xs font-bold py-2
rounded-lg hover:opacity-90 transition-opacity">Launch Review</button>
## </div>
## <!-- Task 2 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-primary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-primary uppercase">Standard</span>
<span class="text-[10px] text-on-surface-variant">09:15 AM</span>
## </div>
<p class="text-sm font-medium text-on-surface">Finalize Discharge Report</p>
<p class="text-xs text-on-surface-variant mt-1">Patient: Sarah Jenkins</p>
<button class="mt-4 w-full border border-primary text-primary text-xs font-bold
py-2 rounded-lg hover:bg-primary/5 transition-colors">Complete Task</button>
## </div>
## <!-- Task 3 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-primary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-primary uppercase">Follow-up</span>
<span class="text-[10px] text-on-surface-variant">Yesterday</span>
## </div>
<p class="text-sm font-medium text-on-surface">Verify Insurance Pre-Auth</p>
<p class="text-xs text-on-surface-variant mt-1">Provider: Aetna Clinical</p>
<button class="mt-4 w-full border border-primary text-primary text-xs font-bold
py-2 rounded-lg hover:bg-primary/5 transition-colors">Call Provider</button>
## </div>
## </div>
<button class="w-full mt-6 py-3 text-sm text-on-surface-variant font-medium bg-
surface-container-low rounded-lg hover:bg-surface-container-high transition-
colors">
## View All (14 Tasks)
## </button>
## </div>
<!-- Clinical Tip/Ad -->
<div class="relative overflow-hidden rounded-xl p-6 text-white group">
<div class="absolute inset-0 bg-gradient-to-br from-primary to-primary-
container z-0"></div>
<img alt="Laboratory" class="absolute inset-0 w-full h-full object-cover
opacity-20 mix-blend-overlay group-hover:scale-110 transition-transform
duration-700" data-alt="Close up of high-tech laboratory diagnostic equipment
with blue medical lighting and scientific research aesthetic"
src="https://lh3.googleusercontent.com/aida-
public/AB6AXuAyzxubzHQjCA5SCs2T2jz4NtpcKALxm3NIhertJC5c1wCmn08KGWtl0QY01xiQ7fIb
yXsft0HIuahbPrfGn91US83RaY02tennXRa6J8f0HvNMTTfipPUNUP516uqGhXkknhDHdOt3PJdjobt
aOFIvoJ1sdMO6gfJSWv-s2I-
Sc4JCLGvwcG_O0GuZFPOsvaXGFKBuLCZBopufwnYiLNspVlYp8o5vGAEEDljpSSjd4xBAbZJHNXldjC
f5YXT7EdhupZ0PZNf_1ls"/>
<div class="relative z-10">
<span class="material-symbols-outlined mb-4">info</span>
<h4 class="font-bold text-lg mb-2">System Update</h4>
<p class="text-xs opacity-90 leading-relaxed mb-4">New AI-driven hematology

markers are now live for all patients in the Critical category.</p>
<a class="text-xs font-bold underline underline-offset-4" href="#">Learn
## More</a>
## </div>
## </div>
## </div>
## </div>
## </div>
## </main>
## </body></html>
## ===============================================================================
## =
FILE: mediscan_dashboard_with_trend_line\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediScan - Clinical Precision Dashboard</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "surface": "#f8f9fa",
## "on-surface": "#191c1d",
## "surface-container-lowest": "#ffffff",
## "error-container": "#ffdad6",
## "on-primary-fixed-variant": "#004491",
## "surface-bright": "#f8f9fa",
## "outline": "#727784",
## "on-primary": "#ffffff",
## "surface-tint": "#115cb9",
## "on-secondary-container": "#fffbff",
## "on-secondary": "#ffffff",
## "surface-container-highest": "#e1e3e4",
## "on-error": "#ffffff",
## "primary-container": "#0056b3",

## "on-tertiary": "#ffffff",
## "tertiary-container": "#006722",
## "on-background": "#191c1d",
## "on-surface-variant": "#424752",
## "inverse-surface": "#2e3132",
## "secondary-fixed": "#ffdad9",
## "on-tertiary-fixed-variant": "#00531a",
## "primary-fixed-dim": "#acc7ff",
## "surface-variant": "#e1e3e4",
## "surface-container-low": "#f3f4f5",
## "surface-container": "#edeeef",
## "on-tertiary-container": "#6fe87c",
## "primary-fixed": "#d7e2ff",
## "tertiary-fixed-dim": "#66df75",
## "on-tertiary-fixed": "#002106",
## "secondary": "#b6152e",
## "error": "#ba1a1a",
## "on-error-container": "#93000a",
## "tertiary": "#004c17",
## "on-primary-fixed": "#001a40",
## "on-secondary-fixed": "#410008",
## "surface-container-high": "#e7e8e9",
## "secondary-fixed-dim": "#ffb3b2",
## "inverse-primary": "#acc7ff",
## "on-primary-container": "#bbd0ff",
## "primary": "#003f87",
## "background": "#f8f9fa",
## "surface-dim": "#d9dadb",
## "inverse-on-surface": "#f0f1f2",
## "tertiary-fixed": "#83fc8e",
## "secondary-container": "#d93343",
## "on-secondary-fixed-variant": "#92001f",
## "outline-variant": "#c2c6d4"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]
## }
## },
## },
## }
## </script>
## <style>

body { font-family: 'Inter', sans-serif; }
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
## .custom-glass {
background: rgba(255, 255, 255, 0.8);
backdrop-filter: blur(20px);
## }
## </style>
## </head>
<body class="bg-surface text-on-surface antialiased">
<!-- SideNavBar Shell -->
<nav class="flex flex-col fixed left-0 top-0 h-full py-6 bg-slate-50 dark:bg-
slate-900 h-screen w-64 border-r-0 z-50 font-inter text-sm antialiased">
<div class="px-6 mb-10">
<h1 class="text-xl font-bold tracking-tight text-blue-800 dark:text-blue-
300">MediScan</h1>
<p class="text-xs text-on-surface-variant/70 uppercase tracking-widest mt-
1">Clinical Precision</p>
## </div>
<div class="flex-1 space-y-1 px-3">
<a class="flex items-center px-4 py-3 rounded-lg text-blue-700 dark:text-blue-
400 font-semibold border-r-4 border-blue-700 dark:border-blue-400 transition-
colors bg-slate-200/50" href="#">
<span class="material-symbols-outlined mr-3">dashboard</span>
## Dashboard
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">group</span>
## Patients
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">calendar_today</span>
## Appointments
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">analytics</span>
## Analytics
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">description</span>
## Reports

## </a>
## </div>
<div class="px-3 mt-auto">
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">settings</span>
## Settings
## </a>
## </div>
## </nav>
## <!-- Main Content Area -->
<main class="ml-64 min-h-screen">
<!-- TopNavBar Shell -->
<header class="flex justify-between items-center w-full px-8 h-16 sticky top-0
z-40 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md shadow-sm dark:shadow-
none font-inter text-base">
<div class="flex items-center flex-1 max-w-xl">
<div class="relative w-full">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2
text-on-surface-variant">search</span>
<input class="w-full bg-surface-container-low border-none rounded-full py-2 pl-
10 pr-4 focus:ring-2 focus:ring-primary/20 text-sm" placeholder="Search patient
ID, name, or clinician..." type="text"/>
## </div>
## </div>
<div class="flex items-center gap-4 ml-8">
<button class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2
transition-all active:scale-95 duration-200 text-slate-400">
<span class="material-symbols-outlined">notifications</span>
## </button>
<button class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2
transition-all active:scale-95 duration-200 text-slate-400">
<span class="material-symbols-outlined">help_outline</span>
## </button>
<div class="h-8 w-px bg-outline-variant/30 mx-2"></div>
<div class="flex items-center gap-3">
<div class="text-right hidden sm:block">
<p class="text-xs font-bold text-on-surface">Dr. Sarah Chen</p>
<p class="text-[10px] text-on-surface-variant">Senior Hematologist</p>
## </div>
<img alt="Clinician Profile" class="w-10 h-10 rounded-full object-cover border-
2 border-primary-container" data-alt="Professional headshot of a female doctor
in a white lab coat, clean studio lighting, high-end medical professional
aesthetic" src="https://lh3.googleusercontent.com/aida-
public/AB6AXuCXrB3e1MU9LmJZ30QnVVf2sRlJvxMCGGwPCFXp9NxAqlzGMHSSZCdRy-
y9wtsBG2MIb0oBu4zB3WeLINoZutTwHVuQyaEbT7j4lRK8pB2HASP2Q9u7w_hLjHZpkBWQL_QBvDe-
o92NJbrGYWryWmSN5r7uO6-
f4xQxz8B4YugRAxMRV32Bj0nAF8tQkVYRk50oyvKzakmu62q78AskhgXniuEeqe9AVE2bV9TgBa3BOU
5vyZMRfmzznUfANTvl9EovKplKInlYCmQ"/>

## </div>
## </div>
## </header>
## <!-- Content Canvas -->
<div class="p-8 space-y-8">
<!-- Section 1: Clinic Performance (Bento Stats) -->
## <section>
<div class="flex items-end justify-between mb-6">
## <div>
<h2 class="text-[0.75rem] font-bold text-primary uppercase tracking-
widest">Clinic Performance</h2>
<h3 class="text-2xl font-medium text-on-surface mt-1">Live Operations
## Monitor</h3>
## </div>
<p class="text-sm text-on-surface-variant">Last updated: Just now</p>
## </div>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
## <!-- Active Cases -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-primary bg-primary/10 p-2 rounded-
lg">clinical_notes</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-
container/10 px-2 py-1 rounded">+12%</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Active Cases</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">142</h4>
## </div>
## <!-- Critical Results -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-secondary bg-secondary/10 p-2
rounded-lg">emergency_home</span>
<span class="text-[10px] font-bold text-secondary-container bg-secondary-
container/10 px-2 py-1 rounded">URGENT</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Critical Results</p>
<h4 class="text-4xl font-semibold text-secondary mt-2">08</h4>
## </div>
## <!-- Pending Reviews -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-outline bg-surface-container-high
p-2 rounded-lg">pending_actions</span>
<span class="text-[10px] font-bold text-on-surface-variant bg-surface-
container-high px-2 py-1 rounded">2h avg</span>
## </div>

<p class="text-sm text-on-surface-variant font-medium">Pending Reviews</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">24</h4>
## </div>
## <!-- Completed Today -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-tertiary bg-tertiary-container/20
p-2 rounded-lg">task_alt</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-
container/10 px-2 py-1 rounded">88% target</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Completed Today</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">56</h4>
## </div>
## </div>
## </section>
## <!-- Main Layout Grid: Patient Flow + Clinical Insights / Action Required -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
## <!-- Left: Patient Flow & Clinical Insights -->
<div class="lg:col-span-8 space-y-8">
## <!-- Patient Flow -->
<div class="bg-surface-container-low rounded-xl overflow-hidden">
<div class="p-6 bg-surface-container-lowest flex justify-between items-center">
<h3 class="text-lg font-medium text-on-surface">Recently Analyzed Patients</h3>
<button class="text-primary text-sm font-semibold hover:underline">View
## All</button>
## </div>
<div class="divide-y divide-transparent">
## <!-- Patient Item 1 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-
center text-primary font-bold">JD</div>
## <div>
<p class="font-medium text-on-surface">Johnathan Doe</p>
<p class="text-xs text-on-surface-variant">ID: #MS-94021</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-secondary-
container text-white uppercase tracking-wider">Critical</span>
<p class="text-xs text-on-surface-variant w-24">12 mins ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## <!-- Patient Item 2 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-

high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-surface-tint/10 flex items-center
justify-center text-primary font-bold">MS</div>
## <div>
<p class="font-medium text-on-surface">Maria Sanchez</p>
<p class="text-xs text-on-surface-variant">ID: #MS-88123</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-surface-container-
highest text-on-surface-variant uppercase tracking-wider">Moderate</span>
<p class="text-xs text-on-surface-variant w-24">45 mins ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## <!-- Patient Item 3 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-tertiary-container/10 flex items-center
justify-center text-tertiary font-bold">AW</div>
## <div>
<p class="font-medium text-on-surface">Arthur Wright</p>
<p class="text-xs text-on-surface-variant">ID: #MS-77120</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-tertiary-container
text-white uppercase tracking-wider">Normal</span>
<p class="text-xs text-on-surface-variant w-24">1 hour ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## </div>
## </div>
<!-- Clinical Insights (Line Graph) -->
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm">
<div class="flex justify-between items-start mb-8">
## <div>
<h3 class="text-lg font-medium text-on-surface">Clinical Insights</h3>
<p class="text-sm text-on-surface-variant">Diagnostic volume trend (7-day
period)</p>
## </div>
<select class="bg-surface-container-low border-none rounded-lg text-xs font-
semibold py-1 px-3">
<option>Weekly</option>
<option>Monthly</option>

## </select>
## </div>
## <!-- Professional Line Graph Visual -->
<div class="relative h-48 w-full">
## <!-- Vertical Grid Lines -->
<div class="absolute inset-0 flex justify-between px-2 opacity-10">
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
<div class="w-px h-full bg-primary"></div>
## </div>
<!-- Line SVG -->
<svg class="absolute inset-0 w-full h-full" preserveaspectratio="none"
viewbox="0 0 700 200">
## <defs>
<lineargradient id="lineGradient" x1="0%" x2="0%" y1="0%" y2="100%">
<stop offset="0%" stop-color="rgba(0, 63, 135, 0.1)"></stop>
<stop offset="100%" stop-color="rgba(0, 63, 135, 0)"></stop>
## </lineargradient>
## </defs>
## <!-- Area Fill -->
<path d="M 0 120 L 116 100 L 232 60 L 348 20 L 464 45 L 580 90 L 700 130 L 700
200 L 0 200 Z" fill="url(#lineGradient)"></path>
## <!-- Main Line -->
<path d="M 0 120 L 116 100 L 232 60 L 348 20 L 464 45 L 580 90 L 700 130"
fill="none" stroke="#003f87" stroke-linecap="round" stroke-linejoin="round"
stroke-width="3"></path>
## </svg>
## <!-- Interactive Data Points -->
<div class="absolute inset-0 flex justify-between px-2">
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 120px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full bg-primary border-2 border-white shadow-sm
ring-4 ring-primary/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">120</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 100px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full bg-primary border-2 border-white shadow-sm
ring-4 ring-primary/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">140</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-

top: 60px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full bg-primary border-2 border-white shadow-sm
ring-4 ring-primary/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">210</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 20px; transform: translateY(-50%);">
<div class="w-3 h-3 rounded-full bg-primary border-2 border-white shadow-md
ring-4 ring-primary/20"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded">284</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 45px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full bg-primary border-2 border-white shadow-sm
ring-4 ring-primary/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">245</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 90px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full bg-primary border-2 border-white shadow-sm
ring-4 ring-primary/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">180</div>
## </div>
<div class="relative group h-full flex flex-col justify-start" style="margin-
top: 130px; transform: translateY(-50%);">
<div class="w-2.5 h-2.5 rounded-full bg-primary border-2 border-white shadow-sm
ring-4 ring-primary/5"></div>
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-
opacity">95</div>
## </div>
## </div>
## </div>
<div class="flex justify-between mt-4 text-[10px] font-bold text-on-surface-
variant uppercase tracking-widest px-1">
<span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span>
<span>Fri</span><span>Sat</span><span>Sun</span>
## </div>
## </div>
## </div>
## <!-- Right: Action Required Sidebar -->
<div class="lg:col-span-4 space-y-6">
<div class="bg-surface-container-lowest p-6 rounded-xl border-l-4 border-

secondary">
<div class="flex items-center gap-3 mb-6">
<span class="material-symbols-outlined text-secondary" style="font-variation-
settings: 'FILL' 1;">warning</span>
<h3 class="text-lg font-semibold text-on-surface">Action Required</h3>
## </div>
<div class="space-y-4">
## <!-- Task 1 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-secondary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-secondary uppercase">High
## Priority</span>
<span class="text-[10px] text-on-surface-variant">10:45 AM</span>
## </div>
<p class="text-sm font-medium text-on-surface">Review Hematology Lab #4922</p>
<p class="text-xs text-on-surface-variant mt-1">Patient: Robert Miller (ICU-2)
## </p>
<button class="mt-4 w-full bg-secondary text-white text-xs font-bold py-2
rounded-lg hover:opacity-90 transition-opacity">Launch Review</button>
## </div>
## <!-- Task 2 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-primary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-primary uppercase">Standard</span>
<span class="text-[10px] text-on-surface-variant">09:15 AM</span>
## </div>
<p class="text-sm font-medium text-on-surface">Finalize Discharge Report</p>
<p class="text-xs text-on-surface-variant mt-1">Patient: Sarah Jenkins</p>
<button class="mt-4 w-full border border-primary text-primary text-xs font-bold
py-2 rounded-lg hover:bg-primary/5 transition-colors">Complete Task</button>
## </div>
## <!-- Task 3 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-primary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-primary uppercase">Follow-up</span>
<span class="text-[10px] text-on-surface-variant">Yesterday</span>
## </div>
<p class="text-sm font-medium text-on-surface">Verify Insurance Pre-Auth</p>
<p class="text-xs text-on-surface-variant mt-1">Provider: Aetna Clinical</p>
<button class="mt-4 w-full border border-primary text-primary text-xs font-bold
py-2 rounded-lg hover:bg-primary/5 transition-colors">Call Provider</button>
## </div>
## </div>
<button class="w-full mt-6 py-3 text-sm text-on-surface-variant font-medium bg-
surface-container-low rounded-lg hover:bg-surface-container-high transition-
colors">
## View All (14 Tasks)
## </button>
## </div>
<!-- Clinical Tip/Ad -->

<div class="relative overflow-hidden rounded-xl p-6 text-white group">
<div class="absolute inset-0 bg-gradient-to-br from-primary to-primary-
container z-0"></div>
<img alt="Laboratory" class="absolute inset-0 w-full h-full object-cover
opacity-20 mix-blend-overlay group-hover:scale-110 transition-transform
duration-700" data-alt="Close up of high-tech laboratory diagnostic equipment
with blue medical lighting and scientific research aesthetic"
src="https://lh3.googleusercontent.com/aida-
public/AB6AXuAyzxubzHQjCA5SCs2T2jz4NtpcKALxm3NIhertJC5c1wCmn08KGWtl0QY01xiQ7fIb
yXsft0HIuahbPrfGn91US83RaY02tennXRa6J8f0HvNMTTfipPUNUP516uqGhXkknhDHdOt3PJdjobt
aOFIvoJ1sdMO6gfJSWv-s2I-
Sc4JCLGvwcG_O0GuZFPOsvaXGFKBuLCZBopufwnYiLNspVlYp8o5vGAEEDljpSSjd4xBAbZJHNXldjC
f5YXT7EdhupZ0PZNf_1ls"/>
<div class="relative z-10">
<span class="material-symbols-outlined mb-4">info</span>
<h4 class="font-bold text-lg mb-2">System Update</h4>
<p class="text-xs opacity-90 leading-relaxed mb-4">New AI-driven hematology
markers are now live for all patients in the Critical category.</p>
<a class="text-xs font-bold underline underline-offset-4" href="#">Learn
## More</a>
## </div>
## </div>
## </div>
## </div>
## </div>
## </main>
## </body></html>
## ===============================================================================
## =
FILE: mediscan_home_page\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediScan - AI-Powered Drug Recommendation System</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700;800&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>

<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "on-secondary-fixed-variant": "#92001f",
## "on-error-container": "#93000a",
## "inverse-on-surface": "#f0f1f2",
## "on-secondary-fixed": "#410008",
## "on-surface-variant": "#424752",
## "surface-variant": "#e1e3e4",
## "on-primary": "#ffffff",
## "secondary": "#b6152e",
## "surface-container-lowest": "#ffffff",
## "on-secondary-container": "#fffbff",
## "secondary-container": "#d93343",
## "on-tertiary-fixed-variant": "#00531a",
## "on-tertiary-container": "#6fe87c",
## "outline-variant": "#c2c6d4",
## "on-secondary": "#ffffff",
## "surface-container-low": "#f3f4f5",
## "error": "#ba1a1a",
## "on-primary-container": "#bbd0ff",
## "on-background": "#191c1d",
## "surface-container-highest": "#e1e3e4",
## "secondary-fixed": "#ffdad9",
## "inverse-primary": "#acc7ff",
## "surface-tint": "#115cb9",
## "surface-container": "#edeeef",
## "on-primary-fixed-variant": "#004491",
## "primary-fixed-dim": "#acc7ff",
## "primary-fixed": "#d7e2ff",
## "tertiary": "#004c17",
## "tertiary-container": "#006722",
## "on-tertiary": "#ffffff",
## "primary": "#003f87",
## "primary-container": "#0056b3",
## "surface-dim": "#d9dadb",
## "error-container": "#ffdad6",
## "on-primary-fixed": "#001a40",
## "surface-container-high": "#e7e8e9",
## "on-error": "#ffffff",
## "surface-bright": "#f8f9fa",
## "on-surface": "#191c1d",
## "background": "#f8f9fa",
## "surface": "#f8f9fa",
## "inverse-surface": "#2e3132",
## "tertiary-fixed": "#83fc8e",
## "on-tertiary-fixed": "#002106",

## "outline": "#727784",
## "secondary-fixed-dim": "#ffb3b2",
## "tertiary-fixed-dim": "#66df75"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]
## }
## },
## },
## }
## </script>
## <style>
body { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400,
'GRAD' 0, 'opsz' 24; }
.glass-nav { backdrop-filter: blur(20px); border-bottom: 1px solid rgba(194,
## 198, 212, 0.2); }
.hero-gradient { background: linear-gradient(135deg, #003f87 0%, #0056b3 100%);
## }
.asymmetric-grid { display: grid; grid-template-columns: 1.2fr 0.8fr; gap:
## 2rem; }
@media (max-width: 768px) { .asymmetric-grid { grid-template-columns: 1fr; } }
## </style>
## </head>
<body class="text-on-background bg-surface">
<!-- TopNavBar -->
<nav class="fixed top-0 w-full z-50 bg-slate-50/80 dark:bg-slate-900/80
backdrop-blur-md shadow-sm dark:shadow-none transition-all duration-300 ease-
in-out">
<div class="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto">
<div class="text-2xl font-bold tracking-tight text-blue-900 dark:text-blue-100
font-sans antialiased">MediScan</div>
<div class="hidden md:flex items-center gap-8">
<a class="text-blue-700 dark:text-blue-400 font-semibold border-b-2 border-
blue-700 dark:border-blue-400 pb-1 font-sans antialiased text-sm tracking-wide"
href="#">Home</a>
<a class="text-slate-600 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors font-sans antialiased text-sm
tracking-wide" href="#">About</a>
<a class="text-slate-600 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors font-sans antialiased text-sm
tracking-wide" href="#">Support</a>

<button class="bg-primary text-on-primary px-6 py-2 rounded-lg font-medium
text-sm hover:opacity-90 transition-all">Portal Login</button>
## </div>
<button class="md:hidden p-2 hover:bg-slate-100/50 rounded-lg">
<span class="material-symbols-outlined">menu</span>
## </button>
## </div>
<div class="bg-slate-200/50 dark:bg-slate-800/50 h-[1px]"></div>
## </nav>
<main class="pt-20">
## <!-- Hero Section -->
<section class="relative px-6 py-24 md:py-32 overflow-hidden bg-surface">
<div class="max-w-7xl mx-auto asymmetric-grid items-center">
<div class="z-10">
<div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-
fixed text-on-primary-fixed text-xs font-bold tracking-widest uppercase mb-6">
<span class="material-symbols-outlined text-sm" style="font-variation-settings:
'FILL' 1;">bolt</span>
Next-Gen Medical AI
## </div>
<h1 class="text-5xl md:text-7xl font-semibold text-on-surface tracking-tight
leading-[1.1] mb-8">
AI-Powered Drug Recommendation System.
## </h1>
<p class="text-xl text-on-surface-variant max-w-xl mb-10 leading-relaxed">
Analyze your symptoms and medical reports with precision. Experience a
sanctuary of digital health guided by advanced clinical algorithms.
## </p>
<div class="flex flex-col sm:flex-row gap-4">
<button class="hero-gradient text-on-primary px-8 py-4 rounded-lg font-semibold
text-lg shadow-xl shadow-primary/20 hover:scale-[1.02] transition-transform
flex items-center justify-center gap-3">
## Start Diagnosis
<span class="material-symbols-outlined">arrow_forward</span>
## </button>
<button class="bg-surface-container-highest text-on-surface px-8 py-4 rounded-
lg font-semibold text-lg hover:bg-surface-container-high transition-colors">
## View Sample Report
## </button>
## </div>
<div class="mt-12 flex items-center gap-6">
<div class="flex -space-x-3">
<img class="w-10 h-10 rounded-full border-2 border-surface" data-
alt="professional male doctor in white coat smiling with stethoscope"
src="https://lh3.googleusercontent.com/aida-
public/AB6AXuCCs2o0GkiGgilpcSDqmtZP22mQMylRD7CwL0ywcMlFbCE-nTZl2R-
91JUrA_GdFBitQjXPqg_0av-
41vqjAd7QvPBs_Wi224HcjTTUvTNV7GSXRtvRijnJ77rc6AU_drt4a1hSZaGVj-
rVXH5pqWj0NTfOu3DPzSA8Ali-RgY8HVjm6ASwQCEE35WTvhvTzIbYT2k6u-PJtNC6Ii7GgIylhc4-
ilZ-xLYvorj867fzPAtWOiHAzUbhVKy4H97rm5Vm5CvR8cpDsbo"/>

<img class="w-10 h-10 rounded-full border-2 border-surface" data-alt="female
medical specialist looking professional in clinical setting"
src="https://lh3.googleusercontent.com/aida-public/AB6AXuBi_P-
YKwZsJLi5uKtNk30iGB2WQQ19gkSPTW3-hL34WvJvPxaZhU_JV5IMIhr3N5iMVCLNXyJQ8tZrx-
ktVBPdS1hRjX4KCGMn_lIduOggROUOSKdTwqJ2K7eWKwESG_mc3wExufa1Cdfs0H-GOk6K-m28-
jrpnxLyXgsrEiExJRvTeaHcgeXwhVpFCMnva-6-
vqkqht2j6szwO_4mFnUlhjNHDCingV9Tbqi292YeehvDt7NTap60epPkkDUsRrGJJTfKo_gBUxk"/>
<img class="w-10 h-10 rounded-full border-2 border-surface" data-alt="middle
aged male physician with kind expression"
src="https://lh3.googleusercontent.com/aida-public/AB6AXuCAFXj-
DfiEYj6pEiuv64VCwn99fGiwktOdU0G_HFraC5A2SlL3wdNsYxDDKDIeG_U3Ejtw2xNTIeq8Eb34ubD
pzw3MhLGaPb--
mstp2rQzczkpMcpYrkj3oZwoD2Pzfcsm7S8L_77Wuk87ngBmDEMprHsW1eHTuBphhKguaXdFkyn9PSV
w2OeQDxYnqDjlgpx6bu9Kgc0l6fcYY7DkIL5mEblZj1s7o3KgCBpCyRxU-
djHbVaHz81gR9ja7Ls4RmgA7VupXMp6hWU"/>
## </div>
<p class="text-sm text-on-surface-variant">Trusted by <span class="text-primary
font-bold">500+</span> healthcare professionals</p>
## </div>
## </div>
<div class="relative hidden md:block">
<div class="absolute -top-20 -right-20 w-96 h-96 bg-primary-fixed/20 rounded-
full blur-3xl"></div>
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-2xl relative z-10
border border-outline-variant/10">
<div class="flex items-center justify-between mb-8">
<h3 class="text-lg font-semibold text-on-surface">Vitals Monitoring</h3>
<span class="text-xs bg-tertiary-container text-on-tertiary px-2 py-1 rounded-
full">System Stable</span>
## </div>
<div class="space-y-6">
<div class="h-24 w-full bg-surface-container-low rounded-lg overflow-hidden
relative">
<div class="absolute inset-0 opacity-10 bg-[radial-
gradient(#003f87_1px,transparent_1px)] [background-size:16px_16px]"></div>
<!-- Micro-chart placeholder -->
<svg class="absolute inset-0 w-full h-full" viewbox="0 0 400 100">
<path d="M0 50 Q 50 20, 100 50 T 200 50 T 300 50 T 400 50" fill="none"
stroke="#115cb9" stroke-width="3"></path>
## </svg>
## </div>
<div class="grid grid-cols-2 gap-4">
<div class="p-4 bg-surface-container-low rounded-lg">
<span class="text-xs text-on-surface-variant block mb-1">Heart Rate</span>
<span class="text-2xl font-bold text-primary">72 BPM</span>
## </div>
<div class="p-4 bg-surface-container-low rounded-lg">
<span class="text-xs text-on-surface-variant block mb-1">Blood Oxygen</span>
<span class="text-2xl font-bold text-primary">98%</span>
## </div>

## </div>
## </div>
## </div>
## </div>
## </div>
## </section>
## <!-- Features Bento Grid -->
<section class="px-6 py-24 bg-surface-container-low">
<div class="max-w-7xl mx-auto">
<div class="mb-16">
<h2 class="text-3xl md:text-4xl font-semibold text-on-surface mb-4">Precision
## Diagnostics</h2>
<p class="text-on-surface-variant max-w-2xl">Advanced clinical modules designed
for high-accuracy medical analysis and decision support.</p>
## </div>
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
## <!-- Feature 1: Large -->
<div class="md:col-span-2 bg-surface-container-lowest p-8 rounded-xl shadow-sm
hover:shadow-md transition-shadow group">
<div class="flex flex-col h-full">
<div class="w-12 h-12 rounded-lg bg-primary-fixed flex items-center justify-
center text-primary mb-6 group-hover:scale-110 transition-transform">
<span class="material-symbols-outlined">analytics</span>
## </div>
<h3 class="text-2xl font-semibold text-on-surface mb-3">Disease Prediction</h3>
<p class="text-on-surface-variant mb-8 flex-grow">Our proprietary AI engines
process thousands of data points to identify potential underlying conditions
before symptoms escalate.</p>
<img alt="" class="rounded-lg object-cover h-48 w-full" data-alt="microscopic
medical data visualization on a laboratory computer screen in a clean clinical
environment" src="https://lh3.googleusercontent.com/aida-
public/AB6AXuDcSoiz7CsDiJi_yDTPjh5eeradG4kgQlk8dm9aQSyefybfOCZLIU3Zodqxl_XRt1Xx
3pxjR_ASs4Hrg_87Ng6Qc4mp_C9V7LKwdkNf-
nnwQJwqmODK5Donzt0HzB9Sl8CLb9q_Te1yv6TFm2vNuzvb7kgt4U706b3v86--
u7T_awv5z_D9oGE4aKtH_2Aa1nP2b0sV0Hr3DHN0ofk4qYDeh-yapmyDbI4-_6dQyyHr7KFLtH-
hBBxdw_XsjUrDkTF0T5KcuTRMyaY"/>
## </div>
## </div>
## <!-- Feature 2: Small -->
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm hover:shadow-
md transition-shadow">
<div class="w-12 h-12 rounded-lg bg-secondary-fixed flex items-center justify-
center text-secondary mb-6">
<span class="material-symbols-outlined">medical_information</span>
## </div>
<h3 class="text-xl font-semibold text-on-surface mb-3">Drug
## Recommendations</h3>
<p class="text-on-surface-variant">Evidence-based medication suggestions cross-
referenced with your specific medical history and current prescriptions.</p>
## </div>

## <!-- Feature 3: Small -->
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm hover:shadow-
md transition-shadow">
<div class="w-12 h-12 rounded-lg bg-tertiary-fixed flex items-center justify-
center text-tertiary mb-6">
<span class="material-symbols-outlined">description</span>
## </div>
<h3 class="text-xl font-semibold text-on-surface mb-3">Report Analysis</h3>
<p class="text-on-surface-variant">Upload any lab result or clinical report to
receive an instant, plain-English breakdown of your data.</p>
## </div>
## <!-- Feature 4: Large -->
<div class="md:col-span-2 bg-surface-container-lowest p-8 rounded-xl shadow-sm
hover:shadow-md transition-shadow group flex flex-col md:flex-row gap-8">
<div class="flex-1">
<div class="w-12 h-12 rounded-lg bg-on-primary-fixed flex items-center justify-
center text-primary-fixed mb-6">
<span class="material-symbols-outlined">priority_high</span>
## </div>
<h3 class="text-2xl font-semibold text-on-surface mb-3">Severity Checks</h3>
<p class="text-on-surface-variant mb-6">Real-time triage system that classifies
health risks to ensure urgent cases receive immediate attention.</p>
<ul class="space-y-3">
<li class="flex items-center gap-2 text-sm text-on-surface">
<span class="material-symbols-outlined text-tertiary text-sm" style="font-
variation-settings: 'FILL' 1;">check_circle</span>
## Automated Triage
## </li>
<li class="flex items-center gap-2 text-sm text-on-surface">
<span class="material-symbols-outlined text-tertiary text-sm" style="font-
variation-settings: 'FILL' 1;">check_circle</span>
## Risk Factor Heatmaps
## </li>
## </ul>
## </div>
<div class="flex-1 rounded-lg overflow-hidden">
<img alt="" class="object-cover w-full h-full" data-alt="close up of medical
monitoring tablet showing critical patient data and health graphs"
src="https://lh3.googleusercontent.com/aida-
public/AB6AXuBfhVTFfN8ehFvfOzsg5c2B8iMp7pXO3moLEBPfnIdw68LQNNdSEiLF29TPZK-
CBImEy1kXJNv7GzrXp1U7GvpBqPG54TtmpzaQRdx4ZaXok_HESalB1LuAjcOzITQCfTFTDSUPK7GVlo
jkrkteFzR4KX7u-08U7H01bCtTCvlyCEPR8RVXBRV4x44WxMVenOhHwoePcSX7tM-
LaWfgg9r6ElLS33bcKONCSeYSJztM77N0oT1Bkhxx236MB8moCj-eNYDhPUL2eZ8"/>
## </div>
## </div>
## </div>
## </div>
## </section>
## <!-- Trust Section -->
<section class="px-6 py-24 bg-surface">

<div class="max-w-7xl mx-auto text-center">
<h3 class="text-sm font-bold uppercase tracking-widest text-on-surface-variant
mb-12">Built on Clinical Authority</h3>
<div class="flex flex-wrap justify-center items-center gap-12 md:gap-24
opacity-60">
<div class="flex items-center gap-2 text-xl font-bold"><span class="material-
symbols-outlined text-3xl">health_metrics</span> BioTech</div>
<div class="flex items-center gap-2 text-xl font-bold"><span class="material-
symbols-outlined text-3xl">clinical_notes</span> MediCore</div>
<div class="flex items-center gap-2 text-xl font-bold"><span class="material-
symbols-outlined text-3xl">science</span> LabQuest</div>
<div class="flex items-center gap-2 text-xl font-bold"><span class="material-
symbols-outlined text-3xl">vital_signs</span> HealthFlow</div>
## </div>
## </div>
## </section>
## </main>
## <!-- Footer -->
<footer class="w-full mt-auto py-12 bg-slate-100 dark:bg-slate-950 border-t
border-slate-200 dark:border-slate-800">
<div class="flex flex-col items-center gap-4 text-center px-4 w-full">
<div class="text-sm font-semibold text-slate-700 dark:text-slate-
300">MediScan</div>
<div class="flex flex-wrap justify-center gap-6">
<a class="text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 text-xs font-normal transition-colors duration-200"
href="#">Privacy Policy</a>
<a class="text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 text-xs font-normal transition-colors duration-200"
href="#">Terms of Service</a>
<a class="text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 text-xs font-normal transition-colors duration-200"
href="#">Medical Disclaimer</a>
## </div>
<p class="text-xs font-normal leading-relaxed text-slate-500 dark:text-slate-
400 max-w-md opacity-90">
© 2024 MediScan. For educational purposes only. Always consult a qualified
medical professional.
## </p>
## </div>
## </footer>
<!-- FAB for quick diagnosis - contextual only on home -->
<button class="fixed bottom-8 right-8 w-14 h-14 bg-primary text-on-primary
rounded-full shadow-2xl flex items-center justify-center hover:scale-110
transition-transform z-40">
<span class="material-symbols-outlined text-3xl">add</span>
## </button>
## </body></html>

## ===============================================================================
## =
FILE: mediscan_input_upload\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediScan - Analysis Input</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "on-secondary-fixed-variant": "#92001f",
## "on-error-container": "#93000a",
## "inverse-on-surface": "#f0f1f2",
## "on-secondary-fixed": "#410008",
## "on-surface-variant": "#424752",
## "surface-variant": "#e1e3e4",
## "on-primary": "#ffffff",
## "secondary": "#b6152e",
## "surface-container-lowest": "#ffffff",
## "on-secondary-container": "#fffbff",
## "secondary-container": "#d93343",
## "on-tertiary-fixed-variant": "#00531a",
## "on-tertiary-container": "#6fe87c",
## "outline-variant": "#c2c6d4",
## "on-secondary": "#ffffff",
## "surface-container-low": "#f3f4f5",
## "error": "#ba1a1a",
## "on-primary-container": "#bbd0ff",
## "on-background": "#191c1d",
## "surface-container-highest": "#e1e3e4",
## "secondary-fixed": "#ffdad9",
## "inverse-primary": "#acc7ff",

## "surface-tint": "#115cb9",
## "surface-container": "#edeeef",
## "on-primary-fixed-variant": "#004491",
## "primary-fixed-dim": "#acc7ff",
## "primary-fixed": "#d7e2ff",
## "tertiary": "#004c17",
## "tertiary-container": "#006722",
## "on-tertiary": "#ffffff",
## "primary": "#003f87",
## "primary-container": "#0056b3",
## "surface-dim": "#d9dadb",
## "error-container": "#ffdad6",
## "on-primary-fixed": "#001a40",
## "surface-container-high": "#e7e8e9",
## "on-error": "#ffffff",
## "surface-bright": "#f8f9fa",
## "on-surface": "#191c1d",
## "background": "#f8f9fa",
## "surface": "#f8f9fa",
## "inverse-surface": "#2e3132",
## "tertiary-fixed": "#83fc8e",
## "on-tertiary-fixed": "#002106",
## "outline": "#727784",
## "secondary-fixed-dim": "#ffb3b2",
## "tertiary-fixed-dim": "#66df75"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]
## }
## },
## },
## }
## </script>
## <style>
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
## .glass-nav {
backdrop-filter: blur(20px);
-webkit-backdrop-filter: blur(20px);

## }
## </style>
## </head>
<body class="bg-surface font-body text-on-surface antialiased">
## <!-- Top Navigation Bar -->
<nav class="fixed top-0 w-full z-50 bg-slate-50/80 dark:bg-slate-900/80
backdrop-blur-md shadow-sm dark:shadow-none">
<div class="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto
transition-all duration-300 ease-in-out">
<div class="text-2xl font-bold tracking-tight text-blue-900 dark:text-blue-100
font-headline">MediScan</div>
<div class="hidden md:flex items-center gap-8 text-sm font-sans antialiased
tracking-wide">
<a class="text-slate-600 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors" href="#">About</a>
<a class="text-slate-600 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors" href="#">Support</a>
<div class="flex items-center gap-3 pl-4 border-l border-slate-200 dark:border-
slate-800">
<span class="text-on-surface-variant font-medium">Dr. Julianne Miller</span>
<div class="w-8 h-8 rounded-full bg-primary-fixed overflow-hidden">
<img alt="Profile" data-alt="professional portrait of a female doctor in a
white lab coat with a warm friendly expression"
src="https://lh3.googleusercontent.com/aida-
public/AB6AXuCgWMp20zKF6j0_ehxrgv_9GugCWsyETuK4n-frJLWQDQ-
PzUyXFc39yA3dJl43HZj9SGQCX8vEfnawcJj-x55hFs-
BZzv47fcVYpSQ2Hq0jkLG1OO4CBRPy_Un00Npr9mgy3YzseQRkuuyaTAUQB1Z1QV4JjgWctSJRoufcd
nexuTrWpQ2GOdAeuiWoy2Dtx_SPOhavlaV2PwmWnhkPVIhoWTngp0aSqPGYAOYoPj4OnwbNxj2n7dsd
tkkPdbzSF9eMS3UHm3EJt8"/>
## </div>
## </div>
## </div>
<button class="md:hidden text-on-surface-variant">
<span class="material-symbols-outlined">menu</span>
## </button>
## </div>
<div class="bg-slate-200/50 dark:bg-slate-800/50 h-[1px]"></div>
## </nav>
<main class="pt-28 pb-20 px-6 max-w-7xl mx-auto min-h-screen flex flex-col">
## <!-- Header Section -->
<header class="mb-12">
<h1 class="text-3xl md:text-5xl font-medium tracking-tight mb-4 text-on-
surface">New Clinical Analysis</h1>
<p class="text-on-surface-variant text-lg max-w-2xl leading-relaxed">Input
patient parameters and diagnostic reports to generate a comprehensive AI-
assisted medical assessment.</p>
## </header>
<!-- Bento Grid Layout for Forms -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
## <!-- Left Column: Patient & History -->

<div class="lg:col-span-7 space-y-8">
## <!-- Patient Details Card -->
<section class="bg-surface-container-lowest p-8 rounded-xl transition-all
duration-300">
<div class="flex items-center gap-3 mb-8">
<div class="w-10 h-10 rounded-lg bg-primary/5 flex items-center justify-
center">
<span class="material-symbols-outlined text-primary">person</span>
## </div>
<h2 class="text-xl font-medium">Patient Details</h2>
## </div>
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
<div class="space-y-2">
<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider block">Age</label>
<input class="w-full px-4 py-3 bg-surface-container-low border-none rounded-lg
focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-
all" placeholder="Years" type="number"/>
## </div>
<div class="space-y-2">
<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider block">Gender</label>
<select class="w-full px-4 py-3 bg-surface-container-low border-none rounded-lg
focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-
all">
<option>Male</option>
<option>Female</option>
<option>Other</option>
## </select>
## </div>
<div class="space-y-2">
<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider block">Weight (kg)</label>
<input class="w-full px-4 py-3 bg-surface-container-low border-none rounded-lg
focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-
all" placeholder="00.0" type="number"/>
## </div>
## </div>
## </section>
## <!-- Medical History Card -->
<section class="bg-surface-container-lowest p-8 rounded-xl transition-all
duration-300">
<div class="flex items-center gap-3 mb-8">
<div class="w-10 h-10 rounded-lg bg-tertiary/5 flex items-center justify-
center">
<span class="material-symbols-outlined text-tertiary">history_edu</span>
## </div>
<h2 class="text-xl font-medium">Medical History</h2>
## </div>
<div class="space-y-2">

<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider block">Existing Diseases &amp; Conditions</label>
<textarea class="w-full px-4 py-3 bg-surface-container-low border-none rounded-
lg focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest
transition-all resize-none" placeholder="Document previous diagnoses, chronic
conditions, and ongoing treatments..." rows="5"></textarea>
## </div>
## </section>
## </div>
## <!-- Right Column: Symptoms & Upload -->
<div class="lg:col-span-5 space-y-8">
## <!-- Symptom Analysis Card -->
<section class="bg-surface-container-lowest p-8 rounded-xl transition-all
duration-300">
<div class="flex items-center gap-3 mb-8">
<div class="w-10 h-10 rounded-lg bg-secondary/5 flex items-center justify-
center">
<span class="material-symbols-outlined text-secondary">monitor_heart</span>
## </div>
<h2 class="text-xl font-medium">Symptom Analysis</h2>
## </div>
<div class="space-y-6">
<div class="flex flex-wrap gap-2">
<span class="px-3 py-1.5 bg-secondary-container/10 text-secondary-container
border border-secondary-container/20 rounded-full text-xs font-medium cursor-
pointer hover:bg-secondary-container/20 transition-colors">Persistent
## Cough</span>
<span class="px-3 py-1.5 bg-surface-container-high text-on-surface-variant
rounded-full text-xs font-medium cursor-pointer hover:bg-surface-container-
highest transition-colors">Fatigue</span>
<span class="px-3 py-1.5 bg-surface-container-high text-on-surface-variant
rounded-full text-xs font-medium cursor-pointer hover:bg-surface-container-
highest transition-colors">Dizziness</span>
<span class="px-3 py-1.5 bg-surface-container-high text-on-surface-variant
rounded-full text-xs font-medium cursor-pointer hover:bg-surface-container-
highest transition-colors">Nausea</span>
<span class="px-3 py-1.5 bg-surface-container-high text-on-surface-variant
rounded-full text-xs font-medium cursor-pointer hover:bg-surface-container-
highest transition-colors">Joint Pain</span>
## </div>
<div class="space-y-2">
<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider block">Additional Observations</label>
<input class="w-full px-4 py-3 bg-surface-container-low border-none rounded-lg
focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-
all" placeholder="Type symptoms to add..." type="text"/>
## </div>
## </div>
## </section>
<!-- Report Upload Module (Anvil Style) -->

<section class="bg-surface-container-lowest p-8 rounded-xl transition-all
duration-300">
<div class="flex items-center gap-3 mb-8">
<div class="w-10 h-10 rounded-lg bg-primary/5 flex items-center justify-
center">
<span class="material-symbols-outlined text-primary">upload_file</span>
## </div>
<h2 class="text-xl font-medium">Report Upload Module</h2>
## </div>
<div class="relative group cursor-pointer">
<div class="border-2 border-dashed border-outline-variant rounded-xl p-10 flex
flex-col items-center justify-center gap-4 transition-all group-hover:border-
primary group-hover:bg-primary/5">
<div class="w-16 h-16 rounded-full bg-surface-container flex items-center
justify-center transition-all group-hover:scale-110">
<span class="material-symbols-outlined text-primary text-
## 3xl">cloud_upload</span>
## </div>
<div class="text-center">
<p class="text-on-surface font-medium mb-1">Upload PDF/Image Reports</p>
<p class="text-on-surface-variant text-sm">Drag &amp; Drop or <span
class="text-primary font-semibold">Browse Files</span></p>
## </div>
<input class="absolute inset-0 opacity-0 cursor-pointer" type="file"/>
## </div>
## </div>
<div class="mt-4 flex items-center gap-2 text-xs text-on-surface-variant">
<span class="material-symbols-outlined text-[16px]">info</span>
<span>Supported formats: PDF, PNG, JPG (Max 20MB)</span>
## </div>
## </section>
## </div>
## </div>
<!-- CTA Action Footer -->
<div class="mt-12 flex flex-col md:flex-row items-center justify-between gap-6
p-8 bg-surface-container-low rounded-xl">
<div class="flex items-center gap-4">
<span class="material-symbols-outlined text-tertiary-container text-
## 3xl">verified_user</span>
<p class="text-sm text-on-surface-variant leading-tight">Data is encrypted
using clinical-grade 256-bit protocols.<br/>Compliance verified for healthcare
standards.</p>
## </div>
<button class="w-full md:w-auto px-10 py-5 bg-gradient-to-br from-primary to-
primary-container text-on-primary rounded-lg font-semibold text-lg shadow-xl
shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all flex
items-center justify-center gap-3">
<span>Generate Analysis</span>
<span class="material-symbols-outlined">clinical_notes</span>
## </button>

## </div>
## </main>
## <!-- Footer -->
<footer class="w-full mt-auto py-12 bg-slate-100 dark:bg-slate-950 border-t
border-slate-200 dark:border-slate-800">
<div class="flex flex-col items-center gap-4 text-center px-4 w-full">
<div class="text-sm font-semibold text-slate-700 dark:text-slate-
300">MediScan</div>
<div class="flex flex-wrap justify-center gap-6">
<a class="text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 transition-colors duration-200 text-xs font-normal
leading-relaxed" href="#">Privacy Policy</a>
<a class="text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 transition-colors duration-200 text-xs font-normal
leading-relaxed" href="#">Terms of Service</a>
<a class="text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 transition-colors duration-200 text-xs font-normal
leading-relaxed" href="#">Medical Disclaimer</a>
## </div>
<p class="text-xs font-normal leading-relaxed text-slate-500 dark:text-slate-
400 max-w-xl">
© 2024 MediScan. For educational purposes only. Always consult a qualified
medical professional.
## </p>
## </div>
## </footer>
## </body></html>
## ===============================================================================
## =
FILE: mediscan_notification_settings\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Clinical Portal - Notification Settings</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700;800;900&amp;display=swap"
rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"

rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "on-primary-fixed": "#001a40",
## "tertiary-fixed-dim": "#66df75",
## "primary": "#003f87",
## "surface-container-highest": "#e1e3e4",
## "outline-variant": "#c2c6d4",
## "surface-variant": "#e1e3e4",
## "surface": "#f8f9fa",
## "on-surface-variant": "#424752",
## "tertiary-container": "#006722",
## "surface-container-high": "#e7e8e9",
## "on-surface": "#191c1d",
## "on-background": "#191c1d",
## "secondary": "#b6152e",
## "secondary-fixed-dim": "#ffb3b2",
## "surface-dim": "#d9dadb",
## "on-tertiary": "#ffffff",
## "outline": "#727784",
## "on-primary-container": "#bbd0ff",
## "inverse-primary": "#acc7ff",
## "on-tertiary-fixed": "#002106",
## "inverse-on-surface": "#f0f1f2",
## "background": "#f8f9fa",
## "primary-fixed": "#d7e2ff",
## "on-error": "#ffffff",
## "surface-container-lowest": "#ffffff",
## "surface-bright": "#f8f9fa",
## "on-secondary-fixed-variant": "#92001f",
## "on-primary": "#ffffff",
## "on-primary-fixed-variant": "#004491",
## "on-tertiary-fixed-variant": "#00531a",
## "on-secondary-container": "#fffbff",
## "on-secondary-fixed": "#410008",
## "primary-container": "#0056b3",
## "secondary-fixed": "#ffdad9",
## "surface-container": "#edeeef",
## "tertiary": "#004c17",
## "secondary-container": "#d93343",
## "on-tertiary-container": "#6fe87c",
## "on-error-container": "#93000a",
## "surface-container-low": "#f3f4f5",
## "primary-fixed-dim": "#acc7ff",
## "on-secondary": "#ffffff",
## "error": "#ba1a1a",

## "tertiary-fixed": "#83fc8e",
## "inverse-surface": "#2e3132",
## "surface-tint": "#115cb9",
## "error-container": "#ffdad6"
## },
"borderRadius": {
"DEFAULT": "0.5rem",
## "lg": "1rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter", "sans-serif"],
"body": ["Inter", "sans-serif"],
"label": ["Inter", "sans-serif"]
## }
## }
## }
## }
## </script>
## <style>
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
body { font-family: 'Inter', sans-serif; }
## </style>
## </head>
<body class="bg-surface text-on-surface flex min-h-screen">
<!-- SideNavBar Anchor -->
<aside class="h-screen w-64 fixed left-0 top-0 bg-slate-50 dark:bg-slate-900
border-r border-slate-200/50 dark:border-slate-800/50 flex flex-col py-6 z-50">
<div class="px-6 mb-8">
<h1 class="text-lg font-black text-blue-900 dark:text-blue-200">Clinical
## Portal</h1>
## </div>
<div class="px-6 mb-10 flex items-center gap-3">
<div class="w-10 h-10 rounded-full overflow-hidden bg-primary-container flex
items-center justify-center">
<img alt="Dr. Richardson" class="w-full h-full object-cover" data-
alt="Professional headshot of a senior male doctor in clinical attire with a
friendly, authoritative expression"
src="https://lh3.googleusercontent.com/aida-public/AB6AXuBWqOlvl5arSPHCCgVKj-
uQbaMtWUdJy_7ykjlhyav17Mii3RD4b_QkTttNBPzd9wH72oDFYHdS0xY6ty99AMwVW3tIyGr8D6zFL
sR2cjcgb8jK6fHrU5G7GFsl4_zyiDuLt_cbJtHrI-
7mhu8WLI8jSwEw3wxyGCFVAJaiKcWanDxwL4L84l4M9rHkxWw0XrfXqOUKPnjpM8VTAhk8S5-
lY8NI64I3T2So8A3WvyNCMoX1pDyjJXHQ2LwxkScm412xqinQv--tRXU"/>
## </div>
<div class="flex flex-col">
<span class="text-sm font-bold text-on-surface">Dr. Richardson</span>
<span class="text-[10px] text-on-surface-variant uppercase tracking-

wider">Senior Hematologist</span>
## </div>
## </div>
<nav class="flex-1 px-4 space-y-1">
<a class="flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400
hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900
dark:hover:text-slate-100 transition-all duration-200 ease-in-out text-sm font-
medium tracking-tight rounded-lg" href="#">
<span class="material-symbols-outlined" data-icon="dashboard">dashboard</span>
<span>Dashboard</span>
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400
hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900
dark:hover:text-slate-100 transition-all duration-200 ease-in-out text-sm font-
medium tracking-tight rounded-lg" href="#">
<span class="material-symbols-outlined" data-icon="group">group</span>
<span>Patients</span>
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400
hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900
dark:hover:text-slate-100 transition-all duration-200 ease-in-out text-sm font-
medium tracking-tight rounded-lg" href="#">
<span class="material-symbols-outlined" data-
icon="calendar_today">calendar_today</span>
<span>Schedule</span>
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400
hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900
dark:hover:text-slate-100 transition-all duration-200 ease-in-out text-sm font-
medium tracking-tight rounded-lg" href="#">
<span class="material-symbols-outlined" data-
icon="notifications_active">notifications_active</span>
<span>Alerts</span>
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-blue-700 dark:text-blue-400
font-bold border-r-4 border-blue-700 dark:border-blue-400 bg-slate-200 dark:bg-
slate-800 transition-all duration-200 ease-in-out text-sm tracking-tight
rounded-lg" href="#">
<span class="material-symbols-outlined" data-icon="settings">settings</span>
<span>Settings</span>
## </a>
## </nav>
<div class="mt-auto px-4 space-y-1 pt-6 border-t border-slate-200/50
dark:border-slate-800/50">
<a class="flex items-center gap-3 px-4 py-2 text-slate-600 dark:text-slate-400
hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900 transition-all
text-xs font-medium" href="#">
<span class="material-symbols-outlined" data-
icon="contact_support">contact_support</span>
<span>Support</span>

## </a>
<a class="flex items-center gap-3 px-4 py-2 text-slate-600 dark:text-slate-400
hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-secondary transition-all
text-xs font-medium" href="#">
<span class="material-symbols-outlined" data-icon="logout">logout</span>
<span>Log Out</span>
## </a>
## </div>
## </aside>
## <!-- Main Content Canvas -->
<main class="ml-64 flex-1 flex flex-col">
<!-- TopAppBar Anchor -->
<header class="bg-white dark:bg-slate-950 shadow-sm dark:shadow-none sticky
top-0 z-40 flex justify-between items-center px-10 py-4 w-full">
<div class="flex items-center gap-4">
<span class="text-xl font-bold text-blue-800 dark:text-blue-
300">Settings</span>
<span class="text-outline-variant">/</span>
<span class="text-sm font-semibold text-blue-700 dark:text-blue-
400">Notification Preferences</span>
## </div>
<div class="flex items-center gap-6">
<div class="relative flex items-center bg-slate-50 dark:bg-slate-900 rounded-
full px-4 py-2 w-64">
<span class="material-symbols-outlined text-slate-400 text-sm">search</span>
<input class="bg-transparent border-none focus:ring-0 text-sm w-full
placeholder:text-slate-400" placeholder="Search settings..." type="text"/>
## </div>
<div class="flex items-center gap-4">
<span class="material-symbols-outlined text-slate-500 cursor-pointer
hover:text-primary transition-colors" data-icon="help">help</span>
<span class="material-symbols-outlined text-slate-500 cursor-pointer
hover:text-primary transition-colors" data-
icon="account_circle">account_circle</span>
## </div>
## </div>
## </header>
## <!-- Content Area -->
<div class="p-10 max-w-5xl mx-auto w-full">
## <!-- Header Section -->
<div class="mb-12">
<h2 class="text-[1.75rem] font-medium text-on-surface mb-2">Notification
## Preferences</h2>
<p class="text-on-surface-variant max-w-2xl leading-relaxed">
Tailor your clinical communication experience. Manage how and when you receive
critical alerts, patient updates, and system security information.
## </p>
## </div>
<!-- Bento Grid Layout for Settings -->
<div class="space-y-6">

## <!-- Clinical Alerts Section -->
<section class="bg-surface-container-lowest rounded-xl p-8 shadow-
## [0_12px_32px_rgba(25,28,29,0.04)]">
<div class="flex items-center gap-3 mb-8">
<div class="w-10 h-10 rounded-lg bg-primary-container/10 flex items-center
justify-center text-primary">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL'
## 1;">medical_services</span>
## </div>
<h3 class="text-xl font-medium">Clinical Alerts</h3>
## </div>
## <!-- Notification Channel Labels -->
<div class="grid grid-cols-12 gap-4 mb-4 px-4">
<div class="col-span-6"></div>
<div class="col-span-2 text-center text-[0.75rem] font-bold text-on-surface-
variant uppercase tracking-widest">Push</div>
<div class="col-span-2 text-center text-[0.75rem] font-bold text-on-surface-
variant uppercase tracking-widest">Email</div>
<div class="col-span-2 text-center text-[0.75rem] font-bold text-on-surface-
variant uppercase tracking-widest">SMS</div>
## </div>
<div class="divide-y-0 space-y-2">
## <!-- Critical Results Row -->
<div class="grid grid-cols-12 gap-4 items-center p-4 hover:bg-surface-
container-low transition-colors rounded-lg group">
<div class="col-span-6">
<div class="font-medium text-on-surface">Critical Results</div>
<div class="text-sm text-on-surface-variant">Immediate notification for
abnormal pathology or urgent diagnostics.</div>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>

## </label>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
## </div>
## <!-- New Analyses Row -->
<div class="grid grid-cols-12 gap-4 items-center p-4 hover:bg-surface-
container-low transition-colors rounded-lg group">
<div class="col-span-6">
<div class="font-medium text-on-surface">New Analyses</div>
<div class="text-sm text-on-surface-variant">Updates on computational results
and routine lab processing.</div>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']

after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
## </div>
## </div>
## </section>
## <!-- Appointment Reminders Section -->
<section class="bg-surface-container-low rounded-xl p-8">
<div class="flex items-center gap-3 mb-8">
<div class="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center
justify-center text-on-surface-variant">
<span class="material-symbols-outlined">event_available</span>
## </div>
<h3 class="text-xl font-medium">Appointment Reminders</h3>
## </div>
<div class="space-y-2">
## <!-- Upcoming Consultations -->
<div class="grid grid-cols-12 gap-4 items-center p-4 bg-surface-container-
lowest rounded-lg group">
<div class="col-span-6">
<div class="font-medium text-on-surface">Upcoming Consultations</div>
<div class="text-sm text-on-surface-variant">Reminders sent 24 hours prior to
scheduled patient visits.</div>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">

<input class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
## </div>
## <!-- Rescheduling -->
<div class="grid grid-cols-12 gap-4 items-center p-4 bg-surface-container-
lowest rounded-lg group">
<div class="col-span-6">
<div class="font-medium text-on-surface">Rescheduling</div>
<div class="text-sm text-on-surface-variant">Notifies you when a patient
requests to move an appointment.</div>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>

## </div>
## </div>
## </div>
## </section>
## <!-- System & Security Section -->
<section class="bg-surface-container-lowest rounded-xl p-8 shadow-
## [0_12px_32px_rgba(25,28,29,0.04)]">
<div class="flex items-center gap-3 mb-8">
<div class="w-10 h-10 rounded-lg bg-secondary-container/10 flex items-center
justify-center text-secondary">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL'
## 1;">security</span>
## </div>
<h3 class="text-xl font-medium">System &amp; Security</h3>
## </div>
<div class="space-y-2">
## <!-- Login Alerts -->
<div class="grid grid-cols-12 gap-4 items-center p-4 hover:bg-surface-
container-low transition-colors rounded-lg group">
<div class="col-span-6">
<div class="font-medium text-on-surface">Login Alerts</div>
<div class="text-sm text-on-surface-variant">Get notified of new logins from
unrecognized devices.</div>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none
rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" type="checkbox"/>
<div class="w-11 h-6 bg-surface-container-highest peer-focus:outline-none

rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-
translate-x-full peer-checked:after:border-white after:content-['']
after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-
gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-
all peer-checked:bg-primary"></div>
## </label>
## </div>
## </div>
## <!-- Data Privacy Updates -->
<div class="grid grid-cols-12 gap-4 items-center p-4 hover:bg-surface-
container-low transition-colors rounded-lg group">
<div class="col-span-6">
<div class="font-medium text-on-surface">Data Privacy Updates</div>
<div class="text-sm text-on-surface-variant">Mandatory legal notices regarding
patient data handling.</div>
## </div>
<div class="col-span-2 flex justify-center">
<div class="w-11 h-6 bg-primary/20 rounded-full flex items-center justify-
center cursor-not-allowed">
<div class="w-5 h-5 bg-primary/50 rounded-full"></div>
## </div>
## </div>
<div class="col-span-2 flex justify-center">
<label class="relative inline-flex items-center cursor-pointer">
<input checked="" class="sr-only peer" disabled="" type="checkbox"/>
<div class="w-11 h-6 bg-primary rounded-full opacity-50 cursor-not-allowed
after:content-[''] after:absolute after:top-[2px] after:start-[24px] after:bg-
white after:rounded-full after:h-5 after:w-5"></div>
## </label>
## </div>
<div class="col-span-2 flex justify-center">
<div class="w-11 h-6 bg-primary/20 rounded-full flex items-center justify-
center cursor-not-allowed">
<div class="w-5 h-5 bg-primary/50 rounded-full"></div>
## </div>
## </div>
## </div>
## </div>
## </section>
## <!-- Action Footer -->
<div class="mt-12 flex items-center justify-between py-6">
<div class="flex items-center gap-2 text-on-surface-variant text-sm">
<span class="material-symbols-outlined text-sm">info</span>
<span>All changes are logged for clinical audit compliance.</span>
## </div>
<div class="flex items-center gap-4">
<button class="px-8 py-3 bg-surface-container-highest text-on-surface font-
medium rounded-lg hover:bg-surface-dim transition-colors">
Reset to Default
## </button>

<button class="px-8 py-3 bg-gradient-to-br from-primary to-primary-container
text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all
active:scale-95">
## Save Changes
## </button>
## </div>
## </div>
## </div>
## </div>
## <!-- Decorative Asymmetric Element -->
<div class="fixed bottom-0 right-0 p-12 pointer-events-none opacity-20 hidden
lg:block">
<span class="material-symbols-outlined text-[12rem] text-primary-container
select-none">notifications</span>
## </div>
## </main>
## </body></html>
## ===============================================================================
## =
FILE: mediscan_patient_history\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Patient History | MediScan</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "surface-container-low": "#f3f4f5",
## "tertiary": "#004c17",
## "surface-variant": "#e1e3e4",
## "primary-container": "#0056b3",

## "on-secondary-container": "#fffbff",
## "error": "#ba1a1a",
## "primary-fixed": "#d7e2ff",
## "tertiary-fixed": "#83fc8e",
## "surface": "#f8f9fa",
## "on-surface-variant": "#424752",
## "surface-container-highest": "#e1e3e4",
## "secondary-fixed": "#ffdad9",
## "primary-fixed-dim": "#acc7ff",
## "inverse-primary": "#acc7ff",
## "on-tertiary": "#ffffff",
## "on-tertiary-container": "#6fe87c",
## "on-error-container": "#93000a",
## "on-tertiary-fixed": "#002106",
## "on-secondary-fixed-variant": "#92001f",
## "tertiary-fixed-dim": "#66df75",
## "secondary-fixed-dim": "#ffb3b2",
## "secondary": "#b6152e",
## "error-container": "#ffdad6",
## "on-primary-fixed-variant": "#004491",
## "on-primary-fixed": "#001a40",
## "tertiary-container": "#006722",
## "on-surface": "#191c1d",
## "on-secondary-fixed": "#410008",
## "surface-tint": "#115cb9",
## "secondary-container": "#d93343",
## "on-background": "#191c1d",
## "inverse-on-surface": "#f0f1f2",
## "primary": "#003f87",
## "surface-container": "#edeeef",
## "on-tertiary-fixed-variant": "#00531a",
## "on-primary": "#ffffff",
## "surface-bright": "#f8f9fa",
## "on-secondary": "#ffffff",
## "on-error": "#ffffff",
## "outline-variant": "#c2c6d4",
## "outline": "#727784",
## "on-primary-container": "#bbd0ff",
## "surface-dim": "#d9dadb",
## "inverse-surface": "#2e3132",
## "surface-container-lowest": "#ffffff",
## "surface-container-high": "#e7e8e9",
## "background": "#f8f9fa"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },

"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]
## }
## },
## },
## }
## </script>
## <style>
body { font-family: 'Inter', sans-serif; }
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
.tonal-shift-bg { background-color: #f3f4f5; }
## </style>
## </head>
<body class="bg-surface text-on-surface antialiased">
<!-- TopNavBar -->
<nav class="fixed top-0 w-full z-50 bg-white/80 dark:bg-slate-900/80 backdrop-
blur-md shadow-sm dark:shadow-none">
<div class="flex justify-between items-center w-full px-6 py-3 max-w-full mx-
auto">
<div class="flex items-center gap-8">
<span class="text-xl font-bold tracking-tight text-blue-900 dark:text-blue-
200">MediScan</span>
<div class="hidden md:flex gap-6 items-center">
<a class="text-slate-500 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors" href="#">Dashboard</a>
<a class="text-blue-700 dark:text-blue-400 font-semibold border-b-2 border-
blue-700 dark:border-blue-400 pb-1" href="#">Patients</a>
<a class="text-slate-500 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors" href="#">Appointments</a>
<a class="text-slate-500 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors" href="#">Reports</a>
## </div>
## </div>
<div class="flex items-center gap-4">
<div class="relative hidden sm:block">
<input class="bg-slate-100/50 dark:bg-slate-800/50 border-none rounded-full px-
4 py-1.5 text-sm focus:ring-2 ring-blue-700/20 w-64" placeholder="Search
patients..." type="text"/>
## </div>
<div class="flex items-center gap-2">
<button class="p-2 rounded-full hover:bg-slate-50 dark:hover:bg-slate-800
transition-all active:scale-95 duration-200">
<span class="material-symbols-outlined text-slate-600">notifications</span>
## </button>
<button class="p-2 rounded-full hover:bg-slate-50 dark:hover:bg-slate-800
transition-all active:scale-95 duration-200">

<span class="material-symbols-outlined text-slate-600">settings</span>
## </button>
<button class="ml-2 bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-
semibold active:scale-95 duration-200">Emergency</button>
<img alt="Dr. Julianne Miller" class="w-10 h-10 rounded-full border-2 border-
white shadow-sm ml-2" data-alt="professional portrait of a female doctor with a
stethoscope, warm lighting, clinical office environment"
src="https://lh3.googleusercontent.com/aida-public/AB6AXuD42EC-4qkPKEtGXdb-
3PuLKmibCM3WvFNL4C9QLHR4JErsBZlNeJQfDLx4sg-
Yn7wNYqMsl8mvyVGEtm2RCZUxO9VCXOjMyh0QIrztuX9pgPzK6JENUc0xchVNLER11P-
L4TcVWpnaIvvzippcu2AlaX4FdMmPBZ-kMjrRUKbw7cuvmy59NolUrOR7-
zCQSeYliQxz80UJ0U_T6JGUTM7L6AvmJpSyd8rLtcsXWJ8yg8T55wECFlvMQOD6kefWm-
Lm9GAozkl5By4"/>
## </div>
## </div>
## </div>
## </nav>
<main class="pt-24 pb-12 px-6 max-w-7xl mx-auto">
## <!-- Header Section -->
<header class="flex flex-col md:flex-row justify-between items-start md:items-
end mb-10 gap-6">
## <div>
<span class="text-xs font-bold uppercase tracking-widest text-primary mb-2
block">Patient Records</span>
<h1 class="text-[1.75rem] font-medium text-on-surface leading-tight">Patient
## History: Arthur Morgan</h1>
<p class="text-on-surface-variant mt-1">Medical ID: #MS-99210-AM</p>
## </div>
<div class="flex gap-3">
<button class="flex items-center gap-2 px-6 py-2.5 bg-surface-container-highest
text-on-surface rounded-lg font-medium hover:bg-surface-variant transition-all
active:scale-95">
<span class="material-symbols-outlined text-sm">download</span>
Export CSV
## </button>
<button class="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-br from-
primary to-primary-container text-white rounded-lg font-medium shadow-sm
hover:brightness-110 transition-all active:scale-95">
<span class="material-symbols-outlined text-sm">add</span>
## New Analysis
## </button>
## </div>
## </header>
## <!-- Bento Grid Layout -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
<!-- Left Column: Search and List -->
<section class="lg:col-span-8 space-y-6">
<!-- Search and Filters -->
<div class="p-4 bg-surface-container-low rounded-xl flex flex-wrap items-center
gap-4">

<div class="flex-1 min-w-[240px] relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2
text-on-surface-variant text-lg">search</span>
<input class="w-full bg-surface-container-lowest border-none rounded-lg pl-10
pr-4 py-2 focus:ring-2 ring-primary/20 text-sm" placeholder="Search by
condition, date, or severity..." type="text"/>
## </div>
<div class="flex gap-2">
<button class="px-3 py-2 bg-surface-container-lowest rounded-lg text-sm font-
medium border border-outline-variant/20 flex items-center gap-2">
<span class="material-symbols-outlined text-sm">filter_list</span>
## Filters
## </button>
<select class="px-3 py-2 bg-surface-container-lowest rounded-lg text-sm font-
medium border border-outline-variant/20 focus:ring-0">
<option>Newest First</option>
<option>Severity: High</option>
<option>Oldest First</option>
## </select>
## </div>
## </div>
<!-- Past Analyses Table (No Borders) -->
<div class="bg-surface-container-lowest rounded-xl overflow-hidden shadow-
## [0_12px_32px_rgba(25,28,29,0.04)]">
<div class="p-6">
<h2 class="text-lg font-medium mb-4">Past Analyses</h2>
<div class="space-y-1">
## <!-- Header -->
<div class="grid grid-cols-12 px-4 py-3 text-xs font-bold uppercase tracking-
wider text-on-surface-variant bg-surface-container-low/50 rounded-lg">
<div class="col-span-3">Analysis Date</div>
<div class="col-span-4">Predicted Condition</div>
<div class="col-span-3 text-center">Severity</div>
<div class="col-span-2 text-right">Actions</div>
## </div>
## <!-- Row 1: Critical -->
<div class="grid grid-cols-12 px-4 py-5 items-center hover:bg-surface-
container-low transition-all group">
<div class="col-span-3 text-sm font-medium">Oct 24, 2024</div>
<div class="col-span-4 text-sm">Hypertension (Stage 2)</div>
<div class="col-span-3 flex justify-center">
<span class="px-3 py-1 bg-secondary-container text-white text-[10px] font-bold
uppercase tracking-tighter rounded-full">Critical</span>
## </div>
<div class="col-span-2 text-right">
<button class="text-primary font-semibold text-xs hover:underline active:scale-
95">View Report</button>
## </div>
## </div>
## <!-- Row 2: Moderate -->

<div class="grid grid-cols-12 px-4 py-5 items-center hover:bg-surface-
container-low transition-all">
<div class="col-span-3 text-sm font-medium">Sep 12, 2024</div>
<div class="col-span-4 text-sm">Type 2 Diabetes Risk</div>
<div class="col-span-3 flex justify-center">
<span class="px-3 py-1 bg-primary text-white text-[10px] font-bold uppercase
tracking-tighter rounded-full">Moderate</span>
## </div>
<div class="col-span-2 text-right">
<button class="text-primary font-semibold text-xs hover:underline active:scale-
95">View Report</button>
## </div>
## </div>
## <!-- Row 3: Normal -->
<div class="grid grid-cols-12 px-4 py-5 items-center hover:bg-surface-
container-low transition-all">
<div class="col-span-3 text-sm font-medium">Aug 05, 2024</div>
<div class="col-span-4 text-sm">Iron Deficiency (Anemia)</div>
<div class="col-span-3 flex justify-center">
<span class="px-3 py-1 bg-tertiary-container text-white text-[10px] font-bold
uppercase tracking-tighter rounded-full">Normal</span>
## </div>
<div class="col-span-2 text-right">
<button class="text-primary font-semibold text-xs hover:underline active:scale-
95">View Report</button>
## </div>
## </div>
## <!-- Row 4: Normal -->
<div class="grid grid-cols-12 px-4 py-5 items-center hover:bg-surface-
container-low transition-all">
<div class="col-span-3 text-sm font-medium">Jun 18, 2024</div>
<div class="col-span-4 text-sm">Cardiovascular Screening</div>
<div class="col-span-3 flex justify-center">
<span class="px-3 py-1 bg-tertiary-container text-white text-[10px] font-bold
uppercase tracking-tighter rounded-full">Normal</span>
## </div>
<div class="col-span-2 text-right">
<button class="text-primary font-semibold text-xs hover:underline active:scale-
95">View Report</button>
## </div>
## </div>
## </div>
## </div>
## </div>
## </section>
## <!-- Right Column: Trends & Quick Stats -->
<aside class="lg:col-span-4 space-y-6">
## <!-- Symptom Trends Card -->
<div class="bg-surface-container-lowest p-6 rounded-xl shadow-
## [0_12px_32px_rgba(25,28,29,0.04)]">

<h2 class="text-lg font-medium mb-6">Symptom Trends</h2>
<div class="space-y-6">
## <!-- Fatigue Trend -->
## <div>
<div class="flex justify-between items-end mb-2">
<span class="text-sm font-medium text-on-surface">Fatigue</span>
<span class="text-xs text-error font-semibold flex items-center gap-1">
<span class="material-symbols-outlined text-[14px]">trending_up</span>
## +12%
## </span>
## </div>
<div class="h-12 w-full flex items-end gap-1 px-1">
<div class="flex-1 bg-primary/10 h-[20%] rounded-t-sm"></div>
<div class="flex-1 bg-primary/10 h-[35%] rounded-t-sm"></div>
<div class="flex-1 bg-primary/20 h-[50%] rounded-t-sm"></div>
<div class="flex-1 bg-primary/20 h-[45%] rounded-t-sm"></div>
<div class="flex-1 bg-primary/40 h-[70%] rounded-t-sm"></div>
<div class="flex-1 bg-primary/60 h-[85%] rounded-t-sm"></div>
<div class="flex-1 bg-primary/100 h-[65%] rounded-t-sm"></div>
## </div>
## </div>
## <!-- Cough Trend -->
## <div>
<div class="flex justify-between items-end mb-2">
<span class="text-sm font-medium text-on-surface">Persistent Cough</span>
<span class="text-xs text-tertiary-container font-semibold flex items-center
gap-1">
<span class="material-symbols-outlined text-[14px]">trending_down</span>
## -4%
## </span>
## </div>
<div class="h-12 w-full flex items-end gap-1 px-1">
<div class="flex-1 bg-surface-tint/60 h-[80%] rounded-t-sm"></div>
<div class="flex-1 bg-surface-tint/60 h-[75%] rounded-t-sm"></div>
<div class="flex-1 bg-surface-tint/40 h-[60%] rounded-t-sm"></div>
<div class="flex-1 bg-surface-tint/30 h-[40%] rounded-t-sm"></div>
<div class="flex-1 bg-surface-tint/20 h-[30%] rounded-t-sm"></div>
<div class="flex-1 bg-surface-tint/10 h-[15%] rounded-t-sm"></div>
<div class="flex-1 bg-surface-tint/10 h-[20%] rounded-t-sm"></div>
## </div>
## </div>
## </div>
## </div>
## <!-- Patient Overview Card -->
<div class="bg-gradient-to-br from-primary to-primary-container p-6 rounded-xl
text-white">
<h3 class="text-white/80 text-xs font-bold uppercase tracking-wider mb-
4">Current Health Score</h3>
<div class="flex items-baseline gap-2 mb-6">
<span class="text-5xl font-semibold tracking-tight">84</span>

<span class="text-xl opacity-60">/ 100</span>
## </div>
<div class="space-y-4">
<div class="flex items-center justify-between text-sm py-2 border-b border-
white/10">
<span class="opacity-80">Last Checkup</span>
<span class="font-medium">2 days ago</span>
## </div>
<div class="flex items-center justify-between text-sm py-2 border-b border-
white/10">
<span class="opacity-80">Compliance</span>
<span class="font-medium">Excellent</span>
## </div>
## </div>
## </div>
## <!-- Next Appointment Prompt -->
<div class="p-6 bg-tertiary-container/10 rounded-xl border-l-4 border-tertiary-
container">
<h4 class="text-tertiary-container font-bold text-xs uppercase tracking-widest
mb-2">Next Milestone</h4>
<p class="text-on-surface text-sm font-medium mb-3">Re-evaluate Hypertension
status following new medication cycle.</p>
<div class="flex items-center gap-2 text-xs font-semibold text-on-surface-
variant">
<span class="material-symbols-outlined text-[14px]">calendar_today</span>
Nov 12, 2024 at 10:30 AM
## </div>
## </div>
## </aside>
## </div>
## </main>
## <!-- Footer -->
<footer class="w-full border-t border-slate-200 dark:border-slate-800 bg-slate-
50 dark:bg-slate-950">
<div class="w-full py-8 px-6 flex flex-col md:flex-row justify-between items-
center gap-4">
<div class="flex flex-col gap-2">
<p class="text-slate-600 dark:text-slate-400 text-xs font-medium uppercase
tracking-wider">© 2024 MediScan Precision Systems. All Rights Reserved.</p>
## </div>
<div class="flex flex-wrap justify-center gap-6">
<a class="text-slate-500 dark:text-slate-500 text-xs font-medium uppercase
tracking-wider hover:text-blue-700 dark:hover:text-blue-300 underline
transition-all" href="#">Medical Disclaimer</a>
<a class="text-slate-500 dark:text-slate-500 text-xs font-medium uppercase
tracking-wider hover:text-blue-700 dark:hover:text-blue-300 underline
transition-all" href="#">Privacy Policy</a>
<a class="text-slate-500 dark:text-slate-500 text-xs font-medium uppercase
tracking-wider hover:text-blue-700 dark:hover:text-blue-300 underline
transition-all" href="#">HIPAA Compliance</a>

<a class="text-slate-500 dark:text-slate-500 text-xs font-medium uppercase
tracking-wider hover:text-blue-700 dark:hover:text-blue-300 underline
transition-all" href="#">Terms of Service</a>
## </div>
## </div>
## </footer>
## </body></html>
## ===============================================================================
## =
FILE: mediscan_processing\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediScan - Processing Your Data</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700;800&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "on-secondary-fixed-variant": "#92001f",
## "on-error-container": "#93000a",
## "inverse-on-surface": "#f0f1f2",
## "on-secondary-fixed": "#410008",
## "on-surface-variant": "#424752",
## "surface-variant": "#e1e3e4",
## "on-primary": "#ffffff",
## "secondary": "#b6152e",
## "surface-container-lowest": "#ffffff",
## "on-secondary-container": "#fffbff",
## "secondary-container": "#d93343",
## "on-tertiary-fixed-variant": "#00531a",
## "on-tertiary-container": "#6fe87c",
## "outline-variant": "#c2c6d4",

## "on-secondary": "#ffffff",
## "surface-container-low": "#f3f4f5",
## "error": "#ba1a1a",
## "on-primary-container": "#bbd0ff",
## "on-background": "#191c1d",
## "surface-container-highest": "#e1e3e4",
## "secondary-fixed": "#ffdad9",
## "inverse-primary": "#acc7ff",
## "surface-tint": "#115cb9",
## "surface-container": "#edeeef",
## "on-primary-fixed-variant": "#004491",
## "primary-fixed-dim": "#acc7ff",
## "primary-fixed": "#d7e2ff",
## "tertiary": "#004c17",
## "tertiary-container": "#006722",
## "on-tertiary": "#ffffff",
## "primary": "#003f87",
## "primary-container": "#0056b3",
## "surface-dim": "#d9dadb",
## "error-container": "#ffdad6",
## "on-primary-fixed": "#001a40",
## "surface-container-high": "#e7e8e9",
## "on-error": "#ffffff",
## "surface-bright": "#f8f9fa",
## "on-surface": "#191c1d",
## "background": "#f8f9fa",
## "surface": "#f8f9fa",
## "inverse-surface": "#2e3132",
## "tertiary-fixed": "#83fc8e",
## "on-tertiary-fixed": "#002106",
## "outline": "#727784",
## "secondary-fixed-dim": "#ffb3b2",
## "tertiary-fixed-dim": "#66df75"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]
## }
## },
## },
## }
## </script>
## <style>

## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
## .scan-animation {
position: relative;
overflow: hidden;
## }
## .scan-line {
position: absolute;
top: 0;
left: 0;
width: 100%;
height: 2px;
background: linear-gradient(90deg, transparent, #115cb9, transparent);
animation: scan 2s linear infinite;
## }
@keyframes scan {
0% { top: 0; opacity: 0; }
50% { opacity: 1; }
100% { top: 100%; opacity: 0; }
## }
## .pulse-soft {
animation: pulse-soft 3s ease-in-out infinite;
## }
@keyframes pulse-soft {
0%, 100% { transform: scale(1); opacity: 1; }
50% { transform: scale(1.05); opacity: 0.8; }
## }
## </style>
## </head>
<body class="bg-surface text-on-surface font-body min-h-screen flex flex-col
selection:bg-primary-container selection:text-on-primary-container">
<!-- TopNavBar - Shared Component -->
<header class="fixed top-0 w-full z-50 bg-slate-50/80 dark:bg-slate-900/80
backdrop-blur-md shadow-sm dark:shadow-none transition-all duration-300 ease-
in-out">
<div class="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto">
<div class="text-2xl font-bold tracking-tight text-blue-900 dark:text-blue-100
font-headline">
MediScan
## </div>
<nav class="hidden md:flex items-center gap-8 font-sans antialiased text-sm
tracking-wide">
<a class="text-slate-600 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors" href="#">About</a>
<a class="text-slate-600 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors" href="#">Support</a>
## </nav>
<div class="md:hidden">
<span class="material-symbols-outlined text-on-surface-variant">menu</span>

## </div>
## </div>
<div class="bg-slate-200/50 dark:bg-slate-800/50 h-[1px]"></div>
## </header>
## <!-- Main Canvas: Processing Journey -->
<main class="flex-grow flex items-center justify-center pt-24 pb-12 px-6">
<div class="max-w-4xl w-full">
<!-- Asymmetrical Bento-style Layout for Processing States -->
<div class="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
<!-- Left Column: High-End Loading Visual -->
<div class="md:col-span-7 flex flex-col items-center justify-center relative
py-12">
<div class="relative w-72 h-72 md:w-96 md:h-96 flex items-center justify-
center">
## <!-- Abstract Medical Visuals -->
<div class="absolute inset-0 rounded-full bg-primary/5 pulse-soft"></div>
<div class="absolute inset-8 rounded-full border border-primary/10"></div>
## <!-- The Primary Loading Animation Element -->
<div class="relative z-10 w-48 h-48 md:w-64 md:h-64 rounded-full bg-surface-
container-lowest flex flex-col items-center justify-center overflow-hidden
shadow-2xl shadow-primary/5">
<div class="scan-line"></div>
<!-- Central Medical Icon with Material Symbols -->
<div class="flex flex-col items-center gap-3">
<span class="material-symbols-outlined text-6xl md:text-8xl text-primary"
style="font-variation-settings: 'FILL' 1;">ecg_heart</span>
<div class="flex gap-1">
<div class="w-1.5 h-1.5 rounded-full bg-primary animate-bounce"
style="animation-delay: 0s;"></div>
<div class="w-1.5 h-1.5 rounded-full bg-primary animate-bounce"
style="animation-delay: 0.2s;"></div>
<div class="w-1.5 h-1.5 rounded-full bg-primary animate-bounce"
style="animation-delay: 0.4s;"></div>
## </div>
## </div>
<!-- Image Prompt Background (Subtle Texture) -->
<div class="absolute inset-0 -z-10 opacity-5">
<div class="w-full h-full bg-[url('https://images.unsplash.com/photo-
## 1631549916768-4119b2e5f926?q=80&amp;w=2000&amp;auto=format&amp;fit=crop')]"
data-alt="ultra-minimalist background with smooth light blue and white abstract
gradients representing clinical precision and medical scanning technology">
## </div>
## </div>
## </div>
## <!-- Secondary Floating Data Points -->
<div class="absolute top-4 right-4 p-4 rounded-xl bg-surface-container-lowest
shadow-sm border border-outline-variant/10">
<span class="text-[10px] font-bold text-primary block tracking-widest uppercase
mb-1">Status</span>
<div class="flex items-center gap-2">

<span class="w-2 h-2 rounded-full bg-tertiary"></span>
<span class="text-xs font-medium">Server Active</span>
## </div>
## </div>
## </div>
## </div>
## <!-- Right Column: Contextual Progress & Human Assurance -->
<div class="md:col-span-5 flex flex-col gap-8">
## <div>
<span class="label-md text-primary bg-primary/10 px-3 py-1 rounded-full mb-4
inline-block">Analysis in Progress</span>
<h1 class="text-4xl md:text-5xl font-headline font-semibold text-on-surface
tracking-tight leading-tight mb-4">
Analyzing <span class="text-primary italic">Your</span> Health Profile
## </h1>
<p class="text-body-lg text-on-surface-variant leading-relaxed">
Our clinical engine is cross-referencing your inputs with over 15,000 medical
journals and proprietary diagnostic patterns.
## </p>
## </div>
<!-- Progress Sequence List (No Divider Rule Applied) -->
<div class="space-y-4">
<div class="flex items-center gap-4 p-4 bg-surface-container-low rounded-xl">
<div class="w-8 h-8 rounded-full bg-tertiary flex items-center justify-center">
<span class="material-symbols-outlined text-on-tertiary text-sm" style="font-
variation-settings: 'FILL' 1;">check</span>
## </div>
<span class="text-body-lg font-medium text-on-surface">Processing Medical
## Reports...</span>
## </div>
<div class="flex items-center gap-4 p-4 bg-surface-container-high rounded-xl">
<div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center
animate-pulse">
<span class="material-symbols-outlined text-on-primary text-
sm">neurology</span>
## </div>
<span class="text-body-lg font-semibold text-on-surface">Analyzing Symptoms...
## </span>
## </div>
<div class="flex items-center gap-4 p-4 opacity-50">
<div class="w-8 h-8 rounded-full bg-surface-container-highest flex items-center
justify-center">
<span class="material-symbols-outlined text-on-surface-variant text-
sm">medication</span>
## </div>
<span class="text-body-lg text-on-surface-variant">Calculating Drug
## Recommendations...</span>
## </div>
## </div>
## <!-- Reassurance Module -->

<div class="p-6 bg-tertiary/5 rounded-2xl border-l-4 border-tertiary">
<div class="flex gap-3">
<span class="material-symbols-outlined text-tertiary">verified_user</span>
<div class="flex flex-col gap-1">
<span class="text-sm font-bold text-tertiary">Confidential &amp; Secure</span>
<p class="text-xs text-on-surface-variant leading-snug">
Your clinical data is end-to-end encrypted. We prioritize your privacy as much
as your recovery.
## </p>
## </div>
## </div>
## </div>
## </div>
## </div>
## </div>
## </main>
<!-- Interactive Bottom Status (Replaces FAB for this context) -->
<div class="fixed bottom-12 left-1/2 -translate-x-1/2 w-full max-w-sm px-6">
<div class="bg-surface-container-lowest/80 backdrop-blur-md rounded-2xl p-4
shadow-xl border border-outline-variant/10 flex items-center justify-between">
<div class="flex flex-col">
<span class="text-[10px] font-bold text-on-surface-variant tracking-widest
uppercase">Estimated wait</span>
<span class="text-lg font-headline font-semibold text-primary">12
## Seconds</span>
## </div>
<button class="bg-surface-container-highest text-on-surface font-label font-
bold px-4 py-2 rounded-lg transition-all hover:bg-surface-variant active:scale-
## 95">
## CANCEL
## </button>
## </div>
## </div>
## <!-- Footer - Shared Component -->
<footer class="w-full mt-auto py-12 bg-slate-100 dark:bg-slate-950 border-t
border-slate-200 dark:border-slate-800 transition-all duration-300">
<div class="flex flex-col items-center gap-4 text-center px-4 w-full">
<div class="text-sm font-semibold text-slate-700 dark:text-slate-
300">MediScan</div>
<div class="flex flex-wrap justify-center gap-6 mb-2">
<a class="text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 transition-colors duration-200 text-xs"
href="#">Privacy Policy</a>
<a class="text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 transition-colors duration-200 text-xs"
href="#">Terms of Service</a>
<a class="text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 transition-colors duration-200 text-xs"
href="#">Medical Disclaimer</a>
## </div>

<p class="text-xs font-normal leading-relaxed text-slate-500 dark:text-slate-
400 max-w-2xl">
© 2024 MediScan. For educational purposes only. Always consult a qualified
medical professional.
## </p>
## </div>
## </footer>
## </body></html>
## ===============================================================================
## =
FILE: mediscan_profile_management\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediScan Pro - Patient Profile Management</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@400;500;600;700;800;900&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "secondary-fixed": "#ffdad9",
## "error-container": "#ffdad6",
## "inverse-surface": "#2e3132",
## "tertiary-fixed": "#83fc8e",
## "secondary-container": "#d93343",
## "on-background": "#191c1d",
## "surface-variant": "#e1e3e4",
## "on-secondary-fixed": "#410008",
## "primary-fixed-dim": "#acc7ff",
## "surface": "#f8f9fa",
## "on-surface-variant": "#424752",
## "surface-bright": "#f8f9fa",
## "on-tertiary": "#ffffff",

## "on-primary": "#ffffff",
## "inverse-primary": "#acc7ff",
## "on-secondary": "#ffffff",
## "surface-container": "#edeeef",
## "tertiary-fixed-dim": "#66df75",
## "primary": "#003f87",
## "on-secondary-container": "#fffbff",
## "on-error": "#ffffff",
## "surface-tint": "#115cb9",
## "secondary": "#b6152e",
## "primary-fixed": "#d7e2ff",
## "on-primary-container": "#bbd0ff",
## "on-tertiary-container": "#6fe87c",
## "surface-container-low": "#f3f4f5",
## "surface-container-lowest": "#ffffff",
## "surface-container-highest": "#e1e3e4",
## "on-primary-fixed-variant": "#004491",
## "outline": "#727784",
## "on-tertiary-fixed": "#002106",
## "surface-container-high": "#e7e8e9",
## "surface-dim": "#d9dadb",
## "tertiary": "#004c17",
## "secondary-fixed-dim": "#ffb3b2",
## "error": "#ba1a1a",
## "inverse-on-surface": "#f0f1f2",
## "on-secondary-fixed-variant": "#92001f",
## "outline-variant": "#c2c6d4",
## "on-tertiary-fixed-variant": "#00531a",
## "on-surface": "#191c1d",
## "on-primary-fixed": "#001a40",
## "primary-container": "#0056b3",
## "background": "#f8f9fa",
## "on-error-container": "#93000a",
## "tertiary-container": "#006722"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]
## }
## },
## },
## }
## </script>

## <style>
body { font-family: 'Inter', sans-serif; }
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
.no-scrollbar::-webkit-scrollbar { display: none; }
## </style>
## </head>
<body class="bg-surface text-on-surface selection:bg-primary-fixed">
<div class="flex min-h-screen overflow-hidden">
<!-- SideNavBar Navigation Context: Preferences Active -->
<aside class="h-screen w-64 sticky top-0 bg-gradient-to-b from-[#f8f9fa] to-
[#f3f4f5] dark:from-slate-950 dark:to-slate-900 flex flex-col gap-4 p-6 shrink-
## 0">
<div class="mb-8">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-primary-container flex items-center
justify-center">
<span class="material-symbols-outlined text-on-primary-container" style="font-
variation-settings: 'FILL' 1;">medical_services</span>
## </div>
## <div>
<h1 class="text-lg font-black text-[#003f87] dark:text-blue-500 leading-
none">MediScan Pro</h1>
<p class="text-[10px] uppercase tracking-widest text-on-surface-variant font-
bold">Clinical Portal</p>
## </div>
## </div>
## </div>
<nav class="flex-1 space-y-2">
## <!-- Tab: Patient List -->
<a class="flex items-center gap-3 px-4 py-3 text-sm font-medium text-slate-500
dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-
slate-900 dark:hover:text-slate-100 transition-all rounded-lg group" href="#">
<span class="material-symbols-outlined group-active:scale-95 transition-
transform">group</span>
<span>Patient List</span>
## </a>
## <!-- Tab: Health Records -->
<a class="flex items-center gap-3 px-4 py-3 text-sm font-medium text-slate-500
dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-
slate-900 dark:hover:text-slate-100 transition-all rounded-lg group" href="#">
<span class="material-symbols-outlined group-active:scale-95 transition-
transform">description</span>
<span>Health Records</span>
## </a>
<!-- Tab: AI Analysis -->
<a class="flex items-center gap-3 px-4 py-3 text-sm font-medium text-slate-500
dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-
slate-900 dark:hover:text-slate-100 transition-all rounded-lg group" href="#">

<span class="material-symbols-outlined group-active:scale-95 transition-
transform">psychology</span>
<span>AI Analysis</span>
## </a>
<!-- Tab: Preferences (ACTIVE) -->
<a class="flex items-center gap-3 px-4 py-3 text-sm font-bold text-[#003f87]
dark:text-blue-400 bg-[#ffffff] dark:bg-slate-800 rounded-lg shadow-sm
transition-all scale-100" href="#">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL'
## 1;">tune</span>
<span>Preferences</span>
## </a>
## <!-- Tab: Security -->
<a class="flex items-center gap-3 px-4 py-3 text-sm font-medium text-slate-500
dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-
slate-900 dark:hover:text-slate-100 transition-all rounded-lg group" href="#">
<span class="material-symbols-outlined group-active:scale-95 transition-
transform">shield</span>
<span>Security</span>
## </a>
## </nav>
<div class="mt-auto">
<button class="w-full py-4 bg-primary text-on-primary font-bold rounded-lg
shadow-md hover:bg-primary-container transition-colors flex items-center
justify-center gap-2 active:scale-95 transition-transform">
<span class="material-symbols-outlined">add</span>
<span>New Patient</span>
## </button>
## </div>
## </aside>
## <!-- Main Content Area -->
<main class="flex-1 overflow-y-auto no-scrollbar bg-surface relative">
## <!-- Sticky Header -->
<header class="sticky top-0 z-30 bg-surface/80 backdrop-blur-xl px-12 py-8 flex
justify-between items-end">
<div class="space-y-1">
<p class="text-label-md font-bold text-primary uppercase tracking-widest text-
[0.7rem]">Settings &amp; Access</p>
<h2 class="text-3xl font-medium tracking-tight text-on-surface">Profile
## Management</h2>
## </div>
<button class="px-8 py-3 bg-gradient-to-br from-primary to-primary-container
text-on-primary font-semibold rounded-lg shadow-xl shadow-primary/10
hover:opacity-90 active:scale-95 transition-all">
## Save Changes
## </button>
## </header>
<div class="max-w-5xl mx-auto px-12 pb-24 space-y-12">
## <!-- Bento Layout Section -->
<div class="grid grid-cols-12 gap-6">

## <!-- Profile Photo Card -->
<div class="col-span-12 lg:col-span-4 bg-surface-container-lowest p-8 rounded-
xl flex flex-col items-center justify-center text-center">
<div class="relative group">
<div class="w-40 h-40 rounded-full border-4 border-surface-container overflow-
hidden bg-surface-container-low transition-transform group-hover:scale-[1.02]">
<img alt="Clinician profile picture" class="w-full h-full object-cover" data-
alt="portrait of a professional female clinician in her 40s wearing a white lab
coat with a warm approachable expression"
src="https://lh3.googleusercontent.com/aida-public/AB6AXuAfGN2MDkzKoq__Bz6P-
jJ8WK-30g78-
xXgwBDYNQe5NnbxM_kv7FkoCWaAZ7stoWfly7EPxmCUbJlAuPy_skwiAxCMQLCzVwmKsinrjBGSRSpA
l2MXMpKDsdhcO4SEqdRzh9pyzlzj3mOcW1IZvAXJUNZCfOHOlZzJ9E8C3is1B_DKukAVZgwbfnbiVo7
9zmA_QT4yI-YduUWOLt7qNIvjCpaFpchmyNOrsoKDP4StHxnvj_Fqjtmj8HQVdSNBnKKAG7E48i-
GCcs"/>
## </div>
<button class="absolute bottom-2 right-2 w-10 h-10 bg-primary text-on-primary
rounded-full flex items-center justify-center shadow-lg border-2 border-white
hover:scale-110 transition-transform">
<span class="material-symbols-outlined text-base">edit</span>
## </button>
## </div>
<h3 class="mt-6 font-medium text-lg">Dr. Elena Rodriguez</h3>
<p class="text-on-surface-variant text-sm">Chief of Cardiology</p>
<a class="mt-4 text-primary text-sm font-semibold hover:underline"
href="#">Edit Photo</a>
## </div>
## <!-- Personal Information Form Card -->
<div class="col-span-12 lg:col-span-8 bg-surface-container-lowest p-8 rounded-
xl">
<div class="flex items-center gap-3 mb-8">
<span class="material-symbols-outlined text-primary">badge</span>
<h3 class="text-title-lg font-medium">Personal Information</h3>
## </div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
<div class="space-y-2">
<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider">Full Name</label>
<input class="w-full bg-surface-container-low border-none rounded-lg py-3 px-4
focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-
all" type="text" value="Elena Rodriguez"/>
## </div>
<div class="space-y-2">
<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider">Date of Birth</label>
<input class="w-full bg-surface-container-low border-none rounded-lg py-3 px-4
focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-
all" type="date" value="1982-05-14"/>
## </div>
<div class="space-y-2">

<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider">Gender</label>
<select class="w-full bg-surface-container-low border-none rounded-lg py-3 px-4
focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-
all">
<option selected="">Female</option>
<option>Male</option>
<option>Non-binary</option>
<option>Prefer not to say</option>
## </select>
## </div>
<div class="space-y-2">
<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider">Contact Phone</label>
<input class="w-full bg-surface-container-low border-none rounded-lg py-3 px-4
focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-
all" type="tel" value="+1 (555) 012-3456"/>
## </div>
<div class="col-span-full space-y-2">
<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider">Email Address</label>
<input class="w-full bg-surface-container-low border-none rounded-lg py-3 px-4
focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-
all" type="email" value="e.rodriguez@mediscan.health"/>
## </div>
## </div>
## </div>
## <!-- Medical Preferences Card -->
<div class="col-span-12 lg:col-span-7 bg-surface-container-low/50 p-8 rounded-
xl">
<div class="flex items-center gap-3 mb-8">
<span class="material-symbols-outlined text-primary">clinical_notes</span>
<h3 class="text-title-lg font-medium">Medical Preferences</h3>
## </div>
<div class="space-y-6">
## <!-- Toggle 1 -->
<div class="flex items-center justify-between p-4 bg-surface-container-lowest
rounded-lg">
<div class="space-y-1">
<p class="font-medium text-on-surface">Allow AI Data Processing</p>
<p class="text-xs text-on-surface-variant">Enable advanced clinical pattern
recognition on your diagnostics.</p>
## </div>
<div class="relative inline-flex h-6 w-11 items-center rounded-full bg-primary
cursor-pointer">
<span class="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white
transition"></span>
## </div>
## </div>
## <!-- Toggle 2 -->

<div class="flex items-center justify-between p-4 bg-surface-container-lowest
rounded-lg">
<div class="space-y-1">
<p class="font-medium text-on-surface">Emergency Contact Notifications</p>
<p class="text-xs text-on-surface-variant">Automatically alert designated
contacts for urgent alerts.</p>
## </div>
<div class="relative inline-flex h-6 w-11 items-center rounded-full bg-primary
cursor-pointer">
<span class="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white
transition"></span>
## </div>
## </div>
## <!-- Selection -->
<div class="space-y-2 pt-2">
<label class="text-xs font-bold text-on-surface-variant uppercase tracking-
wider">Language Preference</label>
<div class="flex gap-2">
<button class="px-4 py-2 bg-primary text-on-primary text-sm font-medium
rounded-full">English</button>
<button class="px-4 py-2 bg-surface-container-highest text-on-surface text-sm
font-medium rounded-full hover:bg-surface-variant transition-
colors">Spanish</button>
<button class="px-4 py-2 bg-surface-container-highest text-on-surface text-sm
font-medium rounded-full hover:bg-surface-variant transition-
colors">French</button>
## </div>
## </div>
## </div>
## </div>
## <!-- Security & Auth Card -->
<div class="col-span-12 lg:col-span-5 bg-surface-container-lowest p-8 rounded-
xl shadow-sm border border-outline-variant/10">
<div class="flex items-center gap-3 mb-8">
<span class="material-symbols-outlined text-secondary">security</span>
<h3 class="text-title-lg font-medium">Security &amp; Access</h3>
## </div>
<div class="space-y-8">
<div class="p-5 bg-secondary-fixed/30 rounded-xl">
<div class="flex items-start gap-4">
<span class="material-symbols-outlined text-secondary mt-1">vibration</span>
<div class="space-y-1">
<p class="font-bold text-on-secondary-fixed-variant">Two-Factor Auth</p>
<p class="text-sm text-on-secondary-fixed-variant/80">Enabled via Mobile
## App</p>
## </div>
<button class="ml-auto text-secondary text-xs font-bold uppercase tracking-
widest hover:underline">Manage</button>
## </div>
## </div>

<div class="space-y-4">
<p class="text-sm font-medium text-on-surface">Update Password</p>
<div class="space-y-3">
<input class="w-full bg-surface-container-low border-none rounded-lg py-3 px-4
text-sm focus:ring-2 focus:ring-primary transition-all" placeholder="Current
password" type="password"/>
<input class="w-full bg-surface-container-low border-none rounded-lg py-3 px-4
text-sm focus:ring-2 focus:ring-primary transition-all" placeholder="New
password" type="password"/>
<button class="w-full py-3 border border-primary text-primary font-semibold
rounded-lg hover:bg-primary/5 transition-colors">Update Credentials</button>
## </div>
## </div>
<div class="pt-4 border-t border-surface-variant flex items-center justify-
between text-xs text-on-surface-variant">
<span>Last login: 2 hours ago</span>
<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-
tertiary-container"></span> Seattle, WA</span>
## </div>
## </div>
## </div>
## </div>
## <!-- Subtle Data Visibility Stats -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-8 pt-6">
<div class="flex gap-4 items-center opacity-70">
<span class="material-symbols-outlined text-3xl text-outline">history</span>
## <div>
<p class="text-[0.65rem] font-bold uppercase tracking-tighter text-on-surface-
variant">Last Profile Update</p>
<p class="text-sm font-medium">Oct 24, 2023</p>
## </div>
## </div>
<div class="flex gap-4 items-center opacity-70">
<span class="material-symbols-outlined text-3xl text-
outline">verified_user</span>
## <div>
<p class="text-[0.65rem] font-bold uppercase tracking-tighter text-on-surface-
variant">Account Status</p>
<p class="text-sm font-medium">Verified Clinician</p>
## </div>
## </div>
<div class="flex gap-4 items-center opacity-70">
<span class="material-symbols-outlined text-3xl text-outline">storage</span>
## <div>
<p class="text-[0.65rem] font-bold uppercase tracking-tighter text-on-surface-
variant">Data Residency</p>
<p class="text-sm font-medium">US-WEST-2 (Encrypted)</p>
## </div>
## </div>
## </div>

## </div>
## </main>
## </div>
## </body></html>
## ===============================================================================
## =
FILE: mediscan_results_dashboard\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediScan Results Dashboard</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "on-secondary-fixed-variant": "#92001f",
## "on-error-container": "#93000a",
## "inverse-on-surface": "#f0f1f2",
## "on-secondary-fixed": "#410008",
## "on-surface-variant": "#424752",
## "surface-variant": "#e1e3e4",
## "on-primary": "#ffffff",
## "secondary": "#b6152e",
## "surface-container-lowest": "#ffffff",
## "on-secondary-container": "#fffbff",
## "secondary-container": "#d93343",
## "on-tertiary-fixed-variant": "#00531a",
## "on-tertiary-container": "#6fe87c",
## "outline-variant": "#c2c6d4",
## "on-secondary": "#ffffff",
## "surface-container-low": "#f3f4f5",
## "error": "#ba1a1a",

## "on-primary-container": "#bbd0ff",
## "on-background": "#191c1d",
## "surface-container-highest": "#e1e3e4",
## "secondary-fixed": "#ffdad9",
## "inverse-primary": "#acc7ff",
## "surface-tint": "#115cb9",
## "surface-container": "#edeeef",
## "on-primary-fixed-variant": "#004491",
## "primary-fixed-dim": "#acc7ff",
## "primary-fixed": "#d7e2ff",
## "tertiary": "#004c17",
## "tertiary-container": "#006722",
## "on-tertiary": "#ffffff",
## "primary": "#003f87",
## "primary-container": "#0056b3",
## "surface-dim": "#d9dadb",
## "error-container": "#ffdad6",
## "on-primary-fixed": "#001a40",
## "surface-container-high": "#e7e8e9",
## "on-error": "#ffffff",
## "surface-bright": "#f8f9fa",
## "on-surface": "#191c1d",
## "background": "#f8f9fa",
## "surface": "#f8f9fa",
## "inverse-surface": "#2e3132",
## "tertiary-fixed": "#83fc8e",
## "on-tertiary-fixed": "#002106",
## "outline": "#727784",
## "secondary-fixed-dim": "#ffb3b2",
## "tertiary-fixed-dim": "#66df75"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]
## }
## },
## },
## }
## </script>
## <style>
body { font-family: 'Inter', sans-serif; }
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400,
'GRAD' 0, 'opsz' 24; }

.glass-panel { backdrop-filter: blur(20px); }
## </style>
## </head>
<body class="bg-surface text-on-surface min-h-screen flex flex-col">
<nav class="fixed top-0 w-full z-50 bg-slate-50/80 dark:bg-slate-900/80
backdrop-blur-md shadow-sm dark:shadow-none">
<div class="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto w-
full">
<div class="text-2xl font-bold tracking-tight text-blue-900 dark:text-blue-
100">MediScan</div>
<div class="hidden md:flex items-center gap-8 font-sans antialiased text-sm
tracking-wide">
<a class="text-slate-600 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors" href="#">About</a>
<a class="text-slate-600 dark:text-slate-400 hover:text-blue-600
dark:hover:text-blue-300 transition-colors" href="#">Support</a>
<button class="bg-primary hover:bg-primary-container text-on-primary px-6 py-2
rounded-lg transition-all duration-300 ease-in-out font-semibold">Sign
## Out</button>
## </div>
## </div>
<div class="bg-slate-200/50 dark:bg-slate-800/50 h-[1px]"></div>
## </nav>
<main class="flex-grow pt-24 pb-12 px-4 max-w-5xl mx-auto w-full space-y-8">
<section class="bg-secondary-container rounded-xl p-6 flex flex-col md:flex-row
items-center gap-6 animate-pulse-subtle">
<div class="bg-on-secondary p-4 rounded-full flex items-center justify-center
shadow-lg">
<span class="material-symbols-outlined text-secondary text-4xl" data-
weight="fill" style="font-variation-settings: 'FILL' 1;">emergency_home</span>
## </div>
<div class="flex-grow text-center md:text-left">
<h2 class="text-on-secondary text-sm font-bold tracking-[0.1em] uppercase mb-
1">Severity: CRITICAL</h2>
<p class="text-on-secondary-container text-xl md:text-2xl font-medium">Seek
emergency medical care immediately.</p>
## </div>
<button class="bg-on-secondary text-secondary px-8 py-4 rounded-xl font-bold
text-lg hover:bg-opacity-90 transition-all flex items-center gap-2">
<span class="material-symbols-outlined">call</span>
## Emergency Contacts
## </button>
## </section>
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
<div class="md:col-span-2 space-y-6">
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm">
<h3 class="text-on-surface-variant font-label text-xs font-bold uppercase
tracking-widest mb-6">Analysis Overview</h3>
<div class="flex flex-col md:flex-row justify-between items-start md:items-
center gap-6">

## <div>
<p class="text-on-surface-variant text-sm mb-1">Predicted Condition</p>
<h1 class="text-headline-md font-semibold text-primary">Type 2 Diabetes</h1>
## </div>
<div class="bg-surface-container-low p-6 rounded-xl flex flex-col items-
center">
<span class="text-display-lg text-primary leading-none">88%</span>
<span class="text-label-md text-on-surface-variant mt-2">Confidence
## Score</span>
## </div>
## </div>
<div class="mt-8 pt-8 border-t border-outline-variant/20">
<h4 class="text-title-lg font-medium mb-4">Patient Observations</h4>
<div class="grid grid-cols-2 gap-4">
<div class="p-4 bg-surface-container-low rounded-lg">
<span class="text-xs text-on-surface-variant">Blood Glucose</span>
<p class="text-lg font-bold">248 mg/dL</p>
## </div>
<div class="p-4 bg-surface-container-low rounded-lg">
<span class="text-xs text-on-surface-variant">HbA1c Level</span>
<p class="text-lg font-bold">8.4%</p>
## </div>
## </div>
## </div>
## </div>
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm">
<div class="flex items-center justify-between mb-8">
<h3 class="text-title-lg font-semibold flex items-center gap-3">
<span class="material-symbols-outlined text-primary" data-weight="fill"
style="font-variation-settings: 'FILL' 1;">pill</span>
## Drug Recommendations
## </h3>
<span class="text-xs text-on-surface-variant bg-surface-container-high px-3 py-
1 rounded-full italic">Consult physician before use</span>
## </div>
<div class="space-y-4">
<div class="group hover:bg-surface-container-low p-5 rounded-lg transition-
colors border border-transparent hover:border-outline-variant/30">
<div class="flex justify-between items-start">
## <div>
<h4 class="text-lg font-bold text-on-surface">Metformin</h4>
<p class="text-sm text-primary font-medium">Biguanide</p>
## </div>
<div class="text-right">
<p class="text-sm font-semibold">500–2000 mg daily</p>
<p class="text-xs text-on-surface-variant">Standard Dosage</p>
## </div>
## </div>
<div class="mt-3 flex items-center gap-2 text-xs text-error font-medium bg-
error-container/30 p-2 rounded">

<span class="material-symbols-outlined text-sm">warning</span>
Precautions: Check renal function periodically.
## </div>
## </div>
<div class="group hover:bg-surface-container-low p-5 rounded-lg transition-
colors border border-transparent hover:border-outline-variant/30">
<div class="flex justify-between items-start">
## <div>
<h4 class="text-lg font-bold text-on-surface">Glipizide</h4>
<p class="text-sm text-primary font-medium">Sulfonylurea</p>
## </div>
<div class="text-right">
<p class="text-sm font-semibold">5–10 mg before meals</p>
<p class="text-xs text-on-surface-variant">Standard Dosage</p>
## </div>
## </div>
<div class="mt-3 flex items-center gap-2 text-xs text-error font-medium bg-
error-container/30 p-2 rounded">
<span class="material-symbols-outlined text-sm">warning</span>
Precautions: Monitor for hypoglycemia symptoms.
## </div>
## </div>
## </div>
## </div>
## </div>
<aside class="space-y-6">
<div class="bg-primary rounded-xl p-8 text-on-primary shadow-xl">
<h4 class="text-label-md font-bold uppercase tracking-widest mb-6 opacity-
80">Next Steps</h4>
<div class="space-y-4">
<button class="w-full bg-on-primary text-primary font-bold py-4 rounded-lg flex
items-center justify-center gap-3 hover:bg-primary-fixed transition-colors">
<span class="material-symbols-outlined">picture_as_pdf</span>
Download Report (PDF)
## </button>
<button class="w-full bg-primary-container text-white font-bold py-4 rounded-lg
flex items-center justify-center gap-3 hover:bg-opacity-90 transition-colors
border border-on-primary/20">
<span class="material-symbols-outlined">refresh</span>
## Start New Analysis
## </button>
## </div>
<div class="mt-8 space-y-4">
<div class="flex items-start gap-4">
<span class="material-symbols-outlined mt-1 opacity-70">local_hospital</span>
<p class="text-sm leading-relaxed opacity-90">Find nearby emergency care
facilities and hospitals with endocrinology specialists.</p>
## </div>
## </div>
## </div>

<div class="bg-surface-container-low rounded-xl p-8">
<h4 class="text-label-md font-bold uppercase mb-4">Location Context</h4>
<div class="aspect-square rounded-lg overflow-hidden bg-surface-variant
relative grayscale opacity-70">
<img alt="Map view showing medical centers in the surrounding area" class="w-
full h-full object-cover" data-alt="a minimalist medical map graphic showing
clinic icons and transit lines in a clean architectural style" data-
location="Medical District" src="https://lh3.googleusercontent.com/aida-
public/AB6AXuAxRLeDIw5fchLdQkEIaT9_bVCQmaQvl6-
u4hP6k121fY34iQw5gwvIHzOvEfxW271H3oyc3H6Cie8cPigStrEnfglYei6J560r_jVYhTY2jhUp29
hFvIi2Ew5tr9PauWDXSZr6EEFnJafvETbpgrghmLC8vt9N6pw9hv42o5RbxqaR-WWiRjq-
aHJO4t5JU413Ga0zOkOCAtD4_VLzFklyQo8RFb29b6nuIJZMutYh_NScwNdma7CDDZyRcTHKR25KOxT
ZMa11Ekw"/>
<div class="absolute inset-0 bg-primary/10 pointer-events-none"></div>
<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
<span class="material-symbols-outlined text-secondary text-3xl animate-
bounce">location_on</span>
## </div>
## </div>
## </div>
## </aside>
## </div>
## </main>
<footer class="w-full mt-auto py-12 bg-slate-100 dark:bg-slate-950 border-t
border-slate-200 dark:border-slate-800">
<div class="flex flex-col items-center gap-4 text-center px-4 w-full">
<div class="text-sm font-semibold text-slate-700 dark:text-slate-
300">MediScan</div>
<p class="text-xs font-normal leading-relaxed text-slate-500 dark:text-slate-
400 max-w-md">
© 2024 MediScan. For educational purposes only. Always consult a qualified
medical professional.
## </p>
<div class="flex gap-6 mt-2">
<a class="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 transition-colors duration-200" href="#">Privacy
## Policy</a>
<a class="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 transition-colors duration-200" href="#">Terms of
## Service</a>
<a class="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-800
dark:hover:text-slate-200 transition-colors duration-200" href="#">Medical
## Disclaimer</a>
## </div>
## </div>
## </footer>
## </body></html>
## ===============================================================================
## =

FILE: mediscan_updated_dashboard_overview\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>MediScan - Clinical Precision Dashboard</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "surface": "#f8f9fa",
## "on-surface": "#191c1d",
## "surface-container-lowest": "#ffffff",
## "error-container": "#ffdad6",
## "on-primary-fixed-variant": "#004491",
## "surface-bright": "#f8f9fa",
## "outline": "#727784",
## "on-primary": "#ffffff",
## "surface-tint": "#115cb9",
## "on-secondary-container": "#fffbff",
## "on-secondary": "#ffffff",
## "surface-container-highest": "#e1e3e4",
## "on-error": "#ffffff",
## "primary-container": "#0056b3",
## "on-tertiary": "#ffffff",
## "tertiary-container": "#006722",
## "on-background": "#191c1d",
## "on-surface-variant": "#424752",
## "inverse-surface": "#2e3132",
## "secondary-fixed": "#ffdad9",
## "on-tertiary-fixed-variant": "#00531a",
## "primary-fixed-dim": "#acc7ff",
## "surface-variant": "#e1e3e4",
## "surface-container-low": "#f3f4f5",

## "surface-container": "#edeeef",
## "on-tertiary-container": "#6fe87c",
## "primary-fixed": "#d7e2ff",
## "tertiary-fixed-dim": "#66df75",
## "on-tertiary-fixed": "#002106",
## "secondary": "#b6152e",
## "error": "#ba1a1a",
## "on-error-container": "#93000a",
## "tertiary": "#004c17",
## "on-primary-fixed": "#001a40",
## "on-secondary-fixed": "#410008",
## "surface-container-high": "#e7e8e9",
## "secondary-fixed-dim": "#ffb3b2",
## "inverse-primary": "#acc7ff",
## "on-primary-container": "#bbd0ff",
## "primary": "#003f87",
## "background": "#f8f9fa",
## "surface-dim": "#d9dadb",
## "inverse-on-surface": "#f0f1f2",
## "tertiary-fixed": "#83fc8e",
## "secondary-container": "#d93343",
## "on-secondary-fixed-variant": "#92001f",
## "outline-variant": "#c2c6d4"
## },
"borderRadius": {
"DEFAULT": "0.25rem",
## "lg": "0.5rem",
## "xl": "0.75rem",
## "full": "9999px"
## },
"fontFamily": {
"headline": ["Inter"],
"body": ["Inter"],
"label": ["Inter"]
## }
## },
## },
## }
## </script>
## <style>
body { font-family: 'Inter', sans-serif; }
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
## .custom-glass {
background: rgba(255, 255, 255, 0.8);
backdrop-filter: blur(20px);
## }
## </style>
## </head>

<body class="bg-surface text-on-surface antialiased">
<!-- SideNavBar Shell -->
<nav class="flex flex-col fixed left-0 top-0 h-full py-6 bg-slate-50 dark:bg-
slate-900 h-screen w-64 border-r-0 z-50 font-inter text-sm antialiased">
<div class="px-6 mb-10">
<h1 class="text-xl font-bold tracking-tight text-blue-800 dark:text-blue-
300">MediScan</h1>
<p class="text-xs text-on-surface-variant/70 uppercase tracking-widest mt-
1">Clinical Precision</p>
## </div>
<div class="flex-1 space-y-1 px-3">
<a class="flex items-center px-4 py-3 rounded-lg text-blue-700 dark:text-blue-
400 font-semibold border-r-4 border-blue-700 dark:border-blue-400 transition-
colors bg-slate-200/50" href="#">
<span class="material-symbols-outlined mr-3">dashboard</span>
## Dashboard
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">group</span>
## Patients
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">calendar_today</span>
## Appointments
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">analytics</span>
## Analytics
## </a>
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">description</span>
## Reports
## </a>
## </div>
<div class="px-3 mt-auto">
<a class="flex items-center px-4 py-3 rounded-lg text-slate-500 dark:text-
slate-400 hover:text-blue-600 dark:hover:text-blue-300 hover:bg-slate-200/50
transition-colors" href="#">
<span class="material-symbols-outlined mr-3">settings</span>
## Settings
## </a>
## </div>

## </nav>
## <!-- Main Content Area -->
<main class="ml-64 min-h-screen">
<!-- TopNavBar Shell -->
<header class="flex justify-between items-center w-full px-8 h-16 sticky top-0
z-40 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md shadow-sm dark:shadow-
none font-inter text-base">
<div class="flex items-center flex-1 max-w-xl">
<div class="relative w-full">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2
text-on-surface-variant">search</span>
<input class="w-full bg-surface-container-low border-none rounded-full py-2 pl-
10 pr-4 focus:ring-2 focus:ring-primary/20 text-sm" placeholder="Search patient
ID, name, or clinician..." type="text"/>
## </div>
## </div>
<div class="flex items-center gap-4 ml-8">
<button class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2
transition-all active:scale-95 duration-200 text-slate-400">
<span class="material-symbols-outlined">notifications</span>
## </button>
<button class="hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full p-2
transition-all active:scale-95 duration-200 text-slate-400">
<span class="material-symbols-outlined">help_outline</span>
## </button>
<div class="h-8 w-px bg-outline-variant/30 mx-2"></div>
<div class="flex items-center gap-3">
<div class="text-right hidden sm:block">
<p class="text-xs font-bold text-on-surface">Dr. Sarah Chen</p>
<p class="text-[10px] text-on-surface-variant">Senior Hematologist</p>
## </div>
<img alt="Clinician Profile" class="w-10 h-10 rounded-full object-cover border-
2 border-primary-container" data-alt="Professional headshot of a female doctor
in a white lab coat, clean studio lighting, high-end medical professional
aesthetic" src="https://lh3.googleusercontent.com/aida-
public/AB6AXuCXrB3e1MU9LmJZ30QnVVf2sRlJvxMCGGwPCFXp9NxAqlzGMHSSZCdRy-
y9wtsBG2MIb0oBu4zB3WeLINoZutTwHVuQyaEbT7j4lRK8pB2HASP2Q9u7w_hLjHZpkBWQL_QBvDe-
o92NJbrGYWryWmSN5r7uO6-
f4xQxz8B4YugRAxMRV32Bj0nAF8tQkVYRk50oyvKzakmu62q78AskhgXniuEeqe9AVE2bV9TgBa3BOU
5vyZMRfmzznUfANTvl9EovKplKInlYCmQ"/>
## </div>
## </div>
## </header>
## <!-- Content Canvas -->
<div class="p-8 space-y-8">
<!-- Section 1: Clinic Performance (Bento Stats) -->
## <section>
<div class="flex items-end justify-between mb-6">
## <div>
<h2 class="text-[0.75rem] font-bold text-primary uppercase tracking-

widest">Clinic Performance</h2>
<h3 class="text-2xl font-medium text-on-surface mt-1">Live Operations
## Monitor</h3>
## </div>
<p class="text-sm text-on-surface-variant">Last updated: Just now</p>
## </div>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
## <!-- Active Cases -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-primary bg-primary/10 p-2 rounded-
lg">clinical_notes</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-
container/10 px-2 py-1 rounded">+12%</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Active Cases</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">142</h4>
## </div>
## <!-- Critical Results -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-secondary bg-secondary/10 p-2
rounded-lg">emergency_home</span>
<span class="text-[10px] font-bold text-secondary-container bg-secondary-
container/10 px-2 py-1 rounded">URGENT</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Critical Results</p>
<h4 class="text-4xl font-semibold text-secondary mt-2">08</h4>
## </div>
## <!-- Pending Reviews -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-outline bg-surface-container-high
p-2 rounded-lg">pending_actions</span>
<span class="text-[10px] font-bold text-on-surface-variant bg-surface-
container-high px-2 py-1 rounded">2h avg</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Pending Reviews</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">24</h4>
## </div>
## <!-- Completed Today -->
<div class="bg-surface-container-lowest p-6 rounded-xl transition-all hover:bg-
white border border-transparent hover:border-outline-variant/20">
<div class="flex justify-between items-start mb-4">
<span class="material-symbols-outlined text-tertiary bg-tertiary-container/20
p-2 rounded-lg">task_alt</span>
<span class="text-[10px] font-bold text-tertiary-container bg-tertiary-

container/10 px-2 py-1 rounded">88% target</span>
## </div>
<p class="text-sm text-on-surface-variant font-medium">Completed Today</p>
<h4 class="text-4xl font-semibold text-on-surface mt-2">56</h4>
## </div>
## </div>
## </section>
## <!-- Main Layout Grid: Patient Flow + Clinical Insights / Action Required -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
## <!-- Left: Patient Flow & Clinical Insights -->
<div class="lg:col-span-8 space-y-8">
## <!-- Patient Flow -->
<div class="bg-surface-container-low rounded-xl overflow-hidden">
<div class="p-6 bg-surface-container-lowest flex justify-between items-center">
<h3 class="text-lg font-medium text-on-surface">Recently Analyzed Patients</h3>
<button class="text-primary text-sm font-semibold hover:underline">View
## All</button>
## </div>
<div class="divide-y divide-transparent">
## <!-- Patient Item 1 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-
center text-primary font-bold">JD</div>
## <div>
<p class="font-medium text-on-surface">Johnathan Doe</p>
<p class="text-xs text-on-surface-variant">ID: #MS-94021</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-secondary-
container text-white uppercase tracking-wider">Critical</span>
<p class="text-xs text-on-surface-variant w-24">12 mins ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## <!-- Patient Item 2 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-surface-tint/10 flex items-center
justify-center text-primary font-bold">MS</div>
## <div>
<p class="font-medium text-on-surface">Maria Sanchez</p>
<p class="text-xs text-on-surface-variant">ID: #MS-88123</p>
## </div>
## </div>
<div class="flex items-center gap-8">

<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-surface-container-
highest text-on-surface-variant uppercase tracking-wider">Moderate</span>
<p class="text-xs text-on-surface-variant w-24">45 mins ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## <!-- Patient Item 3 -->
<div class="p-6 flex items-center justify-between hover:bg-surface-container-
high transition-colors">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-tertiary-container/10 flex items-center
justify-center text-tertiary font-bold">AW</div>
## <div>
<p class="font-medium text-on-surface">Arthur Wright</p>
<p class="text-xs text-on-surface-variant">ID: #MS-77120</p>
## </div>
## </div>
<div class="flex items-center gap-8">
<span class="px-3 py-1 rounded-full text-[10px] font-bold bg-tertiary-container
text-white uppercase tracking-wider">Normal</span>
<p class="text-xs text-on-surface-variant w-24">1 hour ago</p>
<button class="material-symbols-outlined text-on-surface-
variant">chevron_right</button>
## </div>
## </div>
## </div>
## </div>
<!-- Clinical Insights (Chart Mockup) -->
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm">
<div class="flex justify-between items-start mb-8">
## <div>
<h3 class="text-lg font-medium text-on-surface">Clinical Insights</h3>
<p class="text-sm text-on-surface-variant">Diagnostic volume trend (7-day
period)</p>
## </div>
<select class="bg-surface-container-low border-none rounded-lg text-xs font-
semibold py-1 px-3">
<option>Weekly</option>
<option>Monthly</option>
## </select>
## </div>
<!-- Asymmetric Sparkline/Chart Visual -->
<div class="h-48 flex items-end gap-2 px-2">
<div class="flex-1 bg-primary/10 rounded-t-md h-[42%] transition-all hover:bg-
primary/20 relative group">
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded hidden group-hover:block">120</div>
## </div>
<div class="flex-1 bg-primary/10 rounded-t-md h-[63%] transition-all hover:bg-

primary/20 relative group">
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded hidden group-hover:block">180</div>
## </div>
<div class="flex-1 bg-primary/10 rounded-t-md h-[86%] transition-all hover:bg-
primary/20 relative group">
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded hidden group-hover:block">245</div>
## </div>
<div class="flex-1 bg-primary rounded-t-md h-[100%] relative group">
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded">284</div>
## </div>
<div class="flex-1 bg-primary/10 rounded-t-md h-[74%] transition-all hover:bg-
primary/20 relative group">
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded hidden group-hover:block">210</div>
## </div>
<div class="flex-1 bg-primary/10 rounded-t-md h-[49%] transition-all hover:bg-
primary/20 relative group">
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded hidden group-hover:block">140</div>
## </div>
<div class="flex-1 bg-primary/10 rounded-t-md h-[33%] transition-all hover:bg-
primary/20 relative group">
<div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-on-surface text-white
text-[10px] py-1 px-2 rounded hidden group-hover:block">95</div>
## </div>
## </div>
<div class="flex justify-between mt-4 text-[10px] font-bold text-on-surface-
variant uppercase tracking-widest px-1">
<span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span>
<span>Fri</span><span>Sat</span><span>Sun</span>
## </div>
## </div>
## </div>
## <!-- Right: Action Required Sidebar -->
<div class="lg:col-span-4 space-y-6">
<div class="bg-surface-container-lowest p-6 rounded-xl border-l-4 border-
secondary">
<div class="flex items-center gap-3 mb-6">
<span class="material-symbols-outlined text-secondary" style="font-variation-
settings: 'FILL' 1;">warning</span>
<h3 class="text-lg font-semibold text-on-surface">Action Required</h3>
## </div>
<div class="space-y-4">
## <!-- Task 1 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-secondary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-secondary uppercase">High

## Priority</span>
<span class="text-[10px] text-on-surface-variant">10:45 AM</span>
## </div>
<p class="text-sm font-medium text-on-surface">Review Hematology Lab #4922</p>
<p class="text-xs text-on-surface-variant mt-1">Patient: Robert Miller (ICU-2)
## </p>
<button class="mt-4 w-full bg-secondary text-white text-xs font-bold py-2
rounded-lg hover:opacity-90 transition-opacity">Launch Review</button>
## </div>
## <!-- Task 2 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-primary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-primary uppercase">Standard</span>
<span class="text-[10px] text-on-surface-variant">09:15 AM</span>
## </div>
<p class="text-sm font-medium text-on-surface">Finalize Discharge Report</p>
<p class="text-xs text-on-surface-variant mt-1">Patient: Sarah Jenkins</p>
<button class="mt-4 w-full border border-primary text-primary text-xs font-bold
py-2 rounded-lg hover:bg-primary/5 transition-colors">Complete Task</button>
## </div>
## <!-- Task 3 -->
<div class="p-4 bg-surface rounded-lg border-l-2 border-primary/30">
<div class="flex justify-between items-start mb-2">
<span class="text-[10px] font-bold text-primary uppercase">Follow-up</span>
<span class="text-[10px] text-on-surface-variant">Yesterday</span>
## </div>
<p class="text-sm font-medium text-on-surface">Verify Insurance Pre-Auth</p>
<p class="text-xs text-on-surface-variant mt-1">Provider: Aetna Clinical</p>
<button class="mt-4 w-full border border-primary text-primary text-xs font-bold
py-2 rounded-lg hover:bg-primary/5 transition-colors">Call Provider</button>
## </div>
## </div>
<button class="w-full mt-6 py-3 text-sm text-on-surface-variant font-medium bg-
surface-container-low rounded-lg hover:bg-surface-container-high transition-
colors">
## View All (14 Tasks)
## </button>
## </div>
<!-- Clinical Tip/Ad -->
<div class="relative overflow-hidden rounded-xl p-6 text-white group">
<div class="absolute inset-0 bg-gradient-to-br from-primary to-primary-
container z-0"></div>
<img alt="Laboratory" class="absolute inset-0 w-full h-full object-cover
opacity-20 mix-blend-overlay group-hover:scale-110 transition-transform
duration-700" data-alt="Close up of high-tech laboratory diagnostic equipment
with blue medical lighting and scientific research aesthetic"
src="https://lh3.googleusercontent.com/aida-
public/AB6AXuAyzxubzHQjCA5SCs2T2jz4NtpcKALxm3NIhertJC5c1wCmn08KGWtl0QY01xiQ7fIb
yXsft0HIuahbPrfGn91US83RaY02tennXRa6J8f0HvNMTTfipPUNUP516uqGhXkknhDHdOt3PJdjobt
aOFIvoJ1sdMO6gfJSWv-s2I-

Sc4JCLGvwcG_O0GuZFPOsvaXGFKBuLCZBopufwnYiLNspVlYp8o5vGAEEDljpSSjd4xBAbZJHNXldjC
f5YXT7EdhupZ0PZNf_1ls"/>
<div class="relative z-10">
<span class="material-symbols-outlined mb-4">info</span>
<h4 class="font-bold text-lg mb-2">System Update</h4>
<p class="text-xs opacity-90 leading-relaxed mb-4">New AI-driven hematology
markers are now live for all patients in the Critical category.</p>
<a class="text-xs font-bold underline underline-offset-4" href="#">Learn
## More</a>
## </div>
## </div>
## </div>
## </div>
## </div>
## </main>
## </body></html>
## ===============================================================================
## =
FILE: patient_list_detailed_view_1\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700;800&amp;family=Material+Symbols+Outlined:
wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
## <style>
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
body { font-family: 'Inter', sans-serif; }
## </style>
<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "on-surface-variant": "#424752",
## "surface-variant": "#e1e3e4",

## "secondary": "#b6152e",
## "on-primary-fixed": "#001a40",
## "secondary-fixed": "#ffdad9",
## "primary-fixed": "#d7e2ff",
## "on-error-container": "#93000a",
## "surface-container-low": "#f3f4f5",
## "on-secondary-container": "#fffbff",
## "surface-container-high": "#e7e8e9",
## "on-primary-fixed-variant": "#004491",
## "background": "#f8f9fa",
## "surface-container-highest": "#e1e3e4",
## "surface-bright": "#f8f9fa",
## "surface": "#f8f9fa",
## "primary-fixed-dim": "#acc7ff",
## "on-tertiary-fixed": "#002106",
## "outline": "#727784",
## "on-tertiary-fixed-variant": "#00531a",
## "tertiary-container": "#006722",
## "inverse-on-surface": "#f0f1f2",
## "secondary-container": "#d93343",
## "outline-variant": "#c2c6d4",
## "surface-container": "#edeeef",
## "on-tertiary-container": "#6fe87c",
## "on-secondary-fixed": "#410008",
## "on-primary-container": "#bbd0ff",
## "on-secondary": "#ffffff",
## "inverse-primary": "#acc7ff",
## "tertiary-fixed": "#83fc8e",
## "on-background": "#191c1d",
## "on-tertiary": "#ffffff",
## "on-surface": "#191c1d",
## "error": "#ba1a1a",
## "on-error": "#ffffff",
## "surface-dim": "#d9dadb",
## "on-primary": "#ffffff",
## "error-container": "#ffdad6",
## "tertiary": "#004c17",
## "on-secondary-fixed-variant": "#92001f",
## "inverse-surface": "#2e3132",
## "secondary-fixed-dim": "#ffb3b2",
## "tertiary-fixed-dim": "#66df75",
## "surface-tint": "#115cb9",
## "surface-container-lowest": "#ffffff",
## "primary-container": "#0056b3",
## "primary": "#003f87"
## },
"borderRadius": {
"DEFAULT": "0.5rem",
## "lg": "1rem",
## "xl": "0.75rem",

## "full": "9999px"
## }
## }
## }
## }
## </script>
## </head>
<body class="bg-background text-on-background min-h-screen">
<!-- SideNavBar -->
<aside class="fixed left-0 top-0 h-full flex flex-col py-6 bg-slate-50 dark:bg-
slate-900 w-64 border-r-0 z-50">
<div class="px-6 mb-10">
<h1 class="text-xl font-bold tracking-tight text-blue-900 dark:text-blue-
200">Pulse Portal</h1>
<p class="text-xs text-on-surface-variant mt-1">Dr. Julian Vance</p>
## </div>
<nav class="flex-1 px-4 space-y-1">
<a class="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400
hover:text-blue-600 dark:hover:text-blue-300 transition-colors" href="#">
<span class="material-symbols-outlined" data-icon="dashboard">dashboard</span>
## Dashboard
## </a>
## <!-- Active Tab: Patients -->
<a class="flex items-center gap-3 px-4 py-3 text-blue-700 dark:text-blue-400
font-semibold bg-white dark:bg-slate-950 rounded-l-full shadow-sm translate-x-1
duration-200" href="#">
<span class="material-symbols-outlined" data-icon="group">group</span>
## Patients
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400
hover:text-blue-600 dark:hover:text-blue-300 transition-colors" href="#">
<span class="material-symbols-outlined" data-
icon="calendar_today">calendar_today</span>
## Appointments
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400
hover:text-blue-600 dark:hover:text-blue-300 transition-colors" href="#">
<span class="material-symbols-outlined" data-icon="analytics">analytics</span>
## Analytics
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400
hover:text-blue-600 dark:hover:text-blue-300 transition-colors" href="#">
<span class="material-symbols-outlined" data-
icon="description">description</span>
## Reports
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400
hover:text-blue-600 dark:hover:text-blue-300 transition-colors" href="#">
<span class="material-symbols-outlined" data-icon="settings">settings</span>
## Settings

## </a>
## </nav>
<div class="px-6 pt-6 mt-auto">
<div class="flex items-center gap-3 p-2 rounded-xl bg-surface-container-low">
<img alt="Clinician profile picture" class="w-10 h-10 rounded-full object-
cover" data-alt="professional portrait of a male doctor in his 40s wearing a
white clinical coat and stethoscope in a bright office"
src="https://lh3.googleusercontent.com/aida-
public/AB6AXuAGjggVl85htWpaFTluWZDHhrmkbSeUY7kR5LG9rYvHhh71MOYhWEO6vq-
SuAmkokpO9EOHLdrlPRW76bf4FSsNmr6heOdqmj4HhXfw3LbcrwOdCVYFRcZaJV3VUC_pwYltPMBmZF
dZyoPzkH5I4bLZ-wN86l5-
QsAnvFKEn6IK5n5mlSTSQy2o4azoaARC9IS0LhKG52g8SYmyHJ1dxqK0W8DkilsY4fvYcgxwVMTesL6
UNydR0iICZePlrUDoX4ypYXBVutpwBcM"/>
<div class="overflow-hidden">
<p class="text-sm font-semibold truncate text-on-surface">Dr. J. Vance</p>
<p class="text-[10px] uppercase tracking-wider text-on-surface-
variant">Cardiologist</p>
## </div>
## </div>
## </div>
## </aside>
<!-- TopNavBar -->
<header class="w-full h-16 sticky top-0 z-40 bg-white/80 dark:bg-slate-950/80
backdrop-blur-md flex items-center justify-between px-8 ml-64 w-
[calc(100%-16rem)] shadow-sm dark:shadow-none shadow-slate-200/50">
<div class="flex items-center gap-6">
<span class="text-lg font-semibold text-slate-900 dark:text-slate-50">Clinical
## Intelligence</span>
<div class="relative group">
<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-
none">
<span class="material-symbols-outlined text-outline text-sm" data-
icon="search">search</span>
## </div>
<input class="bg-surface-container-low border-none rounded-full py-1.5 pl-10
pr-4 text-sm w-64 focus:ring-2 focus:ring-blue-500/20 transition-all"
placeholder="Global search..." type="text"/>
## </div>
## </div>
<div class="flex items-center gap-4">
<button class="text-slate-500 hover:text-blue-600 transition-opacity">
<span class="material-symbols-outlined" data-
icon="notifications">notifications</span>
## </button>
<button class="text-slate-500 hover:text-blue-600 transition-opacity">
<span class="material-symbols-outlined" data-
icon="emergency_home">emergency_home</span>
## </button>
<div class="h-4 w-[1px] bg-outline-variant/30"></div>
<button class="text-sm font-medium tracking-wide text-blue-700 dark:text-blue-

400">Support</button>
## </div>
## </header>
## <!-- Main Content -->
<main class="ml-64 p-8">
## <!-- Header Section -->
<div class="flex items-end justify-between mb-10">
## <div>
<h2 class="text-[1.75rem] font-medium text-on-surface leading-tight">Patient
## Directory</h2>
<p class="text-on-surface-variant mt-1">Manage and monitor active clinical
records in real-time.</p>
## </div>
<button class="bg-gradient-to-br from-primary to-primary-container text-on-
primary px-8 py-4 rounded-lg flex items-center gap-2 font-medium shadow-lg
shadow-primary/10 hover:opacity-90 transition-opacity">
<span class="material-symbols-outlined" data-
icon="person_add">person_add</span>
## New Patient
## </button>
## </div>
## <!-- Filters & Search Bento -->
<div class="grid grid-cols-12 gap-6 mb-8">
<div class="col-span-12 lg:col-span-8 bg-surface-container-lowest p-4 rounded-
xl flex items-center gap-4 shadow-sm">
<div class="flex-1 relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2
text-outline" data-icon="filter_list">filter_list</span>
<input class="w-full bg-surface-container-low border-none rounded-lg py-2 pl-10
text-sm focus:ring-2 focus:ring-primary/20" placeholder="Search by name, ID, or
clinical flag..." type="text"/>
## </div>
<div class="flex gap-2">
<button class="px-4 py-2 bg-surface-container-high rounded-lg text-sm font-
medium hover:bg-surface-variant transition-colors">Critical</button>
<button class="px-4 py-2 bg-surface-container-low rounded-lg text-sm font-
medium hover:bg-surface-variant transition-colors">Moderate</button>
<button class="px-4 py-2 bg-surface-container-low rounded-lg text-sm font-
medium hover:bg-surface-variant transition-colors">Normal</button>
## </div>
## </div>
<div class="col-span-12 lg:col-span-4 bg-surface-container-lowest p-4 rounded-
xl flex items-center justify-between shadow-sm">
<div class="flex flex-col">
<span class="text-[0.75rem] font-bold text-outline uppercase tracking-
wider">Active Monitoring</span>
<span class="text-xl font-semibold text-primary">124 Patients</span>
## </div>
<span class="material-symbols-outlined text-primary-container text-3xl" data-
icon="monitoring">monitoring</span>

## </div>
## </div>
## <!-- Patient List Table -->
<div class="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead class="bg-surface-container-low">
## <tr>
<th class="px-6 py-4 text-[0.75rem] font-bold text-outline uppercase tracking-
widest">Patient Details</th>
<th class="px-6 py-4 text-[0.75rem] font-bold text-outline uppercase tracking-
widest">Clinical Status</th>
<th class="px-6 py-4 text-[0.75rem] font-bold text-outline uppercase tracking-
widest">Clinical Flags</th>
<th class="px-6 py-4 text-[0.75rem] font-bold text-outline uppercase tracking-
widest">Last Activity</th>
<th class="px-6 py-4 text-[0.75rem] font-bold text-outline uppercase tracking-
widest text-right">Actions</th>
## </tr>
## </thead>
<tbody class="divide-y divide-transparent">
## <!-- Row 1 -->
<tr class="hover:bg-surface-container-high/50 transition-colors group">
<td class="px-6 py-5">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-primary-fixed flex items-center justify-
center text-primary font-bold">EH</div>
## <div>
<div class="font-medium text-on-surface">Eleanor Hughes</div>
<div class="text-xs text-on-surface-variant">ID: #PX-99201</div>
## </div>
## </div>
## </td>
<td class="px-6 py-5">
<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-
secondary-container text-on-secondary-container text-xs font-semibold">
<span class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></span>
## Critical
## </span>
## </td>
<td class="px-6 py-5">
<div class="flex flex-wrap gap-2">
<span class="text-[10px] px-2 py-0.5 rounded border border-error/20 bg-error-
container/10 text-error font-medium">Elevated Glucose</span>
<span class="text-[10px] px-2 py-0.5 rounded border border-error/20 bg-error-
container/10 text-error font-medium">Low SpO2</span>
## </div>
## </td>
<td class="px-6 py-5 text-sm text-on-surface-variant">2 mins ago</td>
<td class="px-6 py-5 text-right">

<button class="p-2 rounded-lg hover:bg-surface-container-highest transition-
colors">
<span class="material-symbols-outlined text-on-surface-variant" data-
icon="more_vert">more_vert</span>
## </button>
## </td>
## </tr>
## <!-- Row 2 -->
<tr class="hover:bg-surface-container-high/50 transition-colors group">
<td class="px-6 py-5">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-tertiary-fixed flex items-center justify-
center text-tertiary font-bold">MR</div>
## <div>
<div class="font-medium text-on-surface">Marcus Rodriguez</div>
<div class="text-xs text-on-surface-variant">ID: #PX-98115</div>
## </div>
## </div>
## </td>
<td class="px-6 py-5">
<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-
tertiary-container text-on-tertiary-container text-xs font-semibold">
<span class="w-1.5 h-1.5 rounded-full bg-white"></span>
## Normal
## </span>
## </td>
<td class="px-6 py-5">
<span class="text-[10px] px-2 py-0.5 rounded bg-surface-container-high text-on-
surface-variant font-medium">Routine Baseline</span>
## </td>
<td class="px-6 py-5 text-sm text-on-surface-variant">45 mins ago</td>
<td class="px-6 py-5 text-right">
<button class="p-2 rounded-lg hover:bg-surface-container-highest transition-
colors">
<span class="material-symbols-outlined text-on-surface-variant" data-
icon="more_vert">more_vert</span>
## </button>
## </td>
## </tr>
## <!-- Row 3 -->
<tr class="hover:bg-surface-container-high/50 transition-colors group">
<td class="px-6 py-5">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-surface-container-high flex items-center
justify-center text-on-surface-variant font-bold">SM</div>
## <div>
<div class="font-medium text-on-surface">Sarah Miller</div>
<div class="text-xs text-on-surface-variant">ID: #PX-98002</div>
## </div>
## </div>

## </td>
<td class="px-6 py-5">
<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange-
100 text-orange-700 text-xs font-semibold">
<span class="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
## Moderate
## </span>
## </td>
<td class="px-6 py-5">
<div class="flex flex-wrap gap-2">
<span class="text-[10px] px-2 py-0.5 rounded border border-orange-200 bg-
orange-50 text-orange-700 font-medium">Tachycardia</span>
## </div>
## </td>
<td class="px-6 py-5 text-sm text-on-surface-variant">2 hours ago</td>
<td class="px-6 py-5 text-right">
<button class="p-2 rounded-lg hover:bg-surface-container-highest transition-
colors">
<span class="material-symbols-outlined text-on-surface-variant" data-
icon="more_vert">more_vert</span>
## </button>
## </td>
## </tr>
## <!-- Row 4 -->
<tr class="hover:bg-surface-container-high/50 transition-colors group">
<td class="px-6 py-5">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-primary-fixed flex items-center justify-
center text-primary font-bold">JW</div>
## <div>
<div class="font-medium text-on-surface">Julian White</div>
<div class="text-xs text-on-surface-variant">ID: #PX-97881</div>
## </div>
## </div>
## </td>
<td class="px-6 py-5">
<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-
tertiary-container text-on-tertiary-container text-xs font-semibold">
<span class="w-1.5 h-1.5 rounded-full bg-white"></span>
## Normal
## </span>
## </td>
<td class="px-6 py-5">
<span class="text-[10px] px-2 py-0.5 rounded bg-surface-container-high text-on-
surface-variant font-medium">Stable</span>
## </td>
<td class="px-6 py-5 text-sm text-on-surface-variant">5 hours ago</td>
<td class="px-6 py-5 text-right">
<button class="p-2 rounded-lg hover:bg-surface-container-highest transition-
colors">

<span class="material-symbols-outlined text-on-surface-variant" data-
icon="more_vert">more_vert</span>
## </button>
## </td>
## </tr>
## </tbody>
## </table>
## </div>
## <!-- Pagination -->
<div class="px-6 py-4 bg-surface-container-low flex items-center justify-
between border-t border-outline-variant/10">
<span class="text-xs text-on-surface-variant font-medium">Showing 4 of 124
## Patients</span>
<div class="flex gap-2">
<button class="p-1.5 rounded-md hover:bg-surface-container-highest transition-
colors disabled:opacity-30" disabled="">
<span class="material-symbols-outlined text-sm" data-
icon="chevron_left">chevron_left</span>
## </button>
<button class="px-3 py-1 text-xs font-bold bg-primary text-on-primary
rounded">1</button>
<button class="px-3 py-1 text-xs font-medium text-on-surface-variant hover:bg-
surface-container-highest rounded">2</button>
<button class="px-3 py-1 text-xs font-medium text-on-surface-variant hover:bg-
surface-container-highest rounded">3</button>
<button class="p-1.5 rounded-md hover:bg-surface-container-highest transition-
colors">
<span class="material-symbols-outlined text-sm" data-
icon="chevron_right">chevron_right</span>
## </button>
## </div>
## </div>
## </div>
## <!-- Detail Insights Asymmetric Layout -->
<div class="mt-8 flex flex-col lg:flex-row gap-6">
<div class="flex-1 bg-surface-container-low p-6 rounded-xl border border-
transparent">
<div class="flex items-center justify-between mb-4">
<h3 class="text-sm font-bold uppercase tracking-widest text-outline">Clinical
## Activity Trend</h3>
<span class="material-symbols-outlined text-primary" data-
icon="trending_up">trending_up</span>
## </div>
<div class="h-32 w-full bg-surface-container-lowest rounded-lg flex items-end
justify-between px-6 py-4 gap-2">
<div class="w-full bg-primary-fixed h-1/2 rounded-t-sm"></div>
<div class="w-full bg-primary-fixed h-2/3 rounded-t-sm"></div>
<div class="w-full bg-primary h-5/6 rounded-t-sm"></div>
<div class="w-full bg-primary-fixed h-1/2 rounded-t-sm"></div>
<div class="w-full bg-primary-fixed h-1/3 rounded-t-sm"></div>

<div class="w-full bg-primary-fixed h-3/4 rounded-t-sm"></div>
<div class="w-full bg-primary-fixed h-1/2 rounded-t-sm"></div>
## </div>
<p class="text-[0.75rem] text-on-surface-variant mt-4 font-medium italic">Peak
activity recorded between 08:00 - 11:00 AM</p>
## </div>
<div class="w-full lg:w-80 bg-gradient-to-br from-primary-container to-primary
p-6 rounded-xl text-white flex flex-col justify-between shadow-xl shadow-
primary/20">
## <div>
<span class="material-symbols-outlined text-3xl mb-4" data-
icon="auto_awesome">auto_awesome</span>
<h3 class="text-xl font-semibold mb-2">Smart Triage</h3>
<p class="text-sm text-blue-100/80 leading-relaxed">System AI has flagged 2 new
patients for priority review based on vital trend deviations.</p>
## </div>
<button class="mt-6 w-full py-3 bg-white text-primary font-bold rounded-lg
text-sm hover:bg-blue-50 transition-colors">
## Review Priority (2)
## </button>
## </div>
## </div>
## </main>
## </body></html>
## ===============================================================================
## =
FILE: patient_list_detailed_view_2\code.html
## ======================================================================
## ==========
<!DOCTYPE html>
<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries">
## </script>
<link href="https://fonts.googleapis.com/css2?
family=Inter:wght@300;400;500;600;700;800&amp;family=Material+Symbols+Outlined:
wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?
family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
rel="stylesheet"/>
## <style>
## .material-symbols-outlined {
font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
## }
body { font-family: 'Inter', sans-serif; }
## </style>

<script id="tailwind-config">
tailwind.config = {
darkMode: "class",
theme: {
extend: {
## "colors": {
## "on-surface-variant": "#424752",
## "surface-variant": "#e1e3e4",
## "secondary": "#b6152e",
## "on-primary-fixed": "#001a40",
## "secondary-fixed": "#ffdad9",
## "primary-fixed": "#d7e2ff",
## "on-error-container": "#93000a",
## "surface-container-low": "#f3f4f5",
## "on-secondary-container": "#fffbff",
## "surface-container-high": "#e7e8e9",
## "on-primary-fixed-variant": "#004491",
## "background": "#f8f9fa",
## "surface-container-highest": "#e1e3e4",
## "surface-bright": "#f8f9fa",
## "surface": "#f8f9fa",
## "primary-fixed-dim": "#acc7ff",
## "on-tertiary-fixed": "#002106",
## "outline": "#727784",
## "on-tertiary-fixed-variant": "#00531a",
## "tertiary-container": "#006722",
## "inverse-on-surface": "#f0f1f2",
## "secondary-container": "#d93343",
## "outline-variant": "#c2c6d4",
## "surface-container": "#edeeef",
## "on-tertiary-container": "#6fe87c",
## "on-secondary-fixed": "#410008",
## "on-primary-container": "#bbd0ff",
## "on-secondary": "#ffffff",
## "inverse-primary": "#acc7ff",
## "tertiary-fixed": "#83fc8e",
## "on-background": "#191c1d",
## "on-tertiary": "#ffffff",
## "on-surface": "#191c1d",
## "error": "#ba1a1a",
## "on-error": "#ffffff",
## "surface-dim": "#d9dadb",
## "on-primary": "#ffffff",
## "error-container": "#ffdad6",
## "tertiary": "#004c17",
## "on-secondary-fixed-variant": "#92001f",
## "inverse-surface": "#2e3132",
## "secondary-fixed-dim": "#ffb3b2",
## "tertiary-fixed-dim": "#66df75",
## "surface-tint": "#115cb9",

## "surface-container-lowest": "#ffffff",
## "primary-container": "#0056b3",
## "primary": "#003f87"
## },
"borderRadius": {
"DEFAULT": "0.5rem",
## "lg": "1rem",
## "xl": "0.75rem",
## "full": "9999px"
## }
## }
## }
## }
## </script>
## </head>
<body class="bg-background text-on-background min-h-screen">
<!-- SideNavBar -->
<aside class="fixed left-0 top-0 h-full flex flex-col py-6 bg-slate-50 dark:bg-
slate-900 w-64 border-r-0 z-50">
<div class="px-6 mb-10">
<h1 class="text-xl font-bold tracking-tight text-blue-900 dark:text-blue-
200">Pulse Portal</h1>
<p class="text-xs text-on-surface-variant mt-1">Dr. Julian Vance</p>
## </div>
<nav class="flex-1 px-4 space-y-1">
<a class="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400
hover:text-blue-600 dark:hover:text-blue-300 transition-colors" href="#">
<span class="material-symbols-outlined" data-icon="dashboard">dashboard</span>
## Dashboard
## </a>
## <!-- Active Tab: Patients -->
<a class="flex items-center gap-3 px-4 py-3 text-blue-700 dark:text-blue-400
font-semibold bg-white dark:bg-slate-950 rounded-l-full shadow-sm translate-x-1
duration-200" href="#">
<span class="material-symbols-outlined" data-icon="group">group</span>
## Patients
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400
hover:text-blue-600 dark:hover:text-blue-300 transition-colors" href="#">
<span class="material-symbols-outlined" data-
icon="calendar_today">calendar_today</span>
## Appointments
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400
hover:text-blue-600 dark:hover:text-blue-300 transition-colors" href="#">
<span class="material-symbols-outlined" data-icon="analytics">analytics</span>
## Analytics
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400
hover:text-blue-600 dark:hover:text-blue-300 transition-colors" href="#">

<span class="material-symbols-outlined" data-
icon="description">description</span>
## Reports
## </a>
<a class="flex items-center gap-3 px-4 py-3 text-slate-500 dark:text-slate-400
hover:text-blue-600 dark:hover:text-blue-300 transition-colors" href="#">
<span class="material-symbols-outlined" data-icon="settings">settings</span>
## Settings
## </a>
## </nav>
<div class="px-6 pt-6 mt-auto">
<div class="flex items-center gap-3 p-2 rounded-xl bg-surface-container-low">
<img alt="Clinician profile picture" class="w-10 h-10 rounded-full object-
cover" data-alt="professional portrait of a male doctor in his 40s wearing a
white clinical coat and stethoscope in a bright office"
src="https://lh3.googleusercontent.com/aida-
public/AB6AXuAGjggVl85htWpaFTluWZDHhrmkbSeUY7kR5LG9rYvHhh71MOYhWEO6vq-
SuAmkokpO9EOHLdrlPRW76bf4FSsNmr6heOdqmj4HhXfw3LbcrwOdCVYFRcZaJV3VUC_pwYltPMBmZF
dZyoPzkH5I4bLZ-wN86l5-
QsAnvFKEn6IK5n5mlSTSQy2o4azoaARC9IS0LhKG52g8SYmyHJ1dxqK0W8DkilsY4fvYcgxwVMTesL6
UNydR0iICZePlrUDoX4ypYXBVutpwBcM"/>
<div class="overflow-hidden">
<p class="text-sm font-semibold truncate text-on-surface">Dr. J. Vance</p>
<p class="text-[10px] uppercase tracking-wider text-on-surface-
variant">Cardiologist</p>
## </div>
## </div>
## </div>
## </aside>
<!-- TopNavBar -->
<header class="w-full h-16 sticky top-0 z-40 bg-white/80 dark:bg-slate-950/80
backdrop-blur-md flex items-center justify-between px-8 ml-64 w-
[calc(100%-16rem)] shadow-sm dark:shadow-none shadow-slate-200/50">
<div class="flex items-center gap-6">
<span class="text-lg font-semibold text-slate-900 dark:text-slate-50">Clinical
## Intelligence</span>
<div class="relative group">
<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-
none">
<span class="material-symbols-outlined text-outline text-sm" data-
icon="search">search</span>
## </div>
<input class="bg-surface-container-low border-none rounded-full py-1.5 pl-10
pr-4 text-sm w-64 focus:ring-2 focus:ring-blue-500/20 transition-all"
placeholder="Global search..." type="text"/>
## </div>
## </div>
<div class="flex items-center gap-4">
<button class="text-slate-500 hover:text-blue-600 transition-opacity">
<span class="material-symbols-outlined" data-

icon="notifications">notifications</span>
## </button>
<button class="text-slate-500 hover:text-blue-600 transition-opacity">
<span class="material-symbols-outlined" data-
icon="emergency_home">emergency_home</span>
## </button>
<div class="h-4 w-[1px] bg-outline-variant/30"></div>
<button class="text-sm font-medium tracking-wide text-blue-700 dark:text-blue-
400">Support</button>
## </div>
## </header>
## <!-- Main Content -->
<main class="ml-64 p-8">
## <!-- Header Section -->
<div class="flex items-end justify-between mb-10 gap-4">
## <div>
<h2 class="text-[1.75rem] font-medium text-on-surface leading-tight">Patient
## Directory</h2>
<p class="text-on-surface-variant mt-1">Manage and monitor active clinical
records in real-time.</p>
## </div>
<button class="border border-outline-variant text-on-surface-variant px-6 py-4
rounded-lg flex items-center gap-2 font-medium hover:bg-surface-container-high
transition-colors">
<span class="material-symbols-outlined" data-icon="download">download</span>
Export to CSV
</button><button class="bg-gradient-to-br from-primary to-primary-container
text-on-primary px-8 py-4 rounded-lg flex items-center gap-2 font-medium
shadow-lg shadow-primary/10 hover:opacity-90 transition-opacity">
<span class="material-symbols-outlined" data-
icon="person_add">person_add</span>
## New Patient
## </button>
## </div>
## <!-- Filters & Search Bento -->
<div class="grid grid-cols-12 gap-6 mb-8">
<div class="col-span-12 lg:col-span-8 bg-surface-container-lowest p-4 rounded-
xl flex items-center gap-4 shadow-sm">
<div class="flex-1 relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2
text-outline" data-icon="filter_list">filter_list</span>
<input class="w-full bg-surface-container-low border-none rounded-lg py-2 pl-10
text-sm focus:ring-2 focus:ring-primary/20" placeholder="Search by name, ID, or
clinical flag..." type="text"/>
## </div>
<div class="flex gap-2">
<button class="px-4 py-2 bg-surface-container-high rounded-lg text-sm font-
medium hover:bg-surface-variant transition-colors">Critical</button>
<button class="px-4 py-2 bg-surface-container-low rounded-lg text-sm font-
medium hover:bg-surface-variant transition-colors">Moderate</button>

<button class="px-4 py-2 bg-surface-container-low rounded-lg text-sm font-
medium hover:bg-surface-variant transition-colors">Normal</button>
## </div>
## </div>
<div class="col-span-12 lg:col-span-4 bg-surface-container-lowest p-4 rounded-
xl flex items-center justify-between shadow-sm">
<div class="flex flex-col">
<span class="text-[0.75rem] font-bold text-outline uppercase tracking-
wider">Active Monitoring</span>
<span class="text-xl font-semibold text-primary">124 Patients</span>
## </div>
<span class="material-symbols-outlined text-primary-container text-3xl" data-
icon="monitoring">monitoring</span>
## </div>
## </div>
## <!-- Patient List Table -->
<div class="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
<div class="overflow-x-auto">
<table class="w-full text-left border-collapse">
<thead class="bg-surface-container-low">
## <tr>
<th class="px-6 py-4 text-[0.75rem] font-bold text-outline uppercase tracking-
widest">Patient Details</th>
<th class="px-6 py-4 text-[0.75rem] font-bold text-outline uppercase tracking-
widest">Clinical Status</th>
<th class="px-6 py-4 text-[0.75rem] font-bold text-outline uppercase tracking-
widest">Clinical Flags</th>
<th class="px-6 py-4 text-[0.75rem] font-bold text-outline uppercase tracking-
widest">Last Activity</th>
<th class="px-6 py-4 text-[0.75rem] font-bold text-outline uppercase tracking-
widest text-right">Actions</th>
## </tr>
## </thead>
<tbody class="divide-y divide-transparent">
## <!-- Row 1 -->
<tr class="hover:bg-surface-container-high/50 transition-colors group">
<td class="px-6 py-5">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-primary-fixed flex items-center justify-
center text-primary font-bold">EH</div>
## <div>
<div class="font-medium text-on-surface">Eleanor Hughes</div>
<div class="text-xs text-on-surface-variant">ID: #PX-99201</div>
## </div>
## </div>
## </td>
<td class="px-6 py-5">
<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-
secondary-container text-on-secondary-container text-xs font-semibold">
<span class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></span>

## Critical
## </span>
## </td>
<td class="px-6 py-5">
<div class="flex flex-wrap gap-2">
<span class="text-[10px] px-2 py-0.5 rounded border border-error/20 bg-error-
container/10 text-error font-medium">Elevated Glucose</span>
<span class="text-[10px] px-2 py-0.5 rounded border border-error/20 bg-error-
container/10 text-error font-medium">Low SpO2</span>
## </div>
## </td>
<td class="px-6 py-5 text-sm text-on-surface-variant">2 mins ago</td>
<td class="px-6 py-5 text-right">
<button class="p-2 rounded-lg hover:bg-surface-container-highest transition-
colors">
<span class="material-symbols-outlined text-on-surface-variant" data-
icon="more_vert">more_vert</span>
## </button>
## </td>
## </tr>
## <!-- Row 2 -->
<tr class="hover:bg-surface-container-high/50 transition-colors group">
<td class="px-6 py-5">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-tertiary-fixed flex items-center justify-
center text-tertiary font-bold">MR</div>
## <div>
<div class="font-medium text-on-surface">Marcus Rodriguez</div>
<div class="text-xs text-on-surface-variant">ID: #PX-98115</div>
## </div>
## </div>
## </td>
<td class="px-6 py-5">
<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-
tertiary-container text-on-tertiary-container text-xs font-semibold">
<span class="w-1.5 h-1.5 rounded-full bg-white"></span>
## Normal
## </span>
## </td>
<td class="px-6 py-5">
<span class="text-[10px] px-2 py-0.5 rounded bg-surface-container-high text-on-
surface-variant font-medium">Routine Baseline</span>
## </td>
<td class="px-6 py-5 text-sm text-on-surface-variant">45 mins ago</td>
<td class="px-6 py-5 text-right">
<button class="p-2 rounded-lg hover:bg-surface-container-highest transition-
colors">
<span class="material-symbols-outlined text-on-surface-variant" data-
icon="more_vert">more_vert</span>
## </button>

## </td>
## </tr>
## <!-- Row 3 -->
<tr class="hover:bg-surface-container-high/50 transition-colors group">
<td class="px-6 py-5">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-surface-container-high flex items-center
justify-center text-on-surface-variant font-bold">SM</div>
## <div>
<div class="font-medium text-on-surface">Sarah Miller</div>
<div class="text-xs text-on-surface-variant">ID: #PX-98002</div>
## </div>
## </div>
## </td>
<td class="px-6 py-5">
<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange-
100 text-orange-700 text-xs font-semibold">
<span class="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
## Moderate
## </span>
## </td>
<td class="px-6 py-5">
<div class="flex flex-wrap gap-2">
<span class="text-[10px] px-2 py-0.5 rounded border border-orange-200 bg-
orange-50 text-orange-700 font-medium">Tachycardia</span>
## </div>
## </td>
<td class="px-6 py-5 text-sm text-on-surface-variant">2 hours ago</td>
<td class="px-6 py-5 text-right">
<button class="p-2 rounded-lg hover:bg-surface-container-highest transition-
colors">
<span class="material-symbols-outlined text-on-surface-variant" data-
icon="more_vert">more_vert</span>
## </button>
## </td>
## </tr>
## <!-- Row 4 -->
<tr class="hover:bg-surface-container-high/50 transition-colors group">
<td class="px-6 py-5">
<div class="flex items-center gap-4">
<div class="w-10 h-10 rounded-full bg-primary-fixed flex items-center justify-
center text-primary font-bold">JW</div>
## <div>
<div class="font-medium text-on-surface">Julian White</div>
<div class="text-xs text-on-surface-variant">ID: #PX-97881</div>
## </div>
## </div>
## </td>
<td class="px-6 py-5">
<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-

tertiary-container text-on-tertiary-container text-xs font-semibold">
<span class="w-1.5 h-1.5 rounded-full bg-white"></span>
## Normal
## </span>
## </td>
<td class="px-6 py-5">
<span class="text-[10px] px-2 py-0.5 rounded bg-surface-container-high text-on-
surface-variant font-medium">Stable</span>
## </td>
<td class="px-6 py-5 text-sm text-on-surface-variant">5 hours ago</td>
<td class="px-6 py-5 text-right">
<button class="p-2 rounded-lg hover:bg-surface-container-highest transition-
colors">
<span class="material-symbols-outlined text-on-surface-variant" data-
icon="more_vert">more_vert</span>
## </button>
## </td>
## </tr>
## </tbody>
## </table>
## </div>
## <!-- Pagination -->
<div class="px-6 py-4 bg-surface-container-low flex items-center justify-
between border-t border-outline-variant/10">
<span class="text-xs text-on-surface-variant font-medium">Showing 4 of 124
## Patients</span>
<div class="flex gap-2">
<button class="p-1.5 rounded-md hover:bg-surface-container-highest transition-
colors disabled:opacity-30" disabled="">
<span class="material-symbols-outlined text-sm" data-
icon="chevron_left">chevron_left</span>
## </button>
<button class="px-3 py-1 text-xs font-bold bg-primary text-on-primary
rounded">1</button>
<button class="px-3 py-1 text-xs font-medium text-on-surface-variant hover:bg-
surface-container-highest rounded">2</button>
<button class="px-3 py-1 text-xs font-medium text-on-surface-variant hover:bg-
surface-container-highest rounded">3</button>
<button class="p-1.5 rounded-md hover:bg-surface-container-highest transition-
colors">
<span class="material-symbols-outlined text-sm" data-
icon="chevron_right">chevron_right</span>
## </button>
## </div>
## </div>
## </div>
## <!-- Detail Insights Asymmetric Layout -->
<div class="mt-8 flex flex-col lg:flex-row gap-6">
<div class="flex-1 bg-surface-container-low p-6 rounded-xl border border-
transparent">

<div class="flex items-center justify-between mb-4">
<h3 class="text-sm font-bold uppercase tracking-widest text-outline">Clinical
## Activity Trend</h3>
<span class="material-symbols-outlined text-primary" data-
icon="trending_up">trending_up</span>
## </div>
<div class="h-32 w-full bg-surface-container-lowest rounded-lg flex items-end
justify-between px-6 py-4 gap-2">
<div class="w-full bg-primary-fixed h-1/2 rounded-t-sm"></div>
<div class="w-full bg-primary-fixed h-2/3 rounded-t-sm"></div>
<div class="w-full bg-primary h-5/6 rounded-t-sm"></div>
<div class="w-full bg-primary-fixed h-1/2 rounded-t-sm"></div>
<div class="w-full bg-primary-fixed h-1/3 rounded-t-sm"></div>
<div class="w-full bg-primary-fixed h-3/4 rounded-t-sm"></div>
<div class="w-full bg-primary-fixed h-1/2 rounded-t-sm"></div>
## </div>
<p class="text-[0.75rem] text-on-surface-variant mt-4 font-medium italic">Peak
activity recorded between 08:00 - 11:00 AM</p>
## </div>
<div class="w-full lg:w-80 bg-gradient-to-br from-primary-container to-primary
p-6 rounded-xl text-white flex flex-col justify-between shadow-xl shadow-
primary/20">
## <div>
<span class="material-symbols-outlined text-3xl mb-4" data-
icon="auto_awesome">auto_awesome</span>
<h3 class="text-xl font-semibold mb-2">Smart Triage</h3>
<p class="text-sm text-blue-100/80 leading-relaxed">System AI has flagged 2 new
patients for priority review based on vital trend deviations.</p>
## </div>
<button class="mt-6 w-full py-3 bg-white text-primary font-bold rounded-lg
text-sm hover:bg-blue-50 transition-colors">
## Review Priority (2)
## </button>
## </div>
## </div>
## </main>
## </body></html>
## ===============================================================================
## =
FILE: server_code\drug_logic.py
## ======================================================================
## ==========
server_code/drug_logic.py
Contains mapping of diseases to recommended drugs,
dosages, and precautions.

## DRUG_DATABASE = {
"Type 2 Diabetes": {
"drug": "Metformin",
"dosage": "500mg twice a daily after meals",
"precautions": "Avoid sugary foods. Monitor blood glucose regularly."
## },
"Hypertension": {
"drug": "Amlodipine",
"dosage": "5mg once daily",
"precautions": "Reduce salt intake. Monitor blood pressure."
## },
## "COVID-19": {
"drug": "Paracetamol, Vitamin C & Zinc",
"dosage": "500mg SOS for fever, daily supplements",
"precautions": "Isolate, rest, and stay hydrated."
## },
"Malaria": {
"drug": "Artemether-Lumefantrine",
"dosage": "As prescribed by physician (usually 6 doses over 3 days)",
"precautions": "Complete the full course even if symptoms improve."
## },
"Typhoid": {
"drug": "Ciprofloxacin",
"dosage": "500mg twice daily for 7 days",
"precautions": "Drink boiled or purified water. Eat safely prepared food."
## }
## }
def get_drug_info(disease_name):
"""Returns drug recommendation based on the mapped disease."""
return DRUG_DATABASE.get(disease_name, {
"drug": "Consult Doctor",
"dosage": "N/A",
"precautions": "No specific data found for this disease. Please consult a
healthcare professional."
## })
## ===============================================================================
## =
FILE: server_code\model.py
## ======================================================================
## ==========
server_code/model.py
ML model logic using scikit-learn
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from sklearn.pipeline import make_pipeline
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
Dynamically load the dataset instead of using
dummy data
csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
## 'symptoms_disease.csv')
diseases = []
symptoms = []
if os.path.exists(csv_path):
df = pd.read_csv(csv_path)
# The CSV has 'disease' and 'symptoms' columns
for idx, row in df.iterrows():
disease = row['disease']
sym_text = str(row['symptoms']).replace('_', ' ')
else:
# Fallback just in case CSV is missing, but this shouldn't happen
diseases = ["Unknown"] * 3
symptoms = ["no symptoms found"] * 3
Using a simple TF-IDF + Logistic Regression
pipeline
model = make_pipeline(TfidfVectorizer(stop_words='english'),
LogisticRegression())
model.fit(symptoms, diseases)
def predict_single_disease(text):
## """
Predict disease based on extracted text or symptoms.
Uses ML model (TF-IDF + Logistic Regression).
## """
try:
if not text or len(text.strip()) < 3:
return "Unknown (Text too short)"
`# We duplicate and vary the dataset slightly to avoid single-sample-
per-class warnings`
`diseases.extend([disease, disease, disease])`
`symptoms.extend([sym_text, sym_text + " mild", sym_text + " severe"])`

def predict_disease_with_probabilities(text):
## """
Predict disease and return the top probabilities.
Returns a tuple: (main_disease_name, confidence, top_predictions_list)
## """
try:
if not text or len(text.strip()) < 3:
return "Unknown (Text too short)", 0.0, []
## ===============================================================================
## =
FILE: server_code\prediction.py
## ======================================================================
## ==========
server_code/prediction.py
import anvil.server
import anvil.media
import tempfile
import os
`prediction = model.predict([text])[0]`
`return prediction`
`except Exception as e:`
`print(f"Error in predict_single_disease: {e}")`
`return "Prediction Error"`
`# Get raw probabilities`
`probs = model.predict_proba([text])[0]`
`classes = model.classes_`
`# Pair classes with probabilities`
`results = list(zip(classes, probs))`
`results.sort(key=lambda x: x[1], reverse=True)`
`main_disease = results[0][0]`
`confidence = float(results[0][1])`
`# Format top predictions as dicts`
`top_preds = [{"disease": d, "confidence": float(c)} for d, c in
results[1:6]]`
`return main_disease, confidence, top_preds`
`except Exception as e:`
`print(f"Error in predict_disease_with_probabilities: {e}")`
`return "Prediction Error", 0.0, []`

Important for pure-Anvil hosting: if these are
separate Server Modules,
Anvil allows importing them simply by their module
name. If you use a package folder,
you might use: from . import model
Here we assume they are configured as standard
Server Modules or Uplink modules:
try:
import model
import drug_logic
import severity
except ImportError:
# Fallback for Anvil Package Structure
from . import model
from . import drug_logic
from . import severity
try:
import pdfplumber
except ImportError:
print("Warning: pdfplumber not found. PDF extraction will fail.")
try:
import pytesseract
from PIL import Image
except ImportError:
print("Warning: pytesseract or Pillow not found. Image extraction will fail.")
def extract_text_from_pdf(file_path):
text = ""
try:
with pdfplumber.open(file_path) as pdf:
for page in pdf.pages:
page_text = page.extract_text()
if page_text:
text += page_text + "\n"
except Exception as e:
print(f"PDF Extraction Error: {e}")
return text
def extract_text_from_image(file_path):
text = ""
try:
img = Image.open(file_path)
text = pytesseract.image_to_string(img)
except Exception as e:

print(f"Image Extraction Error: {e}")
return text
## @anvil.server.callable
def predict_disease(symptoms_text):
## """
Predict disease from manually entered symptoms.
## """
print(f"Analyzing symptoms: {symptoms_text[:100]}...")
## @anvil.server.callable
def analyze_report(media_file):
## """
Extracts text from an Anvil Media object (PDF/Image) and predicts disease.
## """
if not media_file:
return {"error": "File is empty or missing."}
`disease = model.predict_single_disease(symptoms_text)`
`drug_info = drug_logic.get_drug_info(disease)`
`severity_level = severity.analyze_severity(symptoms_text)`
## `return {`
`"disease": disease,`
`"drug": drug_info["drug"],`
`"dosage": drug_info["dosage"],`
`"precautions": drug_info["precautions"],`
`"severity": severity_level,`
`"extracted_text": "Manual input provided."`
## `}`
`print(f"Analyzing uploaded report: {media_file.name}")`
`# Save media_file to a temporary file`
`with tempfile.NamedTemporaryFile(delete=False) as tmp:`
`# get_bytes() is available on Anvil Media objects`
## `tmp.write(media_file.get_bytes())`
`tmp_path = tmp.name`
## `extracted_text = ""`
## `try:`
`if media_file.name.lower().endswith(".pdf"):`
`extracted_text = extract_text_from_pdf(tmp_path)`
`elif media_file.name.lower().endswith((".png", ".jpg", ".jpeg")):`
`extracted_text = extract_text_from_image(tmp_path)`
## `else:`
`return {"error": "Unsupported file format. Please upload a PDF or
## Image."}`
## `finally:`

## ===============================================================================
## =
FILE: server_code\severity.py
## ======================================================================
## ==========
server_code/severity.py
Rule-based severity classification
## CRITICAL_KEYWORDS = [
"chest pain", "heart attack", "stroke", "very high glucose",
"severe bleeding", "unconscious", "breathing difficulty", "coma", "critical",
## "severe"
## ]
## MODERATE_KEYWORDS = [
"fever", "pain", "high blood pressure", "elevated", "infection",
## "cough", "weakness", "dizziness", "nausea", "vomiting"
## ]
def analyze_severity(text_or_symptoms):
## """
Rule-based classification of severity based on keywords in text.
Returns Critical, Moderate, or Normal.
## `os.remove(tmp_path)`
`if not extracted_text.strip():`
`return {"error": "Could not extract text from the provided file. It
might be empty or unreadable."}`
`print(f"Extracted {len(extracted_text)} characters.")`
`disease = model.predict_single_disease(extracted_text)`
`drug_info = drug_logic.get_drug_info(disease)`
`severity_level = severity.analyze_severity(extracted_text)`
`# Create a small summary snippet`
`snippet = extracted_text[:200] + "..." if len(extracted_text) > 200 else
extracted_text`
## `return {`
`"disease": disease,`
`"drug": drug_info["drug"],`
`"dosage": drug_info["dosage"],`
`"precautions": drug_info["precautions"],`
`"severity": severity_level,`
`"extracted_text": snippet`
## `}`

## """
if not text_or_symptoms:
return "Unknown"
`text_lower = str(text_or_symptoms).lower()`
`# Check for critical keywords`
`for word in CRITICAL_KEYWORDS:`
`if word in text_lower:`
`return "Critical"`
`# Check for moderate keywords`
`for word in MODERATE_KEYWORDS:`
`if word in text_lower:`
`return "Moderate"`
`# Default fallback`
`return "Normal"`