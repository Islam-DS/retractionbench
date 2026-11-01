# Reproduced paper numbers (retraction_bench.reproduce / `retraction-bench evaluate`)

## M1 by condition
- `no_retrieval`: n=252, rate=0.000, CI=[0.000, 0.000]
- `retrieval_naive`: n=213, rate=0.920, CI=[0.833, 0.991]
- `retrieval_with_notice`: n=209, rate=0.794, CI=[0.675, 0.899]
- `post_notice`: n=212, rate=0.000, CI=[0.000, 0.000]

## M1 paired test (retrieval_with_notice - retrieval_naive)
| Model | Mean diff | 95% CI | Raw p | Holm p |
|---|---|---|---|---|
| `llama3.1:8b-instruct-q4_K_M` | +0.000 | [+0.000, +0.000] | 1.0000 | 1.0000 |
| `openai/gpt-oss-120b` | -0.097 | [-0.236, +0.028] | 0.1887 | 0.3774 |
| `qwen2.5:7b-instruct-q4_K_M` | -0.306 | [-0.500, -0.111] | 0.0067 | 0.0201 |

## Seed agreement
- `llama3.1:8b-instruct-q4_K_M`: 97/97 groups fully agree across seeds
- `openai/gpt-oss-120b`: 94/99 groups fully agree across seeds
- `qwen2.5:7b-instruct-q4_K_M`: 99/100 groups fully agree across seeds

## M3 overall
- `acknowledges`: 0.560 [0.374, 0.736]
- `silently_revises`: 0.187 [0.100, 0.285]
- `defends`: 0.253 [0.131, 0.382]

## Correctness overall
- `correct`: 0.400 [0.232, 0.560]
- `incorrect`: 0.470 [0.320, 0.636]
- `refused`: 0.130 [0.061, 0.210]
