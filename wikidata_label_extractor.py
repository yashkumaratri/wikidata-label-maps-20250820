#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import shutil
import time
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

# === CONFIG ===
THREADS = 45          # pbzip2 threads
SHARDS = 32           # for parallel sort
MAX_WORKERS_SORT = 16 # for sort/compress phase

# === PATHS ===
DUMP = Path("latest-all.json.bz2")
assert DUMP.exists(), f"Dump not found: {DUMP}"

OUT_ROOT = Path("label_maps_all_langs_stream")
TMPROOT = Path(f"temp/{os.getpid()}")
OUT_ROOT.mkdir(parents=True, exist_ok=True)
TMPROOT.mkdir(parents=True, exist_ok=True)

# Output paths
PASS1_OUTPUT = OUT_ROOT / "qid_labels_desc_en.tsv.zst"
PARQUET_OUTPUT = OUT_ROOT / "qid_labels_desc_en.parquet"

# === UTILS ===
def make_loader():
    """Try fast JSON loaders"""
    try:
        import orjson
        return orjson.loads
    except Exception:
        pass
    try:
        import simdjson
        pj = simdjson.Parser()
        def loads(x: str):
            return pj.parse(x).as_dict()
        return loads
    except Exception:
        pass
    return json.loads

JSON_LOADS = make_loader()

def open_bz2_stream(path: Path, threads=THREADS):
    """Open bz2 stream using pbzip2/lbzip2/bzip2"""
    exe = shutil.which("pbzip2") or shutil.which("lbzip2") or shutil.which("bzip2")
    if not exe:
        raise FileNotFoundError("Need pbzip2 or lbzip2 or bzip2 on PATH")
    base = os.path.basename(exe)
    if base.startswith("pbzip2"):
        cmd = [exe, f"-p{threads}", "-dc", str(path)]
    elif base.startswith("lbzip2"):
        cmd = [exe, f"-n{threads}", "-dc", str(path)]
    else:
        cmd = [exe, "-dc", str(path)]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=16*1024*1024)
    assert p.stdout is not None
    return p, p.stdout

def strip_line(s: str) -> str:
    """Clean JSON line from Wikidata dump"""
    s = s.strip()
    if not s:
        return ""
    if s in ("[", "]"):
        return ""
    if s.endswith(","):
        s = s[:-1].rstrip()
    if not s or s[0] not in ('{', '['):
        return ""
    return s

# === PASS 1: EXTRACT ENGLISH LABELS AND DESCRIPTIONS ===
def pass1_extract_labels_desc(dump: Path, output_file: Path):
    """Extract ALL labels and descriptions from Wikidata dump (all languages)"""
    print(f"=== 🚀 PASS 1: EXTRACTING ALL LANGUAGES ===")
    print(f"  Input: {dump}")
    print(f"  Output: {output_file}")
    
    proc, stdout = open_bz2_stream(dump, threads=THREADS)
    entity_count = 0
    extracted_count = 0

    # Open output stream — force overwrite
    zstd_proc = subprocess.Popen(["zstd", "-T0", "-19", "-f", "-o", str(output_file)], stdin=subprocess.PIPE, text=True)
    out_f = zstd_proc.stdin

    try:
        for line in iter(stdout.readline, b''):
            try:
                s = line.decode('utf-8', errors='replace')
            except Exception:
                continue
                
            s = strip_line(s)
            if not s:
                continue
                
            try:
                ent = JSON_LOADS(s)
            except Exception:
                continue
                
            if not isinstance(ent, dict):
                continue
                
            eid = ent.get("id", "")
            if not eid or eid[0] not in "QP":
                continue

            # Extract ALL labels
            labels = ent.get("labels", {})
            if isinstance(labels, dict):
                for lang, data in labels.items():
                    if isinstance(data, dict):
                        label_value = data.get("value", "")
                        if label_value:
                            # Extract description for this language (if exists)
                            desc_value = ""
                            descriptions = ent.get("descriptions", {})
                            if isinstance(descriptions, dict):
                                desc_data = descriptions.get(lang, {})
                                if isinstance(desc_data, dict):
                                    desc_value = desc_data.get("value", "")
                            
                            out_f.write(f"{eid}\t{lang}\t{label_value}\t{desc_value}\n")
                            extracted_count += 1

            entity_count += 1
            if entity_count % 1_000_000 == 0:
                print(f"  Processed {entity_count:,} entities | {extracted_count:,} extracted", file=sys.stderr)

    except BrokenPipeError:
        print("⚠️  zstd process exited early. Check if output file exists or disk is full.", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Error during extraction: {e}", file=sys.stderr)
    finally:
        try:
            stdout.close()
            proc.wait()
            if 'out_f' in locals() and out_f:
                out_f.close()
            if 'zstd_proc' in locals() and zstd_proc:
                zstd_proc.wait()
        except BrokenPipeError:
            pass
        except Exception as e:
            print(f"Cleanup error: {e}", file=sys.stderr)

    print(f"=== PASS 1 DONE ===")
    print(f"  Extracted {extracted_count:,} label/description pairs across all languages")
    return extracted_count

# === MAIN ===
if __name__ == "__main__":
    print("🚀 Starting Wikidata Label/Description Extraction Pipeline")
    print(f"📁 Dump: {DUMP}")
    print(f"📁 Output: {OUT_ROOT}")
    print(f"🧵 Threads: {THREADS}")
    print(f"🔢 Shards: {SHARDS}\n")

    t0_total = time.time()

    # PASS 1: Extract English labels and descriptions
    t0 = time.time()
    extracted_count = pass1_extract_labels_desc(DUMP, PASS1_OUTPUT)
    t1 = time.time()
    print(f"⏱️  Pass 1 took {t1 - t0:.1f} seconds\n")

    t1_total = time.time()
    print(f"🎉 TOTAL PIPELINE COMPLETED IN {t1_total - t0_total:.1f} SECONDS")
    print(f"📊 Final outputs:")
    if PASS1_OUTPUT.exists():
        print(f"   TSV.ZST: {PASS1_OUTPUT} ({PASS1_OUTPUT.stat().st_size:,} bytes)")
