import os
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "600"

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "rajacsp/tamima-7b-base-v0.1"

tok = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    dtype=torch.float16,
    offload_folder="offload",
)

# Model stats
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
model_size_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 ** 2)

print(f"Model: {model_name}")
print(f"Vocab size: {tok.vocab_size:,}")
print(f"Total parameters: {total_params:,}")
print(f"Trainable parameters: {trainable_params:,}")
print(f"Model size (approx): {model_size_mb:,.2f} MB")
print(f"Dtype: {next(model.parameters()).dtype}")
print(f"Layers: {model.config.num_hidden_layers}")
print(f"Hidden size: {model.config.hidden_size}")
print(f"Attention heads: {model.config.num_attention_heads}")
print(f"Max sequence length: {model.config.max_position_embeddings}")
