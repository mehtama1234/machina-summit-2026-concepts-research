# MACHINA Summit 2026 Concepts Research

Transcript-backed local study site for the MACHINA Summit 2026 YouTube playlist:

<https://www.youtube.com/playlist?list=PLQ0DCBKscYII>

The project follows the same lightweight pattern as the Stanford CS329A concept lab:

```text
raw-material/youtube/       playlist metadata, captions, clean transcripts
analysis/concepts/          first-pass concept atlas
analysis/evidence/          transcript-backed evidence anchors
scripts/                    download, analysis, build, validation
site/                       generated static HTML site
```

## Build

```bash
python3 scripts/download_youtube_transcripts.py
python3 scripts/generate_analysis.py
python3 scripts/build_site.py
python3 scripts/validate_all.py
```

## Review

Open:

```text
site/index.html
site/concepts.html
site/talks.html
site/transcripts.html
```

The current concept atlas is a first-pass transcript/title map. Use it as the route for deeper talk-by-talk first-principles writeups.
