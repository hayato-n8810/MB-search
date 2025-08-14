/**
 * @name pattern_248_String_constructor
 * @description Automatically generated pattern from code diff.
 * @kind problem
 * @problem.severity warning
 * @id js/performance/pattern-248-string-constructor
 * @tags performance
 *       maintainability
 */

import javascript

from NewExpr newExpr
where
  newExpr.getCallee().(Identifier).getName() = "String"
select newExpr, "Automatically generated pattern from code diff."
