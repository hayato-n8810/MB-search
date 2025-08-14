/**
 * @name pattern_1_concat_method_in_loop
 * @description Detects concat method calls that may have performance implications for arrays.
 * @kind problem
 * @problem.severity warning
 * @id js/performance/pattern-1-concat-method-in-loop
 * @tags performance
 *       maintainability
 */

import javascript

from CallExpr callExpr
where
  callExpr.getCallee() instanceof PropAccess and
  callExpr.getCallee().(PropAccess).getPropertyName() = "concat" and
  exists(LoopStmt loop | loop.getBody().getAChildStmt*() = callExpr.getEnclosingStmt())
select callExpr, "Detects concat method calls that may have performance implications for arrays."
