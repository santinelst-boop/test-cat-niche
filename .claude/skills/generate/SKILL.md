---
name: generate
description: Generate images and short videos (e.g. cat breed photos, hero images, social ads) through pay-as-you-go model aggregators — kie.ai, fal.ai, WaveSpeed — instead of a Higgsfield-style subscription. Routes to the cheapest provider with a key, falls back on failure, enforces a $ budget, downloads outputs locally and logs every prompt. Use when the user types /generate or asks to create/edit images or image-to-video.
---

# /generate

All work goes through one script (no dependencies, Node 18+):

```
node .claude/skills/generate/scripts/generate.mjs --list                      # models, providers, prices, which keys are set
node .claude/skills/generate/scripts/generate.mjs --model <key> --prompt "..." [options]
node .claude/skills/generate/scripts/generate.mjs --spent [--session <name>]  # estimated spend from the log
```

Options: `--provider auto|kie|fal|wavespeed` (default auto = cheapest with a key), `--ref <path-or-url>` (repeatable; switches to the model's edit endpoint), `--aspect 1:1|16:9|9:16|4:5|3:2`, `--resolution 1K|2K|4K`, `--duration 5`, `--count N`, `--param key=value` (raw provider field, JSON-parsed), `--budget <usd>`, `--session <name>`, `--name <slug>`, `--out <dir>` (default `generations/`), `--dry-run`, `--prompt-file <file>`.

## Hard rules

1. **Quote before you spend.** For anything beyond a single image, run with `--dry-run` first and tell the user the model, provider and estimated total. Ask before going over $1 unless the user already set a budget.
2. **Always pass `--budget` and `--session`** when the user gives a budget ("max $3"). The script refuses jobs that would exceed it, counting everything already logged under that session.
3. **Never loop on failures.** The script already falls back kie → fal → wavespeed. If all fail, report the errors; don't retry blindly (a retry may bill twice).
4. Never print or commit API keys. Keys live in `.env.local` (gitignored): `KIE_API_KEY`, `FAL_KEY`, `WAVESPEED_API_KEY`. If none are set, tell the user which to add.
5. Prices in `models.json` are estimates and entries marked `verify: true` were not checked against live docs. If a provider answers "model not found" / 4xx validation, look up the current id on the provider's model page and fix `models.json` rather than guessing again.

## Workflow

1. **Route.** Pick the model for the job (see below), run `--list` to see which providers have keys.
2. **References & prompts.** Read any reference images the user gave (look at them) and write one distinct, specific prompt per output: subject, composition, lighting, lens/style, palette, text to render (exact words in quotes), aspect. When the user wants variety, make each prompt genuinely different, not paraphrases. If the user wants to review prompts first, show them and wait.
3. **Generate.** One script call per prompt (calls are independent, so run them in parallel when there are several). Local `--ref` files are sent inline (fal/wavespeed); kie.ai needs public URLs, so local refs automatically skip kie.
4. **Log & show.** Outputs land in `generations/YYYY-MM-DD/` with a `.prompt.txt` next to each, and one JSON line per job in `generations/log.jsonl` (prompt, model, provider, params, est. cost, files). Look at the results yourself before reporting, then list file paths + total spend.
5. **Use in the site.** When the user picks an image for the site, copy it to `public/images/<breed-or-section>/` with a descriptive kebab-case name, convert large PNGs to `.webp` if a tool is available, and reference it with `next/image` and a real Romanian `alt` text.

## Choosing a model

| Need | Model key |
|---|---|
| Cheap photoreal breed photos, bulk | `seedream-4` or `nano-banana` |
| Consistent cat across several scenes / edits from a reference | `nano-banana` (edit) or `nano-banana-pro` |
| Text inside the image (ads, infographics, thumbnails) | `gpt-image-2` (cheapest on kie: ~$0.03/1K, $0.05/2K, $0.08/4K) |
| Hero video from a still | `kling-i2v` or `seedance-fast` (need `--ref`) |

## Adding a model

Copy the provider's model id and input schema from its page (fal.ai and WaveSpeed have "copy for LLMs"/API tabs; kie.ai has per-model docs), add an entry to `models.json` with `id`, optional `edit_id`, `ref_field`, `est_usd`, then test with one `--dry-run` and one real call.

## Content rules for this site

Cat images for breed pages must look like the actual breed (coat pattern, ear shape, eye colour). Never present AI images as photos of a specific real cat or breeder; no fake "customer" photos or reviews.
