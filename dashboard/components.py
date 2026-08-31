"""Accessible text-plus-colour renderers."""
import streamlit as st
PALETTE={"low":"#0072B2","medium":"#E69F00","high":"#D55E00"}
SYMBOLS={"low":"▲","medium":"▲▲","high":"▲▲▲"}
def risk_badge(score:float,band:str)->None:
    """Present every risk state with number, word, symbol, and safe colour."""
    st.markdown(f"<span style='color:{PALETTE[band]};font-weight:bold'>Risk {score:.1f} / 100 — {band.title()} {SYMBOLS[band]}</span>",unsafe_allow_html=True)
