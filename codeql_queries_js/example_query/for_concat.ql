/**
 * @name Array concat in loop
 * @description Detects usage of array concat method inside loops which can be inefficient
 * @kind problem
 * @problem.severity warning
 * @id js/performance/array-concat-in-loop
 * @tags performance
 *       maintainability
 */

import javascript

from MethodCallExpr concatCall, LoopStmt loop
where
  // concatメソッドの呼び出しを検出
  concatCall.getMethodName() = "concat" and
  // ループの本体内に含まれているかチェック
  loop.getBody().getAChildStmt*() = concatCall.getEnclosingStmt()
select concatCall, "Array concat method called inside loop. Consider using push() or other efficient alternatives for better performance."