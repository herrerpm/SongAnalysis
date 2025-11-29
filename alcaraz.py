import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURATION & DESIGN SYSTEM ---
st.set_page_config(page_title="Sonic DNA", page_icon="⚡", layout="wide")

# The "Neon Glass" Design System
st.markdown("""
<style>
    /* 1. BACKGROUND: Deep Void with Aurora Gradients */
    .stApp {
        background-color: #000000;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(111, 0, 255, 0.15) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(0, 212, 255, 0.15) 0%, transparent 40%);
        background-attachment: fixed;
    }

    /* 2. GLASS CARDS (The Container for everything) */
    div[data-testid="stMetric"], div[class*="stPlotlyChart"], div.css-1r6slb0 {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 24px -1px rgba(0, 0, 0, 0.2) !important;
    }

    /* 3. NEON TYPOGRAPHY */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #ffffff !important;
        letter-spacing: -0.02em;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.2);
    }
    
    p, label, span {
        color: #8F9BB3 !important;
        font-size: 0.9rem;
    }

    /* 4. METRIC VALUES (The "Wow" Numbers) */
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #A0A0A0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* 5. SELECTBOX STYLING */
    .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 10px;
    }
    
    /* Remove Plotly Modebar */
    .modebar { display: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    
    # 1. Convert timestamp to datetime
    df['ts'] = pd.to_datetime(df['ts'])
    
    # 2. Handle Timezone Conversion (UTC -> CST/Chicago)
    if df['ts'].dt.tz is None:
        df['ts'] = df['ts'].dt.tz_localize('UTC')
    df['ts'] = df['ts'].dt.tz_convert('America/Chicago')
    df['date'] = df['ts'].dt.date
    
    # 3. Normalize Audio Features
    features = ['energy', 'brightness', 'rhythm_ratio', 'dynamic_range', 'tempo']
    for col in features:
        if col in df.columns:
            min_v, max_v = df[col].min(), df[col].max()
            if max_v != min_v:
                df[f'{col}_norm'] = (df[col] - min_v) / (max_v - min_v)
            else:
                df[f'{col}_norm'] = 0

    # 4. Map Pitch Class (Key/Dominant Note)
    # If explicit 'dominant_note' exists, use it. Otherwise map 'key' (0-11).
    if 'dominant_note' in df.columns:
        df['music_key'] = df['dominant_note']
    elif 'key' in df.columns:
        # Standard Pitch Class Notation
        pitch_map = {
            0: 'C', 1: 'C♯', 2: 'D', 3: 'D♯', 4: 'E', 5: 'F', 
            6: 'F♯', 7: 'G', 8: 'G♯', 9: 'A', 10: 'A♯', 11: 'B', -1: 'Unknown'
        }
        df['music_key'] = df['key'].map(pitch_map)
    else:
        df['music_key'] = "Unknown"

    return df

# --- 3. UI LAYOUT ---

# HEADER
c1, c2 = st.columns([1, 8])
with c1:
    st.markdown("# ⚡")
with c2:
    st.title("Sonic DNA")
    st.markdown("INTERACTIVE AUDIO INTELLIGENCE SYSTEM")

st.markdown("---")

uploaded_file = st.file_uploader("📂 INJECT DATASET (CSV)", type="csv")

if uploaded_file:
    df = load_data(uploaded_file)

    # === SECTION 1: THE MACRO VIEW ===
    st.subheader("1. Global Frequency")
    
    # KPI Grid
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Stream Time", f"{int(df['ms_played'].sum()/3600000):,}h")
    k2.metric("Library Size", f"{df['master_metadata_track_name'].nunique():,} Tracks")
    
    if 'master_metadata_album_artist_name' in df.columns:
        top_artist = df['master_metadata_album_artist_name'].mode()[0]
    else:
        top_artist = "N/A"
    k3.metric("Top Artist", top_artist)
    
    # Calculate "Focus Hour" (CST)
    peak_hour = df['ts'].dt.hour.mode()[0]
    am_pm = "AM" if peak_hour < 12 else "PM"
    display_hour = peak_hour if peak_hour <= 12 else peak_hour - 12
    display_hour = 12 if display_hour == 0 else display_hour
    k4.metric("Peak Focus Hour", f"{display_hour}:00 {am_pm}")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # SPLIT LAYOUT: TOP SONGS (Left) | TIME RADAR (Right)
    col_top, col_radar = st.columns([1, 1])

    with col_top:
        st.markdown("### 🏆 Top 5 Recurring Tracks")
        top_5 = df.groupby('master_metadata_track_name')['ms_played'].sum().reset_index()
        top_5 = top_5.sort_values('ms_played', ascending=False).head(5)
        
        for idx, row in enumerate(top_5.iterrows()):
            r = row[1]
            track_name = r['master_metadata_track_name']
            if len(track_name) > 35:
                track_name = track_name[:32] + "..."
                
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.05); padding:10px 15px; margin-bottom:10px; border-radius:10px; border:1px solid rgba(255,255,255,0.1); display:flex; align-items:center; justify-content:space-between;">
                <div style="display:flex; align-items:center; gap:15px;">
                    <h3 style="margin:0; font-size:1.2rem; color:#00D4FF !important;">#{idx+1}</h3>
                    <p style="color:white !important; font-weight:bold; margin:0;">{track_name}</p>
                </div>
                <p style="font-size:0.8rem; color:#888; margin:0;">{int(r['ms_played']/60000)} mins</p>
            </div>
            """, unsafe_allow_html=True)

    with col_radar:
        st.markdown("### ⏰ Circadian Rhythm (CST)")
        hourly_counts = df['ts'].dt.hour.value_counts().sort_index()
        hourly_counts = hourly_counts.reindex(range(24), fill_value=0)
        
        hours_labels = [f"{h if h<=12 else h-12}{'am' if h<12 else 'pm'}" for h in range(24)]
        hours_labels[0] = "12am"
        hours_labels[12] = "12pm"

        values = hourly_counts.values.tolist()
        values += values[:1]
        theta = hours_labels + [hours_labels[0]]

        fig_clock = go.Figure(go.Scatterpolar(
            r=values, theta=theta, fill='toself', line_color='#B026FF',
            fillcolor='rgba(176, 38, 255, 0.3)', mode='lines'
        ))

        fig_clock.update_layout(
            polar=dict(
                radialaxis=dict(visible=False),
                angularaxis=dict(
                    direction="clockwise", period=24, gridcolor="rgba(255,255,255,0.1)",
                    linecolor="rgba(255,255,255,0.1)", tickfont=dict(color="#8F9BB3", size=10)
                ),
                bgcolor="rgba(0,0,0,0)"
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20, l=40, r=40),
            showlegend=False, height=300
        )
        st.plotly_chart(fig_clock, use_container_width=True)

    # --- NEW CHART: MUSICAL KEY HISTOGRAM ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🎹 Musical Identity: Dominant Keys")
    
    # 1. Aggregate Data
    if 'music_key' in df.columns:
        key_counts = df['music_key'].value_counts().reset_index()
        key_counts.columns = ['Key', 'Count']
        
        # 2. Filter out 'Unknown' if strictly needed, or keep it
        key_counts = key_counts[key_counts['Key'] != 'Unknown']

        # 3. Create Bar Chart
        fig_keys = px.bar(
            key_counts, 
            x='Key', 
            y='Count',
            color='Count', # Gradient effect based on frequency
            color_continuous_scale=['#2c074f', '#B026FF', '#00D4FF'] # Deep Purple to Cyan
        )
        
        fig_keys.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title=None,
            yaxis_title=None,
            coloraxis_showscale=False,
            margin=dict(t=10, b=10),
            hovermode="x unified"
        )
        st.plotly_chart(fig_keys, use_container_width=True)
    else:
        st.info("No 'key' or 'dominant_note' data found in CSV.")

    st.markdown("---")

    # === SECTION 2: THE DEEP DIVE ===
    st.subheader("2. Track Inspector")
    
    top_tracks_list = df['master_metadata_track_name'].value_counts().head(50).index.tolist()
    selected_track = st.selectbox("Select a Track to Analyze:", top_tracks_list)
    track_df = df[df['master_metadata_track_name'] == selected_track]
    
    col_viz1, col_viz2 = st.columns([1, 2])
    
    with col_viz1:
        st.markdown(f"### 🧬 DNA: {selected_track}")
        radar_cols = ['energy_norm', 'brightness_norm', 'rhythm_ratio_norm', 'dynamic_range_norm']
        available_cols = [c for c in radar_cols if c in track_df.columns]
        
        if available_cols:
            track_features = track_df[available_cols].mean().values.tolist()
            track_features += track_features[:1]
            labels = [c.replace('_norm','').capitalize() for c in available_cols]
            labels += labels[:1]

            fig_radar = go.Figure(data=go.Scatterpolar(
                r=track_features, theta=labels, fill='toself',
                line_color='#00D4FF', fillcolor='rgba(0, 212, 255, 0.2)'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 1], gridcolor="rgba(255,255,255,0.1)", showticklabels=False),
                    bgcolor="rgba(0,0,0,0)"
                ),
                paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20), showlegend=False
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.warning("Audio features not found in dataset.")
        
        st.metric("Total Plays", len(track_df))
        if 'skipped' in track_df.columns:
            skip_pct = (track_df['skipped'].sum() / len(track_df)) * 100
            st.metric("Skip Probability", f"{skip_pct:.1f}%")

    with col_viz2:
        st.markdown(f"### 📅 Timeline: {selected_track}")
        daily_plays = track_df.groupby('date').size().reset_index(name='plays')
        
        fig_line = px.area(daily_plays, x='date', y='plays', template='plotly_dark')
        fig_line.update_traces(line_color='#B026FF', fill='tozeroy', fillcolor='rgba(176, 38, 255, 0.1)')
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title=None, yaxis_title="Plays", margin=dict(t=0, l=0, r=0, b=0),
            hovermode="x unified"
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.markdown("### 📱 Platform Context")
        if 'platform' in track_df.columns:
            platform_counts = track_df['platform'].value_counts().reset_index()
            platform_counts.columns = ['platform_name', 'count']
            
            fig_bar = px.bar(
                platform_counts, x='platform_name', y='count', color='platform_name',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, margin=dict(t=0, b=0), xaxis_title=None, yaxis_title=None
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # === SECTION 3: THE SONIC RACE ===
    st.subheader("3. The Sonic Race")
    st.markdown("Monthly cumulative listening history. Press **Play** to watch the leaderboard evolve.")

    top_20_global = df['master_metadata_track_name'].value_counts().head(20).index.tolist()
    race_df = df[df['master_metadata_track_name'].isin(top_20_global)].copy()

    race_df['month'] = race_df['ts'].dt.to_period('M')
    monthly_counts = race_df.groupby(['month', 'master_metadata_track_name']).size().reset_index(name='monthly_plays')
    pivot_race = monthly_counts.pivot(index='month', columns='master_metadata_track_name', values='monthly_plays').fillna(0)
    cumsum_race = pivot_race.cumsum()
    
    race_final = cumsum_race.reset_index().melt(id_vars='month', var_name='track', value_name='total_plays')
    race_final['month_str'] = race_final['month'].astype(str)
    
    fig_race = px.bar(
        race_final, x="total_plays", y="track", animation_frame="month_str",
        animation_group="track", orientation="h",
        range_x=[0, race_final['total_plays'].max() * 1.1],
        color="track", color_discrete_sequence=px.colors.qualitative.Bold,
    )

    fig_race.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, l=0, r=0, b=0), xaxis_title="Cumulative Plays", yaxis_title=None,
        showlegend=False, height=600, yaxis={'categoryorder':'total ascending'},
        font=dict(color="#ffffff"),
        updatemenus=[dict(
            type="buttons", bgcolor="rgba(0,0,0,0.5)", bordercolor="#ffffff",
            font=dict(color="#ffffff"),
            buttons=[dict(label="▶ Play", method="animate", args=[None, dict(frame=dict(duration=800, redraw=True), fromcurrent=True)])]
        )]
    )
    
    fig_race.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig_race.update_yaxes(showgrid=False)
    st.plotly_chart(fig_race, use_container_width=True)

else:
    st.info("Waiting for data injection...")