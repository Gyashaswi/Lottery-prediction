import sqlite3
from src.ingest.config import DB_SIMPLE, DB_STAR
from src.ingest.logger import get_logger

log = get_logger("indices")

def run_sql(db_path, stmts):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    for s in stmts:
        cur.execute(s)
    con.commit()
    con.execute("VACUUM;")
    con.close()

def main():
    run_sql(DB_SIMPLE, [
        "CREATE INDEX IF NOT EXISTS idx_mm_date        ON mega_millions_draws(draw_date);",
        "CREATE INDEX IF NOT EXISTS idx_pb_date        ON powerball_draws(draw_date);",
        "CREATE INDEX IF NOT EXISTS idx_t5_date        ON take5_draws(draw_date);",
        "CREATE INDEX IF NOT EXISTS idx_c4l_date       ON cash4life_draws(draw_date);",
        "CREATE INDEX IF NOT EXISTS idx_nyl_date       ON ny_lotto_draws(draw_date);",
        "CREATE INDEX IF NOT EXISTS idx_num_date_sess  ON numbers_draws(draw_date, session);",
        "CREATE INDEX IF NOT EXISTS idx_w4_date_sess   ON win4_draws(draw_date, session);",
    ])
    log.info(f"[idx] built on {DB_SIMPLE}")

    run_sql(DB_STAR, [
        "CREATE INDEX IF NOT EXISTS idx_fs_draws       ON fact_set_draws(game_id, draw_date);",
        "CREATE INDEX IF NOT EXISTS idx_fsnums_all     ON fact_set_numbers(game_id, draw_date, position);",
        "CREATE INDEX IF NOT EXISTS idx_fdaily_all     ON fact_daily_draws(game_id, draw_date, session_id);",
        "CREATE INDEX IF NOT EXISTS idx_dim_date       ON dim_date(date, year, month, day);",
    ])
    log.info(f"[idx] built on {DB_STAR}")

if __name__ == "__main__":
    main()
