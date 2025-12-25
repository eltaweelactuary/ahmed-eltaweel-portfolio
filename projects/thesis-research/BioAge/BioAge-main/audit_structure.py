import re

def estimate_pages(text):
    words = len(text.split())
    # Academic standard: ~300 words per page (double spaced, 12pt)
    # or ~400-500 words per page (single spaced)
    # Let's assume 350 words/page as a safe average for a thesis with tables/figures.
    return words / 350, words

def audit_structure(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"--- THESIS STRUCTURE & PAGE BALANCE AUDIT: {file_path} ---\n")
    
    # Split by Chapters
    # Regex lookahead to find "CHAPTER X" or "REFERENCES" or "APPENDICES"
    sections = re.split(r'(?=^(\*\*|#+\s+)?CHAPTER\s+\d+|(?=^(\*\*|#+\s+)?REFERENCES)|(?=^(\*\*|#+\s+)?APPENDICES))', content, flags=re.MULTILINE)
    
    # Filter out empty splits and small captures
    clean_sections = []
    current_header = "Front Matter"
    current_text = ""
    
    # Identify headers
    header_pattern = re.compile(r'^(\*\*|#+\s+)?(CHAPTER\s+\d+|REFERENCES|APPENDICES)', re.IGNORECASE)

    # Initial preamble check
    # The split keeps the delimiter, so we need to reconstruct
    # Actually re.split with capturing group keeps the delimiter.
    # Let's use a simpler parsing loop.
    
    chapters = {}
    lines = content.split('\n')
    current_chap = "Front Matter"
    chapters[current_chap] = []
    
    for line in lines:
        match = header_pattern.match(line.strip())
        if match:
            # New section
            current_chap = line.strip().replace('*', '').replace('#', '').strip()
            # Simplify name (e.g. "CHAPTER 1: INTRO..." -> "CHAPTER 1")
            if ":" in current_chap:
                current_chap = current_chap.split(":")[0].strip()
            chapters[current_chap] = []
        
        chapters[current_chap].append(line)

    # Analyze each chapter
    print(f"{'SECTION':<25} | {'WORDS':<8} | {'EST. PAGES':<10} | {'STATUS'}")
    print("-" * 60)
    
    total_pages = 0
    balanced = True
    
    for title, lines in chapters.items():
        text = "\n".join(lines)
        pgs, wds = estimate_pages(text)
        total_pages += pgs
        
        # Check balance (Target ~15-25 pages)
        status = "OK"
        if "CHAPTER" in title:
            if pgs < 10: status = "SHORT (Expand?)"
            elif pgs > 30: status = "LONG (Trim?)"
        
        print(f"{title[:25]:<25} | {wds:<8} | {pgs:<10.1f} | {status}")

    print("-" * 60)
    print(f"TOTAL ESTIMATED PAGES: {total_pages:.1f} (Target: 80-120)")
    print("")

    # Hierarchy Check
    print("--- HIERARCHY CHECK (First 3 levels) ---")
    for title, lines in chapters.items():
        if "CHAPTER" not in title: continue
        print(f"\n[{title}]")
        for line in lines:
            # Check for H2 (X.Y) and H3 (X.Y.Z)
            # Regex for "X.Y " or "X.Y.Z "
            # We assume standard formatting "## X.Y" or "**X.Y"
            
            # 2.2 or 2.2.1
            match = re.match(r'^\s*(\*\*|#+)?\s*(\d+\.\d+(\.\d+)?)\.?', line.strip())
            if match:
                print(f"  {line.strip().replace('*', '')[:60]}...")

if __name__ == "__main__":
    audit_structure("Final_Thesis_Manuscript.md")
