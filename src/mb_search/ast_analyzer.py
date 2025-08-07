# ASTの生成から構造的な差分を見つけるためのモジュール
import json
import subprocess
import os
from functools import reduce

def generate_ast(code_snippet: str, filename="temp_code.js") -> dict:
    """与えられたコードスニペットからAST(JSON)を生成する"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code_snippet)
    
    # プロジェクトルートからの相対パスを使用
    ast_parser_path = os.path.join(os.path.dirname(__file__), "..", "..", "js_code", "ast_parser.js")
    
    result = subprocess.run(
        ["node", ast_parser_path, filename],
        capture_output=True,
        text=True,
        check=True
    )
    
    os.remove(filename)
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
    """指定されたパスの祖先にループ構造があるか再帰的に判定する"""
    if not path:
        return False
        
    parent_path = path[:-1]
    current_node = _get_property_by_path(ast_root, parent_path)
    
    if current_node and isinstance(current_node, dict) and current_node.get('type') in ['ForStatement', 'WhileStatement', 'DoWhileStatement', 'ForInStatement', 'ForOfStatement']:
        return True
        
    return _is_in_loop_recursive(ast_root, parent_path)

def _get_property_by_path(node: dict, path: list):
    """ASTノードからパスでプロパティを取得するヘルパー関数"""
    try:
        return reduce(lambda d, k: d[k], path, node)
    except (KeyError, TypeError, IndexError):
        return None