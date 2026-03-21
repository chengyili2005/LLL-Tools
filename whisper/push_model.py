# Temporary script to push a saved model.

import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from peft import PeftModel

# ============= Config =============
WHISPER = "medium"
MODEL_NAME = f"openai/whisper-{WHISPER}"
CHECKPOINT_DIR = "./whisper-medium-DINA/checkpoint-41148"
HUB_REPO = f"chengyili2005/whisper-{WHISPER}-DINA"

# ============= Load base + adapter =============
base_model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
model = PeftModel.from_pretrained(base_model, CHECKPOINT_DIR)
processor = WhisperProcessor.from_pretrained(MODEL_NAME, language="english", task="transcribe")

# ============= Push =============
model.push_to_hub(HUB_REPO)
processor.push_to_hub(HUB_REPO)

print("Done!")