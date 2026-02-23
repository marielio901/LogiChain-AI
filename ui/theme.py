from html import escape

import streamlit as st


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
  --lc-bg: #f3f7fc;
  --lc-bg-soft: #edf4fd;
  --lc-surface: #ffffff;
  --lc-border: #d8e4f3;
  --lc-shadow: 0 10px 28px rgba(23, 67, 121, 0.08);
  --lc-primary: #3f9dff;
  --lc-primary-strong: #2385eb;
  --lc-primary-soft: #e8f3ff;
  --lc-text: #10243b;
  --lc-muted: #5b6f87;
}

html, body, [class*="css"] {
  font-family: "Plus Jakarta Sans", "Manrope", sans-serif;
  color: var(--lc-text);
}

[data-testid="stAppViewContainer"],
.stApp {
  background: radial-gradient(circle at 14% -8%, #edf5ff 0%, #f6f9fd 44%, #f3f7fc 100%);
}

[data-testid="stMainBlockContainer"] {
  max-width: 100% !important;
  width: 100%;
  padding-top: 1.1rem;
  padding-left: 1.5rem;
  padding-right: 1.5rem;
  padding-bottom: 2.4rem;
}

h1, h2, h3, h4 {
  font-family: "Outfit", "Plus Jakarta Sans", sans-serif;
  color: #0f2740;
  letter-spacing: 0.01em;
}

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #f8fbff 0%, #f1f6fd 100%);
  border-right: 1px solid #d6e3f2;
}

section[data-testid="stSidebar"] > div {
  padding-top: 0.9rem;
}

.lc-sidebar-brand {
  padding: 0.34rem 0.16rem 0.5rem 0.16rem;
}

.lc-brand-title {
  font-family: "Outfit", sans-serif;
  font-size: 1.95rem;
  font-weight: 700;
  color: #102f4f;
  line-height: 1.15;
  letter-spacing: 0.01em;
}

.lc-brand-subtitle {
  font-size: 0.86rem;
  color: #56708c;
  margin-top: 0.24rem;
}

.lc-sidebar-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, #cad9ec 12%, #cad9ec 88%, transparent 100%);
  margin: 0.84rem 0 0.64rem 0;
}

.lc-nav-menu {
  display: flex;
  flex-direction: column;
  gap: 0.62rem;
  padding-top: 0.12rem;
}

.lc-nav-item {
  text-decoration: none !important;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-height: 46px;
  border-radius: 12px;
  border: 1px solid #d5e2f2;
  background: rgba(255, 255, 255, 0.82);
  padding: 0.56rem 0.76rem;
  transition: all 0.18s ease;
}

.lc-nav-item:hover {
  border-color: #95c3f6;
  background: #f4f9ff;
}

.lc-nav-item.is-active {
  background: linear-gradient(180deg, #eaf5ff 0%, #e4f1ff 100%);
  border-color: #56a7f8;
  box-shadow: inset 0 0 0 1px rgba(67, 150, 237, 0.2), 0 6px 14px rgba(74, 145, 217, 0.16);
}

.lc-nav-icon {
  width: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #6f89a4;
  font-size: 0.93rem;
}

.lc-nav-label {
  color: #2e4b68;
  font-size: 0.98rem;
  font-weight: 600;
  line-height: 1.2;
}

.lc-nav-item.is-active .lc-nav-label,
.lc-nav-item.is-active .lc-nav-icon {
  color: #0f5eb8;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] label {
  color: #59748f !important;
}

.stButton > button,
.stDownloadButton > button {
  border-radius: 11px;
  border: 1px solid #79b8f8;
  background: linear-gradient(135deg, #55acff 0%, #2e8fee 100%);
  color: #ffffff;
  font-weight: 600;
  letter-spacing: 0.01em;
  box-shadow: 0 8px 18px rgba(48, 130, 220, 0.24);
}

.stButton > button:hover,
.stDownloadButton > button:hover {
  border-color: #2788e9;
  background: linear-gradient(135deg, #4fa8ff 0%, #237fd9 100%);
}

.stButton > button[kind="secondary"] {
  background: #f8fbff;
  color: #1b5393;
  border-color: #9ec7f5;
  box-shadow: none;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stDateInput input,
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
  border-radius: 12px !important;
  border: 1px solid #d3e2f4 !important;
  background: #ffffff !important;
}

.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus,
.stDateInput input:focus {
  border-color: #74b4f8 !important;
  box-shadow: 0 0 0 1px #74b4f8 !important;
}

.stCheckbox {
  padding-top: 0.15rem;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 0.45rem;
  border-bottom: 1px solid #d7e4f4;
  padding-bottom: 0.2rem;
  overflow-x: auto;
}

.stTabs [data-baseweb="tab"] {
  border: 1px solid #d8e4f3;
  border-bottom: 0;
  border-radius: 12px 12px 0 0;
  background: #ffffff;
  color: #3f5871;
  padding: 0.48rem 0.82rem;
  font-weight: 600;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: #eaf4ff;
  color: #0e59b3;
  box-shadow: inset 0 -3px 0 #5eaeff;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 16px;
  border: 1px solid #dae6f4;
  background: #ffffff;
  box-shadow: var(--lc-shadow);
}

div[data-testid="stVerticalBlockBorderWrapper"] > div {
  padding: 0.95rem 1rem;
  background: #ffffff;
  border-radius: 15px;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stPlotlyChart"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stPlotlyChart"]) > div {
  background: #ffffff !important;
}

[data-testid="stPlotlyChart"],
[data-testid="stPlotlyChart"] > div,
[data-testid="stPlotlyChart"] .js-plotly-plot,
[data-testid="stPlotlyChart"] .plot-container,
[data-testid="stPlotlyChart"] .svg-container {
  background: #ffffff !important;
  border-radius: 12px;
}

[data-testid="stDataFrame"] > div {
  border-radius: 14px;
  border: 1px solid #d7e3f2;
  box-shadow: 0 8px 22px rgba(25, 69, 120, 0.08);
  overflow: hidden;
}

[data-testid="stAlert"] {
  border-radius: 12px;
  border: 1px solid #d8e4f3;
}

.lc-page-header {
  background: var(--lc-surface);
  border: 1px solid #d8e4f2;
  border-radius: 18px;
  box-shadow: var(--lc-shadow);
  padding: 1.08rem 1.18rem;
  margin-bottom: 0.95rem;
}

.lc-page-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.lc-page-title {
  margin: 0;
  font-size: 2rem;
  line-height: 1.1;
}

.lc-page-subtitle {
  margin: 0.45rem 0 0 0;
  max-width: 72ch;
  color: var(--lc-muted);
  font-size: 0.98rem;
}

.lc-badge {
  border-radius: 999px;
  border: 1px solid #a9cefa;
  background: #ecf6ff;
  color: #1b65c2;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.28rem 0.66rem;
  white-space: nowrap;
}

.lc-panel-header {
  margin: 0.95rem 0 0.62rem 0;
}

.lc-panel-title-row {
  display: flex;
  align-items: center;
  gap: 0.52rem;
}

.lc-panel-icon {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e9f4ff;
  color: #1a6ecb;
  font-family: "Outfit", sans-serif;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.lc-panel-title {
  margin: 0;
  font-size: 1.08rem;
  line-height: 1.2;
}

.lc-panel-subtitle {
  margin: 0.35rem 0 0 0;
  color: var(--lc-muted);
  font-size: 0.9rem;
}

.lc-empty-state {
  background: #ffffff;
  border: 1px dashed #a7cbf5;
  border-radius: 14px;
  padding: 0.95rem 1rem;
  box-shadow: 0 8px 20px rgba(27, 77, 133, 0.08);
  margin-top: 0.25rem;
}

.lc-empty-head {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.lc-empty-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #eaf4ff;
  color: #1f6dc9;
  font-family: "Outfit", sans-serif;
  font-size: 0.72rem;
  font-weight: 700;
}

.lc-empty-title {
  font-family: "Outfit", sans-serif;
  font-size: 1rem;
  font-weight: 600;
  color: #153454;
}

.lc-empty-description {
  margin: 0.48rem 0 0 0;
  color: #506a84;
  font-size: 0.9rem;
}

.lc-kpi-card {
  background: #ffffff;
  border: 1px solid #dae7f5;
  border-radius: 16px;
  box-shadow: 0 10px 24px rgba(23, 65, 111, 0.08);
  padding: 0.95rem 1rem;
  min-height: 124px;
  margin-bottom: 0.8rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.lc-kpi-head {
  display: flex;
  align-items: center;
  gap: 0.62rem;
}

.lc-kpi-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #ebf5ff;
  color: #2479d7;
  font-family: "Outfit", sans-serif;
  font-size: 0.74rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.lc-kpi-label {
  font-size: 0.86rem;
  font-weight: 600;
  color: #3f5872;
  line-height: 1.2;
}

.lc-kpi-value {
  margin-top: 0.68rem;
  font-family: "Outfit", sans-serif;
  font-size: 1.74rem;
  font-weight: 700;
  color: #102f4f;
  line-height: 1.07;
  overflow-wrap: anywhere;
}

.lc-chart-title {
  margin: 0.1rem 0 0.45rem 0;
  font-family: "Outfit", sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: #123252;
}

.lc-kanban-column-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
  margin: 0.15rem 0 0.62rem 0;
  color: #143352;
  font-family: "Outfit", sans-serif;
  font-size: 1.04rem;
  font-weight: 600;
}

.lc-kanban-count {
  min-width: 30px;
  height: 24px;
  border-radius: 999px;
  border: 1px solid #b8d6f5;
  background: #ebf5ff;
  color: #1566c1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 700;
}

.lc-kanban-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.38rem;
  margin-bottom: 0.36rem;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.lc-kanban-meta),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.lc-kanban-meta) > div {
  background: #ffffff !important;
}

.lc-kanban-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 24px;
  padding: 0.1rem 0.52rem;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 0.76rem;
  font-weight: 700;
  line-height: 1.2;
}

.lc-status-gerado {
  background: #eef6ff;
  border-color: #bed9f8;
  color: #1f6fbe;
}

.lc-status-assinado {
  background: #effcf7;
  border-color: #bae8d3;
  color: #1d8761;
}

.lc-status-protocolado {
  background: #f4f1ff;
  border-color: #d3c7fb;
  color: #6540bf;
}

.lc-status-em_vigor {
  background: #fff7eb;
  border-color: #f4d9b3;
  color: #b06a00;
}

.lc-status-finalizado {
  background: #edf6f2;
  border-color: #c4e0d3;
  color: #2f7a57;
}

.lc-risk-low {
  background: #edf9f3;
  border-color: #bfe6cf;
  color: #1b7c4f;
}

.lc-risk-medium {
  background: #fff9eb;
  border-color: #f5dfb0;
  color: #9f6200;
}

.lc-risk-high {
  background: #fff0ef;
  border-color: #f3c2bf;
  color: #b43933;
}

.lc-risk-unknown {
  background: #f3f6fa;
  border-color: #d6e0eb;
  color: #50657d;
}

@media (max-width: 960px) {
  [data-testid="stMainBlockContainer"] {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .lc-page-title {
    font-size: 1.65rem;
  }

  .lc-kpi-value {
    font-size: 1.48rem;
  }

  .stTabs [data-baseweb="tab"] {
    font-size: 0.84rem;
    padding: 0.44rem 0.68rem;
  }
}

@media (max-width: 640px) {
  .lc-page-header {
    padding: 0.94rem 0.92rem;
  }

  .lc-page-subtitle,
  .lc-panel-subtitle,
  .lc-empty-description {
    font-size: 0.86rem;
  }

  .lc-kpi-card {
    min-height: 108px;
  }

  .lc-chart-title {
    font-size: 0.98rem;
  }
}
</style>
"""


def _initials(text: str, fallback: str = "LC") -> str:
    tokens = [token for token in text.replace("-", " ").replace("_", " ").split() if token]
    initials = "".join(token[0] for token in tokens[:2]).upper()
    if len(initials) == 1:
        initials += "X"
    return initials or fallback


def apply_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str, badge: str | None = None) -> None:
    badge_html = f'<span class="lc-badge">{escape(badge)}</span>' if badge else ""
    subtitle_html = f'<p class="lc-page-subtitle">{escape(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f"""
        <section class="lc-page-header">
          <div class="lc-page-title-row">
            <h1 class="lc-page-title">{escape(title)}</h1>
            {badge_html}
          </div>
          {subtitle_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_panel_header(title: str, subtitle: str | None = None, icon: str | None = None) -> None:
    icon_token = _initials(icon or title, fallback="HD")
    subtitle_html = f'<p class="lc-panel-subtitle">{escape(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f"""
        <section class="lc-panel-header">
          <div class="lc-panel-title-row">
            <span class="lc-panel-icon">{escape(icon_token)}</span>
            <h3 class="lc-panel-title">{escape(title)}</h3>
          </div>
          {subtitle_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, description: str, icon: str = "info") -> None:
    icon_token = _initials(icon, fallback="IN")
    st.markdown(
        f"""
        <section class="lc-empty-state">
          <div class="lc-empty-head">
            <span class="lc-empty-icon">{escape(icon_token)}</span>
            <span class="lc-empty-title">{escape(title)}</span>
          </div>
          <p class="lc-empty-description">{escape(description)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <section class="lc-sidebar-brand">
          <div class="lc-brand-title">LogiChain AI</div>
          <div class="lc-brand-subtitle">Contract Intelligence Platform</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
