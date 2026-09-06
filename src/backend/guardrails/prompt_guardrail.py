import logging
from ..models.guardrail_model import GuardrailRequest, GuardrailResponse
import re

class PromptGuardrail:
    def __init__(self):
        self._maximum_length = 1000
        self._override_patterns = [
            re.compile(r"ignore\s+(?:all\s+|previous\s+|prior\s+)?(?:instructions?|directives?|rules?|constraints?|prompts?)", re.IGNORECASE),
            re.compile(r"disregard\s+(?:all\s+|previous\s+|prior\s+)?(?:instructions?|directives?|rules?|constraints?|prompts?)", re.IGNORECASE),
            re.compile(r"override\s+(?:all\s+|previous\s+|prior\s+)?(?:instructions?|directives?|rules?|constraints?|prompts?)", re.IGNORECASE),
            re.compile(r"instead\s+of\s+the\s+(?:above|previous|original)\s+instructions?", re.IGNORECASE),
            re.compile(r"forget\s+(?:everything|what\s+you\s+were\s+told|your\s+instructions?|previous\s+instructions?)", re.IGNORECASE),
            re.compile(r"you\s+must\s+now\s+(?:ignore|disregard|override)", re.IGNORECASE)
        ]

        self._extraction_patterns = [
            re.compile(r"(?:reveal|show|print|output|display|expose|tell\s+me|explain)\s+(?:your\s+|the\s+|our\s+)?(?:system\s+)?(?:prompt|instruction|rule|developer|configuration|directive|setup)", re.IGNORECASE),
            re.compile(r"what\s+is\s+your\s+(?:system\s+)?(?:prompt|instruction|directive|setup|configuration)", re.IGNORECASE),
            re.compile(r"how\s+are\s+you\s+(?:configured|set\s+up)", re.IGNORECASE),
            re.compile(r"repeat\s+the\s+(?:above|preceding|initial)\s+(?:text|prompt|instructions?|rules?)", re.IGNORECASE),
            re.compile(r"what\s+did\s+the\s+(?:user|system|developer)\s+ask\s+you\s+to\s+do", re.IGNORECASE)
        ]

        self._role_patterns = [
            re.compile(r"(?:you\s+are\s+now|pretend\s+to\s+be|act\s+as|assume\s+the\s+persona\s+of|play\s+the\s+role\s+of|simulate|impersonate|you\s+must\s+now\s+become)\s+(?:a|an)\s+(?:unrestricted|unfiltered|jailbroken|uncensored|unbound|malicious|evil)", re.IGNORECASE),
            re.compile(r"you\s+are\s+no\s+longer\s+(?:a|an)", re.IGNORECASE),
            re.compile(r"ignore\s+your\s+roles?", re.IGNORECASE),
            re.compile(r"instead\s+of\s+being\s+(?:a|an)", re.IGNORECASE)
        ]

        self._jailbreak_patterns = [
            re.compile(r"(?:dan|do\s+anything\s+now)\s+mode", re.IGNORECASE),
            re.compile(r"bypass\s+(?:security|filters?|guardrails?|restrictions?|safety)", re.IGNORECASE),
            re.compile(r"unfiltered\s+response", re.IGNORECASE),
            re.compile(r"without\s+(?:any\s+)?(?:restrictions?|limitations?|safety|filters?|bounds?|guardrails?|rules?)", re.IGNORECASE),
            re.compile(r"jailbreak", re.IGNORECASE),
            re.compile(r"hypothetical\s+scenario\s+where\s+you\s+can", re.IGNORECASE),
            re.compile(r"you\s+are\s+unbound", re.IGNORECASE),
            re.compile(r"ignore\s+all\s+safety\s+rules?", re.IGNORECASE)
        ]

        self._boundary_patterns = [
            re.compile(r"</?(?:system|instructions?|user|assistant|developer)>", re.IGNORECASE),
            re.compile(r"\[/?(?:system|instructions?|user|assistant|developer)\]", re.IGNORECASE),
            re.compile(r"^(?:system|assistant|user|developer)\s*:", re.IGNORECASE | re.MULTILINE),
            re.compile(r"(?:---|\*\*\*|===)\s*(?:system|assistant|user|developer|instructions?|end|start)\s*(?:---|\*\*\*|===)", re.IGNORECASE)
        ]

        self._obfuscation_patterns = [
            re.compile(r"(?:base64|b64|decode|encode|rot13|caesar\s+cipher|hex|hexadecimal|binary|reverse\s+the\s+text)\s+(?:the\s+following|this|text|string|message)", re.IGNORECASE),
            re.compile(r"\\u[0-9a-fA-F]{4}", re.IGNORECASE),
            re.compile(r"\\x[0-9a-fA-F]{2}", re.IGNORECASE),
            re.compile(r"(?:[A-Za-z0-9+/]{4}){8,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?")
        ]

    def validate(self, request: GuardrailRequest) -> GuardrailResponse:
        logging.info(f"[INFO][prompt_guardrail.py][validate] Validate prompt safety")
        try:
            if len(request.input) > self._maximum_length:
                return GuardrailResponse(
                    is_safe = False,
                    error = "Maximum prompt length exceeded."
                )

            for pattern in self._override_patterns:
                if pattern.search(request.input):
                    return GuardrailResponse(
                        is_safe = False,
                        error = "Direct Instruction Override detected."
                    )

            for pattern in self._extraction_patterns:
                if pattern.search(request.input):
                    return GuardrailResponse(
                        is_safe = False,
                        error = "System Prompt Extraction detected."
                    )

            for pattern in self._role_patterns:
                if pattern.search(request.input):
                    return GuardrailResponse(
                        is_safe = False,
                        error = "Role Manipulation detected."
                    )

            for pattern in self._jailbreak_patterns:
                if pattern.search(request.input):
                    return GuardrailResponse(
                        is_safe = False,
                        error = "Jailbreak detected."
                    )

            for pattern in self._boundary_patterns:
                if pattern.search(request.input):
                    return GuardrailResponse(
                        is_safe = False,
                        error = "Delimiter/Instruction Boundary Manipulation detected."
                    )

            for pattern in self._obfuscation_patterns:
                if pattern.search(request.input):
                    return GuardrailResponse(
                        is_safe = False,
                        error = "Obfuscation Pattern detected."
                    )

            return GuardrailResponse(
                is_safe = True
            )

        except Exception as e:
            logging.error(f"[INFO][prompt_guardrail.py][validate] Error in validating prompt safety: {e}")
            return GuardrailResponse(
                is_safe = False,
                error = "System error"
            )