# pattern_creator.pyで作成したパターンから CodeQLクエリを生成するモジュール
NODE_TYPE_TO_QL_CLASS = {
    "NewExpression": "NewExpr",
    "CallExpression": "MethodCall",
}

PATH_TO_QL_PREDICATE = {
    "['callee', 'name']": ".getCallee().(Identifier).getName()",
    "['callee', 'property', 'name']": ".getMethodName()",
}

def _translate_conditions_to_where_clauses(pattern_conditions: list, ql_variable: str) -> str:
    where_clauses = []
    for cond in pattern_conditions:
        cond_type = cond['type']
        
        if cond_type == 'context_check' and cond['check'] == 'is_in_loop':
            # CodeQLで正しく動作するループ検出ロジックを使用
            where_clauses.append(f"exists(Loop loop | {ql_variable}.getContainer().getEnclosingStmt*() = loop.getBody().getAChildStmt*())")
            continue

        path_str = str(cond.get('path', []))
        predicate = PATH_TO_QL_PREDICATE.get(path_str)
        if not predicate: continue
            
        ql_expression = f"{ql_variable}{predicate}"
        value = cond['value']

        if cond_type == 'property_equals':
            where_clauses.append(f'{ql_expression} = "{value}"')
        
        elif cond_type == 'property_in':
            in_clause = " or ".join([f'{ql_expression} = "{v}"' for v in value])
            where_clauses.append(f"({in_clause})")

    return " and\n  ".join(where_clauses)

def generate_query_from_pattern(pattern: dict) -> str:
    """単一のパターン定義オブジェクトからCodeQLクエリ文字列を生成する"""
    if not pattern: return "-- [ERROR] Invalid pattern provided."

    pattern_name = pattern.get('name', 'CustomGeneratedPattern')
    description = pattern.get('description', 'No description provided.')
    node_type = pattern.get('target_node_type')
    
    ql_class = NODE_TYPE_TO_QL_CLASS.get(node_type)
    if not ql_class: return f"-- [ERROR] No QL class for node: {node_type}"

    ql_variable = ql_class[0].lower() + ql_class[1:]
    where_clauses = _translate_conditions_to_where_clauses(pattern.get('conditions', []), ql_variable)
    if not where_clauses: return f"-- [WARN] No translatable conditions for: {pattern_name}"

    template = f"""/**
 * @name {pattern_name}
 * @description {description}
 * @kind problem
 * @problem.severity warning
 * @id js/performance/{pattern_name.lower()}
 */
import javascript

from {ql_class} {ql_variable}
where
  {where_clauses}
select {ql_variable}, "{description}"
"""
    return template