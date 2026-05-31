# SEO AI Agent — Free MVP

A free, local SEO audit dashboard. Enter any website URL, run a full audit, and download copy-paste ready Word documents for your developer.

## What It Does

- Crawls website pages (BeautifulSoup + Requests)
- Extracts: title, meta description, H1/H2/H3, canonical, slug, images without alt, internal links, schema markup, robots.txt, sitemap.xml
- Generates: SEO title, meta, H1, slug, image alt, schema JSON-LD, developer snippets
- Creates 4 Word documents:
  - `1_Technical_SEO_Audit.docx`
  - `2_Page_Wise_SEO_Audit.docx`
  - `3_Developer_Implementation_Guide.docx`
  - `4_GTM_GA4_Meta_Pixel_Guide.docx`
- Voice input (browser Web Speech API)
- Human approval required — no auto-changes

---

## Tech Stack

| Layer     | Tech                        |
|-----------|-----------------------------|
| Frontend  | Next.js 14 + Tailwind CSS   |
| Backend   | Python FastAPI              |
| Crawler   | BeautifulSoup + Requests    |
| Word Docs | python-docx                 |
| Database  | SQLite (via SQLAlchemy)     |
| Auth      | JWT (python-jose)           |
| Voice     | Browser Web Speech API      |

---

## Setup & Run

### Requirements

- Python 3.10+
- Node.js 18+

---

### Step 1 — Backend Setup

```bash
cd seo-ai-agent/backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

---

### Step 2 — Frontend Setup

Open a new terminal:

```bash
cd seo-ai-agent/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at: http://localhost:3000

---

### Step 3 — Use the App

1. Open http://localhost:3000
2. Click "Create Account" and register
3. Login with your credentials
4. Enter a website URL (e.g. `https://example.com`)
5. Select audit type (Full SEO Audit recommended)
6. Click "Start Audit"
7. Wait for progress to reach 100%
8. Click "View Results" to see the full report
9. Click "Download Word Files" to get all .docx files

---

## Audit Types

| Button | Description |
|--------|-------------|
| Full SEO Audit | Crawls 8 pages, full technical + on-page |
| Technical SEO | robots.txt, sitemap, HTTPS, canonical checks |
| On-Page SEO | Title, meta, H1, content analysis |
| Product Page SEO | E-commerce product pages |
| Category Page SEO | Category / collection pages |
| Blog SEO Plan | Blog/article recommendations |
| GTM/GA4/Meta Pixel | Analytics tracking code guide |

---

## Voice Commands

Click the microphone button and say:
- "Run full SEO audit for https://example.com"
- "Technical SEO audit"
- "Product page SEO"
- "GTM tracking guide"

---

## Generated Word Documents

### 1. Technical SEO Audit.docx
- HTTPS status
- robots.txt analysis
- Sitemap analysis
- All technical issues found
- Developer implementation checklist

### 2. Page Wise SEO Audit.docx
- Per-page: current vs. suggested title, meta, H1
- Canonical tag recommendations
- Slug suggestions
- Schema JSON-LD for each page
- Images missing alt text (with suggestions)
- Internal link recommendations

### 3. Developer Implementation Guide.docx
- Copy-paste HTML snippets for every fix
- Global head tags template
- Schema markup templates
- Image optimization code
- Performance quick wins

### 4. GTM GA4 Meta Pixel Guide.docx
- Google Tag Manager setup steps + code
- GA4 configuration + ecommerce events
- Meta Pixel base code + ecommerce events
- GTM DataLayer examples

---

## Important Notes

- **Human approval required** — review all suggestions before applying
- **No auto-updates** — this tool only generates recommendations
- Works best on publicly accessible URLs (no login-protected pages)
- Crawls up to 8 pages for Full/Technical audits, 3 pages for others
- SQLite database is created automatically at `backend/seo_agent.db`
- Word files saved in `backend/reports/<audit_id>/`

---

## Folder Structure

```
seo-ai-agent/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # SQLite database setup
│   ├── models.py            # Database models
│   ├── auth.py              # JWT authentication
│   ├── crawler.py           # Web crawler (BeautifulSoup)
│   ├── seo_analyzer.py      # SEO analysis + suggestion generation
│   ├── word_generator.py    # Word document creation (python-docx)
│   ├── requirements.txt
│   └── routers/
│       ├── auth.py          # /api/auth/* endpoints
│       ├── audit.py         # /api/audit/* endpoints
│       └── reports.py       # /api/reports/* endpoints
├── frontend/
│   ├── pages/
│   │   ├── index.js         # Login / Register page
│   │   └── dashboard.js     # Main dashboard
│   ├── components/
│   │   ├── VoiceInput.js    # Microphone voice input
│   │   ├── AuditProgress.js # Progress bar + steps
│   │   └── ReportViewer.js  # Results tabs + code blocks
│   └── styles/globals.css
└── README.md
```

---

## Troubleshooting

**Backend won't start:**
- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt` again

**Frontend can't connect to backend:**
- Check `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Make sure backend is running on port 8000

**Audit stuck at 0%:**
- The URL may be blocking crawlers — try a different site
- Check if the site requires JavaScript rendering (static crawling only in MVP)

**Voice input not working:**
- Use Chrome or Edge (Firefox has limited support)
- Allow microphone permission when prompted
- HTTPS required for microphone in production

**Can't download files:**
- Check `backend/reports/` folder exists
- Complete the audit first (progress must be 100%)
