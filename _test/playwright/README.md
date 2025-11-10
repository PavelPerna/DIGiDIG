Playwright test scaffold
========================

This folder contains a small Playwright test that validates the top-pane renders and shows the localized service title.

Requirements (developer machine):
- Python 3.8+
- Install Playwright for Python:

```bash
python -m pip install playwright pytest-playwright
python -m playwright install
```

Run tests:

```bash
pytest _test/playwright -q
```

Notes:
- The test expects the web app to be running and accessible at the URL configured in the test (default: http://localhost:8000). Adjust the URL in `test_header.py` as needed.
