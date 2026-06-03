from __future__ import annotations

import threading
from typing import Any

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from resume_parser.core.logging import get_logger
from resume_parser.core.exceptions import ModelInferenceError
from resume_parser.core.config import Settings


class ModelLoader:
    _instance: "ModelLoader" | None = None
    _lock = threading.Lock()

    def __init__(self, settings: Settings) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.settings = settings
        self.model, self.tokenizer = self._load_model()

    @classmethod
    def get_instance(cls, settings: Settings) -> "ModelLoader":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ModelLoader(settings)
        return cls._instance

    def _load_model(self) -> tuple[Any, Any]:
        model_name = self.settings.MODEL_NAME
        device = self._get_device()
        self.logger.info(
            "Loading transformer model.",
            extra={"event": "model_loader.load_start", "device": str(device), "model_name": model_name},
        )
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            if device.type != "cpu":
                model = model.to(device)
            else:
                model = torch.quantization.quantize_dynamic(
                    model, {torch.nn.Linear}, dtype=torch.qint8
                )
            self.logger.info(
                "Model loaded successfully.",
                extra={"event": "model_loader.load_success", "device": str(device), "model_name": model_name},
            )
            return model, tokenizer
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Failed to load model.", extra={"event": "model_loader.load_failure"})
            fallback = "google/flan-t5-base"
            if fallback != model_name:
                try:
                    tokenizer = AutoTokenizer.from_pretrained(fallback, use_fast=True)
                    model = AutoModelForSeq2SeqLM.from_pretrained(fallback)
                    if device.type != "cpu":
                        model = model.to(device)
                    else:
                        model = torch.quantization.quantize_dynamic(
                            model, {torch.nn.Linear}, dtype=torch.qint8
                        )
                    self.logger.info(
                        "Fallback model loaded successfully.",
                        extra={"event": "model_loader.fallback_success", "device": str(device), "model_name": fallback},
                    )
                    return model, tokenizer
                except Exception as fallback_exc:  # noqa: BLE001
                    self.logger.exception(
                        "Fallback model failed to load.",
                        extra={"event": "model_loader.fallback_failure"},
                    )
                    raise ModelInferenceError("Unable to load any model") from fallback_exc
            raise ModelInferenceError("Unable to load model") from exc

    @staticmethod
    def _get_device() -> torch.device:
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
