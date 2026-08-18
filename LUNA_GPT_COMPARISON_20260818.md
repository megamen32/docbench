# Luna / GPT-5.4 mini comparison

Цены посчитаны в RUB по зафиксированному [pricing snapshot](docbench/pricing_snapshot.json), а не по свежему запросу к каталогу.

## Reasoning — отдельно

- `omniroute-cx-gpt-5.6-luna-low`: `reason=matters`
- `omniroute-cx-gpt-5.6-luna-medium`: `reason=matters`
- `omniroute-cx-gpt-5.6-luna-high`: `reason=matters`
- `omniroute-routerai-gpt-5.4-mini`: `reason=matters`

## Tokens and cost

| model | benchmark | input tokens | output tokens | total tokens | cache read | cache write | reasoning tokens | cost, RUB |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| luna-low | conformance | 13247 | 12805 | 26052 | 0 | 0 | not returned | 0.971904 |
| luna-low | rule-extraction | 1160 | 1632 | 2792 | 0 | 0 | not returned | 0.118169 |
| luna-medium | conformance | 13247 | 14355 | 27602 | 0 | 0 | not returned | 1.072248 |
| luna-medium | rule-extraction | 1160 | 1689 | 2849 | 0 | 0 | not returned | 0.121859 |
| luna-high | conformance | 13247 | 20011 | 33258 | 0 | 0 | not returned | 1.438407 |
| luna-high | rule-extraction | 1160 | 3822 | 4982 | 0 | 0 | not returned | 0.259945 |
| gpt-5.4-mini | conformance | 13247 | 22331 | 35578 | 0 | 0 | not returned | 11.914500 |
| gpt-5.4-mini | rule-extraction | 1160 | 3075 | 4235 | 0 | 0 | not returned | 1.586895 |

В этих сохранённых прогонах провайдер не вернул отдельных cache/reasoning token fields, поэтому `cache read=0`, `cache write=0`, а `reasoning tokens=not returned` — это не предположение о нуле. Новый runner сохраняет и агрегирует эти поля, если endpoint их отдаёт; cache-токены учитываются отдельно и не начисляются дважды.

Исходные результаты: `var/runs/luna-*-20260818/results.json` и `var/runs/gpt-5.4-mini-*-20260818/results.json`.
