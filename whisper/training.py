import os
import torch
import gc
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
torch.backends.cuda.matmul.allow_tf32 = True

def clear_gpu_memory():
    gc.collect()
    torch.cuda.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
clear_gpu_memory()

# ============= Set hyperparameters here =============

LANGUAGE = "english"
WHISPER = "medium"
MODEL_NAME = f"openai/whisper-{WHISPER}"
OUTPUT_DIR = f"./whisper-{WHISPER}-DINA"
RANDOM_STATE = 42
EPOCHS = 10
LR = 5e-5

import pandas as pd
from sklearn.model_selection import train_test_split

# ============= Format the data for HuggingFace =============

# Import and create split
final_df = pd.read_csv('../input/finetuning_data/cv_enes_df.csv')
train_df, test_df = train_test_split(final_df, test_size=0.3, random_state=RANDOM_STATE)
train_df = train_df[['path', 'sentence']]
test_df  = test_df[['path', 'sentence']]

# Load snippets validation dataset — rename columns to match
snippets_df = pd.read_csv('../input/finetuning_data/snippets/data.csv')
snippets_df = snippets_df[['full_path', 'text']].rename(columns={'full_path': 'path', 'text': 'sentence'})

from datasets import Dataset, DatasetDict, Audio

train_hf    = Dataset.from_pandas(train_df,    preserve_index=False)
test_hf     = Dataset.from_pandas(test_df,     preserve_index=False)
snippets_hf = Dataset.from_pandas(snippets_df, preserve_index=False)
dataset_dictionary = DatasetDict({
    "train":    train_hf,
    "test":     test_hf,
    "snippets": snippets_hf,
})

# ============= Format the data for Whisper =============

from transformers import WhisperFeatureExtractor, WhisperTokenizer
feature_extractor = WhisperFeatureExtractor.from_pretrained(MODEL_NAME)
tokenizer = WhisperTokenizer.from_pretrained(MODEL_NAME, language=LANGUAGE, task="transcribe")

from tqdm import tqdm
import numpy as np
import torchaudio
from datasets import Dataset

target_sr = 16000
MAX_LABEL_LENGTH = 448  # Whisper decoder hard limit

def row_generator(hf_dataset):
    skipped = 0
    for row in hf_dataset:  # iterate directly, no len() needed
        labels = tokenizer(row["sentence"]).input_ids
        if len(labels) > MAX_LABEL_LENGTH:
            skipped += 1
            if skipped % 10 == 1:
                print(f"[Filter] Skipped {skipped} sample(s) with labels > {MAX_LABEL_LENGTH} tokens (latest: {len(labels)} tokens)")
            continue
        wf, sr = torchaudio.load(row['path'])
        if sr != target_sr:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
            wf = resampler(wf)
            sr = target_sr
        wf = wf.flatten().numpy()
        features = feature_extractor(wf, sampling_rate=sr).input_features[0]
        features = features.astype("float64")
        yield {
            "input_features": features,
            "labels": labels
        }

from datasets import IterableDataset, IterableDatasetDict
train_processed    = IterableDataset.from_generator(lambda: row_generator(train_hf))
test_processed     = IterableDataset.from_generator(lambda: row_generator(test_hf))
snippets_processed = IterableDataset.from_generator(lambda: row_generator(snippets_hf))

dataset_dictionary = IterableDatasetDict({
    "train":    train_processed,
    "test":     test_processed,
    "snippets": snippets_processed,
})

# ============= Load model & get ready for training =============

from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch
processor = WhisperProcessor.from_pretrained(MODEL_NAME, language=LANGUAGE, task="transcribe")
model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
print("Device:", str(device))

model.generation_config.language = LANGUAGE.lower()
model.generation_config.task = "transcribe"
model.generation_config.forced_decoder_ids = None
from transformers.models.whisper.tokenization_whisper import LANGUAGES, TO_LANGUAGE_CODE
language_code = TO_LANGUAGE_CODE[LANGUAGE.lower()]
token = f"<|{language_code}|>"
token_id = processor.tokenizer.convert_tokens_to_ids(token)
model.generation_config.lang_to_id[token] = token_id

import torch
from dataclasses import dataclass
from typing import Any, Dict, List, Union
@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: Any
    decoder_start_token_id: int
    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        input_features = [{"input_features": feature["input_features"]} for feature in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
        label_features = [{"input_ids": feature["labels"]} for feature in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]
        batch["labels"] = labels
        return batch
data_collator = DataCollatorSpeechSeq2SeqWithPadding(
    processor=processor,
    decoder_start_token_id=model.config.decoder_start_token_id,
)

import re
import evaluate
from unicodedata import normalize as unicode_normalize

wer_metric = evaluate.load("wer")
cer_metric = evaluate.load("cer")

def normalize_text(text: str) -> str:
    text = text.lower()
    text = unicode_normalize("NFKC", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = text.replace("_", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def compute_metrics(pred):
    pred_ids  = pred.predictions
    label_ids = pred.label_ids
    label_ids[label_ids == -100] = tokenizer.pad_token_id
    pred_str  = [normalize_text(s) for s in tokenizer.batch_decode(pred_ids,  skip_special_tokens=True)]
    label_str = [normalize_text(s) for s in tokenizer.batch_decode(label_ids, skip_special_tokens=True)]
    wer = 100 * wer_metric.compute(predictions=pred_str, references=label_str)
    cer = 100 * cer_metric.compute(predictions=pred_str, references=label_str)
    return {"wer": wer, "cer": cer}

from peft import LoraConfig, get_peft_model
config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1,
    bias="none",
)
model = get_peft_model(model, config)
for name, param in model.named_parameters():
    if "encoder" in name:
        param.requires_grad_(False)

trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total     = sum(p.numel() for p in model.parameters())
print(f"Trainable: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")

# ============= Callbacks =============

import csv
from transformers import TrainerCallback, TrainerControl, TrainerState, TrainingArguments
from torch.utils.data import DataLoader


class CSVLoggerCallback(TrainerCallback):
    """Merges test-set and snippets eval metrics into a single logs.csv file."""

    def __init__(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        self.log_file = os.path.join(output_dir, "logs.csv")
        self.pending_row = {}
        self.fieldnames = ["epoch", "step", "test_wer", "test_cer", "snippets_wer", "snippets_cer"]
        # Write header only if starting fresh (not resuming)
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

    def _flush_row(self):
        """Write the buffered row to CSV if it has at least one metric."""
        if self.pending_row and any(k in self.pending_row for k in ["test_wer", "snippets_wer"]):
            with open(self.log_file, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames, extrasaction="ignore")
                writer.writerow(self.pending_row)
            self.pending_row = {}

    def on_evaluate(self, args, state: TrainerState, control: TrainerControl, metrics=None, **kwargs):
        """Fires after the test-set evaluation — buffer wer/cer from metrics dict."""
        self._flush_row()  # flush any leftover row from a previous eval
        self.pending_row = {
            "epoch": round(state.epoch, 2) if state.epoch else "",
            "step":  state.global_step,
            "test_wer": metrics.get("eval_wer", "") if metrics else "",
            "test_cer": metrics.get("eval_cer", "") if metrics else "",
        }

    def on_snippets_eval(self, step, epoch, wer, cer):
        """Called directly from SnippetsEvalCallback to inject snippets metrics."""
        self.pending_row.update({
            "snippets_wer": wer,
            "snippets_cer": cer,
        })
        self._flush_row()


class SnippetsEvalCallback(TrainerCallback):
    """Evaluates on the snippets dataset at the end of every epoch and logs wer/cer."""
    def __init__(self, snippets_dataset, data_collator, tokenizer, processor, model, device, csv_logger=None):
        self.snippets_dataset = snippets_dataset
        self.data_collator    = data_collator
        self.tokenizer        = tokenizer
        self.processor        = processor
        self.model            = model
        self.device           = device
        self.csv_logger       = csv_logger  # optional reference to CSVLoggerCallback

    def on_evaluate(self, args, state: TrainerState, control: TrainerControl, **kwargs):
        dataloader = DataLoader(
            self.snippets_dataset,
            batch_size=args.per_device_eval_batch_size,
            collate_fn=self.data_collator,
        )
        self.model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for batch in dataloader:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                generated = self.model.generate(
                    input_features=batch["input_features"],
                    max_new_tokens=128,
                )
                labels = batch["labels"].clone()
                labels[labels == -100] = self.tokenizer.pad_token_id
                pred_str  = [normalize_text(s) for s in self.tokenizer.batch_decode(generated, skip_special_tokens=True)]
                label_str = [normalize_text(s) for s in self.tokenizer.batch_decode(labels,    skip_special_tokens=True)]
                all_preds.extend(pred_str)
                all_labels.extend(label_str)

        wer = 100 * wer_metric.compute(predictions=all_preds, references=all_labels)
        cer = 100 * cer_metric.compute(predictions=all_preds, references=all_labels)
        print(f"\n[Snippets] Epoch {state.epoch:.0f} — WER: {wer:.2f}  CER: {cer:.2f}")
        # Also write into trainer logs so TensorBoard picks them up
        state.log_history.append({
            "epoch": state.epoch,
            "snippets_wer": wer,
            "snippets_cer": cer,
        })
        # Notify CSV logger so it can complete and flush the row
        if self.csv_logger is not None:
            self.csv_logger.on_snippets_eval(state.global_step, state.epoch, wer, cer)

        return control


# Instantiate loggers — wire csv_logger into snippets_callback
csv_logger = CSVLoggerCallback(output_dir=OUTPUT_DIR)

snippets_callback = SnippetsEvalCallback(
    snippets_dataset = dataset_dictionary["snippets"],
    data_collator    = data_collator,
    tokenizer        = tokenizer,
    processor        = processor,
    model            = model,
    device           = device,
    csv_logger       = csv_logger,
)

# ============= Training arguments (epoch-based) =============

from transformers import Seq2SeqTrainingArguments
PER_DEVICE_BATCH = 4
GRAD_ACCUM = 4
steps_per_epoch = len(train_df) // (PER_DEVICE_BATCH * GRAD_ACCUM)
max_steps = EPOCHS * steps_per_epoch

training_args = Seq2SeqTrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=PER_DEVICE_BATCH,
    gradient_accumulation_steps=GRAD_ACCUM,
    learning_rate=LR,
    warmup_steps=500,
    num_train_epochs=EPOCHS,
    max_steps=max_steps,                   # required for IterableDataset
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
    fp16=False,
    bf16=True,
    eval_strategy="steps",                 # epoch-based eval not supported on IterableDataset
    eval_steps=steps_per_epoch,            # evaluates once per "epoch"
    per_device_eval_batch_size=4,
    predict_with_generate=True,
    generation_max_length=128,
    save_strategy="steps",
    save_steps=steps_per_epoch,
    logging_steps=25,
    report_to=["tensorboard"],
    load_best_model_at_end=True,
    metric_for_best_model="wer",
    greater_is_better=False,
    push_to_hub=True,
)

from transformers import Seq2SeqTrainer, EarlyStoppingCallback
trainer = Seq2SeqTrainer(
    args=training_args,
    model=model,
    train_dataset=dataset_dictionary["train"],
    eval_dataset=dataset_dictionary["test"],   # primary eval = test set
    data_collator=data_collator,
    compute_metrics=compute_metrics,
    processing_class=processor.feature_extractor,
    callbacks=[
        EarlyStoppingCallback(early_stopping_patience=3),
        snippets_callback,   # snippets eval runs after each epoch
        csv_logger,          # CSV logger merges both sets of metrics
    ]
)

# ============= Train =============

torch.cuda.empty_cache()
trainer.train(resume_from_checkpoint=True)

# ============= Push =============

kwargs = {
    "dataset_tags": "private",
    "dataset": "private",
    "dataset_args": "config: english, split: test",
    "language": "en",
    "model_name": f"Whisper {WHISPER.capitalize()} English & Spanish - Chengyi Li",
    "finetuned_from": MODEL_NAME,
    "tasks": "automatic-speech-recognition",
}
trainer.push_to_hub(**kwargs)
processor.push_to_hub(f"chengyili2005/whisper-{WHISPER}-DINA")
clear_gpu_memory()