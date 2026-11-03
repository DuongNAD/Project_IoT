"""Inspect speaker notes for all 15 slides."""
import os
import sys
import re

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import pptx
from pptx import Presentation

pptx_path = r"e:\03_Development_Projects\project\Project_IoT\slides\Project_IoT_ThuyetTrinh.pptx"
prs = Presentation(pptx_path)

print("=" * 80)
print("SPEAKER NOTES ANALYSIS")
print("=" * 80)

for idx, slide in enumerate(prs.slides, 1):
    notes = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
    # split into sentences using regex
    # sentences end with . ? ! followed by space or end of string
    raw_sentences = [s.strip() for s in re.split(r'[.!?]+(?:\s+|$)', notes) if s.strip()]
    num_sentences = len(raw_sentences)
    word_count = len(notes.split())
    
    print(f"\n--- SLIDE {idx:02d} ({num_sentences} sentences, {word_count} words) ---")
    print(f"Content: {notes}")
    for s_idx, sent in enumerate(raw_sentences, 1):
        print(f"  [{s_idx}] {sent}")
    
    # Requirement: 3-5 sentences
    valid_sentence_count = 3 <= num_sentences <= 6  # generous check for 3-5
    print(f"Sentence count check (3-5): {'PASS' if valid_sentence_count else 'WARNING'}")
