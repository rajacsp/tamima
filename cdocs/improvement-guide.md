# How to Improve Tamima on HuggingFace

This document maps goals to the specific scripts and steps needed.

---

## Quick Reference

| Goal | Scripts | Impact |
|------|---------|--------|
| Better Tamil understanding | `run_clm_with_peft.py` + `run_pt.sh` | High |
| Better instruction following | `finetune.py` + `run_finetuning.sh` | High |
| Better tokenizer | `generate_text_corpus.py` → `train.py` → `merge_tokenizer.py` | Medium |
| Publish to HF | `merge_adapter.py` → `push_to_hub.py` or `make_shards.py` | Required |
| Measure improvement | `chatgpt_preds.py` + `run_eval.py` | Diagnostic |

---

## Path 1: Better Tamil Understanding (Continual Pretraining)

**Goal:** Teach the model more Tamil by training on a larger/better corpus.

**Steps:**
1. Gather more Tamil text data (Wikipedia, news, books, web scrapes)
2. Format it as plain text files in a directory
3. Edit `run_pt.sh` — set your paths and hyperparameters
4. Run pretraining:
   ```bash
   bash scripts/train/pretrain/run_pt.sh
   ```
5. Merge the adapter:
   ```bash
   python scripts/train/utils/merge_adapter.py \
     --base_model_path <original_model> \
     --target_model_path ./merged_model \
     --adapter_path <output_dir>/pt_lora_model
   ```
6. Push to HF:
   ```bash
   python scripts/train/utils/push_to_hub.py \
     --target_model_path ./merged_model \
     --repo_id rajacsp/tamima-7b-base-v0.2 \
     --hf_token <token>
   ```

**What matters most:** Quality and diversity of Tamil training data.

---

## Path 2: Better Instruction Following (Fine-tuning)

**Goal:** Make the model respond better to user instructions in Tamil.

**Steps:**
1. Prepare a high-quality instruction dataset (Tamil Alpaca format with instruction/input/output fields)
2. Upload it to HuggingFace Datasets or reference it locally
3. Edit `finetune.py` — update `dataset_name`, `model_name`, and `new_model`
4. Run fine-tuning:
   ```bash
   bash scripts/train/finetune/run_finetuning.sh
   ```
   This trains, merges, shards, and pushes automatically.

**What matters most:** Quality of instruction-response pairs. More diverse, accurate Tamil instructions = better instruct model.

---

## Path 3: Better Tokenizer

**Goal:** Improve how efficiently the model encodes Tamil text (fewer tokens per sentence = faster inference, longer effective context).

**Steps:**
1. Generate a large Tamil corpus:
   ```bash
   python scripts/train/sentencepiece/generate_text_corpus.py \
     --hf-dataset <dataset> --text-col text
   ```
2. Train a new SentencePiece model:
   ```bash
   python scripts/train/sentencepiece/train.py \
     --input-file ./corpus/tamil_corpus.txt --vocab-size 24000
   ```
3. Merge with LLaMA tokenizer:
   ```bash
   python scripts/train/sentencepiece/merge_tokenizer.py \
     --llama_tokenizer_dir <llama_tokenizer> \
     --tamil_sp_model_file ./models/tamil_sp.model
   ```
4. After merging the tokenizer, you MUST retrain the model (Path 1) because the embedding layer size changes.

**When to do this:** Only if the current tokenizer (47,957 vocab) is insufficient. Changing the tokenizer requires full retraining.

---

## Path 4: Evaluate Improvements

**Goal:** Measure whether your changes made the model better.

**Steps:**
1. Generate baseline predictions from GPT-3.5:
   ```bash
   python scripts/eval/chatgpt_preds.py --instructions_csv_path eval_set.csv
   ```
2. Generate predictions from your model (manual or via a separate script)
3. Score all outputs with GPT-4:
   ```bash
   python scripts/eval/run_eval.py --input-csv all_preds.csv --model-output-field tamima
   ```
4. Compare scores between versions.

---

## Hardware Requirements

| Task | Minimum GPU | Recommended |
|------|-------------|-------------|
| Pretraining (7B, LoRA) | 1x A100 40GB | 1x A100 80GB |
| Fine-tuning (7B, LoRA) | 1x A100 40GB | 1x A100 80GB |
| Pretraining (13B, LoRA) | 1x A100 80GB | 2x A100 80GB |
| Inference (7B, FP16) | 1x GPU with 16GB+ VRAM | — |

Using 4-bit quantization during training reduces VRAM requirements significantly but may slightly impact quality.

---

## Key Hyperparameters to Tune

| Parameter | Current Value | Notes |
|-----------|---------------|-------|
| LoRA rank | 64 | Higher = more capacity but slower |
| LoRA alpha | 128 | Usually 2x rank |
| Learning rate | 2e-4 | Lower for larger models |
| Epochs (pretrain) | 1-3 | More data = fewer epochs needed |
| Epochs (finetune) | 2-5 | Watch for overfitting |
| Block size | 512 | Increase if you have the VRAM |
| Batch size | 8-64 | Limited by VRAM |
