/**
 * @name pattern_132_VAR_1_identifier_in_loop
 * @description Automatically generated pattern from code diff.
 * @kind problem
 * @problem.severity warning
 * @id js/performance/pattern-132-var-1-identifier-in-loop
 * @tags performance
 *       maintainability
 */

import javascript

from Identifier identifier
where
  exists(LoopStmt loop | loop.getBody().getAChildStmt*() = identifier.getEnclosingStmt())
select identifier, "Automatically generated pattern from code diff."
