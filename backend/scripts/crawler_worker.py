# backend/scripts/crawler_worker.py
import os
import sys
import json
import logging
import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from backend.services.data_fetcher import get_data_fetcher
from backend.services.snapshot import MetricsCalculator, SnapshotService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CrawlerWorker")

STORAGE_DIR = Path("backend/data/storage")
DETAILS_DIR = STORAGE_DIR / "details"

class CrawlerWorker:
    def __init__(self):
        self.fetcher = get_data_fetcher()
        self.calculator = MetricsCalculator()
        self.snapshot_service = SnapshotService()
        
        # Ensure directories exist
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        DETAILS_DIR.mkdir(parents=True, exist_ok=True)

    async def run(self, test_mode=False):
        logger.info("Starting Crawler Worker v4.0...")
        
        # 1. Fetch market indices
        await self.update_indices()
        
        # 1.5 Prepare benchmark data for SnapshotService
        logger.info("Preparing benchmark data for calculations...")
        bench_df = self.fetcher.get_benchmark_data("000300")
        if bench_df is not None:
            bench_df['benchmark_return'] = bench_df['close'].pct_change()
            self.snapshot_service._benchmark_data = bench_df
        
        # 2. Fetch candidate funds
        # In test mode, we only process a few funds
        funds = self.fetcher.get_all_fund_info()
        candidates = self.fetcher.filter_candidate_funds()
        
        if test_mode:
            candidates = candidates[:10]
            logger.info(f"Test mode: processing {len(candidates)} funds")
        
        processed_funds = []
        
        # 3. Process each fund
        total = len(candidates)
        for idx, fund_dict in enumerate(candidates):
            code = fund_dict['code']
            name = fund_dict['name']
            try:
                logger.info(f"[{idx+1}/{total}] Processing {code} {name}...")
                fund_detail = await self.process_single_fund(code, name)
                if fund_detail:
                    processed_funds.append({
                        "code": fund_detail["code"],
                        "name": fund_detail["name"],
                        "nav_date": fund_detail["nav_date"],
                        "return_1y": fund_detail["metrics"].get("return_1y", 0),
                        "max_drawdown_1y": fund_detail["metrics"].get("max_drawdown", 0),
                        "sharpe_1y": fund_detail["metrics"].get("sharpe", 0),
                        "themes": fund_detail.get("themes", []),
                        "status": "active"
                    })
                    # Save to individual file
                    self.save_json(DETAILS_DIR / f"{code}.json", fund_detail)
            except Exception as e:
                logger.error(f"Failed to process {code}: {e}")

        # 4. Save aggregated fund list
        self.save_json(STORAGE_DIR / "fund_list.json", processed_funds)
        logger.info(f"Crawler Worker completed. Processed {len(processed_funds)} funds.")

    async def update_indices(self):
        logger.info("Updating market indices...")
        indices = ["000300", "000001", "399006"] # HS300, SSE, GEM
        index_data = {}
        for symbol in indices:
            df = self.fetcher.get_benchmark_data(symbol)
            if df is not None:
                # Convert to highcharts format [timestamp, value]
                history = [[int(row['date'].timestamp() * 1000), float(row['close'])] for _, row in df.iterrows()]
                index_data[symbol] = {
                    "symbol": symbol,
                    "history": history[-500:] # Last 500 days
                }
        self.save_json(STORAGE_DIR / "indices.json", index_data)

    async def process_single_fund(self, code: str, name: str):
        nav_df = self.fetcher.get_fund_nav(code)
        if nav_df is None or len(nav_df) < 20:
            return None
            
        # Calculate metrics using SnapshotService logic
        metrics = self.snapshot_service._calculate_fund_metrics(code, nav_df)
        if not metrics:
            return None
            
        # Format history for charts
        history_nav = [[int(row['date'].timestamp() * 1000), float(row['nav'])] for _, row in nav_df.iterrows()]
        
        # Simulation of events (In reality would fetch from news/announcements)
        events = [
            {"date": "2025-09-24", "type": "macro", "desc": "央行降准政策发布"},
            {"date": "2026-01-20", "type": "dividend", "desc": "季度分红"}
        ]

        return {
            "code": code,
            "name": name,
            "nav_date": metrics.get("nav_date", ""),
            "metrics": metrics,
            "themes": self.fetcher.identify_themes(name),
            "history_nav": history_nav[-1000:], # Max 1000 days
            "holdings": [], # Placeholder for now
            "events": events
        }

    def save_json(self, path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

async def run_worker(test_mode=False):
    worker = CrawlerWorker()
    await worker.run(test_mode=test_mode)

if __name__ == "__main__":
    asyncio.run(run_worker(test_mode=True))
