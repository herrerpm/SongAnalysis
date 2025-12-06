import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pycountry
import numpy as np
import os

st.set_page_config(page_title="Audio Analytics", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* 1. ANIMATIONS (The "Load on Scroll" feel) */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translate3d(0, 20px, 0); }
        to { opacity: 1; transform: translate3d(0, 0, 0); }
    }

    /* Apply animation to all main containers */
    .element-container, .stPlotlyChart {
        animation: fadeInUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) both;
    }

    /* 2. BACKGROUND */
    .stApp {
        background-color: #050505;
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(111, 0, 255, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 85% 30%, rgba(0, 212, 255, 0.08) 0%, transparent 50%);
        background-attachment: fixed;
        font-family: 'Inter', sans-serif;
    }

    /* 3. GLASS CARDS */
    div[data-testid="stMetric"], div[class*="stPlotlyChart"] {
        background: rgba(20, 20, 20, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    }

    /* ON HOVER: Lift up and Glow */
    div[data-testid="stMetric"]:hover, div[class*="stPlotlyChart"]:hover {
        transform: translateY(-5px);
        border-color: rgba(0, 212, 255, 0.3) !important;
        box-shadow: 0 10px 40px -10px rgba(0, 212, 255, 0.2) !important;
    }

    /* 4. CUSTOM TOP 5 TRACK CARD STYLES */
    .track-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 12px 15px;
        margin-bottom: 8px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
        cursor: default;
    }

    .track-card:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateX(5px);
        border-color: rgba(0, 212, 255, 0.5);
    }

    .track-rank { font-size: 1rem; color: #00D4FF; font-weight: bold; margin-right: 15px; }
    .track-title { font-weight: 500; color: #ffffff; }
    .track-duration { font-size: 0.8rem; color: #888; }

    /* 5. TYPOGRAPHY */
    h1, h2, h3 { color: #ffffff !important; font-weight: 800; letter-spacing: -0.5px; }
    p, label, span, div[data-testid="stMarkdownContainer"] p { color: #8F9BB3 !important; }

    /* 6. METRIC VALUES */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #FFFFFF 0%, #A0A0A0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* 7. SCROLLBAR */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #050505; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #00D4FF; }

    /* UTILS */
    .modebar { display: none !important; }
    .stFileUploader > div > div { background-color: rgba(255,255,255,0.02); border: 1px dashed rgba(255,255,255,0.2); }
</style>
""", unsafe_allow_html=True)


# --- 2. DATA ENGINE ---
@st.cache_data
def load_data(file):
    # pandas read_csv handles both file-like objects (uploads) and string paths (local files)
    df = pd.read_csv(file)

    # 1. Convert timestamp to datetime
    if 'ts' in df.columns:
        df['ts'] = pd.to_datetime(df['ts'])
        if df['ts'].dt.tz is None:
            df['ts'] = df['ts'].dt.tz_localize('UTC')
        df['ts'] = df['ts'].dt.tz_convert('America/Chicago')
        df['date'] = df['ts'].dt.date

    # 2. Normalize Audio Features
    features = ['energy', 'brightness', 'rhythm_ratio', 'dynamic_range', 'tempo']
    for col in features:
        if col in df.columns:
            min_v, max_v = df[col].min(), df[col].max()
            if max_v != min_v:
                df[f'{col}_norm'] = (df[col] - min_v) / (max_v - min_v)
            else:
                df[f'{col}_norm'] = 0

    return df


def style_chart(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#8F9BB3"),
        hoverlabel=dict(bgcolor="#000000", bordercolor="#333333", font=dict(color="#FFFFFF", size=12))
    )
    return fig


def get_iso3(iso2):
    if not isinstance(iso2, str): return None
    if iso2 == 'XW': return None
    if iso2 == 'XK': return 'KOS'
    try:
        return pycountry.countries.get(alpha_2=iso2).alpha_3
    except:
        return None


# --- 3. UI LAYOUT ---

st.title("Audio Analytics ⚡")
st.markdown("Interact with your listening history. Hover over cards to inspect details.")

uploaded_file = st.file_uploader("", type="csv", help="Upload your Spotify History CSV")

# --- NEW LOGIC START ---
# Define your default file name here.
# Make sure this file exists in the same folder as this script.
DEFAULT_FILE_PATH = "streaming_data_with_artist_countries.csv"

df = None

if uploaded_file:
    df = load_data(uploaded_file)
elif os.path.exists(DEFAULT_FILE_PATH):
    df = load_data(DEFAULT_FILE_PATH)
    st.toast(f"Using default data from {DEFAULT_FILE_PATH}", icon="💾")
# --- NEW LOGIC END ---

# Change the condition from 'if uploaded_file:' to 'if df is not None:'
if df is not None:

    # === SECTION 1: THE DASHBOARD ===
    st.markdown("### 1. Global Frequency")

    # KPI Grid
    k1, k3, k4 = st.columns(3)

    if 'ms_played' in df.columns:
        total_hours = int(df['ms_played'].sum() / (3600000))
        k1.metric("Stream Time", f"{total_hours:,} hrs", delta="All time")
    else:
        k1.metric("Stream Time", "N/A")

    if 'master_metadata_album_artist_name' in df.columns:
        top_artist = df['master_metadata_album_artist_name'].mode()[0]
        artist_tracks = df[df['master_metadata_album_artist_name'] == top_artist][
            'master_metadata_track_name'].nunique()
        k3.metric("Top Artist", top_artist, delta=f"{artist_tracks} unique tracks")
    else:
        k3.metric("Top Artist", "N/A")

    if 'ts' in df.columns:
        peak_hour = df['ts'].dt.hour.mode()[0]
        am_pm = "AM" if peak_hour < 12 else "PM"
        display_hour = peak_hour if peak_hour <= 12 else peak_hour - 12
        display_hour = 12 if display_hour == 0 else display_hour
        k4.metric("Peak Vibe", f"{display_hour}:00 {am_pm}", delta="Most active")
    else:
        k4.metric("Peak Focus Hour", "N/A")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GLOBAL ORIGIN MAP ---
    if 'Country Code' in df.columns and 'Country' in df.columns:
        if 'Play Count' not in df.columns:
            country_stats = df.groupby(['Country Code', 'Country']).size().reset_index(name='Play Count')
        else:
            country_stats = df.groupby(['Country Code', 'Country'])['Play Count'].sum().reset_index()

        country_stats['iso_a3'] = country_stats['Country Code'].apply(get_iso3)
        country_stats['Log Scale'] = np.log10(country_stats['Play Count'].replace(0, 1))

        fig_map = px.choropleth(
            country_stats,
            locations="iso_a3",
            color="Log Scale",
            hover_name="Country",
            hover_data={"iso_a3": False, "Log Scale": False, "Play Count": ":,"},
            color_continuous_scale="Viridis",
        )

        fig_map.update_geos(
            showcountries=True, countrycolor="rgba(255, 255, 255, 0.1)",
            showcoastlines=False, showland=True, landcolor="#0F0F0F",
            showocean=False, bgcolor="rgba(0,0,0,0)",
            projection_type="natural earth"
        )

        fig_map.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=500, dragmode="pan", coloraxis_showscale=False)
        style_chart(fig_map)
        st.plotly_chart(fig_map, use_container_width=True)

    # SPLIT LAYOUT: TOP SONGS | TIME RADAR
    col_top, col_radar = st.columns([1, 1])

    with col_top:
        st.markdown("### 🏆 Replay Value")
        if 'ms_played' in df.columns:
            top_5 = df.groupby('master_metadata_track_name')['ms_played'].sum().reset_index()
            top_5 = top_5.sort_values('ms_played', ascending=False).head(5)

            for idx, row in enumerate(top_5.iterrows()):
                r = row[1]
                track_name = r['master_metadata_track_name']
                if isinstance(track_name, str) and len(track_name) > 35:
                    track_name = track_name[:32] + "..."

                # USING THE NEW CSS CLASS "track-card" FOR HOVER EFFECTS
                st.markdown(f"""
                <div class="track-card">
                    <div style="display:flex; align-items:center;">
                        <span class="track-rank">#{idx + 1}</span>
                        <span class="track-title">{track_name}</span>
                    </div>
                    <span class="track-duration">{int(r['ms_played'] / 60000)} mins</span>
                </div>
                """, unsafe_allow_html=True)

    with col_radar:
        with col_radar:
            st.markdown("### ⏰ Circadian Rhythm")
            if 'ts' in df.columns:
                hourly_counts = df['ts'].dt.hour.value_counts().sort_index().reindex(range(24), fill_value=0)

                hourly_df = hourly_counts.to_frame(name='Play Count')
                hourly_df['Hour'] = hourly_df.index

                fig_area = px.area(hourly_df, x='Hour', y='Play Count')

                fig_area.update_traces(
                    line_shape='spline',
                    line_color='#00D4FF',
                    fillcolor='rgba(0, 212, 255, 0.15)',
                    hovertemplate=(
                            '<b>Hour:</b> %{x}<br>' +
                            '<b>Total Plays:</b> %{y:,.0f}<extra></extra>'
                    )
                )

                fig_area.update_layout(
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=300,
                    xaxis=dict(
                        title="Hour of Day",
                        tickmode='array', tickvals=[0, 6, 12, 18, 23],
                        ticktext=['12am', '6am', '12pm', '6pm', '11pm'],
                        showgrid=False,
                    ),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False, title="Play Count"),
                    # Keep hovermode="x unified" to show a single box for the whole vertical line at the X value
                    hovermode="x unified"
                )
                style_chart(fig_area)
                st.plotly_chart(fig_area, use_container_width=True)

    # === SECTION 2: THE DEEP DIVE ===
    st.markdown("---")
    st.subheader("2. Track Inspector")

    top_tracks_list = df['master_metadata_track_name'].value_counts().head(50).index.tolist()
    # Check if list is not empty before selecting
    if top_tracks_list:
        selected_track = st.selectbox("Select Track:", top_tracks_list)
        track_df = df[df['master_metadata_track_name'] == selected_track]

        col_viz1, col_viz2 = st.columns([1, 2])

        with col_viz1:
            st.markdown(f"**DNA: {selected_track}**")
            radar_cols = ['energy_norm', 'brightness_norm', 'rhythm_ratio_norm', 'dynamic_range_norm', 'tempo_norm']
            available_cols = [c for c in radar_cols if c in track_df.columns]

            if available_cols:
                track_features = track_df[available_cols].mean().values.tolist()
                track_features += track_features[:1]  # Close loop
                labels = [c.replace('_norm', '').replace('_', ' ').title() for c in available_cols]
                labels += labels[:1]

                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=track_features, theta=labels, fill='toself',
                    line_color='#B026FF', fillcolor='rgba(176, 38, 255, 0.2)',
                ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1.1], showticklabels=False,
                                        gridcolor="rgba(255,255,255,0.1)"),
                        angularaxis=dict(tickfont=dict(size=10, color='#888'), rotation=90),
                        bgcolor="rgba(0,0,0,0)"
                    ),
                    margin=dict(t=30, b=30, l=40, r=40),
                    height=350,
                    showlegend=False
                )
                style_chart(fig_radar)
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("Audio features unavailable.")

        with col_viz2:
            st.markdown(f"**Trend: {selected_track}**")
            if 'date' in track_df.columns:
                daily_plays = track_df.groupby('date').size().reset_index(name='plays')
                fig_line = px.bar(daily_plays, x='date', y='plays')
                fig_line.update_traces(marker_color='#B026FF', marker_line_width=0, opacity=0.8)
                fig_line.update_layout(
                    xaxis_title=None, yaxis_title="Plays",
                    margin=dict(t=10, l=0, r=0, b=0),
                    height=350,
                    bargap=0.1
                )
                style_chart(fig_line)
                st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")
    # === SECTION 3: ANIMATED RACE ===
    st.subheader("3. The Audio Race")
    st.caption("Click 'Play' to watch the monthly leaderboard evolution.")

    # 1. DATA PREP
    top_n_global = df['master_metadata_track_name'].value_counts().head(12).index.tolist()
    race_df = df[df['master_metadata_track_name'].isin(top_n_global)].copy()

    if not race_df.empty:
        race_df['month'] = race_df['ts'].dt.to_period('M')

        monthly_counts = race_df.groupby(['month', 'master_metadata_track_name']).size().reset_index(
            name='monthly_plays')
        pivot_race = monthly_counts.pivot(index='month', columns='master_metadata_track_name',
                                          values='monthly_plays').fillna(0)
        cumsum_race = pivot_race.cumsum()
        race_final = cumsum_race.reset_index().melt(id_vars='month', var_name='track', value_name='total_plays')
        race_final['month_str'] = race_final['month'].astype(str)

        # 2. BUILD CHART
        neon_palette = [
            "#00D4FF", "#FF007A", "#B026FF", "#00FF94", "#FFD700",
            "#FF9100", "#0057FF", "#FF0000", "#00FFA3", "#D400FF"
        ]

        # Calculate dynamic range safely
        max_val = race_final['total_plays'].max()
        range_x_val = max_val * 1.15 if not pd.isna(max_val) else 10

        fig_race = px.bar(
            race_final, x="total_plays", y="track", animation_frame="month_str",
            animation_group="track", orientation="h", text="total_plays",
            range_x=[0, range_x_val],
            color="track", color_discrete_sequence=neon_palette,
        )

        # FIX: Rotation and Animation glitches
        fig_race.update_traces(
            texttemplate='%{text:,.0f}',
            textposition='outside',
            textangle=0,  # Force horizontal text
            cliponaxis=False,
            width=0.7
        )

        fig_race.layout.updatemenus = [
            dict(
                type="buttons", showactive=False, x=0, y=1.15,
                pad=dict(t=0, r=10),
                buttons=[dict(
                    label="▶ PLAY",
                    method="animate",
                    args=[None, dict(frame=dict(duration=400, redraw=True), fromcurrent=True)]
                )],
                bgcolor="#111", bordercolor="#333", borderwidth=1, font=dict(color="#fff")
            )
        ]

        fig_race.update_layout(
            margin=dict(t=0, l=0, r=0, b=0),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                zeroline=False,
                title="Cumulative Plays"
            ),
            yaxis=dict(
                showgrid=False,
                title=None,
                categoryorder="total ascending"  # Keeps tracks stable
            ),
            showlegend=False, height=550,
        )
        style_chart(fig_race)

        st.plotly_chart(fig_race, use_container_width=True)
    else:
        st.info("Not enough data for the Race Chart.")
else:
    st.markdown("""
    <div style='text-align: center; padding: 100px;'>
        <h3 style='opacity: 0.5;'>Waiting for data injection...</h3>
        <div style='margin-top: 20px; height: 2px; width: 200px; background: linear-gradient(90deg, transparent, #00D4FF, transparent); margin-left: auto; margin-right: auto;'></div>
        <p style='color: #666; margin-top: 10px; font-size: 0.8rem;'>Upload a CSV or add 'spotify_history.csv' to the app folder.</p>
    </div>
    """, unsafe_allow_html=True)