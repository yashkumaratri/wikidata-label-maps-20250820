# Wikidata Multilingual Label Maps 2025 🏷️

Comprehensive multilingual label and description maps extracted from the 2025 Wikidata dump. This dataset contains labels and descriptions for Wikidata entities (Q-items and P-properties) across **613 languages**.

## 📊 Dataset Overview

- **📊 Total Records**: 725,274,530 label/description pairs
- **🆔 Unique Entities**: 117,229,348 (Q-items and P-properties)
- **🌍 Languages**: 613 unique language codes
- **📝 With Descriptions**: 339,691,043 pairs (46.8% coverage)
- **📦 File Size**: ~9.97 GB compressed

### Entity Breakdown
- **Q-items**: 724,987,441 records (99.96%)
- **P-properties**: 287,089 records (0.04%)

### Language Distribution - Top 20 Languages by Label Count

| Language | Count | Percentage |
|----------|--------|------------|
| en (English) | 90,445,991 | 12.5% |
| nl (Dutch) | 56,171,796 | 7.7% |
| ast (Asturian) | 19,027,483 | 2.6% |
| fr (French) | 17,971,824 | 2.5% |
| de (German) | 17,094,083 | 2.4% |
| es (Spanish) | 16,174,147 | 2.2% |
| mul (Multiple) | 15,585,604 | 2.1% |
| it (Italian) | 11,831,736 | 1.6% |
| sq (Albanian) | 11,331,135 | 1.6% |
| ga (Irish) | 10,648,122 | 1.5% |

*Note: The dataset includes 613 total languages, from major world languages to regional dialects and constructed languages.*

## 📦 Files

- `qid_labels_desc.parquet` - Main dataset file with columns:
  - `id`: Entity ID (Q-items and P-properties)
  - `len`: Language code (613 unique languages)
  - `label`: Entity label in the specified language
  - `des`: Entity description in the specified language (may be empty)

## 📦 Pre-built Datasets

Access the complete datasets on Hugging Face:

- **All Languages (2025)**: [`yashkumaratri/wikidata-label-maps-2025-all-languages`](https://huggingface.co/datasets/yashkumaratri/wikidata-label-maps-2025-all-languages) (Recommended)
- **English only Snapshot**: [`yashkumaratri/wikidata-label-maps-20250820`](https://huggingface.co/datasets/yashkumaratri/wikidata-label-maps-20250820)

```bash
# Clone the repository
git clone https://github.com/yourusername/wikidata-label-mapper.git
cd wikidata-label-mapper

# Install Python dependencies
pip install -r requirements.txt

# System dependencies (Ubuntu/Debian)
sudo apt-get install pbzip2 zstd

# For Parquet support
pip install duckdb
```

### Dependencies

**Required:**
- Python 3.8+
- `pbzip2` or `lbzip2` (for fast decompression)
- `zstd` (for output compression)

**Optional (for better performance):**
- `orjson` or `simdjson` (faster JSON parsing)
- `duckdb` (for Parquet conversion)
- `polars` (for optimized data loading)

## 🔧 Installation

## 🏃‍♂️ Quick Start

### Using Pre-built Datasets

#### Hugging Face Datasets

```python
from datasets import load_dataset

# Load the complete multilingual dataset
dataset = load_dataset("yashkumaratri/wikidata-label-maps-2025-all-languages")

# Access the data (note: column names are 'id', 'len', 'label', 'des')
for example in dataset['train']:
    print(f"QID: {example['id']}")
    print(f"Language: {example['len']}")  # 'len' = language code
    print(f"Label: {example['label']}")
    print(f"Description: {example['des']}")  # 'des' = description
```

#### Polars (Recommended for large datasets)

```python
import polars as pl

# Load Parquet file with Polars (extremely fast)
df = pl.read_parquet("qid_labels_desc.parquet")

# Filter for specific languages
english_labels = df.filter(pl.col("len") == "en")

# Get label for specific QID
label = df.filter(pl.col("id") == "Q42").select("label").item()

# Language statistics
lang_stats = df.group_by("len").len().sort("len", descending=True)
print(lang_stats.head(20))

# Find entities with descriptions in multiple languages
multilang_entities = (df
    .filter(pl.col("des") != "")
    .group_by("id")
    .agg(pl.col("len").count().alias("lang_count"))
    .filter(pl.col("lang_count") > 5)
    .sort("lang_count", descending=True)
)
```

#### DuckDB (SQL Interface)

```python
import duckdb

# Query directly from Parquet
conn = duckdb.connect()

# Get English labels only
english_df = conn.execute("""
    SELECT * FROM 'qid_labels_desc.parquet' 
    WHERE len = 'en'
""").df()

# Search by label pattern
results = conn.execute("""
    SELECT id, label, des 
    FROM 'qid_labels_desc.parquet' 
    WHERE len = 'en' AND label ILIKE '%einstein%'
""").fetchall()

# Language coverage statistics
lang_coverage = conn.execute("""
    SELECT 
        len as language,
        COUNT(*) as total_labels,
        SUM(CASE WHEN des != '' THEN 1 ELSE 0 END) as with_descriptions,
        ROUND(100.0 * SUM(CASE WHEN des != '' THEN 1 ELSE 0 END) / COUNT(*), 2) as desc_coverage_pct
    FROM 'qid_labels_desc.parquet'
    GROUP BY len
    ORDER BY total_labels DESC
    LIMIT 20
""").df()
```

## 🚀 High-Performance Pipeline Features

This repository also includes the extraction pipeline used to create these datasets:

- **Multi-language Support**: Extract labels and descriptions in all available languages
- **High Performance**: Multi-threaded processing with pbzip2/lbzip2 decompression
- **Optimized Storage**: Output in both compressed TSV and Parquet formats
- **Memory Efficient**: Stream processing for handling massive dumps (50GB+)
- **Fast JSON Parsing**: Automatic fallback from orjson → simdjson → standard json
- **HPC Ready**: SLURM job scripts included for cluster environments

### Running the Extraction Pipeline

```bash
# Download latest Wikidata dump
wget https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.bz2

# Run extraction
python3 wikidata_extractor.py
```

## 🖥️ HPC Usage (SLURM)

For processing large Wikidata dumps on HPC clusters:

```bash
# Submit job to SLURM
sbatch wiki.sbatch

# Monitor job
squeue -u $USER
```

The included SLURM script requests:
- 90 CPU cores
- 192GB RAM  
- 7-day time limit
- Automatic cleanup

## 📊 Output Formats

### Parquet (Columnar Storage)
The main dataset format optimized for analytics and fast querying:

**Schema:**
- `id`: VARCHAR - Entity identifier (Q-items and P-properties)
- `len`: VARCHAR - Language code (ISO 639 codes and extensions)
- `label`: VARCHAR - Entity label in the specified language  
- `des`: VARCHAR - Entity description (may be empty string)

**Example rows:**
```
Q42    en    Douglas Adams    English author and humorist
Q42    es    Douglas Adams    escritor británico  
Q42    fr    Douglas Adams    écrivain britannique
Q42    de    Douglas Adams    britischer Schriftsteller
```

## ⚡ Performance Optimizations

### Loading Large Files

```python
import polars as pl

# Lazy loading for memory efficiency (recommended for 725M+ records)
df = pl.scan_parquet("qid_labels_desc.parquet")

# Process in chunks with streaming
result = (df
    .filter(pl.col("len") == "en")
    .select(["id", "label"])
    .collect(streaming=True)
)

# Memory-efficient iteration for large datasets
for batch in df.iter_slices(n_rows=1_000_000):
    # Process each batch of 1M rows
    processed_batch = batch.filter(pl.col("des") != "")
    # ... do something with processed_batch
```

### Parallel Processing

```python
import polars as pl
from concurrent.futures import ProcessPoolExecutor

def process_language_chunk(lang_code):
    return pl.scan_parquet("qid_labels_desc.parquet").filter(
        pl.col("len") == lang_code
    ).collect()

# Process multiple languages in parallel
languages = ["en", "es", "fr", "de", "zh"]
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_language_chunk, languages))
```

## 📈 Dataset Statistics

The 2025 multilingual dataset contains:
- **725,274,530 total records** across 613 languages
- **117,229,348 unique entities** (Q-items and P-properties)  
- **339,691,043 pairs with descriptions** (46.8% coverage)
- **~9.97 GB compressed** Parquet format

### Entity Distribution
- **Q-items**: 724,987,441 records (99.96%)
- **P-properties**: 287,089 records (0.04%)

### Language Coverage
The dataset includes:
- **Major world languages**: English, Spanish, French, German, Chinese, etc.
- **Regional languages**: Asturian, Irish, Albanian, etc.
- **Constructed languages**: Esperanto, Klingon, etc.
- **Historical languages**: Latin, Ancient Greek, etc.
- **Script variants**: Traditional/Simplified Chinese, etc.

## 🔧 Configuration

Key parameters in `wikidata_extractor.py`:

```python
THREADS = 45          # pbzip2 decompression threads
SHARDS = 32           # parallel processing shards
MAX_WORKERS_SORT = 16 # sorting/compression workers
```

Adjust based on your hardware:
- **CPU cores**: Set `THREADS` to 80-90% of available cores
- **RAM**: Ensure 2-4GB per thread for large dumps
- **Storage**: Fast SSD/HDD recommended for temp files

## 🎯 Use Cases

- **Knowledge Graph Construction**: Build multilingual knowledge bases
- **Entity Linking**: Map text mentions to Wikidata entities  
- **Machine Translation**: Cross-lingual entity alignment
- **Information Extraction**: Named entity recognition training data
- **Semantic Search**: Build entity embeddings and search indexes

## 🐛 Troubleshooting

### Common Issues

**Out of Memory**:
```bash
# Reduce thread count
THREADS = 20  # instead of 45
```

**Disk Space**:
```bash
# Use faster compression (trades size for speed)
zstd -T0 -1  # instead of -19
```

**Missing Dependencies**:
```bash
# Install system packages
sudo apt-get install pbzip2 lbzip2 zstd

# Install Python packages
pip install orjson simdjson duckdb polars
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


and ❤️ Thanks to [Polars](https://github.com/pola-rs/polars) 🚀


