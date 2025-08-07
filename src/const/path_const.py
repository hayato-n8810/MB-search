from pathlib import Path

# データセットプロジェクト（リポジトリ）
REPO = Path(__file__).parents[3] / "repository"

ROOT = Path(__file__).parents[2]

JSCODE = ROOT / "js_code"
QUERIES = ROOT / "codeql_queries_js"

SEARCH = ROOT / "src" / "mb_search"
PATTERN = ROOT / "src" / "pattern"
