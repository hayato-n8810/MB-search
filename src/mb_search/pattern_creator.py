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

    # AssignmentExpressionの場合、右辺のCallExpressionを検出対象にする
    if diff_node.get("type") == "AssignmentExpression" and "right" in diff_node:
        right_expr = diff_node["right"]
        if right_expr.get("type") == "CallExpression":
            diff_node = right_expr
            path_to_diff.append("right")

    pattern = {
        "name": "GeneratedPattern",
        "description": "Automatically generated pattern from code diff.",
        "target_node_type": diff_node["type"],
        "conditions": []
    }
    
    # CodeQLのAST構造に合わせた条件生成
    node_type = diff_node["type"]

    if node_type == "ExpressionStatement" and "expression" in diff_node:
        # ラッパーノードの場合は、中の式を解析対象にする
        diff_node = diff_node["expression"]
        path_to_diff.append("expression")
        node_type = diff_node["type"]
        pattern["target_node_type"] = node_type
    
    if node_type == "NewExpression":
        # NewExpr クラスに対応
        callee_name = ast_analyzer._get_property_by_path(diff_node, ["callee", "name"])
        if callee_name:
            pattern["conditions"].append({
                "type": "constructor_call",
                "constructor_name": callee_name,
                "path": ["callee", "name"]
            })
            pattern["name"] = f"pattern_{id}_{callee_name}_constructor"

    elif node_type == "CallExpression":
        # CallExpr クラスに対応
        # メソッド呼び出しの場合（variable.method()）
        if diff_node.get("callee", {}).get("type") == "MemberExpression":
            method_name = ast_analyzer._get_property_by_path(diff_node, ["callee", "property", "name"])
            object_name = ast_analyzer._get_property_by_path(diff_node, ["callee", "object", "name"])
            
            if method_name:
                pattern["conditions"].append({
                    "type": "method_call",
                    "method_name": method_name,
                    "object_name": object_name,
                    "path": ["callee", "property", "name"]
                })
                pattern["name"] = f"pattern_{id}_{method_name}_method"
                
                # 配列メソッドの特別な説明を追加
                if method_name in ["forEach", "push", "concat", "splice", "slice", "map", "filter", "reduce"]:
                    pattern["description"] = f"Detects {method_name} method calls that may have performance implications for arrays."
                else:
                    pattern["description"] = f"Detects {method_name} method calls that may have performance implications."
        
        # 関数呼び出しの場合
        else:
            function_name = ast_analyzer._get_property_by_path(diff_node, ["callee", "name"])
            if function_name:
                pattern["conditions"].append({
                    "type": "function_call",
                    "function_name": function_name,
                    "path": ["callee", "name"]
                })
                pattern["name"] = f"pattern_{id}_{function_name}_function"

    elif node_type == "Literal":
        # Literal クラスに対応
        value = diff_node.get("value")
        raw = diff_node.get("raw")
        if value is not None:
            pattern["conditions"].append({
                "type": "literal_value",
                "value": value,
                "raw": raw,
                "value_type": type(value).__name__
            })
            pattern["name"] = f"pattern_{id}_literal_{type(value).__name__}"

    elif node_type == "Identifier":
        # Identifier クラスに対応
        name = diff_node.get("name")
        if name:
            pattern["conditions"].append({
                "type": "identifier_name",
                "name": name
            })
            pattern["name"] = f"pattern_{id}_{name}_identifier"
    
    # コンテキスト条件の追加（改良版）
    context_conditions = _analyze_context(slow_ast, path_to_diff)
    pattern["conditions"].extend(context_conditions)
    
    # 条件に基づいてパターン名を調整
    for context in context_conditions:
        if context["type"] == "in_loop":
            pattern["name"] += "_in_loop"
        elif context["type"] == "in_function":
            pattern["name"] += "_in_function"

    if len(pattern["conditions"]) == 0:
        return None

    return pattern

def _analyze_context(ast_root: dict, path_to_diff: list) -> list:
    """差分ノードのコンテキストを分析してCodeQLクエリ用の条件を生成"""
    conditions = []
    
    # ループ内かどうかの判定（改良版）
    if ast_analyzer._is_in_loop_recursive(ast_root, path_to_diff):
        conditions.append({
            "type": "in_loop",
            "check": "is_in_loop"
        })
    
    # 関数内かどうかの判定
    if _is_in_function(ast_root, path_to_diff):
        conditions.append({
            "type": "in_function",
            "check": "is_in_function"
        })
    
    # 条件分岐内かどうかの判定
    if _is_in_conditional(ast_root, path_to_diff):
        conditions.append({
            "type": "in_conditional",
            "check": "is_in_conditional"
        })
    
    return conditions

def _is_in_function(ast_root: dict, path: list) -> bool:
    """指定されたパスが関数内にあるかチェック"""
    current_node = ast_root
    for i in range(len(path)):
        parent_path = path[:i+1]
        try:
            parent_node = ast_analyzer._get_property_by_path(ast_root, parent_path[:-1]) if len(parent_path) > 1 else ast_root
            if isinstance(parent_node, dict):
                node_type = parent_node.get("type")
                if node_type in ["FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"]:
                    return True
        except (KeyError, TypeError, IndexError):
            continue
    return False

def _is_in_conditional(ast_root: dict, path: list) -> bool:
    """指定されたパスが条件分岐内にあるかチェック"""
    current_node = ast_root
    for i in range(len(path)):
        parent_path = path[:i+1]
        try:
            parent_node = ast_analyzer._get_property_by_path(ast_root, parent_path[:-1]) if len(parent_path) > 1 else ast_root
            if isinstance(parent_node, dict):
                node_type = parent_node.get("type")
                if node_type in ["IfStatement", "ConditionalExpression", "SwitchStatement"]:
                    return True
        except (KeyError, TypeError, IndexError):
            continue
    return False