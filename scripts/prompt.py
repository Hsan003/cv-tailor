#!/usr/bin/env python3
"""Print a command body (frontmatter stripped) with $ARGUMENTS replaced by the slug.
Usage: prompt.py <slug> [command=tailor]   (command = file name in .claude/commands/)"""
import sys
from pathlib import Path
command = sys.argv[2] if len(sys.argv) > 2 else "tailor"
text = (Path(__file__).resolve().parent.parent / f".claude/commands/{command}.md").read_text()
if text.startswith("---"):
    text = text.split("---", 2)[2]
print(text.strip().replace("$ARGUMENTS", sys.argv[1]))
