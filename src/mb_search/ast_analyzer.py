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

    for key in node1:
        if key not in node2 or key == 'loc':
            continue

        path_to_diff = [key]
        
        if isinstance(node1[key], list) and isinstance(node2[key], list):
            if len(node1[key]) != len(node2[key]):
                if len(node1[key]) > 0 and len(node2[key]) > 0:
                     diff_node, child_path = find_structural_difference(node1[key][0], node2[key][0])
                     if diff_node:
                         return diff_node, path_to_diff + [0] + child_path
                continue

            for i, (child1, child2) in enumerate(zip(node1[key], node2[key])):
                diff_node, child_path = find_structural_difference(child1, child2)
                if diff_node:
                    return diff_node, path_to_diff + [i] + child_path

        elif isinstance(node1[key], dict) and isinstance(node2[key], dict):
            diff_node, child_path = find_structural_difference(node1[key], node2[key])
            if diff_node:
                return diff_node, path_to_diff + child_path

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
#     for (var VAR_2 = 0; VAR_2 < 5000; VAR_2++) VAR_1 = VAR_1.concat([\"1\", \"2\"]);
#     """
#     fast2 = """
#     var VAR_1 = [];
#     for (var VAR_2 = 0; VAR_2 < 5000; VAR_2++) VAR_1.push(\"1\", \"2\");
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