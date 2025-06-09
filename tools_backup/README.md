# Tools Backup

This directory contains exported tools from the website for version control backup.

## Summary
- **Total Tools:** 1
- **Active Tools:** 1
- **Last Updated:** 2025-06-09 19:59:03

## Structure
```
tools_backup/
├── manifest.json          # Complete manifest of all tools
├── README.md              # This file
└── tools/                 # Individual tool directories
    ├── tool-slug-1/
    │   ├── index.html     # Tool HTML content
    │   └── metadata.json  # Tool metadata
    └── tool-slug-2/
        ├── index.html
        └── metadata.json
```

## Active Tools
- **Jupyter Notebook to Python Converter** (`jupyter-notebook-to-python-converter`) - 5 views
  - Convert .ipynb files to clean Python code with cell markers. Features swipe-to-delete cells and live preview.

## Usage
These files are automatically exported from the Django admin when tools are created or updated.

To restore or import these tools, use the Django management command:
```bash
python manage.py import_tools --from-backup
```

## Auto-Export
Tools are automatically exported when:
1. A new tool is created
2. An existing tool is updated
3. The daily cron job runs (if changes detected)

Export command: `python manage.py export_tools`
