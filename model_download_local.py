

from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("/Users/csp/kact/tamima-7b-base-v0.1")
print("loaded ok")