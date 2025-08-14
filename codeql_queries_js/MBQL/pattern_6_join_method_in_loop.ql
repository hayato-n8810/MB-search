/**
 * @name pattern_6_join_method_in_loop
 * @description Detects join method calls that may have performance implications.
 * @kind problem
 * @problem.severity warning
 * @id js/performance/pattern-6-join-method-in-loop
 * @tags performance
 *       maintainability
 */

import javascript

from CallExpr callExpr
where
  callExpr.getCallee() instanceof PropAccess and
  callExpr.getCallee().(PropAccess).getPropertyName() = "join" and
  exists(LoopStmt loop | loop.getBody().getAChildStmt*() = callExpr.getEnclosingStmt())
select callExpr, "Detects join method calls that may have performance implications."
