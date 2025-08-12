# 差分からパターン生成・クエリ生成を行うメインのパイプライン
import json
import os
import pattern_creator
import query_generator

from mb_search import path_const


def create_diff_pattern(id: int, slow_code: str, fast_code: str):
    """コードの差分からパターンを生成する

    Args:
        slow_code (str): MBの実装（遅いコード）
        fast_code (str): MBの実装（速いコード）

    Returns:
        dict: 生成されたパターン(標準出力用)
        ./pattern/diff_pattern.json: 生成されたパターンJSONファイル
    """
    # コードの差分からパターンを自動生成
    created_pattern = pattern_creator.create_pattern_from_diff(id, slow_code, fast_code)

    # 生成されたパターンをdiff_pattern.jsonファイルに保存
    pattern_file_path = path_const.PATTERN / "diff_pattern.json"
    
    # 既存のパターンファイルがあれば読み込み、なければ空のリストで初期化
    existing_patterns = []
    if os.path.exists(pattern_file_path):
        try:
            with open(pattern_file_path, "r", encoding="utf-8") as f:
                existing_patterns = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_patterns = []
    
    # 新しいパターンを既存のリストに追加
    if created_pattern:
        existing_patterns.append(created_pattern)
        
        # パターンディレクトリが存在しない場合は作成
        os.makedirs(path_const.PATTERN, exist_ok=True)
        
        # 更新されたパターンリストをファイルに保存
        with open(pattern_file_path, "w", encoding="utf-8") as f:
            json.dump(existing_patterns, f, ensure_ascii=False, indent=2)

        print(f"\n--> パターンが保存されました: {pattern_file_path}\n")

    if not created_pattern:
        print("\n--> RESULT: パターンが生成されませんでした")
        return
    
    return created_pattern


def generate_query():
    """パターンからCodeQLクエリを生成する

    Returns:
        str: 生成されたCodeQLクエリ
    """
    # 既存のパターンファイルを読み込み
    pattern_file_path = path_const.PATTERN / "diff_pattern.json"
    existing_patterns = []
    if os.path.exists(pattern_file_path):
        try:
            with open(pattern_file_path, "r", encoding="utf-8") as f:
                existing_patterns = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_patterns = []
    
    # パターンからCodeQLクエリを自動生成
    if(existing_patterns == []):
        print("--> パターンが存在しません.")
        return
    
    for pattern in existing_patterns:
        # パターンからクエリを生成
        print(f"--> クエリ生成中: {pattern["name"]}")
        codeql_query = query_generator.generate_query_from_pattern(pattern)

        if codeql_query is None:
            print(f"--> クエリ生成に失敗しました: {pattern["name"]}")
            continue
        print(f"--> クエリ生成成功: {pattern["name"]}")
        # 生成されたクエリをファイルに保存
        save_query_to_file(codeql_query, pattern["name"])
    
    print("\n--> 全てのパターンからのクエリ生成が完了しました。")


def save_query_to_file(codeql_query: str, pattern_name: str):
    """生成されたCodeQLクエリを.qlファイルとして保存する

    Args:
        codeql_query (str): 生成されたCodeQLクエリ
        pattern_name (str): パターン名

    Returns:
        /codeql_queries_js/{pattern_name}.ql: 生成されたCodeQLクエリファイル
    """
    # クエリ保存ディレクトリのパスを取得
    codeql_dir = path_const.QUERIES / "testQL"

    # ファイル名を生成（pattern_nameを小文字に変換し、.qlを付加）
    filename = f"{pattern_name.lower()}.ql"
    filepath = os.path.join(codeql_dir, filename)
    
    # ディレクトリが存在しない場合は作成
    os.makedirs(codeql_dir, exist_ok=True)
    
    # クエリをファイルに保存
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(codeql_query)
    
    print(f"--> クエリが保存されました: {filepath}")



def run_pipeline(slow_code: str, fast_code: str):
    """
    実装対に対して、パターン生成からクエリ生成までのパイプラインを実行する
    """
    print("="*50)
    print("Target Code Pair:")
    print("--- SLOW ---")
    print(slow_code.strip())
    print("\n--- FAST ---")
    print(fast_code.strip())
    print("="*50)

    # ステップ1: コードの差分からパターンを生成
    create_diff_pattern(000, slow_code, fast_code)

    # ステップ2: 生成されたパターンからCodeQLクエリを自動生成し保存
    generate_query()
    
    print("="*50)


if __name__ == "__main__":
    # --- テストケース：ループ内での不要なコンストラクタ呼び出し ---
    slow1 = """
    for (var i = 0; i < 100; i++) {
        var s = new String("hello");
    }"""
    fast1 = """
    for (var i = 0; i < 100; i++) {
        var s = "hello";
    }"""
    run_pipeline(slow1, fast1)