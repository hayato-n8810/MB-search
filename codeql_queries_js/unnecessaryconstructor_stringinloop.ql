/**
 * @name UnnecessaryConstructor_StringInLoop
 * @description Automatically generated pattern from code diff.
 * @kind problem
 * @problem.severity warning
 * @id js/performance/unnecessaryconstructor_stringinloop
 */
import javascript

from NewExpr newExpr
where
  newExpr.getCallee().(Identifier).getName() = "String" and
  exists(Loop loop | newExpr.getContainer().getEnclosingStmt*() = loop.getBody().getAChildStmt*())
select newExpr, "Automatically generated pattern from code diff."
