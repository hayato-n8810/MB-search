# 差分からパターン生成・クエリ生成を行うメインのパイプライン
import json
import os
import pattern_creator
import query_generator

from mb_search import path_const

def save_query_to_file(codeql_query: str, pattern_name: str):
    """
    生成されたCodeQLクエリを.qlファイルとして保存する
    """
    # codeql-queries-jsディレクトリのパスを取得
    codeql_dir = path_const.QUERIES

    # ファイル名を生成（pattern_nameを小文字に変換し、.qlを付加）
    filename = f"{pattern_name.lower()}.ql"
    filepath = os.path.join(codeql_dir, filename)
    
    # ディレクトリが存在しない場合は作成
    os.makedirs(codeql_dir, exist_ok=True)
    
    # クエリをファイルに保存
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(codeql_query)
    
    print(f"\n--> CodeQL query saved to: {filepath}")

def run_pipeline(slow_code: str, fast_code: str):
    """
    単一の実装対に対して、パターン生成からクエリ生成までのパイプラインを実行する
    """
    print("="*50)
    print("Target Code Pair:")
    print("--- SLOW ---")
    print(slow_code.strip())
    print("\n--- FAST ---")
    print(fast_code.strip())
    print("="*50)

    # ステップ1: コードの差分からパターンを自動生成
    print("\n[STEP 1] Generating pattern from code difference...")
    generated_pattern = pattern_creator.create_pattern_from_diff(slow_code, fast_code)
    
    if not generated_pattern:
        print("\n--> RESULT: Could not generate a pattern from the given diff.")
        return

    print("\n--> Generated Pattern Definition:")
    print(json.dumps(generated_pattern, indent=2))

    # ステップ2: 生成されたパターンからCodeQLクエリを自動生成
    print("\n[STEP 2] Generating CodeQL query from generated pattern...")
    codeql_query = query_generator.generate_query_from_pattern(generated_pattern)

    print("\n--> Generated CodeQL Query:")
    print(codeql_query)
    
    # ステップ3: 生成されたCodeQLクエリを.qlファイルとして保存
    save_query_to_file(codeql_query, generated_pattern['name'])
    
    print("="*50)


if __name__ == "__main__":
    # --- ケース1：ループ内での不要なコンストラクタ呼び出し ---
    slow1 = """
    for (var i = 0; i < 100; i++) {
        var s = new String("hello");
    }"""
    fast1 = """
    for (var i = 0; i < 100; i++) {
        var s = "hello";
    }"""
    run_pipeline(slow1, fast1)
    
    # --- ケース2：Array.prototype.map の利用（仮） ---
    # このパターンは現在のヒューリスティックではうまく扱えない可能性がある
    slow2 = "var new_array = old_array.map(x => x+1);"
    fast2 = "for (var x of old_array) { new_array.push(x+1); }"
    # run_pipeline(slow2, fast2) # さらなる拡張が必要な例