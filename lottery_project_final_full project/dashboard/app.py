"""
NY Lottery Analytics Dashboard - Streamlit Application

A local, interactive dashboard for exploring NY Lottery data.
This is for educational and entertainment purposes only.

DISCLAIMER:
- Lottery games are random and independent events
- No analysis can predict future outcomes
- Past results do not influence future draws
- Please gamble responsibly

Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.frequency import FrequencyAnalyzer
from src.analytics.hotcold import HotColdAnalyzer
from src.analytics.trends import TrendAnalyzer
from src.analytics.probability import ProbabilityCalculator
from src.analytics.monte_carlo import MonteCarloSimulator
from src.analytics.strategy import StrategyExplorer

# Page configuration
st.set_page_config(
    page_title="NY Lottery Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .disclaimer {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
</style>
""", unsafe_allow_html=True)

# Database paths
DB_PATH = PROJECT_ROOT / "data" / "lottery_star.db"
DB_SIMPLE_PATH = PROJECT_ROOT / "data" / "lottery.db"

# Game configurations
GAMES = {
    'mega_millions': {'name': 'Mega Millions', 'main_pool': 70, 'pick': 5, 'bonus_pool': 25},
    'powerball': {'name': 'Powerball', 'main_pool': 69, 'pick': 5, 'bonus_pool': 26},
    'take5': {'name': 'Take 5', 'main_pool': 39, 'pick': 5, 'bonus_pool': 0},
    'cash4life': {'name': 'Cash4Life', 'main_pool': 60, 'pick': 5, 'bonus_pool': 4},
    'ny_lotto': {'name': 'NY Lotto', 'main_pool': 59, 'pick': 6, 'bonus_pool': 0},
}

@st.cache_resource
def get_analyzers():
    """Initialize analyzer objects."""
    db_str = str(DB_PATH)
    return {
        'frequency': FrequencyAnalyzer(db_str),
        'hotcold': HotColdAnalyzer(db_str),
        'trends': TrendAnalyzer(db_str),
        'probability': ProbabilityCalculator(),
        'monte_carlo': MonteCarloSimulator(seed=42),
        'strategy': StrategyExplorer(db_str)
    }

@st.cache_data
def get_game_stats():
    """Get basic statistics for all games."""
    if not DB_PATH.exists():
        return None
    
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT 
        dg.game_name,
        COUNT(DISTINCT fsd.draw_date) as total_draws,
        MIN(fsd.draw_date) as first_draw,
        MAX(fsd.draw_date) as last_draw
    FROM fact_set_draws fsd
    JOIN dim_game dg ON fsd.game_id = dg.game_id
    GROUP BY dg.game_name
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def check_data_exists():
    """Check if data has been loaded."""
    return DB_PATH.exists() and DB_SIMPLE_PATH.exists()

# ============== MAIN APP ==============

def main():
    # Header
    st.markdown('<h1 class="main-header">🎯 NY Lottery Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Disclaimer
    st.markdown("""
    <div class="disclaimer">
        <strong>⚠️ Important Disclaimer:</strong> This dashboard is for <strong>educational and entertainment purposes only</strong>.
        Lottery games are random and independent events. No analysis can predict future outcomes. 
        Past results do not influence future draws. Please gamble responsibly.
    </div>
    """, unsafe_allow_html=True)
    
    # Check data
    if not check_data_exists():
        st.error("❌ Database not found! Please run the data pipeline first:")
        st.code("python run_pipeline.py", language="bash")
        st.stop()
    
    # Sidebar
    st.sidebar.title("🎮 Navigation")
    
    page = st.sidebar.radio(
        "Select Page",
        ["📊 Overview", "🔢 Frequency Analysis", "🔥 Hot/Cold Numbers", 
         "📈 Time Trends", "🎲 Probability Calculator", "🎰 Monte Carlo Simulation",
         "📚 About"]
    )
    
    # Load analyzers
    analyzers = get_analyzers()
    
    if page == "📊 Overview":
        render_overview(analyzers)
    elif page == "🔢 Frequency Analysis":
        render_frequency_analysis(analyzers)
    elif page == "🔥 Hot/Cold Numbers":
        render_hotcold_analysis(analyzers)
    elif page == "📈 Time Trends":
        render_trends_analysis(analyzers)
    elif page == "🎲 Probability Calculator":
        render_probability_calculator(analyzers)
    elif page == "🎰 Monte Carlo Simulation":
        render_monte_carlo(analyzers)
    elif page == "📚 About":
        render_about()

def render_overview(analyzers):
    """Render overview page."""
    st.header("📊 Data Overview")
    
    stats = get_game_stats()
    if stats is None or stats.empty:
        st.warning("No data available. Please run the pipeline.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Games", len(stats))
    with col2:
        st.metric("Total Draws", f"{stats['total_draws'].sum():,}")
    with col3:
        earliest = pd.to_datetime(stats['first_draw'].min()).strftime('%Y-%m-%d')
        st.metric("Earliest Data", earliest)
    with col4:
        latest = pd.to_datetime(stats['last_draw'].max()).strftime('%Y-%m-%d')
        st.metric("Latest Data", latest)
    
    st.divider()
    
    # Game breakdown
    st.subheader("📋 Games Summary")
    
    for _, row in stats.iterrows():
        game = row['game_name']
        if game in GAMES:
            with st.expander(f"🎯 {GAMES[game]['name']}", expanded=True):
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Draws", f"{row['total_draws']:,}")
                c2.metric("First Draw", row['first_draw'])
                c3.metric("Last Draw", row['last_draw'])
                
                # Quick frequency chart
                freq = analyzers['frequency'].get_set_draw_frequencies(game)
                if not freq.empty:
                    fig = px.bar(
                        freq.head(15), 
                        x='number', y='count',
                        title="Top 15 Most Frequent Numbers",
                        labels={'number': 'Number', 'count': 'Frequency'}
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)

def render_frequency_analysis(analyzers):
    """Render frequency analysis page."""
    st.header("🔢 Frequency Analysis")
    
    # Game selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        game = st.selectbox(
            "Select Game",
            options=list(GAMES.keys()),
            format_func=lambda x: GAMES[x]['name']
        )
    
    with col2:
        date_range = st.date_input(
            "Date Range (optional)",
            value=[],
            help="Leave empty for all time"
        )
    
    start_date = date_range[0].isoformat() if len(date_range) >= 1 else None
    end_date = date_range[1].isoformat() if len(date_range) >= 2 else None
    
    # Get frequency data
    freq_df = analyzers['frequency'].get_set_draw_frequencies(game, start_date, end_date)
    
    if freq_df.empty:
        st.warning("No data available for selected criteria.")
        return
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Main Numbers", "⭐ Bonus Numbers", "👥 Pairs", "📈 Distribution"])
    
    with tab1:
        st.subheader("Main Number Frequencies")
        
        # Bar chart
        fig = px.bar(
            freq_df, x='number', y='count',
            title=f"{GAMES[game]['name']} - Number Frequency",
            labels={'number': 'Number', 'count': 'Times Drawn'},
            color='count',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap grid
        st.subheader("Frequency Heatmap")
        pool_size = GAMES[game]['main_pool']
        grid_size = 10
        
        # Create grid data
        grid_data = np.zeros((pool_size // grid_size + 1, grid_size))
        for _, row in freq_df.iterrows():
            num = int(row['number'])
            if num <= pool_size:
                r, c = divmod(num - 1, grid_size)
                grid_data[r, c] = row['count']
        
        fig_heat = px.imshow(
            grid_data,
            labels=dict(x="Column", y="Row", color="Frequency"),
            title="Number Frequency Grid",
            color_continuous_scale='YlOrRd'
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Data table
        with st.expander("📋 View Data Table"):
            st.dataframe(freq_df, use_container_width=True)
    
    with tab2:
        if GAMES[game]['bonus_pool'] > 0:
            bonus_df = analyzers['frequency'].get_bonus_frequencies(game, start_date, end_date)
            
            if not bonus_df.empty:
                fig = px.bar(
                    bonus_df, x='bonus', y='count',
                    title=f"{GAMES[game]['name']} - Bonus Ball Frequency",
                    labels={'bonus': 'Bonus Number', 'count': 'Times Drawn'},
                    color='count',
                    color_continuous_scale='Oranges'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No bonus number data available.")
        else:
            st.info(f"{GAMES[game]['name']} does not have a bonus ball.")
    
    with tab3:
        st.subheader("Most Common Number Pairs")
        pairs_df = analyzers['frequency'].get_pair_frequencies(game, top_n=20)
        
        if not pairs_df.empty:
            pairs_df['pair'] = pairs_df.apply(lambda r: f"{int(r['num1'])}-{int(r['num2'])}", axis=1)
            
            fig = px.bar(
                pairs_df, x='pair', y='count',
                title="Top 20 Number Pairs",
                labels={'pair': 'Number Pair', 'count': 'Times Together'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Sum Distribution")
        sum_df = analyzers['frequency'].get_sum_distribution(game)
        
        if not sum_df.empty:
            fig = px.histogram(
                sum_df, x='sum', y='count',
                title="Distribution of Number Sums",
                labels={'sum': 'Sum of Numbers', 'count': 'Frequency'},
                nbins=30
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Odd/Even distribution
        st.subheader("Odd/Even Distribution")
        oe_df = analyzers['frequency'].get_odd_even_distribution(game)
        
        if not oe_df.empty:
            oe_df['combo'] = oe_df.apply(lambda r: f"{int(r['odd_count'])} odd, {int(r['even_count'])} even", axis=1)
            
            fig = px.pie(
                oe_df, values='frequency', names='combo',
                title="Odd/Even Combinations"
            )
            st.plotly_chart(fig, use_container_width=True)

def render_hotcold_analysis(analyzers):
    """Render hot/cold numbers page."""
    st.header("🔥 Hot & Cold Number Analysis")
    
    st.info("""
    **Note:** Hot and cold numbers are based on recent frequency only. 
    They have **no predictive value** - every number has equal probability in each draw.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        game = st.selectbox(
            "Select Game",
            options=list(GAMES.keys()),
            format_func=lambda x: GAMES[x]['name'],
            key="hotcold_game"
        )
    
    with col2:
        days = st.slider("Lookback Period (days)", 7, 365, 30)
    
    # Get hot/cold data
    hc_data = analyzers['hotcold'].get_hot_cold_numbers(game, days=days, top_n=10)
    
    # Display hot and cold side by side
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Hot Numbers (Most Frequent)")
        if not hc_data['hot'].empty:
            fig = px.bar(
                hc_data['hot'], x='number', y='count',
                title=f"Top 10 Hot Numbers (Last {days} days)",
                color_discrete_sequence=['#ff6b6b']
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(hc_data['hot'][['number', 'count', 'percentage']], use_container_width=True)
    
    with col2:
        st.subheader("❄️ Cold Numbers (Least Frequent)")
        if not hc_data['cold'].empty:
            fig = px.bar(
                hc_data['cold'], x='number', y='count',
                title=f"Top 10 Cold Numbers (Last {days} days)",
                color_discrete_sequence=['#4dabf7']
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(hc_data['cold'][['number', 'count', 'percentage']], use_container_width=True)
    
    st.divider()
    
    # Overdue numbers
    st.subheader("⏰ Overdue Numbers")
    overdue_df = analyzers['hotcold'].get_overdue_numbers(game, top_n=10)
    
    if not overdue_df.empty:
        fig = px.bar(
            overdue_df, x='number', y='days_overdue',
            title="Numbers Not Drawn Longest",
            labels={'days_overdue': 'Days Since Last Appearance'},
            color='days_overdue',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.warning("""
        ⚠️ **Gambler's Fallacy Warning:** Just because a number hasn't appeared recently 
        doesn't mean it's "due" to appear. Each draw is independent!
        """)

def render_trends_analysis(analyzers):
    """Render time trends page."""
    st.header("📈 Time Trend Analysis")
    
    game = st.selectbox(
        "Select Game",
        options=list(GAMES.keys()),
        format_func=lambda x: GAMES[x]['name'],
        key="trends_game"
    )
    
    tabs = st.tabs(["📅 Day of Week", "📆 Monthly", "📊 Sum Trend", "🔄 Gap Analysis"])
    
    with tabs[0]:
        st.subheader("Day of Week Distribution")
        weekday_df = analyzers['trends'].get_weekday_distribution(game)
        
        if not weekday_df.empty:
            # Aggregate by weekday
            weekly_agg = weekday_df.groupby('weekday')['count'].sum().reset_index()
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly_agg['weekday'] = pd.Categorical(weekly_agg['weekday'], categories=day_order, ordered=True)
            weekly_agg = weekly_agg.sort_values('weekday')
            
            fig = px.bar(
                weekly_agg, x='weekday', y='count',
                title="Total Numbers Drawn by Day of Week",
                color='count',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:
        st.subheader("Monthly Statistics")
        monthly_df = analyzers['trends'].get_monthly_stats(game)
        
        if not monthly_df.empty:
            monthly_df['date'] = pd.to_datetime(monthly_df['year'].astype(str) + '-' + monthly_df['month'].astype(str).str.zfill(2) + '-01')
            
            fig = px.line(
                monthly_df, x='date', y='draw_count',
                title="Draws Per Month Over Time",
                labels={'draw_count': 'Number of Draws', 'date': 'Month'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[2]:
        st.subheader("Sum Trend Over Time")
        sum_df = analyzers['trends'].get_sum_trend(game)
        
        if not sum_df.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Scatter(x=sum_df['draw_date'], y=sum_df['total_sum'], 
                          mode='markers', name='Draw Sum', opacity=0.5),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(x=sum_df['draw_date'], y=sum_df['rolling_avg'],
                          mode='lines', name='30-Draw Rolling Avg', line=dict(width=2)),
                secondary_y=False
            )
            
            fig.update_layout(title="Sum of Drawn Numbers Over Time")
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[3]:
        st.subheader("Gap Analysis")
        gap_df = analyzers['trends'].get_gap_analysis(game)
        
        if not gap_df.empty:
            fig = px.scatter(
                gap_df, x='avg_gap', y='total_appearances',
                hover_data=['number'],
                title="Number Gap vs Frequency",
                labels={'avg_gap': 'Average Days Between Appearances', 
                       'total_appearances': 'Total Appearances'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("📋 Gap Statistics"):
                st.dataframe(gap_df.sort_values('avg_gap'), use_container_width=True)

def render_probability_calculator(analyzers):
    """Render probability calculator page."""
    st.header("🎲 Probability Calculator")
    
    calc = analyzers['probability']
    
    # Game comparison
    st.subheader("📊 Game Comparison")
    
    comparison = calc.compare_games()
    
    df_compare = pd.DataFrame(comparison)
    df_compare = df_compare[df_compare['game'].isin([g['name'] for g in GAMES.values()])]
    
    fig = px.bar(
        df_compare, x='game', y='jackpot_odds',
        title="Jackpot Odds by Game (Lower = Better Odds)",
        labels={'jackpot_odds': 'Odds (1 in X)', 'game': 'Game'},
        log_y=True,
        color='jackpot_odds',
        color_continuous_scale='RdYlGn_r'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Detailed odds
    st.subheader("🎯 Detailed Prize Odds")
    
    game = st.selectbox(
        "Select Game",
        options=list(GAMES.keys()),
        format_func=lambda x: GAMES[x]['name'],
        key="prob_game"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        odds, odds_str = calc.get_jackpot_odds(game)
        st.metric("Jackpot Odds", odds_str)
        
        prize_odds = calc.get_all_prize_odds(game)
        
        if prize_odds:
            st.write("**All Prize Tiers:**")
            for tier, info in prize_odds.items():
                st.write(f"- {info.get('match', tier)}: 1 in {info['odds']:,} → {info['prize']}")
    
    with col2:
        st.subheader("Expected Value Analysis")
        
        jackpot = st.number_input(
            "Current Jackpot (millions)", 
            min_value=1.0, max_value=2000.0, value=100.0, step=10.0
        )
        
        ev = calc.calculate_expected_value(game, jackpot)
        
        st.metric("Ticket Cost", f"${ev['ticket_cost']:.2f}")
        st.metric("Expected Value", f"${ev['expected_value']:.4f}")
        st.metric("Expected Loss Per Ticket", f"${ev['expected_loss']:.4f}", delta_color="inverse")
        st.metric("Return Percentage", f"{ev['return_percentage']:.2f}%")
        
        st.warning(f"**Note:** {ev['note']}")

def render_monte_carlo(analyzers):
    """Render Monte Carlo simulation page."""
    st.header("🎰 Monte Carlo Simulation")
    
    st.info("""
    Monte Carlo simulations run thousands of random lottery plays to demonstrate 
    mathematical expectations. They show what happens **on average** over many plays.
    """)
    
    sim = analyzers['monte_carlo']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        game = st.selectbox(
            "Select Game",
            options=['mega_millions', 'powerball', 'take5'],
            format_func=lambda x: {'mega_millions': 'Mega Millions', 
                                  'powerball': 'Powerball', 
                                  'take5': 'Take 5'}[x],
            key="mc_game"
        )
    
    with col2:
        tickets = st.number_input("Tickets Per Draw", min_value=1, max_value=100, value=10)
    
    with col3:
        simulations = st.number_input("Number of Simulations", min_value=1000, max_value=100000, value=10000, step=1000)
    
    if st.button("🚀 Run Simulation", type="primary"):
        with st.spinner("Running simulation..."):
            result = sim.simulate_plays(game, num_tickets=tickets, num_simulations=simulations)
        
        st.success("Simulation complete!")
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Total Spent", f"${result.total_spent:,.2f}")
        col2.metric("Total Won", f"${result.total_won:,.2f}")
        col3.metric("Net Result", f"${result.net_result:,.2f}", 
                   delta_color="normal" if result.net_result >= 0 else "inverse")
        col4.metric("ROI", f"{result.roi_percentage:.2f}%")
        
        # Wins breakdown
        if result.wins_by_tier:
            st.subheader("Wins by Prize Tier")
            wins_df = pd.DataFrame([
                {'tier': k, 'wins': v} 
                for k, v in sorted(result.wins_by_tier.items(), key=lambda x: -x[1])
            ])
            
            fig = px.bar(wins_df, x='tier', y='wins', title="Wins by Match Level")
            st.plotly_chart(fig, use_container_width=True)
        
        st.info(f"""
        **Results Summary:**
        - Simulated {result.simulations:,} total ticket plays
        - Jackpot wins: {result.jackpot_wins}
        - This demonstrates the mathematical reality: the house edge means consistent losses over time.
        """)
    
    st.divider()
    
    # Convergence test
    st.subheader("📉 ROI Convergence Over Time")
    
    if st.button("Run Convergence Test"):
        with st.spinner("Running convergence test..."):
            conv_df = sim.run_convergence_test(game, max_simulations=50000, check_points=25)
        
        fig = px.line(
            conv_df, x='simulations', y='roi_pct',
            title="ROI Convergence to Expected Value",
            labels={'simulations': 'Number of Plays', 'roi_pct': 'ROI %'}
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.add_hline(y=-50, line_dash="dot", line_color="red", 
                     annotation_text="Typical long-term ROI")
        st.plotly_chart(fig, use_container_width=True)

def render_about():
    """Render about page."""
    st.header("📚 About This Dashboard")
    
    st.markdown("""
    ### Purpose
    
    This dashboard provides **exploratory data analysis** of NY Lottery games.
    It is designed for **educational and entertainment purposes only**.
    
    ### What This Dashboard Does
    
    ✅ Analyzes historical lottery data  
    ✅ Calculates actual mathematical probabilities  
    ✅ Demonstrates long-term expected outcomes through simulation  
    ✅ Visualizes patterns in past results  
    
    ### What This Dashboard Does NOT Do
    
    ❌ Predict future lottery numbers  
    ❌ Provide any winning strategy  
    ❌ Improve your odds of winning  
    ❌ Identify "due" or "hot" numbers with predictive value  
    
    ### Important Concepts
    
    **Independence:** Each lottery draw is completely independent of previous draws. 
    The balls have no memory.
    
    **Gambler's Fallacy:** The mistaken belief that if something happens more frequently 
    than normal, it will happen less frequently in the future (or vice versa).
    
    **Expected Value:** On average, you will lose money playing the lottery. 
    This is mathematically guaranteed by the game design.
    
    ### Data Source
    
    All data is sourced from the **NY Open Data Portal** via official Socrata APIs.
    
    ### Technologies Used
    
    - **Python** for data processing
    - **SQLite** for data storage
    - **Streamlit** for the dashboard
    - **Plotly** for visualizations
    - **Pandas/NumPy** for analysis
    
    ---
    
    **Remember:** The lottery is entertainment. Only play what you can afford to lose.
    """)

if __name__ == "__main__":
    main()
