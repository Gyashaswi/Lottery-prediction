# 🎯 NY Lottery Analytics - Data Pipeline & Strategy Exploration

End-to-end data engineering and analytics project for NY Lottery games:
**Mega Millions, Powerball, Take 5, Cash4Life, NY Lotto, Numbers, Win4**

This repo showcases skills across **data collection → cleaning → analytics → visualization** with SQLite databases and a local Streamlit dashboard.

---

## ⚠️ Important Disclaimer

**This project is for educational and entertainment purposes only.**

- Lottery games are random and independent events
- No analysis or strategy can predict future outcomes
- Past results do not influence future draws
- The house always has a mathematical edge
- Please gamble responsibly

---

## Features

### Data Pipeline
- **Incremental API ingestion** from NY Open Data (Socrata CSV endpoints)
- **Robust data cleaning** (dates, number parsing, zero-padding)
- **Dual SQLite databases**:
  - `data/lottery.db` — flat tables per game (quick queries/dashboards)
  - `data/lottery_star.db` — normalized star schema (analytics)
- **Data quality checks** with hard fail on issues
- **Optimized indices** + VACUUM for performance

### Analytics Modules (`src/analytics/`)
- **Frequency Analysis** — Number occurrence statistics
- **Hot/Cold Numbers** — Recent frequency patterns (exploratory only)
- **Time Trends** — Seasonal patterns, day-of-week analysis
- **Probability Calculator** — Theoretical odds and expected values
- **Monte Carlo Simulations** — Long-term outcome modeling
- **Strategy Exploration** — Compare selection approaches (educational)

### Visualization
- **EDA Notebooks** — Comprehensive exploratory analysis
- **Streamlit Dashboard** — Interactive local visualization

---

## Architecture

```
NY Open Data APIs
      │
      ▼
  fetch_api.py ──▶ data/processed/*.csv
      │
      ▼
  clean_data.py ──▶ data/clean/*.csv
      │
      ├──▶ load_to_db.py ──▶ data/lottery.db
      │
      └──▶ load_to_star.py ─▶ data/lottery_star.db
              │
              ▼
         dq_checks.py ──▶ Quality validation
              │
              ▼
        build_indices.py ─▶ Performance optimization
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Data Pipeline

```bash
# Run complete pipeline
python run_pipeline.py

# Or run individual steps
python run_pipeline.py --step fetch
python run_pipeline.py --step clean
python run_pipeline.py --step load
python run_pipeline.py --step dq
```

### 3. Launch Dashboard

```bash
streamlit run dashboard/app.py
```

### 4. Explore Notebooks

```bash
jupyter notebook notebooks/
```

---

## Project Structure

```
lottery_project/
├── data/                       # Generated data (gitignored)
│   ├── processed/             # Raw API data
│   ├── clean/                 # Cleaned CSVs
│   ├── lottery.db             # Simple flat-table DB
│   └── lottery_star.db        # Normalized star schema DB
│
├── src/
│   ├── ingest/                # Data pipeline scripts
│   │   ├── fetch_api.py       # API data fetching
│   │   ├── clean_data.py      # Data cleaning
│   │   ├── load_to_db.py      # Flat DB loading
│   │   ├── load_to_star.py    # Star schema loading
│   │   ├── dq_checks.py       # Data quality
│   │   └── build_indices.py   # DB optimization
│   │
│   └── analytics/             # Analysis modules
│       ├── frequency.py       # Frequency analysis
│       ├── hotcold.py         # Hot/cold patterns
│       ├── trends.py          # Time trends
│       ├── probability.py     # Probability math
│       ├── monte_carlo.py     # Monte Carlo sims
│       └── strategy.py        # Strategy exploration
│
├── notebooks/                  # EDA Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_frequency_analysis.ipynb
│   └── 03_simulations.ipynb
│
├── dashboard/                  # Streamlit app
│   └── app.py
│
├── run_pipeline.py             # Master pipeline script
├── requirements.txt
└── README.md
```

---

## Games Covered

| Game | Type | Draw Days | Main Pool | Bonus |
|------|------|-----------|-----------|-------|
| Mega Millions | Set Draw | Tue, Fri | 5 of 70 | 1 of 25 |
| Powerball | Set Draw | Mon, Wed, Sat | 5 of 69 | 1 of 26 |
| Take 5 | Set Draw | Daily | 5 of 39 | None |
| Cash4Life | Set Draw | Daily | 5 of 60 | 1 of 4 |
| NY Lotto | Set Draw | Wed, Sat | 6 of 59 | None |
| Numbers | Daily | Twice Daily | 3 digits | Optional |
| Win4 | Daily | Twice Daily | 4 digits | Optional |

---

## Analytics Examples

### Frequency Analysis
```python
from src.analytics import FrequencyAnalyzer

analyzer = FrequencyAnalyzer()
freq = analyzer.get_set_draw_frequencies('powerball')
print(freq.head(10))
```

### Probability Calculations
```python
from src.analytics import ProbabilityCalculator

calc = ProbabilityCalculator()
odds, odds_str = calc.get_jackpot_odds('mega_millions')
print(f"Mega Millions jackpot odds: {odds_str}")
# Output: Mega Millions jackpot odds: 1 in 302,575,350
```

### Monte Carlo Simulation
```python
from src.analytics import MonteCarloSimulator

sim = MonteCarloSimulator(seed=42)
result = sim.simulate_plays('powerball', num_tickets=10, num_simulations=10000)
print(f"ROI: {result.roi_percentage}%")
```

---

## Technologies Used

- **Python 3.10+**
- **pandas** — Data manipulation
- **SQLite** — Local database storage
- **Streamlit** — Interactive dashboard
- **Plotly/Matplotlib** — Visualizations
- **NumPy/SciPy** — Numerical computations

---

## License

MIT License - See LICENSE file

---

## Author

Built as a portfolio project demonstrating:
- Data engineering pipelines
- Database design (flat + star schema)
- Statistical analysis
- Interactive visualization
- Clean, documented code

**Remember: Play responsibly. The lottery is entertainment, not investment.**
