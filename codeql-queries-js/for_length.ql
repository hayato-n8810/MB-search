/**
 * @name Detect for loops that iterate array length
 * @description Finds for loops that iterate over array length, which might be inefficient
 * @kind problem
 * @problem.severity warning
 * @id javascript/for-loop-array-length
 */

import javascript

from ForStmt forStmt, PropAccess lengthAccess, Variable arrayVar
where
  // for文の条件部分で .length プロパティが使用されている
  lengthAccess.getPropertyName() = "length" and
  // lengthアクセスがfor文のテスト条件に含まれている
  forStmt.getTest().getAChild*() = lengthAccess and
  // 配列変数を特定
  lengthAccess.getBase().(VarAccess).getVariable() = arrayVar and
  // for文の中で同じ配列変数がインデックスアクセスされている可能性がある
  exists(IndexExpr idx |
    idx.getBase().(VarAccess).getVariable() = arrayVar and
    idx.getParent+() = forStmt.getBody()
  )
select forStmt, "For loop iterates over array '" + arrayVar.getName() + "' using .length property, consider using for-of or forEach instead."