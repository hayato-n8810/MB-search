/**
 * @name pattern_195_map_identifier
 * @description Automatically generated pattern from code diff.
 * @kind problem
 * @problem.severity warning
 * @id js/performance/pattern-195-map-identifier
 * @tags performance
 *       maintainability
 */

import javascript

from Identifier identifier
where
  identifier.getName() = "map"
select identifier, "Automatically generated pattern from code diff."
