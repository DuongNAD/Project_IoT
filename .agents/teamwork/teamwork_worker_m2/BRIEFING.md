# BRIEFING — 2026-11-03T10:55:00Z

## Mission
Build slides/assets/guide_screen_sample.png and slides/build_slides.py to generate a 15-slide widescreen dark-themed presentation (slides/Project_IoT_ThuyetTrinh.pptx) strictly following project code and design specifications.

## 🔒 My Identity
- Archetype: implementer
- Roles: implementer, qa
- Working directory: e:\03_Development_Projects\project\Project_IoT\.agents\teamwork\teamwork_worker_m2\
- Original parent: 00c906d7-900c-42be-a553-3eacb15019c9
- Milestone: Milestone 2 - Slide Generation & Asset Creation

## 🔒 Key Constraints
- Exclusively own all files inside `slides/` and `.agents/teamwork/teamwork_worker_m2/`.
- DO NOT create or modify any file outside `slides/` and working directory.
- DO NOT touch project source code, pyproject.toml, or uv.lock.
- DO NOT run git commit or git push.
- DO NOT fabricate or guess metrics/numbers/parameters not present in workspace code; keep placeholders `[...]` intact.
- DO NOT use AI-generated images.
- Generate real UI asset from code without AI (`guide_screen_sample.png`).
- 16:9 widescreen, strict dark theme matching `guide_screen.py`.
- Native PowerPoint shapes for block diagrams.
- Realistic Vietnamese speaker notes for all slides.
- Retain `[...]` placeholders for unknowns.

## Current Parent
- Conversation ID: 00c906d7-900c-42be-a553-3eacb15019c9
- Updated: 2026-11-03T10:55:00Z

## Task Summary
- **What to build**: `slides/assets/guide_screen_sample.png` and `slides/build_slides.py` generating `slides/Project_IoT_ThuyetTrinh.pptx` (15 slides).
- **Success criteria**: Valid, non-empty 15-slide PPTX with dark theme, native diagram shapes, keycaps, embedded guide screen asset, speaker notes, and footers.
- **Interface contracts**: `e:\03_Development_Projects\project\Project_IoT\.agents\teamwork\orchestrator\PROJECT.md`
- **Code layout**: `slides/`

## Change Tracker
- **Files modified / created**:
  - `slides/generate_asset.py`: Python routine generating `guide_screen_sample.png` without AI using `fake_assist()`, `aruco_A4_grid.png`, and `build_guide_screen()`.
  - `slides/assets/guide_screen_sample.png`: 1280x800 real screenshot asset.
  - `slides/build_slides.py`: Automated slide generation script using `python-pptx` (16:9 widescreen, strict dark theme, keycaps, native shapes, speaker notes, footers).
  - `slides/Project_IoT_ThuyetTrinh.pptx`: 15-slide technical presentation (326,968 bytes).
  - `slides/verify_slides.py`: Verification suite checking dimensions, slide count, shapes, notes, footers, and embedded image.
- **Build status**: PASS (Exit code 0, 15/15 slides verified).
- **Pending issues**: None.

## Quality Status
- **Build/test result**: PASS (15 slides, 13.333x7.500 in, all checks passed).
- **Lint status**: Clean.
- **Tests added/modified**: `slides/verify_slides.py` test suite.

## Key Decisions Made
- Used `python-pptx` with explicit widescreen dimensions (`13.333` x `7.5` inches).
- Used exact hex color mapping from `guide_screen.py` (`#191B1E`, `#272A2E`, `#464C52`, `#F5F5F5`, `#9BA0A5`, `#FFB928`, `#5AD76E`, `#F55555`).
- Configured Windows UTF-8 stdout reconfiguration in `build_slides.py` to prevent encoding issues on cp1252 consoles.
- Built diagram shapes using native PowerPoint shapes (`MSO_SHAPE.ROUNDED_RECTANGLE`, `MSO_SHAPE.RECTANGLE`, `MSO_SHAPE.RIGHT_ARROW`, `MSO_SHAPE.DOWN_ARROW`) for direct user editability.
- Embedded `slides/assets/guide_screen_sample.png` on Slide 12.
- Retained all `[...]` placeholders for unknown metrics/parameters.

## Artifact Index
- `slides/build_slides.py` — Slide generator script
- `slides/generate_asset.py` — Real UI asset generation script
- `slides/assets/guide_screen_sample.png` — Real UI screenshot
- `slides/Project_IoT_ThuyetTrinh.pptx` — Generated presentation
- `slides/verify_slides.py` — PPTX verification script
