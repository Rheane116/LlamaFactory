# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important: Repository Identity

This codebase is located at `/data/wengxiaolong/zhouyuanyun/LlamaFactory/` — it is **zhouyuanyun's independent fork** of LlamaFactory, maintained separately from the other LlamaFactory instance at `/data/wengxiaolong/LlamaFactory/`. Do not confuse the two: they have diverged and changes in one do not apply to the other.

## Overview

This is a fork of LlamaFactory adapted for information extraction (IE) research. The primary extension is fine-tuning LLMs (Qwen2.5-7B-Instruct) for joint entity and relation extraction on datasets like SciERC, ACE2005, CoNLL04, and ADE.

## Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Train (SFT with LoRA)
llamafactory-cli train examples/train_lora/scierc_dfsjson_qwen2.5.yaml
# or via bash wrapper:
bash examples/train_lora/train_scierc_dfsjson.bash

# Inference / predict on test set
llamafactory-cli train examples/train_lora/infer_scierc_dfsjson_qwen2.5.yaml
bash examples/train_lora/infer_scierc_dfsjson.bash

# Format, lint, test (upstream)
make style && make quality
WANDB_DISABLED=true pytest -vv --import-mode=importlib tests/ tests_v1/
```

## Custom Modifications to Upstream LlamaFactory

All research-specific additions are in these files:

### New hparams (`src/llamafactory/hparams/finetuning_args.py`)
Added fields to `FinetuningArguments`:
- `compute_relation_f1` — enable entity+relation F1 evaluation
- `f1_format` — output format: `"json"`, `"dfsjson"`, `"dfs"`, or `"sel"`
- `use_asft_loss` / `asft_alpha` — adaptive SFT loss with a reference model
- `use_dft_loss`, `use_eaft_loss` / `eaft_alpha` — experimental loss variants
- `early_stopping_steps`, `disable_shuffling`

### F1 Metrics (`src/llamafactory/train/sft/metric.py`)
Custom metric classes for IE evaluation (all inherit `BaseF1Metric`):
- `JsonF1Metric` — flat JSON format `{"entities": {...}, "relations": [...]}`
- `DfsJsonF1Metric` — DFS-traversal JSON format
- `DfsF1Metric` — DFS string format
- `SelF1Metric` — selection-based format

These are selected in `workflow.py` based on `finetuning_args.f1_format` when `compute_relation_f1=true` and `predict_with_generate=true`.

### Workflow (`src/llamafactory/train/sft/workflow.py`)
Modified `run_sft()` to:
- Wire in the custom F1 metric classes above
- Support `use_asft_loss` with a reference model (`create_ref_model`)
- Write debug logs to `/data/wengxiaolong/zhouyuanyun/LlamaFactory/tmp/`

### Format Parsers (`src/llamafactory/train/sft/format_parser.py`)
Standalone parsers (`JsonParser`, etc.) that decode model output strings into entity/relation dicts for F1 computation.

### Trainer (`src/llamafactory/train/sft/trainer.py`)
`CustomSeq2SeqTrainer` extends HuggingFace `Seq2SeqTrainer`. Handles custom loss variants and generation-based evaluation.

## Data Pipeline

### Datasets (`data/dataset_info.json`)
Registered datasets point to absolute paths under `data/scierc/`. Three formats per split:
- `scierc_json_{train,dev,test}` — flat JSON IE format
- `scierc_dfsjson_{train,dev,test}` — DFS-traversal JSON format
- `scierc_dfs_{train,dev,test}` — DFS string format

### Data Preprocessing (`dataprocess/`)
Scripts to convert raw IE datasets to LlamaFactory-compatible formats:
- `build_graph.py <dataset> <split>` — converts raw JSONL (span-indexed) to graph format with entity names
- `graph_dfsjson.py`, `graph_dfs_raw.py`, `graph_sel_raw.py` — generate training examples in each format
- `doc2sent.py` — document-to-sentence segmentation
- `schema_map.py` — dataset-specific relation/entity type mappings

Raw data lives in `data_raw/{ACE2005,SciERC,CoNLL04,ADE}/`.

## Training Config Structure

YAML configs in `examples/train_lora/` follow this pattern:
```yaml
model_name_or_path: /data/wengxiaolong/huggingface/Qwen2.5-7B-Instruct
stage: sft
finetuning_type: lora
dataset: scierc_dfsjson_train
template: qwen
predict_with_generate: true
compute_relation_f1: true
f1_format: dfsjson          # selects the metric class
metric_for_best_model: eval_scierc_dfsjson_dev_rel_f1
```

For inference-only configs: set `do_train: false`, `do_predict: true`, and point `adapter_name_or_path` to a checkpoint.

## Model & Checkpoint Paths

- Base model: `/data/wengxiaolong/huggingface/Qwen2.5-7B-Instruct`
- LoRA checkpoints: `saves/Qwen2.5-7B/lora/sft-scierc-{json,dfsjson}/`
- Best checkpoint selection uses `load_best_model_at_end: true` with `metric_for_best_model`
