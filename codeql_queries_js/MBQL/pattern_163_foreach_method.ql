/**
 * @name pattern_163_forEach_method
 * @description Detects forEach method calls that may have performance implications for arrays.
 * @kind problem
 * @problem.severity warning
 * @id js/performance/pattern-163-foreach-method
 * @tags performance
 *       maintainability
 */

import javascript

from CallExpr callExpr
where
  callExpr.getCallee() instanceof PropAccess and
  callExpr.getCallee().(PropAccess).getPropertyName() = "forEach"
select callExpr, "Detects forEach method calls that may have performance implications for arrays."
