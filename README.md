# qa_crew

A CrewAI crew that reads research-paper PDFs and files each one as linked Obsidian notes.

Four agents use tools. The PDF Feeder starts the run. For every filename it hands the paper to three agents, in order:

1. **PDF Feeder** takes the list and runs the pipeline once per file. Tool: Feed PDFs (`tools/feed_pdfs.py`).
2. **Paper Extractor** reads that PDF and pulls out title, method, dataset, metrics, and related studies. Tool: Read PDF (`tools/read_pdf.py`).
3. **Librarian** turns those fields into markdown notes with `[[wikilinks]]`. Tool: List Vault Notes (`tools/list_vault_notes.py`).
4. **Obsidian Publisher** saves each note into `obsidian_vault/`. Tool: Save Obsidian Note (`tools/save_obsidian_note.py`).

## Put the PDFs here

Drop the files in `knowledge/`. Only the file name is used, so do not put them in a subfolder.

## Set the PDF list here

In `crew.jsonc`, set `inputs.pdf_filenames` to those file names:

```jsonc
"inputs": {
  "pdf_filenames": ["2505.00527v2.pdf", "2406.09767v3.pdf"]
}
```

The feeder reads this list and runs `paper_crew.jsonc` once per name. One string still works if you only have one PDF: `"pdf_filenames": "2505.00527v2.pdf"`.

## Run

From this directory, with Ollama running `llama3.1:8b` on `http://localhost:11434`:

```bash
crewai run
```

Notes are written under `obsidian_vault/` (`papers/`, `methods/`, `datasets/`, `metrics/`, `studies/`).
