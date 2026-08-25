# Scripts Overview

This document explains every script in the repository and its role in the training/evaluation pipeline.

---

## Training Pipeline (scripts/train/)

### sentencepiece/generate_text_corpus.py

Downloads a HuggingFace dataset and dumps the text column into a plain `.txt` file. This text file is used as a training corpus for the SentencePiece tokenizer.

**Usage:**

```bash
python generate_text_corpus.py --hf-dataset <dataset_name> --text-col <column_name>
```

---

### sentencepiece/train.py

Trains a new SentencePiece tokenizer (unigram model by default) on a text corpus. Produces a `.model` and `.vocab` file with a configurable vocabulary size (default: 20,000 tokens).

**Usage:**

```bash
python train.py --input-file ./corpus/tamil_corpus.txt --vocab-size 20000
```

---

### sentencepiece/merge_tokenizer.py

Takes the original LLaMA tokenizer and merges in the new Tamil tokens from the SentencePiece model. Outputs a combined tokenizer that handles both English and Tamil efficiently. This is how the 16,000 additional Tamil tokens were added to LLaMA's vocabulary.

**Usage:**

```bash
python merge_tokenizer.py --llama_tokenizer_dir <path> --tamil_sp_model_file ./tamil_sp.model
```

---

### sentencepiece/test.py

Simple test script that encodes text using a SentencePiece model to verify it tokenizes correctly. Diagnostic/debugging tool only.

---

### pretrain/run_clm_with_peft.py

The core continual pretraining script. Loads a LLaMA model, applies LoRA adapters (PEFT), resizes embeddings for the new tokenizer, and trains on a Tamil text corpus using causal language modeling (next-token prediction).

Supports:

- 4-bit / 8-bit quantization (BitsAndBytes)
- Flash Attention 2
- DeepSpeed
- Gradient checkpointing

This is the most important script for teaching the model Tamil.

---

### pretrain/run_pt.sh

Shell script that launches pretraining with all hyperparameters configured:

- Learning rate: 2e-4
- LoRA rank: 64, alpha: 128
- Trainable modules: q_proj, v_proj, k_proj, o_proj, gate_proj, down_proj, up_proj
- Modules to save: embed_tokens, lm_head
- Block size: 512

Edit the paths at the top and run this to start pretraining.

---

### pretrain/flash_attn_patch.py

Monkey-patches LLaMA's attention mechanism with Flash Attention 2 for faster training and lower memory usage. Called automatically by `run_clm_with_peft.py` when `--flash_attn True` is set.

---

### finetune/finetune.py

Instruction fine-tunes the base model using SFTTrainer (from TRL) with LoRA/QLoRA. Loads the Tamil Alpaca/Orca dataset, trains for 2 epochs, merges the adapter back into the base model, and pushes directly to HuggingFace Hub.

Key hyperparameters:

- LoRA rank: 64, alpha: 128, dropout: 0.1
- Target modules: all attention + MLP projections
- Batch size: 8, gradient accumulation: 8
- Learning rate: 2e-4 with cosine schedule
- Max sequence length: 512

---

### finetune/make_shards.py

Takes a trained model and splits it into smaller shards (e.g., 2GB each) for easier distribution, then pushes to HuggingFace Hub.

**Usage:**

```bash
python make_shards.py --model_name ./model --save_model_name user/model-sharded --max_shard_size 2GB --push_to_hub --token <hf_token>
```

---

### finetune/run_finetuning.sh

Orchestrates the full finetuning pipeline: runs `finetune.py`, then `make_shards.py` to shard and upload.

---

### utils/merge_adapter.py

Merges a LoRA adapter back into the base model to produce a standalone model that doesn't require the adapter at inference time.

**Usage:**

```bash
python merge_adapter.py --base_model_path <base> --target_model_path <output> --adapter_path <adapter>
```

---

### utils/push_to_hub.py

Uploads a local model directory to HuggingFace Hub as a private repository.

**Usage:**

```bash
python push_to_hub.py --target_model_path ./model --repo_id user/model-name --hf_token <token>
```

---

## Evaluation (scripts/eval/)

### eval/chatgpt_preds.py

Generates GPT-3.5-turbo responses for evaluation instructions in Tamil. Creates a baseline to compare Tamima's outputs against. Uses LangChain with SQLite caching to avoid redundant API calls.

**Usage:**

```bash
python chatgpt_preds.py --instructions_csv_path ./preds/eval.csv --save_path ./preds/gpt_preds.csv
```

---

### eval/run_eval.py

Uses GPT-4 to score model outputs on a 1-10 scale. Reads a CSV of model predictions, asks GPT-4 to rate each response, and produces a scored CSV with score + reasoning.

**Usage:**

```bash
python run_eval.py --input-csv predictions.csv --output-csv scores.csv --model-output-field tamima
```

---

## Utilities (scripts/utils/)

### utils/count_indic_tokens.py

Counts how many tokens in a tokenizer belong to each Indic language (Tamil, Hindi, Telugu, Malayalam, Kannada, Bengali) based on Unicode ranges. Gives a high-level view of tokenizer composition.

**Usage:**

```bash
python count_indic_tokens.py rajacsp/tamima-7b-base-v0.1
```
