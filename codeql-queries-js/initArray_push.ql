/**
 * @name Inefficient array initialization with push in loop
 * @description Detects inefficient array initialization patterns where empty arrays are filled using push() in loops
 * @kind problem
 * @problem.severity warning
 * @id javascript/inefficient-array-push-loop
 * @tags performance
 */

import javascript

from 
  VarDeclStmt varDecl, VariableDeclarator decl, ArrayExpr emptyArray,
  ForStmt loop, CallExpr pushCall, PropAccess pushAccess,
  VarAccess arrayAccess, Variable var
where
  // 空の配列で初期化された変数宣言を検出
  varDecl.getADecl() = decl and
  decl.getInit() = emptyArray and
  emptyArray.getSize() = 0 and
  decl.getBindingPattern().(VarDecl).getVariable() = var and
  
  // forループ内でpush呼び出しを検出
  pushCall.getEnclosingStmt().getParent*() = loop and
  pushCall.getCallee() = pushAccess and
  pushAccess.getPropertyName() = "push" and
  pushAccess.getBase() = arrayAccess and
  
  // 同じ変数に対するアクセスかチェック
  arrayAccess.getVariable() = var

select pushCall, "Inefficient array initialization detected: Empty array '" + var.getName() + "' is being populated with push() in a loop. Consider using typed arrays or Array constructor for better performance."