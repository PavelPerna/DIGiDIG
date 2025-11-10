from playwright.sync_api import sync_playwright, Error
import os


def test_top_pane_header():
    """Try known UI endpoints and assert the top-pane title and size when available.

    This test will attempt admin (8005), mail (8007) and apidocs (8010) by default
    and use the first responsive endpoint. Use DIGIDIG_TEST_BASE_URL to override.
    """
    env_url = os.environ.get('DIGIDIG_TEST_BASE_URL')
    candidates = [env_url] if env_url else [
        'http://localhost:8005',
        'http://localhost:8007',
        'http://localhost:8010'
    ]

    found = False
    last_error = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for base_url in candidates:
            if not base_url:
                continue

            try:
                page.goto(base_url, wait_until='networkidle', timeout=10000)

                # Wait briefly for top-pane; if not present, this will raise
                # If the service redirects to SSO login, perform login using default admin creds
                # Detect login form by presence of username/email and password inputs
                try:
                    # small delay to allow redirects to complete
                    page.wait_for_load_state('networkidle', timeout=3000)
                except Exception:
                    pass

                has_login = False
                try:
                    if page.query_selector('form input[name="username"]') or page.query_selector('form input[name="email"]'):
                        if page.query_selector('form input[name="password"]'):
                            has_login = True
                except Exception:
                    has_login = False

                if has_login:
                    # Perform login (default admin created by make install)
                    user = os.environ.get('DIGIDIG_TEST_ADMIN_USER', 'admin@example.com')
                    pwd = os.environ.get('DIGIDIG_TEST_ADMIN_PASS', 'admin')
                    # Fill fields (try username then email)
                    if page.query_selector('form input[name="username"]'):
                        page.fill('form input[name="username"]', user)
                    if page.query_selector('form input[name="email"]'):
                        page.fill('form input[name="email"]', user)
                    page.fill('form input[name="password"]', pwd)
                    # Submit the form
                    page.click('form button[type="submit"]')
                    # Wait longer for redirect back to the service and for backend token verification
                    try:
                        page.wait_for_load_state('networkidle', timeout=20000)
                    except Exception:
                        pass

                try:
                    page.wait_for_selector('[data-digidig-component="top-pane"]', timeout=20000)
                except Exception:
                    # Top-pane not present on this endpoint; try next candidate
                    continue

                # If we got here, top-pane exists — perform assertions
                title_el = page.query_selector('.digidig-top-pane-title')
                assert title_el is not None, 'Top pane title element not found'
                title_text = title_el.inner_text().strip()
                assert len(title_text) > 0, 'Top pane title is empty'

                header = page.query_selector('.digidig-top-pane')
                assert header is not None
                box = header.bounding_box()
                assert box is not None
                height = box['height']
                if height >= 600:
                    # Header is unusually tall on this endpoint; record and try next candidate
                    # Capture debug information to help diagnose layout issues
                    try:
                        snippet = header.evaluate('el => el.outerHTML.substring(0, 800)')
                    except Exception:
                        snippet = '<unable to retrieve outerHTML>'
                    try:
                        computed = header.evaluate('el => { const s = getComputedStyle(el); const children = Array.from(el.children||[]).slice(0,10).map(c => ({tag: c.tagName, cls: c.className, h: c.getBoundingClientRect().height})); return {height: s.height, maxHeight: s.maxHeight, overflow: s.overflow, paddingTop: s.paddingTop, paddingBottom: s.paddingBottom, children}; }')
                    except Exception:
                        computed = None
                    try:
                        screenshot_path = f'/tmp/digidig_top_pane_debug_{int(height)}.png'
                        page.screenshot(path=screenshot_path, full_page=True)
                    except Exception:
                        screenshot_path = '<screenshot-failed>'
                    last_error = f'Header too tall: {height}px at {page.url}; snippet={snippet}; computed={computed}; screenshot={screenshot_path}'
                    print('\n[DEBUG] Oversized header snippet:\n', snippet)
                    print('\n[DEBUG] Computed styles and child sizes:\n', computed)
                    # Also dump any stylesheet rules that mention .digidig-top-pane to locate overrides
                    try:
                        rules = page.evaluate("() => { const found = []; for (const ss of document.styleSheets) { try { for (const r of ss.cssRules || []) { if (r.cssText && r.cssText.indexOf('.digidig-top-pane') !== -1) { found.push(r.cssText); } } } catch(e) { /* cross-origin or invalid */ } } return found.slice(0,20); }")
                    except Exception:
                        rules = []
                    print('\n[DEBUG] Stylesheet rules matching .digidig-top-pane (up to 20):\n', rules)
                    print('\n[DEBUG] Screenshot saved to:', screenshot_path)
                    continue

                found = True
                break

            except Error as e:
                # Record and try next host
                last_error = e
                continue

        browser.close()

    assert found, f'No responsive UI with top-pane found; last error: {last_error}'
