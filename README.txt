Project structure

.
├── __pycache__/               # Compiled Python files
├── datasets/                 # Directory for storing datasets
│   ├── open_access_enriched.csv             # csv with all urls for papers in Q1_eng_compsi_econ
│   ├── open_access_paper_links_GPTMADE.csv  # csv made by GPT that was used for an initial test
│   ├── Q1_eng_compsi_econ.xlsx              # Q1 papers filtered for these three application areas
│   └── Q1_scopus_papers_verified.xlsx       # All 3283 Q1 papers
├── dev_files/                # Experimental notebooks and scripts
│   ├── GPT_first_test.ipynb       # Initial test with GPT for task automation
│   ├── notte_testing.ipynb        # Notebook for evaluating the Notte API/tool
│   ├── playwright_scraper.py      # Script using Playwright for web scraping
│   └── plots.ipynb                # Visualization and analysis notebook
├── future_research/         # Possible future directions 
│   ├── text_extractor.ipynb       # Experimental text extraction techniques
│   └── unpaywall.ipynb            # Integration with the Unpaywall API for open access papers
├── link_finding.ipynb        # Logic for identifying research paper links
├── pdf_downloading.ipynb     # Script for attempting to download PDFs from URLs
└── README.md                 
