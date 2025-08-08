# ASTの生成から構造的な差分を見つけるためのモジュール
import json
import subprocess
import os
import uuid
from functools import reduce

from mb_search import path_const

def generate_ast(code_snippet: str, filename="temp_code.js") -> dict:
    """与えられたコードスニペットからAST(JSON)を生成する"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code_snippet)
    
    # プロジェクトルートからの相対パスを使用
    ast_parser_path = path_const.JSCODE / "ast_parser.js"

    result = subprocess.run(
        ["node", ast_parser_path, filename],
        capture_output=True,
        text=True,
        check=True
    )
    
    os.remove(filename)

    # デバッグ：ASTをJSONとして出力
    # os.makedirs(path_const.JSCODE / "debug" / "ast", exist_ok=True)
    # debug_file = path_const.JSCODE / "debug" / "ast" / f"ast{uuid.uuid4()}.json"
    # print(f"AST debug file: {debug_file}")
    # with open(debug_file, "w", encoding="utf-8") as f:
    #     json.dump(json.loads(result.stdout), f, ensure_ascii=False, indent=2)

    return json.loads(result.stdout)

def find_structural_difference(node1: dict, node2: dict) -> tuple[dict | None, list]:
    """2つのASTノードを再帰的に比較し、構造的な差分を見つける"""
    if not isinstance(node1, dict) or not isinstance(node2, dict):
        return None, []
        
    if node1.get('type') != node2.get('type'):
        return node1, []

    # 'loc'キーを除いたすべてのキーを比較対象とする
    keys = set(node1.keys()) | set(node2.keys())
    keys.discard('loc')

    for key in sorted(list(keys)): # 順序を固定して再現性を担保
        
        # 片方のノードにしかキーが存在しない場合は差分とみなす
        if key not in node2:
            return node1, [key]
        if key not in node1:
            # fast_code側にのみ存在するノードは差分として扱わない
            continue

        path_to_diff = [key]
        val1 = node1[key]
        val2 = node2[key]
        
        if isinstance(val1, list) and isinstance(val2, list):
            # 共通の長さの部分を比較
            for i, (child1, child2) in enumerate(zip(val1, val2)):
                diff_node, child_path = find_structural_difference(child1, child2)
                if diff_node:
                    return diff_node, path_to_diff + [i] + child_path
            
            # リストの長さが異なる場合、slow_code側（node1）に余分な要素があればそれを差分とする
            if len(val1) > len(val2):
                return val1[len(val2)], path_to_diff + [len(val2)]

        elif isinstance(val1, dict) and isinstance(val2, dict):
            diff_node, child_path = find_structural_difference(val1, val2)
            if diff_node:
                return diff_node, path_to_diff + child_path
        
        # プリミティブな値が異なる場合は差分とする
        elif not isinstance(val1, (dict, list)) and val1 != val2:
            return node1, []

    return None, []

def _is_in_loop_recursive(ast_root: dict, path: list) -> bool:
    """指定されたパスの祖先にループ構造があるか再帰的に判定する（改良版）"""
    if not path:
        return False
    
    # パスを逆順に辿って親ノードをチェック
    for i in range(len(path), 0, -1):
        parent_path = path[:i]
        try:
            # ルートから指定されたパスのノードを取得
            current_node = _get_property_by_path(ast_root, parent_path)
            if isinstance(current_node, dict):
                node_type = current_node.get('type')
                # JavaScriptのループ構造を全て含める
                if node_type in [
                    'ForStatement',           # for (;;) {}
                    'WhileStatement',         # while () {}
                    'DoWhileStatement',       # do {} while ()
                    'ForInStatement',         # for (key in obj) {}
                    'ForOfStatement'          # for (value of iterable) {}
                ]:
                    return True
        except (KeyError, TypeError, IndexError):
            continue
    
    return False

def _get_property_by_path(node: dict, path: list):
    """ASTノードからパスでプロパティを取得するヘルパー関数"""
    try:
        return reduce(lambda d, k: d[k], path, node)
    except (KeyError, TypeError, IndexError):
        return None
    

# if __name__ == "__main__":
#     # テスト用のコードスニペット
#     code1 = """
#     for (var i = 0; i < 100; i++) {
#         var s = new String("hello");
#     }"""
#     code2 = """
#     for (var i = 0; i < 100; i++) {
#         var s = "hello";
#     }"""

#     slow2 = """
#     var VAR_1 = [];
#     VAR_1[1000000] = 10;
#     VAR_1.forEach(function () {}, VAR_1);
#     """
#     fast2 = """
#     var VAR_1 = [];
#     VAR_1[1000000] = 10;
#     var VAR_2 = 0;
#     for (var VAR_3 = 0; VAR_3 < VAR_1.length; VAR_3++) {
#         VAR_2++;
#     }
#     """

#     ast1 = generate_ast(slow2)
#     ast2 = generate_ast(fast2)
    
#     diff_node, path_to_diff = find_structural_difference(ast1, ast2)
    
#     if diff_node:
#         print("Structural difference found:")

#         # デバッグ：ASTをJSONとして出力
#         os.makedirs(path_const.JSCODE / "debug" / "diff", exist_ok=True)
#         debug_file = path_const.JSCODE / "debug" / "diff" / f"diff{uuid.uuid4()}.json"
#         print(f"DIFF debug file: {debug_file}")
#         with open(debug_file, "w", encoding="utf-8") as f:
#             json.dump(diff_node, f, ensure_ascii=False, indent=2)

#         print("\n" + "-" * 20 + "\n")
#         print("Path to difference:", path_to_diff)
#     else:
#         print("No structural difference found.")