Instagram Engine — Automated Content Generation & Publishing
=================================================================

A fully automated Instagram content engine for Prisha Online Documentation.
Generates, designs, and publishes a new high-quality post every day — no human intervention required.

Architecture Overview
=====================

instagram_engine/
└── .github/workflows/       GitHub Actions — daily trigger
└── data/                    Persistent state (post history)
└── fonts/                   TTF fonts for image generation
└── images/                  Generated post images
└── lib/                     Core modules
└── logs/                    Daily operation logs
└── output/                  Temporary output during pipeline runs
└── templates/               JSON templates for content categories
└── tests/                   Validation tests
└── main.py                  Pipeline orchestrator
└── requirements.txt         Python dependencies
└── .env                     Secrets (never commit)
└── .env.example             Template for secrets
└── config.yaml              Business config + API settings
└── README.md                This file

Modules
=======

lib/content_engine.py       — Gemini/OpenAI content generation
lib/image_engine.py         — Pillow image composer
lib/instagram_publisher.py  — Meta Graph API media creation + publishing
lib/dedup_engine.py         — Duplicate detection + topic rotation
lib/logger.py               — Structured logging
utils.py                    — Shared helpers (env, paths, dates)

Pipeline Flow (main.py)
=======================

1. Load config.yaml
2. Load generated_posts.json (history)
3. dedup_engine.pick_category()     → choose diverse category
4. content_engine.generate_post()   → Gemini → JSON content
5. dedup_engine.is_duplicate()      → reject if too similar
6. image_engine.create_image()      → 1080x1080 PNG
7. instagram_publisher.publish()    → upload + publish
8. Save post to generated_posts.json
9. Log everything

Scheduling
==========

GitHub Actions runs daily at 10:00 AM IST (04:30 UTC).
The workflow checks out the repo, installs deps, and runs main.py.

Future Expansion
================

To add LinkedIn/Facebook/X support:
1. Create lib/linkedin_publisher.py (same interface as instagram_publisher)
2. In main.py, loop over [instagram_publisher, linkedin_publisher]
3. Each publisher reads from the SAME content JSON — no duplicate generation needed
4. Platform-specific formatters handle caption length, image ratio, etc.

The architecture is publisher-agnostic. Content is generated once, published N times.
