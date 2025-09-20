#!/bin/bash
#SBATCH -J wikidata_label_extractor
#SBATCH --ntasks=1
#SBATCH -A <account_name>
#SBATCH --partition=standard
#SBATCH --cpus-per-task=90
#SBATCH --mem=192G
#SBATCH -t 7-00:00:00
#SBATCH -o wikidata_label_extractor-%A.out
#SBATCH -e wikidata_label_extractor-%A.err

# === BEGIN JOB INFO ===
echo "🚀 WIKIDATA LABEL EXTRACTION JOB STARTED: $(date)"
echo "📊 Job ID: $SLURM_JOB_ID"
echo "💻 Node: $SLURMD_NODENAME"
echo "⚡ CPUs allocated: $SLURM_CPUS_PER_TASK"
echo "🧠 Memory allocated: 300G"
echo "⏳ Time limit: 7 days"

# === SETUP ===
module purge
module load miniforge

# Working directory
DIR="temp/${SLURM_JOB_ID}"
INPUT_FILE="latest-all.json.bz2"
SCRIPT_DIR="/"  # Where you saved the Python script
SCRIPT_NAME="wikidata_label_extractor.py"

echo "📁 Working directory: $DIR"
mkdir -p "$DIR"
cd "$DIR"

# Activate conda environment
echo "🐍 Activating conda environment..."
conda activate general_updated

# Validate tools
echo "✅ Validating tools..."
command -v python3 >/dev/null || { echo "❌ python3 not found"; exit 1; }
command -v pbzip2 >/dev/null || { echo "❌ pbzip2 not found"; exit 1; }
command -v zstd >/dev/null || { echo "❌ zstd not found"; exit 1; }

# Check input file
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Input file not found: $INPUT_FILE"
    exit 1
fi

echo "📊 Input file info:"
echo "  Path: $INPUT_FILE"
echo "  Size: $(ls -lh "$INPUT_FILE" | awk '{print $5}')"

# Copy script to temp dir (optional, for isolation)
cp "$SCRIPT_DIR/$SCRIPT_NAME" "$DIR/" || { echo "❌ Failed to copy script"; exit 1; }

# Install duckdb if not present
echo "📦 Installing duckdb (for Parquet)..."
pip install duckdb --user

# === RUN PYTHON PIPELINE ===
echo "🔥 STARTING PYTHON PIPELINE: $(date)"
python3 "$SCRIPT_NAME"

EXIT_CODE=$?
echo "🏁 PYTHON PIPELINE FINISHED: $(date) with exit code $EXIT_CODE"

# === REPORT OUTPUT ===
OUTPUT_ROOT="label_maps_all_langs_stream"
echo "📁 Final outputs:"
ls -lh "$OUTPUT_ROOT"/qid_labels_desc_en.* 2>/dev/null || echo "❌ No output files found"

# === CLEANUP ===
echo "🧹 Cleaning up temp directory: $DIR"
rm -rf "$DIR"

# === DONE ===
if [ $EXIT_CODE -eq 0 ]; then
    echo "🎉 SUCCESS: Wikidata label extraction completed!"
else
    echo "❌ FAILURE: Job failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi

echo "🔚 JOB COMPLETED: $(date)"
