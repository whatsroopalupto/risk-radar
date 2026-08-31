# Accessibility

Risk is operationally significant, so every badge has a number (`/ 100`), band word, and ▲ symbol instead of colour alone. Low, medium, and high use the Okabe–Ito blue `#0072B2`, orange `#E69F00`, and vermillion `#D55E00`; text is displayed against the default high-contrast background. Headings use Streamlit’s logical heading APIs, every number has a scale label, and graph edges have a dataframe equivalent for screen-reader access.

These are presentation-layer choices within Streamlit’s constraints. Full WCAG 2.2 AA conformance needs the Phase 3 React frontend; this project does not claim it.
