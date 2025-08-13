# 差分からパターン生成・クエリ生成を行うメインのパイプライン
import json
import os
import pattern_creator
import query_generator

from mb_search import path_const


def create_pattern(id: int, slow_code: str, fast_code: str) -> dict:
    """コードの差分からslowコードのパターンを生成する

    Args:
        slow_code (str): MBの実装（遅いコード）
        fast_code (str): MBの実装（速いコード）

    Returns:
        dict: 生成されたパターン
    """
    # コードの差分からパターンを自動生成
    created_pattern = pattern_creator.create_pattern_from_diff(id, slow_code, fast_code)

    if not created_pattern:
        print("\n--> RESULT: パターンが生成されませんでした")
        return
    
    return created_pattern

def save_pattern(patterns: dict) -> None:
    """生成されたパターンをJSONファイルに保存する

    Args:
        pattern (dict): 生成されたパターンの辞書

    Returns:
        /src/pattern/MB_patterns.jsonにパターンが保存される
    """
    pattern_file_path = path_const.PATTERN / "MB_patterns.json"

    # パターンディレクトリが存在しない場合は作成
    os.makedirs(path_const.PATTERN, exist_ok=True)

    # 更新されたパターンリストをファイルに保存
    with open(pattern_file_path, "w", encoding="utf-8") as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)

    print(f"--> パターンが保存されました: {pattern_file_path}")


def create_query(pattern: dict) -> None:
    """パターンからCodeQLクエリを生成する

    Args:
        pattern (dict): 生成されたパターン

    Returns:
        /codeql_queries_js/MB_QL/にクエリが保存される
    """
    # パターンからクエリを生成
    codeql_query = query_generator.generate_query_from_pattern(pattern)

    if codeql_query is None:
        print(f"--> クエリ生成に失敗しました: {pattern['name']}")
        return None
    
    print(f"--> クエリ生成成功: {pattern['name']}")

    # 生成されたクエリをファイルに保存
    # クエリ保存ディレクトリのパスを取得
    codeql_dir = path_const.QUERIES / "testQL"
    # codeql_dir = path_const.QUERIES / "MBQL"

    # ファイル名を生成（pattern_nameを小文字に変換し、.qlを付加）
    filename = f"{pattern['name'].lower()}.ql"
    filepath = os.path.join(codeql_dir, filename)
    
    # ディレクトリが存在しない場合は作成
    os.makedirs(codeql_dir, exist_ok=True)
    
    # クエリをファイルに保存
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(codeql_query)
    
    print(f"--> クエリが保存されました: {filepath}")


def run_pipeline(slow_code: str, fast_code: str):
    """実装対に対してパターン生成からクエリ生成までのテストを行う

    Args:
        slow_code (str): 遅い実装のコード
        fast_code (str): 速い実装のコード
    """
    print("="*50)
    print("Target Code Pair:")
    print("--- SLOW ---")
    print(slow_code.strip())
    print("\n--- FAST ---")
    print(fast_code.strip())
    print("="*50)

    patterns = []
    # ステップ1: コードの差分からパターンを生成
    patterns.append(create_pattern(000, slow_code, fast_code))

    # ステップ2: 生成されたパターンをJSONファイルに保存
    save_pattern(patterns)

    # ステップ3: 生成されたパターンからCodeQLクエリを自動生成し保存
    for pattern in patterns:
        if pattern:  # Noneでない場合のみ
            create_query(pattern)


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
    # run_pipeline(slow1, fast1)


    # # マイクロベンチマークでパターン生成およびクエリ生成
    # # MB_codes = f"{path_const.MB_DATA}/codes.json"
    # MB_codes = f"{path_const.MB_DATA}/mb_speed_diff_sort.json"

    # # 何件利用するか
    # MAX_ITEMS = 1

    # # JSONファイル読み込み
    # with open(MB_codes, "r", encoding="utf-8") as f:
    #     MB_data = json.load(f)[:MAX_ITEMS]

    # patterns = []
    # for id, item in enumerate(MB_data):
    #     slow_code = item["slow"]
    #     fast_code = item["fast"]
    #     # コードの差分からパターンを生成
    #     patterns.append(create_pattern(id, slow_code, fast_code))

    # # ステップ2: 生成されたパターンをJSONファイルに保存
    # save_pattern(patterns)

    # # ステップ3: 生成されたパターンからCodeQLクエリを自動生成し保存
    # for pattern in patterns:
    #     if pattern:  # Noneでない場合のみ
    #         create_query(pattern)
