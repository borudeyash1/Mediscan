"""
MediScan Enterprise — Negation-Aware Clinical NER & Temporal Extractor
======================================================================
Extracts symptoms, vitals, conditions, and historical findings.
Annotates each entity with:
- SNOMED-CT Concept ID
- Assertion: PRESENT | ABSENT | HYPOTHETICAL | FAMILY_HISTORY
- Temporality: ACUTE | CHRONIC | RESOLVED
- Source Span: exact [start, end] character offsets for UI highlighting
"""

import re
from typing import Any, Tuple
from .models import AssertionType, ExtractedEntity, TemporalityType


SNOMED_LEXICON: dict[str, dict[str, str]] = {
    "chest pain": {"snomed_code": "29857009", "preferred": "Chest pain"},
    "fever": {"snomed_code": "386661004", "preferred": "Fever"},
    "polyuria": {"snomed_code": "28442001", "preferred": "Polyuria"},
    "polydipsia": {"snomed_code": "17173007", "preferred": "Polydipsia"},
    "weight loss": {"snomed_code": "89362005", "preferred": "Weight loss"},
    "weight gain": {"snomed_code": "8943002", "preferred": "Weight gain"},
    "mild headache": {"snomed_code": "25064002", "preferred": "Headache"},
    "headache": {"snomed_code": "25064002", "preferred": "Headache"},
    "shortness of breath": {"snomed_code": "267036007", "preferred": "Dyspnea"},
    "breathlessness": {"snomed_code": "267036007", "preferred": "Dyspnea"},
    "dyspnea": {"snomed_code": "267036007", "preferred": "Dyspnea"},
    "cough": {"snomed_code": "49727002", "preferred": "Cough"},
    "wheezing": {"snomed_code": "56018004", "preferred": "Wheezing"},
    "fatigue": {"snomed_code": "84229001", "preferred": "Fatigue"},
    "weakness": {"snomed_code": "84229001", "preferred": "Weakness"},
    "dizziness": {"snomed_code": "404640003", "preferred": "Dizziness"},
    "vertigo": {"snomed_code": "404640003", "preferred": "Vertigo"},
    "nausea": {"snomed_code": "422587007", "preferred": "Nausea"},
    "vomiting": {"snomed_code": "422400008", "preferred": "Vomiting"},
    "diarrhea": {"snomed_code": "62315008", "preferred": "Diarrhea"},
    "abdominal pain": {"snomed_code": "21522001", "preferred": "Abdominal pain"},
    "palpitations": {"snomed_code": "80313002", "preferred": "Palpitations"},
    "palpitation": {"snomed_code": "80313002", "preferred": "Palpitations"},
    "edema": {"snomed_code": "267038006", "preferred": "Edema"},
    "swelling": {"snomed_code": "267038006", "preferred": "Swelling"},
    "stroke": {"snomed_code": "230690007", "preferred": "Stroke"},
    "heart attack": {"snomed_code": "22298006", "preferred": "Myocardial infarction"},
    "myocardial infarction": {"snomed_code": "22298006", "preferred": "Myocardial infarction"},
    "hypertension": {"snomed_code": "38341003", "preferred": "Hypertension"},
    "high blood pressure": {"snomed_code": "38341003", "preferred": "Hypertension"},
    "diabetes": {"snomed_code": "73211009", "preferred": "Diabetes mellitus"},
    "diabetes mellitus": {"snomed_code": "73211009", "preferred": "Diabetes mellitus"},
    "seizure": {"snomed_code": "91175000", "preferred": "Seizure"},
    "syncope": {"snomed_code": "271594007", "preferred": "Syncope"},
    "fainting": {"snomed_code": "271594007", "preferred": "Syncope"},
    "rash": {"snomed_code": "271807003", "preferred": "Eruption"},
    "jaundice": {"snomed_code": "18165001", "preferred": "Jaundice"},
    "blurred vision": {"snomed_code": "246636008", "preferred": "Blurred vision"},
}

# Negation scope trigger expressions
NEGATION_PRE_TRIGGERS = [
    r"\bdenies\b",
    r"\bdenied\b",
    r"\bdenying\b",
    r"\bno\b",
    r"\bnot\b",
    r"\bwithout\b",
    r"\bnegative\s+for\b",
    r"\bruled\s+out\b",
    r"\bfree\s+of\b",
    r"\bnever\s+had\b",
    r"\babsence\s+of\b",
    r"\bnot\s+experiencing\b",
    r"\bno\s+evidence\s+of\b",
    r"\bno\s+signs\s+of\b",
]

FAMILY_HISTORY_TRIGGERS = [
    r"\bfamily\s+history\s+of\b",
    r"\bmother\s+had\b",
    r"\bfather\s+had\b",
    r"\bsibling\s+with\b",
    r"\bmaternal\b",
    r"\bpaternal\b",
    r"\bparent\s+had\b",
    r"\bparents\s+had\b",
    r"\bbrother\s+with\b",
    r"\bsister\s+with\b",
]

HYPOTHETICAL_TRIGGERS = [
    r"\bif\s+patient\s+develops\b",
    r"\bmonitor\s+for\b",
    r"\breturn\s+if\b",
    r"\bin\s+case\s+of\b",
    r"\brisk\s+of\b",
    r"\bscreen\s+for\b",
    r"\bwatch\s+for\b",
    r"\bprecaution\s+for\b",
]

CHRONIC_DURATION_PATTERNS = [
    r"\bover\s+[0-9]+\s+(?:months?|years?|weeks?)\b",
    r"\bfor\s+[0-9]+\s+(?:months?|years?|weeks?)\b",
    r"\bchronic\b",
    r"\blongstanding\b",
    r"\bhx\s+of\b",
    r"\bhistory\s+of\b",
    r"\bpast\s+[0-9]+\s+(?:months?|years?)\b",
]

RESOLVED_PATTERNS = [
    r"\bresolved\b",
    r"\bpreviously\b",
    r"\bno\s+longer\b",
    r"\bsubsided\b",
    r"\bpast\b",
    r"\bprior\b",
]


class NegationAwareClinicalNER:
    """Extracts clinical concepts with context-aware assertion and temporality tagging."""

    @classmethod
    def get_sentence_boundaries(cls, text: str) -> list[Tuple[int, int]]:
        """Splits text into sentence spans based on punctuation."""
        spans: list[Tuple[int, int]] = []
        start = 0
        for match in re.finditer(r"[.!?;\n]+", text):
            end = match.end()
            if start < end:
                spans.append((start, end))
            start = end
        if start < len(text):
            spans.append((start, len(text)))
        return spans

    @classmethod
    def find_enclosing_sentence(cls, char_idx: int, sentence_spans: list[Tuple[int, int]]) -> Tuple[int, int]:
        """Returns the start and end of the sentence containing char_idx."""
        for s_start, s_end in sentence_spans:
            if s_start <= char_idx < s_end:
                return (s_start, s_end)
        return (0, len(sentence_spans))

    @classmethod
    def evaluate_assertion(
        cls,
        entity_span: Tuple[int, int],
        sentence_text: str,
        entity_rel_span: Tuple[int, int],
    ) -> AssertionType:
        """
        Determines whether the entity is PRESENT, ABSENT, FAMILY_HISTORY, or HYPOTHETICAL.
        Takes into account negation scope and conjunction distribution ("denies chest pain or fever").
        """
        ent_start, ent_end = entity_rel_span
        pre_context = sentence_text[:ent_start]
        post_context = sentence_text[ent_end:]

        # 1. Family History check
        for pattern in FAMILY_HISTORY_TRIGGERS:
            if re.search(pattern, pre_context, re.IGNORECASE):
                return AssertionType.FAMILY_HISTORY

        # 2. Hypothetical check
        for pattern in HYPOTHETICAL_TRIGGERS:
            if re.search(pattern, pre_context, re.IGNORECASE):
                return AssertionType.HYPOTHETICAL

        # 3. Negation check (Pre-negation triggers)
        # Check if pre-negation trigger exists in pre_context without an intervening contrastive word (e.g. "but")
        for trigger in NEGATION_PRE_TRIGGERS:
            for match in re.finditer(trigger, pre_context, re.IGNORECASE):
                trigger_end = match.end()
                between_text = pre_context[trigger_end:]
                # If there's a scope terminator like "but", "however", "except", negation doesn't apply
                if re.search(r"\b(but|however|although|except)\b", between_text, re.IGNORECASE):
                    continue

                # Support comma or coordinating conjunction chain: e.g. "denies chest pain or fever"
                # If between_text contains only words, commas, "or", "and", "nor", negation applies!
                return AssertionType.ABSENT

        # Post-negation triggers (e.g. "chest pain was ruled out", "fever is absent")
        post_trigger = r"^\s*(?:is|was|were)?\s*(?:absent|negative|ruled\s+out|denied)\b"
        if re.search(post_trigger, post_context, re.IGNORECASE):
            return AssertionType.ABSENT

        return AssertionType.PRESENT

    @classmethod
    def evaluate_temporality(
        cls,
        sentence_text: str,
        entity_rel_span: Tuple[int, int],
    ) -> TemporalityType:
        """Detects whether entity is ACUTE, CHRONIC, or RESOLVED."""
        ent_start, ent_end = entity_rel_span
        context_window = sentence_text[max(0, ent_start - 30) : min(len(sentence_text), ent_end + 50)]

        for pattern in RESOLVED_PATTERNS:
            if re.search(pattern, context_window, re.IGNORECASE):
                return TemporalityType.RESOLVED

        for pattern in CHRONIC_DURATION_PATTERNS:
            if re.search(pattern, context_window, re.IGNORECASE) or re.search(pattern, sentence_text, re.IGNORECASE):
                return TemporalityType.CHRONIC

        return TemporalityType.ACUTE

    @classmethod
    def extract_entities(cls, text: str) -> list[ExtractedEntity]:
        """
        Extracts all recognized clinical entities from text with assertion,
        temporality, and exact source spans.
        """
        entities: list[ExtractedEntity] = []
        sentence_spans = cls.get_sentence_boundaries(text)

        # Sort known lexicon phrases by length descending to match longest phrases first
        # (e.g., "mild headache" before "headache", "shortness of breath" before "breath")
        sorted_phrases = sorted(SNOMED_LEXICON.keys(), key=len, reverse=True)

        matched_char_indices: set[int] = set()

        for phrase in sorted_phrases:
            pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                span = match.span()
                # Check for overlap with already matched longer phrases
                if any(idx in matched_char_indices for idx in range(span[0], span[1])):
                    continue

                # Mark indices as matched
                for idx in range(span[0], span[1]):
                    matched_char_indices.add(idx)

                matched_term = match.group(0)
                s_start, s_end = cls.find_enclosing_sentence(span[0], sentence_spans)
                sentence_text = text[s_start:s_end]
                rel_span = (span[0] - s_start, span[1] - s_start)

                assertion = cls.evaluate_assertion(span, sentence_text, rel_span)
                temporality = cls.evaluate_temporality(sentence_text, rel_span)
                snomed_info = SNOMED_LEXICON.get(phrase.lower(), {})
                snomed_code = snomed_info.get("snomed_code")

                entities.append(
                    ExtractedEntity(
                        term=matched_term,
                        snomed_code=snomed_code,
                        assertion=assertion,
                        temporality=temporality,
                        source_span=span,
                        confidence=0.98,
                    )
                )

        # Sort entities by source span start offset
        entities.sort(key=lambda e: e.source_span[0])
        return entities
