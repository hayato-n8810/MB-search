# pattern_creator.pyで作成したパターンから CodeQLクエリを生成するモジュール

# CodeQL JavaScript/TypeScript AST クラスに基づいたクエリ生成

# CodeQLのAST クラスマッピング（公式ドキュメント準拠）
NODE_TYPE_TO_QL_CLASS = {
    "NewExpression": "NewExpr",
    "CallExpression": "CallExpr", 
    "Literal": "Literal",
    "Identifier": "Identifier",
    "MemberExpression": "PropAccess",
    "BinaryExpression": "BinaryExpr",
    "UnaryExpression": "UnaryExpr",
    "AssignmentExpression": "AssignExpr",
    "UpdateExpression": "UpdateExpr",
    "LogicalExpression": "LogicalBinaryExpr",
    "ConditionalExpression": "ConditionalExpr",
    "ArrayExpression": "ArrayExpr",
    "ObjectExpression": "ObjectExpr",
    "FunctionExpression": "FunctionExpr",
    "ArrowFunctionExpression": "ArrowFunctionExpr"
}

def _translate_conditions_to_where_clauses(pattern_conditions: list, ql_variable: str) -> str:
    """パターン条件をCodeQLのwhere句に変換"""
    where_clauses = []
    
    for cond in pattern_conditions:
        cond_type = cond["type"]
        
        # コンストラクタ呼び出しの条件
        if cond_type == "constructor_call":
            constructor_name = cond["constructor_name"]
            where_clauses.append(f"{ql_variable}.getCallee().(Identifier).getName() = '{constructor_name}'")

        # メソッド呼び出しの条件（CallExpr向け - プロパティアクセス）
        elif cond_type == "method_call":
            method_name = cond["method_name"]
            object_name = cond.get("object_name", "")
            
            # CallExprの場合：variable.method() パターン
            where_clauses.append(f"{ql_variable}.getCallee() instanceof PropAccess")
            where_clauses.append(f"{ql_variable}.getCallee().(PropAccess).getPropertyName() = '{method_name}'")

            # オブジェクト名の条件（VAR_で始まらない場合のみ）
            if object_name and not object_name.startswith("VAR_"):
                where_clauses.append(f"{ql_variable}.getCallee().(PropAccess).getBase().(VarAccess).getName() = '{object_name}'")

        # 関数呼び出しの条件
        elif cond_type == "function_call":
            function_name = cond["function_name"]
            # function_nameが"FUNCTION_"で始まらない場合にのみ関数名の条件を追加
            if not function_name.startswith("FUNCTION_"):
                where_clauses.append(f"{ql_variable}.getCallee().(Identifier).getName() = '{function_name}'")

        # リテラル値の条件
        elif cond_type == "literal_value":
            value = cond["value"]
            value_type = cond["value_type"]
            
            if value_type == "str":
                where_clauses.append(f"{ql_variable}.getValue() = '{value}'")
            elif value_type in ["int", "float"]:
                where_clauses.append(f"{ql_variable}.getValue() = '{value}'")
            elif value_type == "bool":
                where_clauses.append(f"{ql_variable}.getValue() = '{str(value).lower()}'")

        # 識別子名の条件
        elif cond_type == "identifier_name":
            name = cond["name"]
            # nameが"VAR_"で始まらない場合にのみ識別子名の条件を追加
            if not name.startswith("VAR_"):
                where_clauses.append(f"{ql_variable}.getName() = '{name}'")
        
        # コンテキスト条件
        elif cond_type == "in_loop":
            where_clauses.append(f"exists(LoopStmt loop | loop.getBody().getAChildStmt*() = {ql_variable}.getEnclosingStmt())")
        
        elif cond_type == "in_function":
            where_clauses.append(f"exists(Function func | func.getBody().getAChildStmt*() = {ql_variable}.getEnclosingStmt())")
        
        elif cond_type == "in_conditional":
            where_clauses.append(f"exists(IfStmt ifstmt | ifstmt.getAChildStmt*() = {ql_variable}.getEnclosingStmt())")

    return " and\n  ".join(where_clauses)

def generate_query_from_pattern(pattern: dict) -> str | None:
    """パターンからCodeQLクエリを生成"""
    if not pattern:
        return None

    pattern_name = pattern.get("name", "CustomGeneratedPattern")
    description = pattern.get("description", "No description provided.")
    node_type = pattern.get("target_node_type")
    conditions = pattern.get("conditions", [])
    
    # メソッド呼び出しパターンの特別処理を優先
    method_conditions = [c for c in conditions if c["type"] == "method_call"]
    if method_conditions and node_type == "CallExpression":
        return _generate_method_call_specific_query(pattern)
    
    # AssignmentExpressionの場合でもメソッド呼び出しがあれば特別処理
    if node_type == "AssignmentExpression" and method_conditions:
        return _generate_method_call_specific_query(pattern)
    
    ql_class = NODE_TYPE_TO_QL_CLASS.get(node_type)
    if not ql_class:
        print(f"[WARNING] 未対応のノードタイプ: {node_type}")
        return None

    # 変数名の生成
    ql_variable = ql_class[0].lower() + ql_class[1:]
    
    where_clauses = _translate_conditions_to_where_clauses(conditions, ql_variable)
    if not where_clauses:
        print(f"[WARNING] 変換可能な条件がありません: {pattern_name}")
        return None

    # CodeQLクエリテンプレート
    template = f"""/**
 * @name {pattern_name}
 * @description {description}
 * @kind problem
 * @problem.severity warning
 * @id js/performance/{pattern_name.lower().replace("_", "-")}
 * @tags performance
 *       maintainability
 */

import javascript

from {ql_class} {ql_variable}
where
  {where_clauses}
select {ql_variable}, "{description}"
"""
    return template

def _generate_method_call_specific_query(pattern: dict) -> str:
    """メソッド呼び出し専用のクエリ生成（CallExpr使用）"""
    pattern_name = pattern.get("name", "MethodCallPattern")
    description = pattern.get("description", "Method call pattern detected.")
    conditions = pattern.get("conditions", [])
    
    # メソッド呼び出し条件を抽出
    method_cond = next((c for c in conditions if c["type"] == "method_call"), None)
    if not method_cond:
        return None
    
    method_name = method_cond["method_name"]
    object_name = method_cond.get("object_name", "")
    
    # where句の構築
    where_clauses = []
    
    # メソッド呼び出しの基本条件（すべてのメソッドで共通）
    where_clauses.append("callExpr.getCallee() instanceof PropAccess")
    where_clauses.append(f"callExpr.getCallee().(PropAccess).getPropertyName() = '{method_name}'")
    
    # オブジェクト名の条件（VAR_で始まらない場合のみ）
    if object_name and not object_name.startswith("VAR_"):
        where_clauses.append(f"callExpr.getCallee().(PropAccess).getBase().(VarAccess).getName() = '{object_name}'")
    
    # コンテキスト条件を追加
    for cond in conditions:
        if cond["type"] == "in_loop":
            where_clauses.append("exists(LoopStmt loop | loop.getBody().getAChildStmt*() = callExpr.getEnclosingStmt())")
        elif cond["type"] == "in_function":
            where_clauses.append("exists(Function func | func.getBody().getAChildStmt*() = callExpr.getEnclosingStmt())")
        elif cond["type"] == "in_conditional":
            where_clauses.append("exists(IfStmt ifstmt | ifstmt.getAChildStmt*() = callExpr.getEnclosingStmt())")
    
    where_clause_str = " and\n  ".join(where_clauses)
    
    template = f"""/**
 * @name {pattern_name}
 * @description {description}
 * @kind problem
 * @problem.severity warning
 * @id js/performance/{pattern_name.lower().replace("_", "-")}
 * @tags performance
 *       maintainability
 */

import javascript

from CallExpr callExpr
where
  {where_clause_str}
select callExpr, "{description}"
"""
    
    return template

def generate_method_call_query(method_name: str, object_type: str = None) -> str:
    """メソッド呼び出しパターン専用クエリ"""
    
    object_condition = ""
    if object_type:
        object_condition = f"callExpr.getCallee().(PropAccess).getBase().getType().hasQualifiedName('{object_type}') and"

    return f"""/**
 * @name Method call pattern: {method_name}
 * @description Detects {method_name} method calls that may have performance implications
 * @kind problem  
 * @problem.severity warning
 * @id js/performance/method-call-{method_name.lower()}
 * @tags performance
 */

import javascript

from CallExpr callExpr
where
  callExpr.getCallee() instanceof PropAccess and
  {object_condition}
  callExpr.getCallee().(PropAccess).getPropertyName() = "{method_name}"
select callExpr, "Method call to {method_name} detected."
"""

# 配列メソッド専用クエリ生成
def generate_array_method_query(method_name: str) -> str:
    """配列メソッド呼び出し専用クエリ（forEach, push, concat等）"""
    
    return f"""/**
 * @name Array method call: {method_name}
 * @description Detects {method_name} method calls on arrays that may have performance implications
 * @kind problem
 * @problem.severity warning
 * @id js/performance/array-method-{method_name.lower()}
 * @tags performance
 *       arrays
 */

import javascript

from CallExpr callExpr
where
  callExpr.getCallee() instanceof PropAccess and
  callExpr.getCallee().(PropAccess).getPropertyName() = "{method_name}" and
  (
    callExpr.getCallee().(PropAccess).getBase().getType() instanceof ArrayType or
    callExpr.getCallee().(PropAccess).getBase().(VarAccess).getVariable().getAnAssignedExpr() instanceof ArrayExpr
  )
select callExpr, "Array method {method_name} call detected - consider performance implications."
"""

# 追加：より堅牢なループ検出のための代替バージョン
def _generate_robust_loop_detection(ql_variable: str) -> str:
    """より堅牢なループ検出条件を生成"""
    return f"""exists(LoopStmt loop | 
    loop.getBody().getAChildStmt*() = {ql_variable}.getEnclosingStmt() or
    {ql_variable}.getEnclosingStmt().getContainer*() = loop
  )"""

def _generate_alternative_loop_detection(ql_variable: str) -> str:
    """instanceof を使った代替ループ検出"""
    return f"{ql_variable}.getEnclosingStmt().getContainer*() instanceof LoopStmt"