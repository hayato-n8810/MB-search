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
  exists(Loop loop | loop.getBody().getAChildStmt*() = newExpr.getEnclosingStmt())
select newExpr, "Unnecessary String constructor call in loop detected."
