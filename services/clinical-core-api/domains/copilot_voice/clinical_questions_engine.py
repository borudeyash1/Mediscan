"""
Clinical Interview Prompt & Dynamic Follow-up Question Engine.
Suggests real-time evidence-based red-flag interview questions
based on incremental patient dialogue and active symptoms.
"""

from typing import Optional, TypedDict
from .models import ClinicalInterviewPrompt


class TriggerRule(TypedDict):
    keywords: list[str]
    trigger: str
    question: str
    rationale: str
    urgency: str


class ClinicalInterviewPromptEngine:
    """Detects symptom triggers in ambient speech and emits targeted clinical follow-up prompts."""

    TRIGGER_RULES: list[TriggerRule] = [
        {
            "keywords": ["chest pain", "angina", "chest pressure", "tightness in chest", "heaviness in chest"],
            "trigger": "Chest Pain",
            "question": "Ask patient about radiation to left arm, neck, or jaw, onset timing, and whether symptoms worsen with exertion or deep inspiration.",
            "rationale": "Differentiate acute coronary syndrome (ACS) from pericarditis, aortic dissection, and musculoskeletal chest wall pain.",
            "urgency": "CRITICAL",
        },
        {
            "keywords": ["short of breath", "shortness of breath", "dyspnea", "hard to breathe", "cant breathe", "can't breathe"],
            "trigger": "Dyspnea / Shortness of Breath",
            "question": "Ask patient about orthopnea (number of pillows needed to sleep), paroxysmal nocturnal dyspnea, and bilateral lower extremity swelling.",
            "rationale": "Evaluate for acute heart failure decompensation, pulmonary embolism, or asthma/COPD exacerbation.",
            "urgency": "HIGH",
        },
        {
            "keywords": ["headache", "head pain", "migraine", "severe headache"],
            "trigger": "Severe Headache",
            "question": "Ask about sudden onset 'thunderclap' intensity within seconds, neck stiffness, photophobia, fever, or focal weakness.",
            "rationale": "Rule out subarachnoid hemorrhage, acute bacterial meningitis, or acute intracranial hypertension.",
            "urgency": "HIGH",
        },
        {
            "keywords": ["fever", "chills", "high temperature", "febrile"],
            "trigger": "Fever / Pyrexia",
            "question": "Ask about rigors, rash, recent mosquito exposure, travel history, productive cough, or burning with urination.",
            "rationale": "Assess for tropical arboviral infections (Dengue, Malaria), pneumonia, pyelonephritis, or evolving sepsis.",
            "urgency": "MEDIUM",
        },
        {
            "keywords": ["sugar", "diabetes", "thirsty", "polydipsia", "urinating frequently", "polyuria"],
            "trigger": "Diabetic Symptoms",
            "question": "Ask about unintended weight loss, blurred vision, numbness/burning in feet, and any episodes of sweating/tremors indicative of hypoglycemia.",
            "rationale": "Detect glycemic dysregulation, diabetic ketoacidosis risk, and peripheral neuropathy.",
            "urgency": "MEDIUM",
        },
        {
            "keywords": ["palpitation", "heart racing", "fluttering", "skipping beats"],
            "trigger": "Palpitations",
            "question": "Ask if the palpitations feel regular or chaotic/irregularly irregular, and whether dizziness, presyncope, or chest tightness accompanied them.",
            "rationale": "Screen for atrial fibrillation, supraventricular tachycardia, or hemodynamically significant ventricular ectopy.",
            "urgency": "HIGH",
        },
        {
            "keywords": ["stomach pain", "abdominal pain", "belly ache", "belly pain"],
            "trigger": "Abdominal Pain",
            "question": "Ask about location (quadrant), radiation to the back or shoulder, association with fatty meals, and presence of melena or hematochezia.",
            "rationale": "Differentiate acute cholecystitis, pancreatitis, appendicitis, and acute mesenteric ischemia.",
            "urgency": "MEDIUM",
        },
        {
            "keywords": ["dizzy", "lightheaded", "passed out", "fainted", "syncope", "blackout"],
            "trigger": "Syncope / Presyncope",
            "question": "Ask if the event occurred upon standing (orthostatic) or with exertion, whether prodromal nausea/sweating was present, and if tongue biting or post-ictal confusion occurred.",
            "rationale": "Differentiate vasovagal syncope and orthostasis from cardiogenic syncope or seizure activity.",
            "urgency": "HIGH",
        },
    ]

    def __init__(self):
        self.fired_triggers: set[str] = set()

    def reset_session(self) -> None:
        """Reset trigger history for a new patient encounter."""
        self.fired_triggers.clear()

    def evaluate_utterance(self, text: str, is_patient: bool = True) -> list[ClinicalInterviewPrompt]:
        """
        Evaluate incremental utterance text and return any newly triggered interview prompts.
        Only patient utterances (or physician confirmation) trigger prompts, avoiding loops.
        """
        lower_text = text.lower()
        new_prompts: list[ClinicalInterviewPrompt] = []

        negation_markers = ["no ", "not ", "denies ", "without ", "never ", "haven't had ", "didn't have "]
        contrastive_delimiters = [", but ", " but ", ". ", "; ", ", however ", " however "]

        for rule in self.TRIGGER_RULES:
            trigger_name = rule["trigger"]
            if trigger_name in self.fired_triggers:
                continue

            # Check if any keyword matches and is NOT negated
            matched = False
            for kw in rule["keywords"]:
                pos = lower_text.find(kw)
                if pos != -1:
                    pre_window = lower_text[max(0, pos - 35):pos]
                    for delim in contrastive_delimiters:
                        if delim in pre_window:
                            pre_window = pre_window.split(delim)[-1]
                    is_negated = any(marker in pre_window for marker in negation_markers)
                    if not is_negated:
                        matched = True
                        break

            if matched:
                self.fired_triggers.add(trigger_name)
                prompt = ClinicalInterviewPrompt(
                    trigger_symptom=trigger_name,
                    suggested_question=rule["question"],
                    clinical_rationale=rule["rationale"],
                    urgency=rule["urgency"],
                )
                new_prompts.append(prompt)

        return new_prompts
