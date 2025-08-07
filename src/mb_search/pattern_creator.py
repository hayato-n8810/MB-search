# MBのAST差分からアンチパターンの検出ルールをヒューリスティックで作成する
import ast_analyzer

def create_pattern_from_diff(id: int, slow_code: str, fast_code: str) -> dict | None:
    """実装対の差分から、アンチパターンの定義を自動生成する

    Args:
        id (int): 実装対のID
        slow_code (str): 差分のパターンになる方
        fast_code (str): 差分のパターンにならない方

    Returns:
        dict | None: 生成されたパターン（差分がない場合はNone）
    """
    slow_ast = ast_analyzer.generate_ast(slow_code, "slow_temp.js")
    fast_ast = ast_analyzer.generate_ast(fast_code, "fast_temp.js")

    diff_node, path_to_diff = ast_analyzer.find_structural_difference(slow_ast, fast_ast)

    if not diff_node:
        return None

    pattern = {
        "name": "GeneratedPattern",
        "description": "Automatically generated pattern from code diff.",
        "target_node_type": diff_node['type'],
        "conditions": []
    }
    
    # --- ヒューリスティックに基づく推論 ---
    node_type = diff_node['type']
    if node_type == 'NewExpression':
        callee_name = ast_analyzer._get_property_by_path(diff_node, ['callee', 'name'])
        if callee_name:
            pattern['conditions'].append({
                "type": "property_equals",
                "path": ["callee", "name"],
                "value": callee_name
            })
            pattern['name'] = f"pattern_{id}_{callee_name}"

    elif node_type == 'CallExpression':
        method_name = ast_analyzer._get_property_by_path(diff_node, ['callee', 'property', 'name'])
        if method_name:
             pattern['conditions'].append({
                "type": "property_equals",
                "path": ["callee", "property", "name"],
                "value": method_name
            })
             pattern['name'] = f"pattern_{id}_{method_name}"
    
    # コンテキスト条件の追加
    if ast_analyzer._is_in_loop_recursive(slow_ast, path_to_diff):
        pattern['conditions'].append({
            "type": "context_check",
            "in_loop": "is_in_loop"
        })
        pattern['name'] += "InLoop"

    if len(pattern['conditions']) == 0:
        return None

    return pattern