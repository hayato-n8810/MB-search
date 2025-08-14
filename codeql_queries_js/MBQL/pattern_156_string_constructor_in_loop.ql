/**
 * @name pattern_156_String_constructor_in_loop
 * @description Automatically generated pattern from code diff.
 * @kind problem
 * @problem.severity warning
 * @id js/performance/pattern-156-string-constructor-in-loop
 * @tags performance
 *       maintainability
 */

import javascript

from NewExpr newExpr
where
  newExpr.getCallee().(Identifier).getName() = "String" and
  exists(LoopStmt loop | loop.getBody().getAChildStmt*() = newExpr.getEnclosingStmt())
select newExpr, "Automatically generated pattern from code diff."
