# backend/database.py
"""
数据库模块 - SQLite 存储
"""

import sqlite3
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from .config import get_settings, ensure_data_dir

logger = logging.getLogger(__name__)


class Database:
    """线程安全的数据库单例"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        ensure_data_dir()
        settings = get_settings()
        self.db_path = settings.DATABASE_PATH
        self._local = threading.local()
        self._check_migrations()
        self._initialized = True
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def _check_migrations(self):
        """检查并执行数据库迁移"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 1. 初始化表
            self._init_tables(cursor)
            
            # 2. 获取当前版本
            cursor.execute("SELECT version FROM schema_version")
            row = cursor.fetchone()
            current_version = row[0] if row else 0
            
            # 3. 定义迁移任务
            # 版本号从 1 开始
            migrations = [
                # v1: 初始版本 (已经在 _init_tables 中创建)
                # v2: 为 fund_metrics 添加 return_1d 列 (示例，实际已在初始表中包含)
                (1, "初始版本", None),
                # (2, "添加 return_1d 到 fund_metrics", "ALTER TABLE fund_metrics ADD COLUMN return_1d REAL"),
            ]
            
            for version, description, sql in migrations:
                if version > current_version:
                    logger.info(f"正在执行数据库迁移 v{version}: {description}")
                    if sql:
                        cursor.execute(sql)
                    
                    # 更新版本号
                    cursor.execute("UPDATE schema_version SET version = ?, updated_at = CURRENT_TIMESTAMP", (version,))
                    if cursor.rowcount == 0:
                        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
                    conn.commit()
            
            logger.info("数据库迁移检查完成")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库迁移失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def _init_tables(self, cursor):
        """初始化基础数据库表"""
        # 版本管理表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 基金基础信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funds (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                fund_type TEXT,
                themes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 快照表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL,
                total_funds INTEGER DEFAULT 0,
                qualified_funds INTEGER DEFAULT 0,
                benchmark TEXT DEFAULT '000300.SH',
                status TEXT DEFAULT 'running',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        """)
        
        # 基金指标表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fund_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                name TEXT,
                score REAL,
                labels TEXT,
                reasons TEXT,
                themes TEXT,
                latest_nav REAL,
                nav_date TEXT,
                alpha REAL,
                beta REAL,
                sharpe REAL,
                annual_return REAL,
                volatility REAL,
                max_drawdown REAL,
                current_drawdown REAL,
                win_rate REAL,
                profit_loss_ratio REAL,
                return_1w REAL,
                return_1m REAL,
                return_3m REAL,
                return_6m REAL,
                return_1y REAL,
                return_1d REAL,
                data_days INTEGER,
                raw_metrics TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(id),
                UNIQUE(snapshot_id, code)
            )
        """)
        
        # AI 缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                content TEXT,
                model TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT
            )
        """)
        
        # 更新日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS update_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                funds_processed INTEGER DEFAULT 0,
                funds_qualified INTEGER DEFAULT 0,
                message TEXT,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        """)
        
        # 自选基金表 (新增)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT NOT NULL,
                fund_name TEXT,
                user_id TEXT DEFAULT 'default',
                notes TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fund_code, user_id)
            )
        """)
        
        # 净值历史缓存表 (新增)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nav_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT NOT NULL,
                nav_date TEXT NOT NULL,
                nav REAL,
                acc_nav REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fund_code, nav_date)
            )
        """)
        
        # 持仓模拟表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT NOT NULL,
                fund_name TEXT,
                user_id TEXT DEFAULT 'default',
                shares REAL NOT NULL,
                cost_price REAL NOT NULL,
                buy_date TEXT NOT NULL,
                sell_date TEXT,
                sell_price REAL,
                status TEXT DEFAULT 'holding',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fund_code, user_id, buy_date)
            )
        """)
        
        # 推荐历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                recommend_date TEXT NOT NULL,
                fund_code TEXT NOT NULL,
                fund_name TEXT,
                category TEXT,
                score REAL,
                nav_at_recommend REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(snapshot_id, fund_code, category)
            )
        """)
        
        # 定投计划表 (新增 Phase 7)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dca_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT NOT NULL,
                fund_name TEXT,
                user_id TEXT DEFAULT 'default',
                base_amount REAL NOT NULL,
                frequency TEXT DEFAULT 'weekly',
                day_of_week INTEGER, -- 0-6 (周一至周日)
                day_of_month INTEGER, -- 1-31
                is_active INTEGER DEFAULT 1,
                last_executed_at TEXT,
                next_scheduled_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fund_code, user_id)
            )
        """)
        
        # 定投执行记录表 (新增 Phase 7)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dca_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER,
                fund_code TEXT NOT NULL,
                fund_name TEXT,
                amount REAL NOT NULL,
                nav REAL,
                shares REAL,
                execute_date TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success',
                FOREIGN KEY (plan_id) REFERENCES dca_plans(id)
            )
        """)
        
        # 风险提醒/通知表 (新增 Phase 7)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL, -- risk, info, system
                title TEXT,
                content TEXT,
                fund_code TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 每日操作建议表 (新增 Phase 7)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_date TEXT NOT NULL,
                fund_code TEXT NOT NULL,
                fund_name TEXT,
                action_type TEXT NOT NULL, -- buy, hold, sell
                reason TEXT,
                amount REAL, -- 建议金额
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(action_date, fund_code, action_type)
            )
        """)
        
        # 用户风险偏好表 (新增 Phase 7)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id TEXT PRIMARY KEY DEFAULT 'default',
                risk_level TEXT DEFAULT 'moderate', -- conservative, moderate, aggressive
                budget REAL DEFAULT 10000,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_snapshot ON fund_metrics(snapshot_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_code ON fund_metrics(code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_score ON fund_metrics(score DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_date ON snapshots(snapshot_date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_cache_key ON ai_cache(cache_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nav_history_code ON nav_history(fund_code, nav_date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_user ON portfolio(user_id, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rec_history_date ON recommendation_history(recommend_date DESC)")
        
        logger.info("数据库基础表初始化完成")
    
    # ==================== 基金操作 ====================
    
    def upsert_fund(self, code: str, name: str, fund_type: str = None, themes: List[str] = None):
        """插入或更新基金信息"""
        themes_json = json.dumps(themes or [], ensure_ascii=False)
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO funds (code, name, fund_type, themes, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(code) DO UPDATE SET
                    name = excluded.name,
                    fund_type = excluded.fund_type,
                    themes = excluded.themes,
                    updated_at = CURRENT_TIMESTAMP
            """, (code, name, fund_type, themes_json))
    
    def get_fund(self, code: str) -> Optional[Dict]:
        """获取基金信息"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM funds WHERE code = ?", (code,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('themes'):
                    try:
                        result['themes'] = json.loads(result['themes'])
                    except:
                        result['themes'] = []
                return result
        return None
    
    def search_funds(self, keyword: str, limit: int = 20) -> List[Dict]:
        """搜索基金"""
        with self.get_cursor() as cursor:
            # 代码精确匹配优先，然后名称模糊匹配
            cursor.execute("""
                SELECT f.*, fm.return_1y, fm.score 
                FROM funds f
                LEFT JOIN (
                    SELECT code, return_1y, score,
                           ROW_NUMBER() OVER (PARTITION BY code ORDER BY id DESC) as rn
                    FROM fund_metrics
                ) fm ON f.code = fm.code AND fm.rn = 1
                WHERE f.code LIKE ? OR f.name LIKE ?
                ORDER BY 
                    CASE WHEN f.code = ? THEN 0 ELSE 1 END,
                    CASE WHEN f.code LIKE ? THEN 0 ELSE 1 END,
                    f.name
                LIMIT ?
            """, (f"{keyword}%", f"%{keyword}%", keyword, f"{keyword}%", limit))
            
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get('themes'):
                    try:
                        item['themes'] = json.loads(item['themes'])
                    except:
                        item['themes'] = []
                results.append(item)
            return results
    
    def get_fund_count(self) -> int:
        """获取基金总数"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM funds")
            return cursor.fetchone()[0]
    
    def get_all_themes(self, snapshot_id: int = None) -> List[Dict]:
        """获取所有唯一的基金主题及其统计"""
        with self.get_cursor() as cursor:
            # 如果没有指定snapshot_id，使用最新的
            if snapshot_id is None:
                snapshot = self.get_latest_snapshot()
                if not snapshot:
                    return []
                snapshot_id = snapshot['id']
            
            # 获取所有基金的themes字段
            cursor.execute("""
                SELECT themes, COUNT(*) as count 
                FROM fund_metrics 
                WHERE snapshot_id = ? AND themes IS NOT NULL AND themes != '[]'
                GROUP BY themes
            """, (snapshot_id,))
            
            # 解析并统计主题
            theme_counts = {}
            for row in cursor.fetchall():
                themes_str = row[0]
                count = row[1]
                try:
                    themes = json.loads(themes_str) if themes_str else []
                    for theme in themes:
                        if theme:
                            theme_counts[theme] = theme_counts.get(theme, 0) + count
                except:
                    pass
            
            # 按数量排序
            sorted_themes = sorted(theme_counts.items(), key=lambda x: -x[1])
            return [{'name': t[0], 'count': t[1]} for t in sorted_themes]
    
    def get_funds_by_theme(self, snapshot_id: int, theme: str, limit: int = 100) -> List[Dict]:
        """获取指定主题的基金列表"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM fund_metrics 
                WHERE snapshot_id = ? AND themes LIKE ?
                ORDER BY score DESC
                LIMIT ?
            """, (snapshot_id, f'%"{theme}"%', limit))
            
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                for field in ['labels', 'reasons', 'themes']:
                    if item.get(field):
                        try:
                            item[field] = json.loads(item[field])
                        except:
                            item[field] = []
                results.append(item)
            return results
    
    # ==================== 快照操作 ====================
    
    def create_snapshot(self, snapshot_date: str, total_funds: int = 0, benchmark: str = '000300.SH') -> int:
        """创建快照，返回快照ID"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO snapshots (snapshot_date, total_funds, benchmark, status)
                VALUES (?, ?, ?, 'running')
            """, (snapshot_date, total_funds, benchmark))
            return cursor.lastrowid
    
    def complete_snapshot(self, snapshot_id: int, qualified_funds: int, status: str = 'success'):
        """完成快照"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE snapshots 
                SET qualified_funds = ?, status = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (qualified_funds, status, snapshot_id))
    
    def get_latest_snapshot(self) -> Optional[Dict]:
        """获取最新成功的快照"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM snapshots 
                WHERE status = 'success'
                ORDER BY completed_at DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_successful_snapshots(self, limit: int = 10) -> List[Dict]:
        """获取最近成功的快照列表"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM snapshots 
                WHERE status = 'success'
                ORDER BY completed_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_running_snapshot(self) -> Optional[Dict]:
        """获取正在运行的快照"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM snapshots 
                WHERE status = 'running'
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== 指标操作 ====================
    
    def save_fund_metrics(self, snapshot_id: int, code: str, metrics: Dict):
        """保存基金指标"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO fund_metrics (
                    snapshot_id, code, name, score, labels, reasons, themes,
                    latest_nav, nav_date, alpha, beta, sharpe, annual_return,
                    volatility, max_drawdown, current_drawdown, win_rate,
                    profit_loss_ratio, return_1w, return_1m, return_3m,
                    return_6m, return_1y, return_1d, data_days, raw_metrics
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_id, code) DO UPDATE SET
                    name = excluded.name,
                    score = excluded.score,
                    labels = excluded.labels,
                    reasons = excluded.reasons,
                    themes = excluded.themes,
                    latest_nav = excluded.latest_nav,
                    nav_date = excluded.nav_date,
                    alpha = excluded.alpha,
                    beta = excluded.beta,
                    sharpe = excluded.sharpe,
                    annual_return = excluded.annual_return,
                    volatility = excluded.volatility,
                    max_drawdown = excluded.max_drawdown,
                    current_drawdown = excluded.current_drawdown,
                    win_rate = excluded.win_rate,
                    profit_loss_ratio = excluded.profit_loss_ratio,
                    return_1w = excluded.return_1w,
                    return_1m = excluded.return_1m,
                    return_3m = excluded.return_3m,
                    return_6m = excluded.return_6m,
                    return_1y = excluded.return_1y,
                    return_1d = excluded.return_1d,
                    data_days = excluded.data_days,
                    raw_metrics = excluded.raw_metrics
            """, (
                snapshot_id, code,
                metrics.get('name'),
                metrics.get('score'),
                json.dumps(metrics.get('labels', []), ensure_ascii=False),
                json.dumps(metrics.get('reasons', []), ensure_ascii=False),
                json.dumps(metrics.get('themes', []), ensure_ascii=False),
                metrics.get('latest_nav'),
                metrics.get('nav_date'),
                metrics.get('alpha'),
                metrics.get('beta'),
                metrics.get('sharpe'),
                metrics.get('annual_return'),
                metrics.get('volatility'),
                metrics.get('max_drawdown'),
                metrics.get('current_drawdown'),
                metrics.get('win_rate'),
                metrics.get('profit_loss_ratio'),
                metrics.get('return_1w'),
                metrics.get('return_1m'),
                metrics.get('return_3m'),
                metrics.get('return_6m'),
                metrics.get('return_1y'),
                metrics.get('return_1d'),
                metrics.get('data_days'),
                json.dumps(metrics, ensure_ascii=False)
            ))
    
    def get_fund_metrics(self, snapshot_id: int, code: str) -> Optional[Dict]:
        """获取基金指标"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM fund_metrics 
                WHERE snapshot_id = ? AND code = ?
            """, (snapshot_id, code))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                # 解析 JSON 字段
                for field in ['labels', 'reasons', 'themes']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            result[field] = []
                return result
        return None
    
    def get_recommendations(self, snapshot_id: int, theme: str = None, limit: int = 100) -> List[Dict]:
        """获取推荐列表"""
        with self.get_cursor() as cursor:
            if theme and theme != 'all':
                cursor.execute("""
                    SELECT * FROM fund_metrics 
                    WHERE snapshot_id = ? AND themes LIKE ?
                    ORDER BY score DESC
                    LIMIT ?
                """, (snapshot_id, f'%"{theme}"%', limit))
            else:
                cursor.execute("""
                    SELECT * FROM fund_metrics 
                    WHERE snapshot_id = ?
                    ORDER BY score DESC
                    LIMIT ?
                """, (snapshot_id, limit))
            
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                # 解析 JSON 字段
                for field in ['labels', 'reasons', 'themes']:
                    if item.get(field):
                        try:
                            item[field] = json.loads(item[field])
                        except:
                            item[field] = []
                results.append(item)
            return results
    
    def get_ranking(self, snapshot_id: int, sort_by: str = 'score', limit: int = 20, theme: str = None) -> List[Dict]:
        """多维榜单查询"""
        valid_sort_fields = {
            'score', 'return_1y', 'return_6m', 'return_3m', 'return_1m', 'return_1w', 'return_1d',
            'sharpe', 'alpha', 'beta', 'volatility', 'max_drawdown'
        }
        
        if sort_by not in valid_sort_fields:
            sort_by = 'score'
            
        # 某些指标是越小越好（如回撤、波动率）
        order = "ASC" if sort_by in ['max_drawdown', 'volatility', 'beta'] else "DESC"
        
        with self.get_cursor() as cursor:
            query = f"SELECT * FROM fund_metrics WHERE snapshot_id = ?"
            params = [snapshot_id]
            
            if theme and theme != 'all':
                query += " AND themes LIKE ?"
                params.append(f'%{theme}%')
                
            query += f" ORDER BY {sort_by} {order} LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                for field in ['labels', 'reasons', 'themes']:
                    if item.get(field):
                        try:
                            item[field] = json.loads(item[field])
                        except:
                            item[field] = []
                results.append(item)
            return results
    
    def get_qualified_funds(self, snapshot_id: int) -> List[Dict]:
        """获取快照中所有入选基金 (含基本信息)"""
        try:
            with self.get_cursor() as cursor:
                # 显式选择字段避免 m.themes 和 f.themes 冲突
                cursor.execute("""
                    SELECT 
                        m.*, 
                        f.fund_type, 
                        f.themes as themes_json,
                        f.name as fund_name
                    FROM fund_metrics m
                    JOIN funds f ON m.code = f.code
                    WHERE m.snapshot_id = ?
                """, (snapshot_id,))
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    # 解析指标中的 themes (JSON)
                    if item.get('themes'):
                        try:
                            item['themes'] = json.loads(item['themes'])
                        except:
                            item['themes'] = []
                    # 同时也提供 themes_json 兼容 snapshot.py:790
                    if item.get('themes_json'):
                        try:
                            item['themes_json'] = item['themes_json'] # 保持原样或解析
                        except:
                            pass
                    results.append(item)
                return results
        except Exception as e:
            logger.error(f"Failed to get qualified funds: {e}")
            return []

    def get_snapshot_metrics(self, snapshot_id: int) -> List[Dict]:
        """别名：供 snapshot.py 调用"""
        return self.get_qualified_funds(snapshot_id)

    def get_funds_by_codes(self, snapshot_id: int, codes: List[str]) -> List[Dict]:
        """按代码批量获取基金指标"""
        if not codes:
            return []
        try:
            placeholders = ','.join(['?'] * len(codes))
            with self.get_cursor() as cursor:
                cursor.execute(f"""
                    SELECT f.code, f.name, f.fund_type, f.themes, m.*
                    FROM fund_metrics m
                    JOIN funds f ON m.code = f.code
                    WHERE m.snapshot_id = ? AND f.code IN ({placeholders})
                """, (snapshot_id, *codes))
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    if item.get('themes'):
                        item['themes'] = json.loads(item['themes'])
                    results.append(item)
                return results
        except Exception as e:
            logger.error(f"Failed to get funds by codes: {e}")
            return []
    
    # ==================== AI 缓存操作 ====================
    
    def get_ai_cache(self, cache_key: str) -> Optional[str]:
        """获取 AI 缓存"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT content FROM ai_cache 
                WHERE cache_key = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """, (cache_key,))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def set_ai_cache(self, cache_key: str, content: str, model: str = None, ttl_hours: int = 24):
        """设置 AI 缓存"""
        expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO ai_cache (cache_key, content, model, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    content = excluded.content,
                    model = excluded.model,
                    expires_at = excluded.expires_at,
                    created_at = CURRENT_TIMESTAMP
            """, (cache_key, content, model, expires_at))
    
    def clear_expired_cache(self) -> int:
        """清理过期缓存，返回清理数量"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM ai_cache 
                WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
            """)
            return cursor.rowcount
    
    # ==================== 日志操作 ====================
    
    def create_update_log(self, task_type: str) -> int:
        """创建更新日志，返回日志ID"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO update_logs (task_type, status)
                VALUES (?, 'running')
            """, (task_type,))
            return cursor.lastrowid
    
    def complete_update_log(
        self, 
        log_id: int, 
        status: str = 'success',
        funds_processed: int = 0,
        funds_qualified: int = 0,
        message: str = None
    ):
        """完成更新日志"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE update_logs 
                SET status = ?, funds_processed = ?, funds_qualified = ?, 
                    message = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, funds_processed, funds_qualified, message, log_id))
    
    def get_recent_logs(self, limit: int = 20) -> List[Dict]:
        """获取最近的更新日志"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM update_logs 
                ORDER BY started_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 自选基金操作 ====================
    
    def add_to_watchlist(self, fund_code: str, fund_name: str = None, user_id: str = 'default', notes: str = None) -> bool:
        """添加基金到自选"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT OR REPLACE INTO watchlist (fund_code, fund_name, user_id, notes, added_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (fund_code, fund_name, user_id, notes))
            return True
        except Exception as e:
            logger.error(f"添加自选失败: {e}")
            return False
    
    def remove_from_watchlist(self, fund_code: str, user_id: str = 'default') -> bool:
        """从自选移除基金"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM watchlist WHERE fund_code = ? AND user_id = ?
                """, (fund_code, user_id))
            return True
        except Exception as e:
            logger.error(f"移除自选失败: {e}")
            return False
    
    def get_watchlist(self, user_id: str = 'default') -> List[Dict]:
        """获取用户的自选列表"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT fund_code, fund_name, notes, added_at 
                FROM watchlist 
                WHERE user_id = ?
                ORDER BY added_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def is_in_watchlist(self, fund_code: str, user_id: str = 'default') -> bool:
        """检查基金是否在自选中"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM watchlist WHERE fund_code = ? AND user_id = ?
            """, (fund_code, user_id))
            return cursor.fetchone() is not None
    
    # ==================== 净值历史缓存 ====================
    
    def save_nav_history(self, fund_code: str, nav_data: List[Dict]) -> int:
        """批量保存净值历史，返回保存数量"""
        if not nav_data:
            return 0
        
        saved = 0
        with self.get_cursor() as cursor:
            for item in nav_data:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO nav_history (fund_code, nav_date, nav, acc_nav)
                        VALUES (?, ?, ?, ?)
                    """, (fund_code, item.get('date'), item.get('nav'), item.get('acc_nav')))
                    saved += 1
                except Exception:
                    pass
        return saved
    
    def get_nav_history(self, fund_code: str, days: int = 60, limit: int = None) -> List[Dict]:
        """获取净值历史"""
        actual_limit = limit if limit is not None else days
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT nav_date, nav, acc_nav
                FROM nav_history
                WHERE fund_code = ?
                ORDER BY nav_date DESC
                LIMIT ?
            """, (fund_code, actual_limit))
            rows = cursor.fetchall()
            return [{'date': r['nav_date'], 'nav': r['nav'], 'acc_nav': r['acc_nav']} for r in rows]
    
    def get_nav_cache_date(self, fund_code: str) -> Optional[str]:
        """获取净值缓存的最新日期"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT MAX(nav_date) as latest FROM nav_history WHERE fund_code = ?
            """, (fund_code,))
            row = cursor.fetchone()
            return row['latest'] if row else None
    
    # ==================== 持仓模拟操作 ====================
    
    def add_portfolio_position(self, fund_code: str, fund_name: str, shares: float, 
                               cost_price: float, buy_date: str, user_id: str = 'default',
                               notes: str = None) -> bool:
        """添加持仓"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO portfolio (fund_code, fund_name, user_id, shares, cost_price, buy_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (fund_code, fund_name, user_id, shares, cost_price, buy_date, notes))
            return True
        except Exception as e:
            logger.error(f"添加持仓失败: {e}")
            return False
    
    def get_portfolio(self, user_id: str = 'default', status: str = 'holding') -> List[Dict]:
        """获取持仓列表"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM portfolio 
                WHERE user_id = ? AND status = ?
                ORDER BY buy_date DESC
            """, (user_id, status))
            return [dict(row) for row in cursor.fetchall()]
    
    def sell_portfolio_position(self, position_id: int, sell_price: float, sell_date: str) -> bool:
        """卖出持仓"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE portfolio 
                    SET status = 'sold', sell_price = ?, sell_date = ?
                    WHERE id = ?
                """, (sell_price, sell_date, position_id))
            return True
        except Exception as e:
            logger.error(f"卖出持仓失败: {e}")
            return False
    
    def get_portfolio_summary(self, user_id: str = 'default') -> Dict:
        """获取持仓汇总"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_positions,
                    SUM(shares * cost_price) as total_cost
                FROM portfolio 
                WHERE user_id = ? AND status = 'holding'
            """, (user_id,))
            row = cursor.fetchone()
            return {
                'total_positions': row['total_positions'] or 0,
                'total_cost': row['total_cost'] or 0
            }
    
    # ==================== 推荐历史操作 ====================
    
    def save_recommendation_history(self, snapshot_id: int, recommend_date: str, 
                                    funds: List[Dict], category: str) -> int:
        """保存推荐历史"""
        saved = 0
        with self.get_cursor() as cursor:
            for fund in funds:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO recommendation_history 
                        (snapshot_id, recommend_date, fund_code, fund_name, category, score, nav_at_recommend)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        snapshot_id, recommend_date, 
                        fund.get('code'), fund.get('name'), category,
                        fund.get('score'), fund.get('latest_nav')
                    ))
                    saved += 1
                except Exception as e:
                    logger.warning(f"保存推荐历史失败: {e}")
        return saved
    
    def get_recommendation_history(self, days: int = 30, category: str = None) -> List[Dict]:
        """获取历史推荐记录"""
        with self.get_cursor() as cursor:
            if category:
                cursor.execute("""
                    SELECT rh.*, nh.nav as current_nav
                    FROM recommendation_history rh
                    LEFT JOIN (
                        SELECT fund_code, nav, nav_date,
                               ROW_NUMBER() OVER (PARTITION BY fund_code ORDER BY nav_date DESC) as rn
                        FROM nav_history
                    ) nh ON rh.fund_code = nh.fund_code AND nh.rn = 1
                    WHERE rh.category = ? AND rh.recommend_date >= date('now', ?)
                    ORDER BY rh.recommend_date DESC, rh.score DESC
                """, (category, f'-{days} days'))
            else:
                cursor.execute("""
                    SELECT rh.*, nh.nav as current_nav
                    FROM recommendation_history rh
                    LEFT JOIN (
                        SELECT fund_code, nav, nav_date,
                               ROW_NUMBER() OVER (PARTITION BY fund_code ORDER BY nav_date DESC) as rn
                        FROM nav_history
                    ) nh ON rh.fund_code = nh.fund_code AND nh.rn = 1
                    WHERE rh.recommend_date >= date('now', ?)
                    ORDER BY rh.recommend_date DESC, rh.score DESC
                """, (f'-{days} days',))
            
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                # 计算推荐以来收益率
                if item.get('nav_at_recommend') and item.get('current_nav'):
                    item['return_since_recommend'] = round(
                        (item['current_nav'] / item['nav_at_recommend'] - 1) * 100, 2
                    )
                else:
                    item['return_since_recommend'] = None
                results.append(item)
            return results
    
    def get_all_snapshots(self, limit: int = 30) -> List[Dict]:
        """获取所有快照列表"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM snapshots 
                WHERE status = 'success'
                ORDER BY snapshot_date DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_top_gainers(self, snapshot_id: int, period: str = '1w', limit: int = 20) -> List[Dict]:
        """获取涨幅榜"""
        period_field = {
            '1w': 'return_1w',
            '1m': 'return_1m',
            '3m': 'return_3m',
            '6m': 'return_6m',
            '1y': 'return_1y'
        }.get(period, 'return_1w')
        
        with self.get_cursor() as cursor:
            cursor.execute(f"""
                SELECT * FROM fund_metrics 
                WHERE snapshot_id = ? AND {period_field} IS NOT NULL
                ORDER BY {period_field} DESC
                LIMIT ?
            """, (snapshot_id, limit))
            
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                for field in ['labels', 'reasons', 'themes']:
                    if item.get(field):
                        try:
                            item[field] = json.loads(item[field])
                        except:
                            item[field] = []
                results.append(item)
            return results

    # ==================== Phase 7: 新增业务模块 ====================
    
    # 1. 每日操作 (Daily Actions)
    def save_daily_actions(self, action_date: str, actions: List[Dict]):
        """保存当日操作建议（全量覆盖）"""
        with self.get_cursor() as cursor:
            # 先清除当天旧数据
            cursor.execute("DELETE FROM daily_actions WHERE action_date = ?", (action_date,))
            for a in actions:
                cursor.execute("""
                    INSERT INTO daily_actions (action_date, fund_code, fund_name, action_type, reason, amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (action_date, a['code'], a['name'], a['action'], a['reason'], a.get('amount')))
                
    def get_daily_actions(self, action_date: str) -> List[Dict]:
        """获取当日操作建议"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM daily_actions WHERE action_date = ?
            """, (action_date,))
            return [dict(row) for row in cursor.fetchall()]

    # 2. 用户偏好 (User Profile)
    def get_user_profile(self, user_id: str = 'default') -> Dict:
        """获取用户偏好，若不存在则返回默认值"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row: return dict(row)
            return {'user_id': user_id, 'risk_level': 'moderate', 'budget': 10000}
            
    def save_user_profile(self, risk_level: str, budget: float, user_id: str = 'default'):
        """保存用户偏好"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO user_profile (user_id, risk_level, budget, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, risk_level, budget))
            
    # 3. 通知与风险提醒 (Notifications)
    def add_notification(self, type: str, title: str, content: str, fund_code: str = None):
        with self.get_cursor() as cursor:
             cursor.execute("""
                 INSERT INTO notifications (type, title, content, fund_code)
                 VALUES (?, ?, ?, ?)
             """, (type, title, content, fund_code))
             
    def get_unread_notifications(self) -> List[Dict]:
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM notifications WHERE is_read = 0 ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
            
    def mark_notification_read(self, notif_id: int):
        with self.get_cursor() as cursor:
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notif_id,))
            
    # 4. 持仓获取模块 (用于一键汇总和盈亏计算)
    def get_holding_portfolio(self, user_id: str = 'default') -> List[Dict]:
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.*, f.name 
                FROM portfolio p
                LEFT JOIN funds f ON p.fund_code = f.code
                WHERE p.user_id = ? AND p.status = 'holding'
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    # 5. 定投计划 (DCA Plans)
    def add_dca_plan(self, fund_code: str, fund_name: str, base_amount: float,
                     frequency: str = 'weekly', day_of_week: int = None,
                     day_of_month: int = None, user_id: str = 'default') -> bool:
        """添加或更新定投计划"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT OR REPLACE INTO dca_plans 
                    (fund_code, fund_name, user_id, base_amount, frequency, day_of_week, day_of_month, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (fund_code, fund_name, user_id, base_amount, frequency, day_of_week, day_of_month))
            return True
        except Exception as e:
            logger.error(f"添加定投计划失败: {e}")
            return False

    def get_dca_plans(self, user_id: str = 'default', only_active: bool = True) -> List[Dict]:
        """获取定投计划列表"""
        query = "SELECT * FROM dca_plans WHERE user_id = ?"
        if only_active:
            query += " AND is_active = 1"
        with self.get_cursor() as cursor:
            cursor.execute(query, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def update_dca_status(self, plan_id: int, is_active: bool):
        """启用/禁用定投计划"""
        with self.get_cursor() as cursor:
            cursor.execute("UPDATE dca_plans SET is_active = ? WHERE id = ?", (1 if is_active else 0, plan_id))

    def save_dca_record(self, plan_id: int, fund_code: str, fund_name: str, 
                        amount: float, nav: float = None, shares: float = None) -> bool:
        """记录定投执行结果"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO dca_records (plan_id, fund_code, fund_name, amount, nav, shares, execute_date)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (plan_id, fund_code, fund_name, amount, nav, shares))
                
                # 同时更新计划的最后执行时间
                cursor.execute("UPDATE dca_plans SET last_executed_at = CURRENT_TIMESTAMP WHERE id = ?", (plan_id,))
            return True
        except Exception as e:
            logger.error(f"保存定投记录失败: {e}")
            return False

    def get_dca_records(self, plan_id: int = None, limit: int = 50) -> List[Dict]:
        """获取定投执行历史"""
        with self.get_cursor() as cursor:
            if plan_id:
                cursor.execute("SELECT * FROM dca_records WHERE plan_id = ? ORDER BY execute_date DESC LIMIT ?", (plan_id, limit))
            else:
                cursor.execute("SELECT * FROM dca_records ORDER BY execute_date DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]



# 全局实例
_db_instance: Optional[Database] = None

def get_db() -> Database:
    """获取数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
