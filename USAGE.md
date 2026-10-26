# Masar (مسار) - Researcher & Scholar User Guide

> **A Plain-Language Guide for Hadith Scholars, Historians, and Digital Humanities Researchers**  
> *No programming experience or command-line knowledge required.*

---

## Table of Contents

1. [What is Masar?](#what-is-masar)
2. [How to Start the Visual Workbench](#how-to-start-the-visual-workbench)
3. [Preparing Your Texts for Masar](#preparing-your-texts-for-masar)
   - [Method 1: Excel or Google Sheets (CSV)](#method-1-excel-or-google-sheets-csv)
   - [Method 2: Copy-Pasting Directly (Word, PDFs, Manuscripts)](#method-2-copy-pasting-directly-word-pdfs-manuscripts)
   - [Method 3: Using Large Pre-Built Databases (`riwayat-corpus`)](#method-3-using-large-pre-built-databases-riwayat-corpus)
4. [Step-by-Step Takhrīj Workflow](#step-by-step-takhrīj-workflow)
   - [Searching for Variant Paths (Takhrīj)](#1-searching-for-variant-paths-takhrīj)
   - [Understanding the Match Quality (The "Receipt")](#2-understanding-the-match-quality-the-receipt)
   - [Fixing Transmitter Names Leaking into the Hadith (Boundary Slider)](#3-fixing-transmitter-names-leaking-into-the-hadith-boundary-slider)
   - [Topical False Positives: What Does the Orange Badge Mean?](#4-topical-false-positives-what-does-the-orange-badge-mean)
   - [Exporting Your Curated Family Bundle](#5-exporting-your-curated-family-bundle)
5. [Arabic Text & Encoding Tips](#arabic-text--encoding-tips)
6. [Frequently Asked Questions](#frequently-asked-questions)

---

## What is Masar?

In traditional Hadith scholarship, **Takhrīj** (تخريج) is the meticulous art of gathering every variant narration, transmission route, and parallel text of a tradition across all compendia (Sunni, Shīʿī, Zaydī, etc.). 

Masar (**مسار** - meaning *trajectory* or *path*) is a specialized digital workbench built to automate the heavy lifting of Takhrīj:
- It searches your collections using **both exact words and paraphrased meanings** (*riwāyah bi-l-maʿnā*).
- It identifies **fragments and excerpts** (*taqṭīʿ*).
- It provides a **visual slider** to separate where the chain of transmitters (*isnād*) ends and the actual hadith text (*matn*) begins.
- It remembers your corrections permanently without ever touching or modifying your original files.

---

## How to Start the Visual Workbench

You do not need to interact with code to use Masar. Once installed on your computer:

1. **Launch the Application**:
   Open your terminal or application launcher and run:
   ```bash
   masar web
   ```
   *(Or launch the backend with `uvicorn masar.api.app:create_app --factory` and run `npm run dev` in `src/web`)*.

2. **Open Your Web Browser**:
   Navigate to:
   ```text
   http://localhost:5173
   ```
   You will see the interactive **Masar Verification Workbench** with a search bar, Arabic text reader, and split adjustment sliders.

---

## Preparing Your Texts for Masar

Masar is completely flexible. You can bring your own data in three easy ways:

### Method 1: Excel or Google Sheets (CSV)

If you are cataloging hadiths from a printed book, thesis, or personal database, a simple spreadsheet is the easiest method.

#### Spreadsheet Columns:

Create a table in Microsoft Excel, Apple Numbers, or Google Sheets with these exact column headers in the first row:

| Column Header | Required? | Description | Example |
| :--- | :--- | :--- | :--- |
| `id` | **Yes** | A unique number or label for each row | `1`, `2`, `bukhari_1`, `ms_folio_12` |
| `collection` | **Yes** | The title of the book or manuscript | `Ṣaḥīḥ al-Bukhārī`, `Musannaf Ibn Abī Shaybah` |
| `matn` | **Yes** | The actual saying, action, or description of the Prophet | `إنما الأعمال بالنيات وإنما لكل امرئ ما نوى` |
| `hadith_number` | Optional | The report number in your edition | `1`, `42`, `105a` |
| `book_number` | Optional | The kitāb / chapter number | `1`, `2`, `Kitab al-Iman` |
| `isnad_raw` | Optional | The transmission chain leading to the report | `حدثنا الحميدي قال حدثنا سفيان قال حدثنا يحيى...` |
| `sect` | Optional | Sectarian classification (`sunni` or `shia`) | `sunni` |
| `primary_narrators` | Optional | Key transmitters or companions (separated by commas) | `Umar ibn al-Khattab, Yahya ibn Said` |

#### How to Save Your Spreadsheet:
> [!IMPORTANT]
> When saving your spreadsheet in Microsoft Excel, always choose **CSV UTF-8 (Comma delimited) (*.csv)**.  
> Do not save as standard "CSV (Comma delimited)" or "Excel 97-2003", because standard CSV will corrupt Arabic letters into question marks (`???`).

---

### Method 2: Copy-Pasting Directly (Word, PDFs, Manuscripts)

If you are transcribing a rare manuscript, copying from Maktaba Shamela, or quoting a PDF:

1. Open the Masar Web Workbench or use the simple command:
   ```bash
   masar add --text "حدثنا يحيى قال سمعت عمر بن الخطاب يقول قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنيات" \
             --collection "Berlin State Library MS 402" \
             --ref "Folio 12b" \
             --family "fam_niyyah"
   ```
2. **Automated Transition Recognition**:  
   You do not need to split the isnād and matn beforehand. Masar’s built-in Arabic detector recognizes classic transition formulas (such as `قال رسول الله صلى الله عليه وسلم`, `سمعت رسول الله يقول`, and `عن النبي قال`) and automatically suggests where the chain ends and the speech begins.
3. You can review the split on your screen and adjust it immediately.

---

### Method 3: Using Large Pre-Built Databases (`riwayat-corpus`)

If you want to search across standard classical hadith compendia:

1. Download the pre-indexed SQLite database from the [**riwayat-corpus**](https://github.com/abdullahansara/riwayat-corpus) project (containing ~925,000 reports across Sunni and Shīʿī collections).
2. Point Masar to your downloaded file:
   ```bash
   masar search --db hadith_master.db --seed "إنما الأعمال بالنيات"
   ```
   *(Or select the database file directly in the visual workbench).*

---

## Step-by-Step Takhrīj Workflow

### 1. Searching for Variant Paths (Takhrīj)

1. In the **Search Bar**, type the core phrase or key words of the tradition in standard Arabic (e.g., `إنما الأعمال بالنيات` or `طلب العلم فريضة`).
2. Choose your **Scope**:
   - **All Collections**: Searches both Sunni and Shīʿī compendia simultaneously.
   - **Sunni Only**: Restricts matches to Sunni works (the Nine Books, Musannaf collections, etc.).
   - **Shīʿī Only**: Restricts matches to Shīʿī works (al-Kāfī, al-Tahdhīb, al-Istibṣār, Man Lā Yaḥḍuruhu al-Faqīh).
3. Click **Search** (or press Enter). Within a fraction of a second, Masar returns all parallel narrations ranked by similarity.

---

### 2. Understanding the Match Quality (The "Receipt")

Every candidate hadith returned by Masar includes a transparent **Explainability Receipt** showing why it was identified as a parallel:

- **Lexical Score (Exact Words)**: How many exact words match your query (using FTS5 BM25).
- **Pericope Score (Passage Alignment / *Taqṭīʿ*)**: Detects whether this hadith is a shorter excerpt or longer version of the same story, even if some words are omitted.
- **Semantic Score (Paraphrase / *Riwāyah bi-l-Maʿnā*)**: Measures concept similarity. If one narrator used `ذهب` and another said `انطلق`, Masar recognizes they convey the same meaning.
- **Isnād Score (Chain Convergence)**: Detects if the reports share the same Companion or common teacher (the Common Link / *Madār*).

---

### 3. Fixing Transmitter Names Leaking into the Hadith (Boundary Slider)

In digitized books and OCR scans, words from the isnād (such as `قال قال رسول الله` or narrator names) often leak into the beginning of the matn text.

1. Click **Inspect** on any hadith candidate.
2. The **Split Editor** displays the text in two highlighted colors:
   - <span style="color: blue;">**Blue Highlight**</span>: The Chain of Transmitters (*Isnād*).
   - <span style="color: green;">**Green Highlight**</span>: The Hadith Text (*Matn*).
3. Simply drag the **Split Slider** left or right until the transition line sits exactly at the true beginning of the speech.
4. Click **Save Split**.
5. **Permanent Accretive Memory**: Masar saves this correction into your personal workspace database (`masar-curated.db`). Next time you or your colleagues search this hadith, it will automatically appear with your clean, corrected boundary.

---

### 4. Topical False Positives: What Does the Orange Badge Mean?

If you search for a hadith about prayer or ablution, a naive search engine might return hundreds of completely different hadiths simply because they mention the words "prayer" or "ablution."

Masar protects you against this with its **Topic Trap Guard**:
- If a hadith shares theological or legal vocabulary with your search, but has **no matching word sequence** and **no common transmitters**, Masar automatically flags it with an orange **`TOPICAL_FALSE_POSITIVE`** badge.
- This prevents unrelated hadiths from polluting your variant study.

---

### 5. Exporting Your Curated Family Bundle

Once you have verified all parallel variants of your hadith:

1. Click **Export Family Bundle**.
2. Masar runs **4 Preflight Quality Checks**:
   - Checks that all hadiths belong to the same agreed tradition.
   - Verifies that no transmitter names bleed into the matn.
   - Ensures transmission chains are properly recorded.
   - Validates standard academic formatting.
3. Save the clean JSON file. You can now use it in your research publication, share it with colleagues, or import it into [**Riwaq**](https://github.com/munir-abbasi/riwaq) to automatically generate Isnad-cum-Matn stemma tree diagrams.

---

## Arabic Text & Encoding Tips

- **Vowel Marks (Tashkīl / Harakāt)**: You do not need to worry about vowel marks. Whether you type `إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ` or `انما الاعمال بالنيات`, Masar automatically strips diacritics and unifies variant spellings of Alif (`أ`, `إ`, `آ` $\to$ `ا`) and Tāʾ Marbūṭah (`ة` $\to$ `ه`).
- **Taqṭīʿ (Truncated / Fragmented Hadiths)**: Classical authors often quote only one sentence of a long hadith. Masar's sliding window algorithm matches small excerpts to their full multi-paragraph parents.
- **UTF-8 Encoding**: Always ensure Arabic files are saved with UTF-8 encoding so text displays correctly across Windows, Mac, and Linux.

---

## Frequently Asked Questions

#### Q: Do I need to be connected to the internet?
**A:** No. Masar runs completely offline on your personal computer. Your research notes, unpublished papers, and manuscript transcriptions never leave your machine.

#### Q: Does Masar modify or overwrite my original files?
**A:** No. Masar treats all source files as strictly read-only. Whenever you fix a typo, repair a boundary split, or group variants, Masar writes your additions into an overlay file (`masar-curated.db`). Your source data is 100% safe.

#### Q: Do I need Riwaq to use Masar?
**A:** No. Masar is a complete, self-contained Takhrīj engine. Riwaq is an optional downstream companion tool if you specifically want to generate formal mathematical stemma trees (ICMA graphs).

#### Q: Can I undo a mistake?
**A:** Yes. Every action in Masar is tracked in a reversible journal. You can undo any split adjustment or grouping with a single click.
