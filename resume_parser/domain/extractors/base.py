from __future__ import annotations

import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Any

import torch
from transformers import PreTrainedModel, PreTrainedTokenizerBase

from resume_parser.core.exceptions import ModelInferenceError


class BaseExtractor(ABC):
    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizerBase,
        config: object,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def extract(self, text: str) -> tuple[Any, float]:
        pass

    def _run_inference(self, prompt: str) -> str:
        try:
            start_time = time.perf_counter()
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024,
            )
            device = next(self.model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.inference_mode():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False,
                )
            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.debug(
                "Inference completed.",
                extra={"event": "model.inference", "duration_ms": duration_ms},
            )
            return result
        except Exception as exc:  # noqa: BLE001
            raise ModelInferenceError("Model inference failed") from exc

    def _compute_confidence(self, result: Any, required_pattern: str | None = None) -> float:
        confidence = 0.0
        if result:
            confidence = 0.7
            text = result if isinstance(result, str) else str(result)
            if required_pattern and re.search(required_pattern, text, re.IGNORECASE):
                confidence += 0.2
            if text.strip():
                confidence += 0.1
        return min(1.0, confidence)
