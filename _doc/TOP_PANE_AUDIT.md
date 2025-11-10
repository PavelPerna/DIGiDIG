Top-pane inclusion audit
========================

Files that include the shared `top-pane` component:

- `services/mail/src/templates/layout.html` — includes `{% include 'top-pane/top-pane.html' %}` and loads the top-pane CSS/JS. Title is expected to come from the handler via `title` template variable; fallback is provided by i18n (`common.service_title`).
- `services/admin/src/templates/layout.html` — includes `{% include '/lib/common/components/top-pane/top-pane.html' %}`. Same notes as above.

Notes and recommendations
------------------------

- The `top-pane` template already provides sensible fallbacks using `i18n.get('common.service_title', 'Service Title')` when `title` is not passed. Therefore most pages will display a localized title even if the controller does not set `title`.
- Recommended (best practice): controllers that render pages should set `title` to a short page-specific value (e.g., "Inbox", "Domains") and allow the layout to append the site name where appropriate. This improves browser tab labels and accessibility.
- Optional: standardize include paths. The admin layout uses an absolute include path (`/lib/common/components/top-pane/top-pane.html`) while mail uses a relative include. Both work with existing Jinja environment; normalization is optional.

Files scanned but not including top-pane (examples)
--------------------------------------------------
- individual page templates under services/*/src/templates/pages typically do not include the top-pane directly — they rely on the service layout to include it.

Next steps
----------
- If you want, I can (pick one):
  - Add a small helper macro `lib/common/components/top-pane/top-pane-wrapper.html` that ensures default `title`/`logo_text` values and can be included uniformly; or
  - Patch a small number of layouts to explicitly pass `title` where missing; or
  - Leave as-is since i18n fallback is already present.

Audit completed on 2025-10-30.
