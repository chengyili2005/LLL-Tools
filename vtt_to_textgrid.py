# I'm going to be completely honest, Copilot built most of the code on this one. I only tweaked it to make it actually work.

from textgrid import TextGrid, IntervalTier
import os
import sys
import re

TIME_RE = re.compile(r'^\s*(\d{2}:\d{2}:\d{2}\.\d{1,3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{1,3})')

def time_to_seconds(t: str) -> float:
    h, m, s = t.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def parse_vtt(path: str):
    cues = []
    with open(path, 'r', encoding='utf-8') as fh:
        lines = [ln.rstrip('\n') for ln in fh]

    i = 0
    while i < len(lines):
        m = TIME_RE.match(lines[i])
        # If the current line is an index (number) and next line is time, skip index
        if not m and i + 1 < len(lines):
            m = TIME_RE.match(lines[i + 1])
            if m:
                i += 1

        if m:
            start_s, end_s = m.groups()
            i += 1
            # Collect text lines until a blank line or next timecode
            text_lines = []
            while i < len(lines) and lines[i].strip() != '' and not TIME_RE.match(lines[i]):
                text_lines.append(lines[i])
                i += 1
            text = '\n'.join(text_lines).strip()
            cues.append((time_to_seconds(start_s), time_to_seconds(end_s), text))
        else:
            i += 1
    return cues

def vtt_to_textgrid(vtt_path: str, output_path: str):
    cues = parse_vtt(vtt_path)
    if not cues:
        print("No cues found in VTT. Exiting.")
        return

    max_time = max(end for (_, end, _) in cues)
    tg = TextGrid()
    tier = IntervalTier(name="FromVTT", maxTime=max_time)

    for start, end, text in cues:
        # Remove speaker information if present (e.g., "Speaker 1: Hello")
        if ':' in text:
            text = text.split(':', 1)[1].strip()

        # Ensure start < end
        if end <= start:
            # skip invalid cue
            continue
        tier.add(start, end, text)

    tg.append(tier)

    # Ensure output directory exists
    out_dir = os.path.dirname(output_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    tg.write(output_path)
    print(f"Finished writing TextGrid to: {output_path}")

def make_output_path(input_path: str, out_arg: str) -> str:
    if os.path.isdir(out_arg):
        base = os.path.splitext(os.path.basename(input_path))[0]
        return os.path.join(out_arg, base + ".TextGrid")
    # if ends with .TextGrid or .textgrid treat as file, otherwise treat as directory name
    if out_arg.lower().endswith(".textgrid"):
        return out_arg
    # create directory if it doesn't exist and place file inside
    if not os.path.exists(out_arg) or os.path.isdir(out_arg):
        os.makedirs(out_arg, exist_ok=True)
        base = os.path.splitext(os.path.basename(input_path))[0]
        return os.path.join(out_arg, base + ".TextGrid")
    return out_arg

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 vtt_to_textgrid.py input.vtt output_dir_or_file")
        sys.exit(1)

    vtt_file = sys.argv[1]
    out_arg = sys.argv[2]

    if not os.path.isfile(vtt_file):
        print(f"VTT file not found: {vtt_file}")
        sys.exit(1)

    output_path = make_output_path(vtt_file, out_arg)
    vtt_to_textgrid(vtt_file, output_path)

