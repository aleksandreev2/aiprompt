# Knowledge layer

`tags/*.csv` contains the project's verified NovelAI/Danbooru tag core split into repository-friendly shards. A single `verified_tags.csv` remains supported as an import/backward-compatibility format.

`source/` contains selected production references exported from Google Drive. Legacy host-specific instruction files are retained for provenance/reference; the local runtime does **not** automatically inject them wholesale. The runtime uses its own concise compiler contract plus the verified vocabulary to avoid contradictory or stale host-specific behavior.

Raw Telegram exports are intentionally not copied into the repository. They remain evidence/staging in Drive and should be promoted only after review.
