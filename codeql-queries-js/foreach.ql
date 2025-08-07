/**
 * @name General forEach performance warning
 * @description Detects forEach usage that could potentially be replaced with faster for loops
 * @kind problem
 * @problem.severity info
 * @id javascript/general-foreach-performance
 * @tags performance
 */

import javascript

from CallExpr forEachCall, PropAccess forEachAccess
where
  // forEach メソッド呼び出しを検出
  forEachCall.getCallee() = forEachAccess and
  forEachAccess.getPropertyName() = "forEach"

select forEachCall, "forEach detected. Consider using a for loop instead: 'for (var i = 0; i < array.length; ++i) {}' for better performance."
