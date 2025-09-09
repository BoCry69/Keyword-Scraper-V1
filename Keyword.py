"""
Keyword Scraper V1 by BoCry69 - Simple & Clean
"""

import sys
import asyncio
import aiohttp
import time
import random
from datetime import datetime
from typing import List, Set, Optional
import re

try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *
except ImportError:
    print("pip install PySide6")
    sys.exit(1)


class ProxyManager:
    def __init__(self):
        self.working_proxies = []
        self.failed_proxies = []
        self.rotation_count = 0
        self.speed = "fast"
        self.timeout = 3

    def set_speed_timeout(self, speed: str, timeout: int):
        self.speed = speed
        self.timeout = timeout

    def validate_proxy_format(self, proxy: str) -> bool:
        patterns = [
            r'^(\d{1,3}\.){3}\d{1,3}:\d+$',
            r'^[^:]+:[^@]+@(\d{1,3}\.){3}\d{1,3}:\d+$',
            r'^https?://(\d{1,3}\.){3}\d{1,3}:\d+$'
        ]
        return any(re.match(pattern, proxy) for pattern in patterns)

    async def test_single_proxy(self, session: aiohttp.ClientSession, proxy: str) -> Optional[dict]:
        if not proxy.startswith(('http://', 'https://')):
            proxy_url = f"http://{proxy}"
        else:
            proxy_url = proxy
        try:
            start = time.time()
            async with session.get("http://httpbin.org/ip", proxy=proxy_url) as r:
                if r.status == 200:
                    return {'proxy': proxy, 'response_time': time.time()-start}
        except Exception:
            pass
        return None

    async def fast_import_and_check(self, proxy_list: List[str], progress_cb=None):
        valid_input = [p.strip() for p in proxy_list if self.validate_proxy_format(p.strip())]
        if not valid_input:
            return 0, 0

        if self.speed == "fast":
            conn_limit, per_host = 200, 100
        elif self.speed == "medium":
            conn_limit, per_host = 100, 50
        else:
            conn_limit, per_host = 50, 25

        connector = aiohttp.TCPConnector(limit=conn_limit, limit_per_host=per_host)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        working, failed = [], []
        done, total = 0, len(valid_input)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [asyncio.create_task(self.test_single_proxy(session, p)) for p in valid_input]
            for t in asyncio.as_completed(tasks):
                res = await t
                if res:
                    working.append(res)
                done += 1
                if progress_cb:
                    progress_cb(int(done*100/total))

        worked_set = {w['proxy'] for w in working}
        failed = [{'proxy': p} for p in valid_input if p not in worked_set]

        self.working_proxies = working
        self.failed_proxies = failed
        return len(working), len(failed)

    def get_random_proxy(self) -> Optional[str]:
        if not self.working_proxies:
            return None
        p = random.choice(self.working_proxies)['proxy']
        self.rotation_count += 1
        return p if p.startswith(('http://','https://')) else f"http://{p}"


class EnhancedKeywordScraper:
    def __init__(self, max_concurrent=30, timeout=8, proxy_manager=None, enabled_engines=None):
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.proxy_manager = proxy_manager
        self.enabled_engines = enabled_engines or {}
        self.session = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=200, limit_per_host=60)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        return self

    async def __aexit__(self, *_):
        if self.session:
            await self.session.close()

    async def _get(self, url, params):
        proxy = self.proxy_manager.get_random_proxy() if self.proxy_manager else None
        try:
            await asyncio.sleep(random.uniform(0.02, 0.08))
            async with self.session.get(url, params=params, proxy=proxy) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            return None

    async def google_enhanced(self, kw: str) -> Set[str]:
        if not self.enabled_engines.get("google", False):
            return set()
        
        results = set()
        base_url = "http://suggestqueries.google.com/complete/search"
        
        clients = ['chrome', 'firefox', 'safari', 'toolbar']
        for client in clients:
            data = await self._get(base_url, {'client': client, 'q': kw, 'hl': 'de'})
            if data and len(data) > 1:
                results.update(data[1][:8])
        
        for char in 'abcdefghijklmnopqrstuvwxyz0123456789':
            expanded_kw = f"{kw} {char}"
            data = await self._get(base_url, {'client': 'chrome', 'q': expanded_kw, 'hl': 'de'})
            if data and len(data) > 1:
                results.update(data[1][:5])
        
        return results

    async def bing_enhanced(self, kw: str) -> Set[str]:
        if not self.enabled_engines.get("bing", False):
            return set()
            
        results = set()
        base_url = "https://api.bing.com/osjson.aspx"
        
        data = await self._get(base_url, {'query': kw})
        if data and len(data) > 1:
            results.update(data[1][:8])
        
        for char in 'abcdefghijklmnopqrstuvwxyz0123456789':
            expanded = f"{kw} {char}"
            data = await self._get(base_url, {'query': expanded})
            if data and len(data) > 1:
                results.update(data[1][:4])
        
        return results

    async def duckduckgo_enhanced(self, kw: str) -> Set[str]:
        if not self.enabled_engines.get("duckduckgo", False):
            return set()
            
        results = set()
        base_url = "https://duckduckgo.com/ac/"
        
        data = await self._get(base_url, {'q': kw, 'type': 'list'})
        if data:
            results.update(item['phrase'] for item in data if 'phrase' in item)
        
        for char in 'abcdefghijklmnopqrstu':
            data = await self._get(base_url, {'q': f"{kw} {char}", 'type': 'list'})
            if data:
                results.update(item['phrase'] for item in data[:3] if 'phrase' in item)
        
        return results

    async def youtube_suggestions(self, kw: str) -> Set[str]:
        if not self.enabled_engines.get("youtube", False):
            return set()
            
        results = set()
        base_url = "http://suggestqueries.google.com/complete/search"
        
        data = await self._get(base_url, {'client': 'youtube', 'ds': 'yt', 'q': kw})
        if data and len(data) > 1:
            results.update(data[1][:6])
        
        return results

    async def amazon_suggestions(self, kw: str) -> Set[str]:
        if not self.enabled_engines.get("amazon", False):
            return set()
            
        results = set()
        base_url = "http://suggestqueries.google.com/complete/search"
        amazon_kw = f"{kw} amazon"
        data = await self._get(base_url, {'client': 'chrome', 'q': amazon_kw, 'hl': 'de'})
        if data and len(data) > 1:
            clean_results = [item.replace(' amazon', '').strip() for item in data[1][:4]]
            results.update(clean_results)
        
        return results

    async def scrape_all_enhanced(self, kw: str) -> Set[str]:
        tasks = [
            self.google_enhanced(kw),
            self.bing_enhanced(kw),
            self.duckduckgo_enhanced(kw),
            self.youtube_suggestions(kw),
            self.amazon_suggestions(kw)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_suggestions = set()
        
        for result in results:
            if isinstance(result, set):
                all_suggestions.update(result)
        
        return {s for s in all_suggestions if 2 <= len(s) <= 100 and s.strip()}

    async def batch(self, kws: List[str], progress_cb=None) -> Set[str]:
        sem = asyncio.Semaphore(self.max_concurrent)
        all_sug = set()
        done, total = 0, len(kws)

        async def run_one(k):
            nonlocal done
            async with sem:
                s = await self.scrape_all_enhanced(k)
                done += 1
                if progress_cb:
                    progress_cb(int(done*100/total))
                return s

        tasks = [run_one(k.strip()) for k in kws if k.strip()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, set):
                all_sug.update(r)
        return all_sug


class FastProxyThread(QThread):
    progress = Signal(int)
    finished = Signal(int, int)
    error = Signal(str)

    def __init__(self, manager: ProxyManager, proxy_list: List[str]):
        super().__init__()
        self.manager = manager
        self.proxy_list = proxy_list

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            ok, bad = loop.run_until_complete(self.manager.fast_import_and_check(self.proxy_list, self.progress.emit))
            loop.close()
            self.finished.emit(ok, bad)
        except Exception as e:
            self.error.emit(str(e))


class EnhancedScrapeThread(QThread):
    progress = Signal(int)
    finished = Signal(set)
    error = Signal(str)

    def __init__(self, kws: List[str], threads: int, enabled_engines: dict, manager: Optional[ProxyManager]):
        super().__init__()
        self.kws = kws
        self.threads = threads
        self.enabled_engines = enabled_engines
        self.manager = manager

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._work())
            loop.close()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    async def _work(self):
        async with EnhancedKeywordScraper(self.threads, enabled_engines=self.enabled_engines, proxy_manager=self.manager) as s:
            return await s.batch(self.kws, self.progress.emit)


class KeywordScraperGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keyword Scraper V1 by BoCry69")
        self.setFixedSize(800, 650)

        self.proxy_manager = ProxyManager()
        self.scrape_thread = None
        self.proxy_thread = None
        self.generated = set()

        self._build_ui()
        self._apply_style()
        self._center()

    def _build_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        main_layout = QVBoxLayout(cw)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Keyword Scraper V1 by BoCry69")
        title.setObjectName("title")
        self.status = QLabel("Ready")
        self.status.setObjectName("status")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.status)
        main_layout.addLayout(header)

        # Main Content
        content = QHBoxLayout()
        content.setSpacing(15)
        
        # Left Column - Scraper
        left_column = QVBoxLayout()
        left_column.setSpacing(12)
        
        # Keywords
        kw_group = QGroupBox("Keywords Input")
        kw_layout = QVBoxLayout(kw_group)
        self.kw_input = QTextEdit()
        self.kw_input.setMaximumHeight(100)
        self.kw_input.setPlaceholderText("Enter keywords (one per line)")
        kw_layout.addWidget(self.kw_input)
        left_column.addWidget(kw_group)

        # Engine Settings
        engine_group = QGroupBox("Search Engines")
        engine_layout = QGridLayout(engine_group)
        self.google_check = QCheckBox("Google (Multi-client + A-Z)")
        self.google_check.setChecked(True)
        self.bing_check = QCheckBox("Bing (Enhanced + Expansion)")
        self.bing_check.setChecked(True)
        self.duck_check = QCheckBox("DuckDuckGo")
        self.duck_check.setChecked(True)
        self.youtube_check = QCheckBox("YouTube")
        self.youtube_check.setChecked(True)
        self.amazon_check = QCheckBox("Amazon-style")
        self.amazon_check.setChecked(True)
        
        engine_layout.addWidget(self.google_check, 0, 0)
        engine_layout.addWidget(self.bing_check, 0, 1)
        engine_layout.addWidget(self.duck_check, 1, 0)
        engine_layout.addWidget(self.youtube_check, 1, 1)
        engine_layout.addWidget(self.amazon_check, 2, 0)
        left_column.addWidget(engine_group)

        # Scraper Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QGridLayout(settings_group)
        settings_layout.addWidget(QLabel("Threads:"), 0, 0)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(15, 100)
        self.threads_spin.setValue(30)
        settings_layout.addWidget(self.threads_spin, 0, 1)
        self.use_proxy_check = QCheckBox("Use Proxies")
        settings_layout.addWidget(self.use_proxy_check, 0, 2)
        left_column.addWidget(settings_group)

        # Scraper Buttons
        scraper_buttons = QHBoxLayout()
        self.start_btn = QPushButton("Start Scraping")
        self.export_btn = QPushButton("Export Results")
        self.export_btn.setEnabled(False)
        self.clear_btn = QPushButton("Clear")
        scraper_buttons.addWidget(self.start_btn)
        scraper_buttons.addWidget(self.export_btn)
        scraper_buttons.addWidget(self.clear_btn)
        left_column.addLayout(scraper_buttons)

        # Progress
        self.scrape_progress = QProgressBar()
        self.scrape_progress.setVisible(False)
        left_column.addWidget(self.scrape_progress)

        content.addLayout(left_column, 1)

        # Right Column - Proxies
        right_column = QVBoxLayout()
        right_column.setSpacing(12)

        # Proxy Input
        proxy_group = QGroupBox("Proxy Management")
        proxy_layout = QVBoxLayout(proxy_group)
        
        self.proxy_input = QTextEdit()
        self.proxy_input.setMaximumHeight(100)
        self.proxy_input.setPlaceholderText("Enter proxies (one per line)")
        proxy_layout.addWidget(self.proxy_input)

        # Proxy Settings
        proxy_settings = QGridLayout()
        proxy_settings.addWidget(QLabel("Speed:"), 0, 0)
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["fast", "medium", "slow"])
        proxy_settings.addWidget(self.speed_combo, 0, 1)
        proxy_settings.addWidget(QLabel("Timeout:"), 0, 2)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 15)
        self.timeout_spin.setValue(3)
        proxy_settings.addWidget(self.timeout_spin, 0, 3)
        proxy_layout.addLayout(proxy_settings)

        # Proxy Buttons
        proxy_buttons = QHBoxLayout()
        self.import_file_btn = QPushButton("Import File")
        self.test_proxies_btn = QPushButton("Import & Test")
        self.clear_proxies_btn = QPushButton("Clear")
        proxy_buttons.addWidget(self.import_file_btn)
        proxy_buttons.addWidget(self.test_proxies_btn)
        proxy_buttons.addWidget(self.clear_proxies_btn)
        proxy_layout.addLayout(proxy_buttons)

        right_column.addWidget(proxy_group)

        # Proxy Progress
        self.proxy_progress = QProgressBar()
        self.proxy_progress.setVisible(False)
        right_column.addWidget(self.proxy_progress)

        # Proxy Results
        proxy_results_group = QGroupBox("Proxy Status")
        proxy_results_layout = QVBoxLayout(proxy_results_group)
        self.proxy_stats = QLabel("0 tested, 0 working, 0 failed")
        self.proxy_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        proxy_results_layout.addWidget(self.proxy_stats)
        self.proxy_list = QTextEdit()
        self.proxy_list.setReadOnly(True)
        self.proxy_list.setMaximumHeight(120)
        proxy_results_layout.addWidget(self.proxy_list)
        right_column.addWidget(proxy_results_group)

        content.addLayout(right_column, 1)
        main_layout.addLayout(content)

        # Results
        results_group = QGroupBox("Scraping Results")
        results_layout = QVBoxLayout(results_group)
        results_header = QHBoxLayout()
        results_header.addWidget(QLabel("Keywords found:"))
        results_header.addStretch()
        self.count_label = QLabel("0")
        self.count_label.setObjectName("count")
        results_header.addWidget(self.count_label)
        results_layout.addLayout(results_header)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Enhanced results from selected engines will appear here...")
        results_layout.addWidget(self.results_text)
        main_layout.addWidget(results_group)

        # Connect signals
        self.start_btn.clicked.connect(self._start)
        self.export_btn.clicked.connect(self._export)
        self.clear_btn.clicked.connect(self._clear)
        self.import_file_btn.clicked.connect(self._import_file)
        self.test_proxies_btn.clicked.connect(self._test_proxies)
        self.clear_proxies_btn.clicked.connect(self._clear_proxies)

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background: #F5F5F5; color: #333; }
            QGroupBox { font-weight: 600; border: 1px solid #CCC; border-radius: 5px; margin-top: 6px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
            QTextEdit, QSpinBox, QComboBox { border: 1px solid #CCC; border-radius: 4px; padding: 5px; background: white; }
            QTextEdit:focus, QSpinBox:focus, QComboBox:focus { border: 2px solid #4CAF50; }
            QPushButton { background: #4CAF50; color: white; border: none; border-radius: 4px; padding: 8px 16px; font-weight: 600; }
            QPushButton:hover { background: #45a049; }
            QPushButton:disabled { background: #CCC; color: #666; }
            QProgressBar { border: 1px solid #CCC; border-radius: 4px; text-align: center; height: 20px; }
            QProgressBar::chunk { background: #4CAF50; border-radius: 4px; }
            QCheckBox { font-weight: 500; }
            QCheckBox::indicator { width: 16px; height: 16px; }
            QCheckBox::indicator:unchecked { border: 1px solid #CCC; border-radius: 3px; background: white; }
            QCheckBox::indicator:checked { border: 1px solid #4CAF50; border-radius: 3px; background: #4CAF50; }
            QLabel#title { font-size: 16px; font-weight: 700; color: #2E7D32; }
            QLabel#status { background: #E8F5E8; color: #2E7D32; border: 1px solid #C8E6C9; border-radius: 10px; padding: 4px 8px; font-weight: 600; }
            QLabel#count { background: #4CAF50; color: white; border-radius: 8px; padding: 2px 8px; font-weight: 700; }
        """)

    def _center(self):
        g = self.frameGeometry()
        c = QApplication.primaryScreen().availableGeometry().center()
        g.moveCenter(c)
        self.move(g.topLeft())

    def _start(self):
        text = self.kw_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Enter keywords.")
            return

        kws = [l.strip() for l in text.splitlines() if l.strip()]
        
        enabled_engines = {
            "google": self.google_check.isChecked(),
            "bing": self.bing_check.isChecked(),
            "duckduckgo": self.duck_check.isChecked(),
            "youtube": self.youtube_check.isChecked(),
            "amazon": self.amazon_check.isChecked()
        }

        if not any(enabled_engines.values()):
            QMessageBox.warning(self, "Warning", "Select at least one engine.")
            return

        manager = self.proxy_manager if (self.use_proxy_check.isChecked() and self.proxy_manager.working_proxies) else None

        self.start_btn.setEnabled(False)
        self.scrape_progress.setVisible(True)
        self.scrape_progress.setValue(0)
        self.status.setText("Scraping...")

        self.scrape_thread = EnhancedScrapeThread(kws, self.threads_spin.value(), enabled_engines, manager)
        self.scrape_thread.progress.connect(self.scrape_progress.setValue)
        self.scrape_thread.finished.connect(self._scrape_done)
        self.scrape_thread.error.connect(self._scrape_err)
        self.scrape_thread.start()

    def _scrape_done(self, suggestions: set):
        self.generated = suggestions
        out = sorted(set(suggestions))
        self.results_text.setPlainText("\n".join(out))
        self.count_label.setText(str(len(out)))
        self.export_btn.setEnabled(len(out) > 0)
        self.start_btn.setEnabled(True)
        self.scrape_progress.setVisible(False)
        self.status.setText("Complete")
        
        enabled_count = sum([
            self.google_check.isChecked(),
            self.bing_check.isChecked(),
            self.duck_check.isChecked(),
            self.youtube_check.isChecked(),
            self.amazon_check.isChecked()
        ])
        
        QMessageBox.information(self, "Scraping Complete", 
            f"Found {len(out)} keywords using {enabled_count} engines with A-Z expansion!")

    def _scrape_err(self, msg: str):
        self.start_btn.setEnabled(True)
        self.scrape_progress.setVisible(False)
        self.status.setText("Error")
        QMessageBox.critical(self, "Error", msg)

    def _export(self):
        if not self.generated:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Results", f"BoCry69_Keywords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "Text (*.txt);;CSV (*.csv)")
        if not path:
            return
        data = sorted(set(self.generated))
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Keyword Scraper V1 by BoCry69\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total keywords: {len(data)}\n\n")
                if path.endswith(".csv"):
                    f.write("keyword\n")
                    for k in data:
                        f.write(f'"{k}"\n')
                else:
                    f.write("\n".join(data))
            QMessageBox.information(self, "Export Success", f"Saved {len(data)} keywords!")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _clear(self):
        self.generated.clear()
        self.results_text.clear()
        self.count_label.setText("0")
        self.export_btn.setEnabled(False)
        self.status.setText("Ready")

    def _import_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Proxies", "", "Text Files (*.txt);;All Files (*.*)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.proxy_input.setPlainText(content)
                QMessageBox.information(self, "Import Success", "Proxies loaded from file!")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    def _test_proxies(self):
        raw = self.proxy_input.toPlainText().strip()
        if not raw:
            QMessageBox.warning(self, "Warning", "Enter proxies.")
            return
        proxies = [l.strip() for l in raw.splitlines() if l.strip()]

        speed = self.speed_combo.currentText()
        timeout = self.timeout_spin.value()
        self.proxy_manager.set_speed_timeout(speed, timeout)

        self.test_proxies_btn.setEnabled(False)
        self.proxy_progress.setVisible(True)
        self.proxy_progress.setValue(0)
        self.status.setText(f"Testing {len(proxies)} proxies...")

        self.proxy_thread = FastProxyThread(self.proxy_manager, proxies)
        self.proxy_thread.progress.connect(self.proxy_progress.setValue)
        self.proxy_thread.finished.connect(self._proxy_done)
        self.proxy_thread.error.connect(self._proxy_err)
        self.proxy_thread.start()

    def _proxy_done(self, ok: int, bad: int):
        self.test_proxies_btn.setEnabled(True)
        self.proxy_progress.setVisible(False)
        self.status.setText("Ready")

        work = sorted(self.proxy_manager.working_proxies, key=lambda x: x.get('response_time', 9e9))
        lines = []
        for i, info in enumerate(work, 1):
            rt = info.get('response_time', 0)
            speed_label = "FAST" if rt < 1 else "GOOD" if rt < 3 else "OK"
            lines.append(f"{i}. {info['proxy']} ({rt:.2f}s {speed_label})")
        
        self.proxy_list.setPlainText("\n".join(lines) if lines else "No working proxies.")
        self.proxy_stats.setText(f"{ok+bad} tested, {ok} working, {bad} failed")
        self.proxy_input.clear()

        QMessageBox.information(self, "Proxy Test Complete", f"Working: {ok} | Failed: {bad}")

    def _proxy_err(self, msg: str):
        self.test_proxies_btn.setEnabled(True)
        self.proxy_progress.setVisible(False)
        self.status.setText("Error")
        QMessageBox.critical(self, "Proxy Error", msg)

    def _clear_proxies(self):
        self.proxy_manager.working_proxies.clear()
        self.proxy_manager.failed_proxies.clear()
        self.proxy_list.clear()
        self.proxy_stats.setText("0 tested, 0 working, 0 failed")
        self.status.setText("Ready")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Keyword Scraper V1 by BoCry69")
    w = KeywordScraperGUI()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
