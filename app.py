from pathlib import Path

import streamlit as st

from db import run_migrations
from ui import (
    render_dashboard_page,
    render_contracts_page,
    render_new_contract_page,
    render_activities_page,
    render_ai_agent_page,
    render_info_page,
)
from ui.theme import apply_theme, render_sidebar_brand


FAVICON_PATH = Path(__file__).parent / "assets" / "favicon.png"
PAGE_ICON = str(FAVICON_PATH) if FAVICON_PATH.exists() else "📊"

st.set_page_config(page_title="LogiChain AI", page_icon=PAGE_ICON, layout="wide")
run_migrations()
apply_theme()

render_sidebar_brand()
menu_labels = {
    "dashboard": ("▣", "Dashboard"),
    "contracts": ("▤", "Contratos"),
    "new_contract": ("✚", "Novo Contrato"),
    "activities": ("◷", "Atividades"),
    "ai": ("◉", "Assistente IA"),
    "info": ("ⓘ", "Informações"),
}

raw_menu = st.query_params.get("menu", "dashboard")
if isinstance(raw_menu, list):
    raw_menu = raw_menu[0] if raw_menu else "dashboard"
menu = raw_menu if raw_menu in menu_labels else "dashboard"

menu_html = ['<nav class="lc-nav-menu">']
for key, (icon, label) in menu_labels.items():
    active = " is-active" if key == menu else ""
    menu_html.append(
        f'<a class="lc-nav-item{active}" href="?menu={key}" target="_self">'
        f'<span class="lc-nav-icon">{icon}</span>'
        f'<span class="lc-nav-label">{label}</span>'
        "</a>"
    )
menu_html.append("</nav>")
st.sidebar.markdown("".join(menu_html), unsafe_allow_html=True)
st.sidebar.markdown('<div class="lc-sidebar-divider"></div>', unsafe_allow_html=True)

if menu == "dashboard":
    render_dashboard_page()
elif menu == "contracts":
    render_contracts_page()
elif menu == "new_contract":
    render_new_contract_page()
elif menu == "activities":
    render_activities_page()
elif menu == "ai":
    render_ai_agent_page()
else:
    render_info_page()
