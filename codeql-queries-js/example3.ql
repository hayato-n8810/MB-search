/**
 * @name Unnecessary String constructor call in a loop
 * @description Finds 'new String()' calls inside loops. Using string literals is more performant.
 * @kind problem
 * @problem.severity warning
 * @id js/performance/unnecessary-string-constructor-in-loop
 */
import javascript

from NewExpr newStringExpr, LoopStmt loop
where
  // 呼び出されているコンストラクタが "String" であることを確認
  newStringExpr.getCallee().(Identifier).getName() = "String" and
  // その呼び出しがループ内に存在することを確認
  loop.getBody().getAChildStmt*() = newStringExpr.getEnclosingStmt()
select newStringExpr, "Unnecessary String constructor call in a loop. Use a string literal '...' for better performance."