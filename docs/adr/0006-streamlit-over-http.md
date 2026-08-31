# Context
The UI must remain swappable.
# Decision
Streamlit calls FastAPI over HTTP only.
# Consequences
The dashboard cannot import backend code.
# Alternatives-rejected
Direct Python imports.
