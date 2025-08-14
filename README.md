# MB-SEARCH

JavaScriptコードの差分からパフォーマンスアンチパターンを自動検出するCodeQLクエリ生成ツール

## 概要

MB-SEARCHは、遅いコードと速いコードの実装対から自動的にパフォーマンスアンチパターンを抽出し、CodeQLクエリを生成するツールです。コード差分のAST解析により、パフォーマンス問題を検出するためのルールを自動作成します。

## 主な機能

- **AST差分解析**: JavaScriptコードペアから構造的差分を抽出
- **パターン自動生成**: 差分情報からアンチパターンの定義を作成
- **CodeQLクエリ生成**: パターンからCodeQLクエリを自動生成
- **ループ検出**: ループ内の非効率な処理を特定
- **メソッド呼び出し分析**: パフォーマンスに影響するメソッド呼び出しを検出

## プロジェクト構成

```
MB-search/
├── src/
│   ├── mb_search/           # メインのPythonモジュール
│   │   ├── main.py          # パイプライン実行
│   │   ├── ast_analyzer.py  # AST解析
│   │   ├── pattern_creator.py  # パターン生成
│   │   └── query_generator.py  # CodeQLクエリ生成
│   ├── pattern/             # 生成されたパターン定義
│   └── const/               # 定数定義
│       └── path_const.py
├── js_code/                 # JavaScript関連ファイル
│   └── ast_parser.js        # ASTパーサー
└── codeql_queries_js/       # 生成されたCodeQLクエリ
    ├── MBQL/                # マイクロベンチマークから作成されたクエリ
    └── testQL/              # テスト用クエリ
```

## インストール

### 必要な環境

- Python 3.13+
- Node.js (esprima用)

### セットアップ

1. リポジトリをクローン
```bash
git clone <repository-url>
cd MB-search
```

2. Python環境のセットアップ
```bash
uv install
```

3. Node.js依存関係のインストール
```bash
npm install
```

## 使用方法

### 基本的な使い方

[`src/mb_search/main.py`](src/mb_search/main.py)でコード実装対を定義して実行：

```python
from mb_search.main import run_pipeline

# 遅いコード（アンチパターン）
slow_code = """
for (var i = 0; i < 100; i++) {
    var s = new String("hello");
}
"""

# 速いコード（推奨パターン）
fast_code = """
for (var i = 0; i < 100; i++) {
    var s = "hello";
}
"""

# パイプライン実行
run_pipeline(slow_code, fast_code)
```

### 実行結果

1. **パターン生成**: [`src/pattern/diff_pattern.json`](src/pattern/diff_pattern.json)にパターンが保存
2. **クエリ生成**: [`codeql_queries_js/testQL/`](codeql_queries_js/testQL/)にCodeQLクエリが生成

## 検出可能なパターンの例

- ループ内のStringコンストラクタ呼び出し
- 配列のforEachメソッド使用
- ループ内のconcatメソッド使用


## 生成されるファイル

### パターンファイル例
```json
[
  {
    "name": "pattern_0_String_constructor_in_loop",
    "description": "Automatically generated pattern from code diff.",
    "target_node_type": "NewExpression",
    "conditions": [
      {
        "type": "constructor_call",
        "constructor_name": "String",
        "path": ["callee", "name"]
      },
      {
        "type": "in_loop",
        "check": "is_in_loop"
      }
    ]
  }
]
```

### CodeQLクエリ例
```ql
/**
 * @name pattern_0_String_constructor_in_loop
 * @description Automatically generated pattern from code diff.
 * @kind problem
 * @problem.severity warning
 * @id js/performance/pattern-0-string-constructor-in-loop
 * @tags performance
 *       maintainability
 */

import javascript

from NewExpr newExpr
where
  newExpr.getCallee().(Identifier).getName() = "String" and
  exists(LoopStmt loop | loop.getBody().getAChildStmt*() = newExpr.getEnclosingStmt())
select newExpr, "Automatically generated pattern from code diff."
```

## アーキテクチャ

### 主要コンポーネント

1. **[`ast_analyzer.py`](src/mb_search/ast_analyzer.py)**: AST生成と差分検出
2. **[`pattern_creator.py`](src/mb_search/pattern_creator.py)**: 差分からパターン定義を生成
3. **[`query_generator.py`](src/mb_search/query_generator.py)**: パターンからCodeQLクエリを生成
4. **[`ast_parser.js`](js_code/ast_parser.js)**: JavaScriptコードのAST生成

### 処理フロー

```
コード差分 → AST生成 → 差分抽出 → パターン生成 → CodeQLクエリ生成
```

パターン生成の際に差分とその親ノードの関係（ループ内部であるなど）をヒューリスティックで検出

## 開発

### テスト実行

```bash
cd src/mb_search
python main.py
```

### 新しいパターンの追加

1. [`main.py`](src/mb_search/main.py)で新しいコード実装対を定義
2. [`run_pipeline()`](src/mb_search/main.py)を実行
3. 生成されたパターンとクエリを確認

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照

## 作者

野口隼杜 (hayato-n8810)