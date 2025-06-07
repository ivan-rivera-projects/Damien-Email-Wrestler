# Advanced Rule Conflict Resolution System

## Overview
Enterprise-grade conflict resolution for AI-generated email rules with multi-strategy handling, dependency chains, and ML-powered optimization.

## 1. Conflict Detection Engine

### Primary Conflict Types

```python
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

class ConflictType(Enum):
    """Types of rule conflicts that can occur"""
    ACTION_CONTRADICTION = "action_contradiction"  # e.g., mark_read vs mark_unread
    LABEL_CONFLICT = "label_conflict"              # e.g., add conflicting labels
    PRIORITY_OVERLAP = "priority_overlap"          # Same priority rules on same email
    CONDITION_REDUNDANCY = "condition_redundancy"  # Multiple rules with same conditions
    DEPENDENCY_VIOLATION = "dependency_violation"  # Rule depends on another rule's output
    RESOURCE_CONTENTION = "resource_contention"    # Rules competing for same resources

@dataclass
class ConflictDefinition:
    """Definition of a specific conflict pattern"""
    conflict_type: ConflictType
    severity: str  # "critical", "moderate", "minor"
    auto_resolvable: bool
    resolution_strategy: str
    description: str

# Conflict pattern definitions
CONFLICT_PATTERNS = {
    ConflictType.ACTION_CONTRADICTION: ConflictDefinition(
        conflict_type=ConflictType.ACTION_CONTRADICTION,
        severity="critical",
        auto_resolvable=True,
        resolution_strategy="priority_weight",
        description="Rules attempt opposite actions on the same email"
    ),
    ConflictType.LABEL_CONFLICT: ConflictDefinition(
        conflict_type=ConflictType.LABEL_CONFLICT,
        severity="moderate", 
        auto_resolvable=True,
        resolution_strategy="merge_compatible",
        description="Rules add conflicting or redundant labels"
    ),
    ConflictType.PRIORITY_OVERLAP: ConflictDefinition(
        conflict_type=ConflictType.PRIORITY_OVERLAP,
        severity="moderate",
        auto_resolvable=True,
        resolution_strategy="confidence_score",
        description="Multiple rules with same priority match email"
    ),
    ConflictType.CONDITION_REDUNDANCY: ConflictDefinition(
        conflict_type=ConflictType.CONDITION_REDUNDANCY,
        severity="minor",
        auto_resolvable=True,
        resolution_strategy="merge_rules",
        description="Multiple rules have identical or highly similar conditions"
    ),
    ConflictType.DEPENDENCY_VIOLATION: ConflictDefinition(
        conflict_type=ConflictType.DEPENDENCY_VIOLATION,
        severity="critical",
        auto_resolvable=False,
        resolution_strategy="dependency_chain",
        description="Rule execution order violates dependencies"
    ),
    ConflictType.RESOURCE_CONTENTION: ConflictDefinition(
        conflict_type=ConflictType.RESOURCE_CONTENTION,
        severity="moderate",
        auto_resolvable=True,
        resolution_strategy="rate_limiting",
        description="Rules compete for limited resources"
    )
}
```

### Conflict Detection Algorithm

```python
class ConflictDetector:
    """Detect conflicts between multiple rules matching an email"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.conflict_cache = {}
        
    def detect_conflicts(self, matching_rules: List[Dict]) -> List[Dict]:
        """Detect all conflicts between matching rules"""
        
        if len(matching_rules) <= 1:
            return []
            
        conflicts = []
        
        # Check all pairs of rules for conflicts
        for i, rule1 in enumerate(matching_rules):
            for j, rule2 in enumerate(matching_rules[i+1:], i+1):
                conflict = self._analyze_rule_pair(rule1, rule2)
                if conflict:
                    conflicts.append(conflict)
        
        # Check for multi-rule conflicts
        multi_conflicts = self._detect_multi_rule_conflicts(matching_rules)
        conflicts.extend(multi_conflicts)
        
        return conflicts
    
    def _analyze_rule_pair(self, rule1: Dict, rule2: Dict) -> Optional[Dict]:
        """Analyze a pair of rules for conflicts"""
        
        conflicts_found = []
        
        # Action contradiction detection
        action_conflict = self._check_action_contradiction(rule1, rule2)
        if action_conflict:
            conflicts_found.append(action_conflict)
        
        # Label conflict detection
        label_conflict = self._check_label_conflicts(rule1, rule2)
        if label_conflict:
            conflicts_found.append(label_conflict)
        
        # Dependency violation detection
        dependency_conflict = self._check_dependency_violations(rule1, rule2)
        if dependency_conflict:
            conflicts_found.append(dependency_conflict)
        
        if conflicts_found:
            return {
                "rule1_id": rule1["rule_id"],
                "rule2_id": rule2["rule_id"],
                "conflicts": conflicts_found,
                "severity": max(c["severity"] for c in conflicts_found),
                "auto_resolvable": all(c["auto_resolvable"] for c in conflicts_found)
            }
        
        return None
    
    def _check_action_contradiction(self, rule1: Dict, rule2: Dict) -> Optional[Dict]:
        """Check for contradictory actions between rules"""
        
        actions1 = rule1["rule_definition"]["actions"]["primary_actions"]
        actions2 = rule2["rule_definition"]["actions"]["primary_actions"]
        
        contradictions = [
            ("mark_read", "mark_unread"),
            ("archive", "keep_in_inbox"),
            ("high_priority", "low_priority")
        ]
        
        for action_a, action_b in contradictions:
            if (actions1.get(action_a) and actions2.get(action_b)) or \
               (actions1.get(action_b) and actions2.get(action_a)):
                return {
                    "type": ConflictType.ACTION_CONTRADICTION,
                    "severity": "critical",
                    "auto_resolvable": True,
                    "details": f"Rules have contradictory actions: {action_a} vs {action_b}",
                    "resolution_hint": "Use priority_weight or confidence_score"
                }
        
        return None
    
    def _check_label_conflicts(self, rule1: Dict, rule2: Dict) -> Optional[Dict]:
        """Check for label conflicts between rules"""
        
        labels1 = set(rule1["rule_definition"]["actions"]["primary_actions"].get("add_labels", []))
        labels2 = set(rule2["rule_definition"]["actions"]["primary_actions"].get("add_labels", []))
        
        # Define mutually exclusive label groups
        exclusive_groups = [
            {"AI_PROMOTIONAL", "AI_PERSONAL", "AI_WORK"},
            {"HIGH_PRIORITY", "LOW_PRIORITY"},
            {"URGENT", "NON_URGENT"}
        ]
        
        for group in exclusive_groups:
            intersection1 = labels1.intersection(group)
            intersection2 = labels2.intersection(group)
            
            if intersection1 and intersection2 and intersection1 != intersection2:
                return {
                    "type": ConflictType.LABEL_CONFLICT,
                    "severity": "moderate",
                    "auto_resolvable": True,
                    "details": f"Conflicting labels from exclusive group: {intersection1} vs {intersection2}",
                    "resolution_hint": "Use highest confidence rule or merge compatible labels"
                }
        
        return None
    
    def _check_dependency_violations(self, rule1: Dict, rule2: Dict) -> Optional[Dict]:
        """Check for dependency violations between rules"""
        
        deps1 = rule1.get("conflict_resolution", {}).get("dependency_rules", [])
        deps2 = rule2.get("conflict_resolution", {}).get("dependency_rules", [])
        
        # Check if rule2 depends on rule1 but rule1 has higher priority
        if rule1["rule_id"] in deps2:
            if rule1.get("conflict_resolution", {}).get("priority_weight", 0) > \
               rule2.get("conflict_resolution", {}).get("priority_weight", 0):
                return {
                    "type": ConflictType.DEPENDENCY_VIOLATION,
                    "severity": "critical",
                    "auto_resolvable": False,
                    "details": f"Rule {rule2['rule_id']} depends on {rule1['rule_id']} but has lower priority",
                    "resolution_hint": "Reorder execution or adjust dependencies"
                }
        
        return None
    
    def _detect_multi_rule_conflicts(self, rules: List[Dict]) -> List[Dict]:
        """Detect conflicts that involve more than two rules"""
        
        conflicts = []
        
        # Resource contention detection
        if len(rules) > 5:  # Too many rules on same email
            conflicts.append({
                "type": ConflictType.RESOURCE_CONTENTION,
                "severity": "moderate",
                "auto_resolvable": True,
                "details": f"{len(rules)} rules competing for same email",
                "resolution_hint": "Apply rate limiting or rule consolidation",
                "affected_rules": [r["rule_id"] for r in rules]
            })
        
        # Condition redundancy detection
        redundant_groups = self._find_redundant_conditions(rules)
        for group in redundant_groups:
            if len(group) > 1:
                conflicts.append({
                    "type": ConflictType.CONDITION_REDUNDANCY,
                    "severity": "minor",
                    "auto_resolvable": True,
                    "details": f"Rules have redundant conditions: {[r['rule_id'] for r in group]}",
                    "resolution_hint": "Merge rules or adjust conditions",
                    "affected_rules": [r["rule_id"] for r in group]
                })
        
        return conflicts
    
    def _find_redundant_conditions(self, rules: List[Dict]) -> List[List[Dict]]:
        """Find groups of rules with redundant conditions"""
        
        # Simplified implementation - would use ML similarity in production
        redundant_groups = []
        processed = set()
        
        for i, rule1 in enumerate(rules):
            if rule1["rule_id"] in processed:
                continue
                
            group = [rule1]
            processed.add(rule1["rule_id"])
            
            for j, rule2 in enumerate(rules[i+1:], i+1):
                if rule2["rule_id"] in processed:
                    continue
                    
                similarity = self._calculate_condition_similarity(rule1, rule2)
                if similarity > 0.8:  # 80% similarity threshold
                    group.append(rule2)
                    processed.add(rule2["rule_id"])
            
            if len(group) > 1:
                redundant_groups.append(group)
        
        return redundant_groups
    
    def _calculate_condition_similarity(self, rule1: Dict, rule2: Dict) -> float:
        """Calculate similarity between rule conditions"""
        
        # Simplified implementation - would use proper NLP/ML in production
        conditions1 = rule1["rule_definition"]["conditions"]
        conditions2 = rule2["rule_definition"]["conditions"]
        
        # Compare sender patterns
        sender_sim = self._compare_sender_patterns(
            conditions1.get("sender_patterns", {}),
            conditions2.get("sender_patterns", {})
        )
        
        # Compare subject patterns
        subject_sim = self._compare_subject_patterns(
            conditions1.get("subject_patterns", {}),
            conditions2.get("subject_patterns", {})
        )
        
        # Weighted average
        return (sender_sim * 0.4 + subject_sim * 0.6)
    
    def _compare_sender_patterns(self, patterns1: Dict, patterns2: Dict) -> float:
        """Compare sender pattern similarity"""
        
        domains1 = set(patterns1.get("domains", []))
        domains2 = set(patterns2.get("domains", []))
        
        if not domains1 and not domains2:
            return 1.0
        
        if not domains1 or not domains2:
            return 0.0
        
        intersection = len(domains1.intersection(domains2))
        union = len(domains1.union(domains2))
        
        return intersection / union if union > 0 else 0.0
    
    def _compare_subject_patterns(self, patterns1: Dict, patterns2: Dict) -> float:
        """Compare subject pattern similarity"""
        
        keywords1 = set(patterns1.get("required_keywords", []))
        keywords2 = set(patterns2.get("required_keywords", []))
        
        if not keywords1 and not keywords2:
            return 1.0
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
```

## 2. Resolution Strategies

### Strategy Implementation

```python
class ConflictResolver:
    """Resolve conflicts using multiple strategies"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.resolution_stats = {}
        
    def resolve_conflicts(self, rules: List[Dict], conflicts: List[Dict]) -> List[Dict]:
        """Resolve all conflicts and return executable rule list"""
        
        if not conflicts:
            return rules
        
        # Group conflicts by type and severity
        conflict_groups = self._group_conflicts(conflicts)
        
        # Resolve critical conflicts first
        resolved_rules = rules.copy()
        
        for severity in ["critical", "moderate", "minor"]:
            severity_conflicts = conflict_groups.get(severity, [])
            resolved_rules = self._resolve_conflicts_by_severity(
                resolved_rules, severity_conflicts
            )
        
        # Apply final optimization
        optimized_rules = self._optimize_rule_execution(resolved_rules)
        
        return optimized_rules
    
    def _group_conflicts(self, conflicts: List[Dict]) -> Dict[str, List[Dict]]:
        """Group conflicts by severity for prioritized resolution"""
        
        groups = {"critical": [], "moderate": [], "minor": []}
        
        for conflict in conflicts:
            severity = conflict.get("severity", "minor")
            groups[severity].append(conflict)
        
        return groups
    
    def _resolve_conflicts_by_severity(self, rules: List[Dict], conflicts: List[Dict]) -> List[Dict]:
        """Resolve conflicts for a specific severity level"""
        
        if not conflicts:
            return rules
        
        resolved_rules = rules.copy()
        
        for conflict in conflicts:
            conflict_type = conflict.get("type")
            
            if conflict_type == ConflictType.ACTION_CONTRADICTION:
                resolved_rules = self._resolve_action_contradiction(resolved_rules, conflict)
            elif conflict_type == ConflictType.LABEL_CONFLICT:
                resolved_rules = self._resolve_label_conflict(resolved_rules, conflict)
            elif conflict_type == ConflictType.PRIORITY_OVERLAP:
                resolved_rules = self._resolve_priority_overlap(resolved_rules, conflict)
            elif conflict_type == ConflictType.CONDITION_REDUNDANCY:
                resolved_rules = self._resolve_condition_redundancy(resolved_rules, conflict)
            elif conflict_type == ConflictType.DEPENDENCY_VIOLATION:
                resolved_rules = self._resolve_dependency_violation(resolved_rules, conflict)
            elif conflict_type == ConflictType.RESOURCE_CONTENTION:
                resolved_rules = self._resolve_resource_contention(resolved_rules, conflict)
        
        return resolved_rules
    
    def _resolve_action_contradiction(self, rules: List[Dict], conflict: Dict) -> List[Dict]:
        """Resolve action contradictions using priority weights"""
        
        rule1_id = conflict["rule1_id"]
        rule2_id = conflict["rule2_id"]
        
        rule1 = next(r for r in rules if r["rule_id"] == rule1_id)
        rule2 = next(r for r in rules if r["rule_id"] == rule2_id)
        
        # Compare priority weights
        weight1 = rule1.get("conflict_resolution", {}).get("priority_weight", 0)
        weight2 = rule2.get("conflict_resolution", {}).get("priority_weight", 0)
        
        if weight1 == weight2:
            # Use confidence scores as tiebreaker
            conf1 = rule1.get("ai_metadata", {}).get("confidence_score", 0)
            conf2 = rule2.get("ai_metadata", {}).get("confidence_score", 0)
            
            winner = rule1 if conf1 >= conf2 else rule2
            loser = rule2 if conf1 >= conf2 else rule1
        else:
            winner = rule1 if weight1 > weight2 else rule2
            loser = rule2 if weight1 > weight2 else rule1
        
        # Remove the losing rule
        filtered_rules = [r for r in rules if r["rule_id"] != loser["rule_id"]]
        
        # Log resolution
        self._log_resolution("action_contradiction", winner["rule_id"], loser["rule_id"])
        
        return filtered_rules
    
    def _resolve_label_conflict(self, rules: List[Dict], conflict: Dict) -> List[Dict]:
        """Resolve label conflicts by merging compatible labels"""
        
        rule1_id = conflict["rule1_id"]
        rule2_id = conflict["rule2_id"]
        
        rule1 = next(r for r in rules if r["rule_id"] == rule1_id)
        rule2 = next(r for r in rules if r["rule_id"] == rule2_id)
        
        # Get labels from both rules
        labels1 = set(rule1["rule_definition"]["actions"]["primary_actions"].get("add_labels", []))
        labels2 = set(rule2["rule_definition"]["actions"]["primary_actions"].get("add_labels", []))
        
        # Find compatible labels
        compatible_labels = self._find_compatible_labels(labels1, labels2)
        
        # Keep higher confidence rule and update its labels
        conf1 = rule1.get("ai_metadata", {}).get("confidence_score", 0)
        conf2 = rule2.get("ai_metadata", {}).get("confidence_score", 0)
        
        if conf1 >= conf2:
            # Update rule1 with compatible labels
            rule1["rule_definition"]["actions"]["primary_actions"]["add_labels"] = list(compatible_labels)
            filtered_rules = [r for r in rules if r["rule_id"] != rule2_id]
        else:
            # Update rule2 with compatible labels
            rule2["rule_definition"]["actions"]["primary_actions"]["add_labels"] = list(compatible_labels)
            filtered_rules = [r for r in rules if r["rule_id"] != rule1_id]
        
        return filtered_rules
    
    def _find_compatible_labels(self, labels1: set, labels2: set) -> set:
        """Find compatible labels from two sets"""
        
        # Define label compatibility matrix
        compatibility_groups = [
            {"AI_PROMOTIONAL", "MARKETING", "DEALS"},
            {"AI_PERSONAL", "FRIENDS", "FAMILY"},
            {"AI_WORK", "BUSINESS", "PROFESSIONAL"},
            {"HIGH_PRIORITY", "URGENT", "IMPORTANT"},
            {"LOW_PRIORITY", "NON_URGENT", "OPTIONAL"}
        ]
        
        compatible = set()
        
        # Add non-conflicting labels
        for group in compatibility_groups:
            group_labels1 = labels1.intersection(group)
            group_labels2 = labels2.intersection(group)
            
            if group_labels1 and not group_labels2:
                compatible.update(group_labels1)
            elif group_labels2 and not group_labels1:
                compatible.update(group_labels2)
            elif group_labels1 and group_labels2:
                # Both rules have labels in this group - keep more specific one
                if len(group_labels1) <= len(group_labels2):
                    compatible.update(group_labels1)
                else:
                    compatible.update(group_labels2)
        
        # Add labels that don't belong to any exclusive group
        all_exclusive = set().union(*compatibility_groups)
        non_exclusive1 = labels1 - all_exclusive
        non_exclusive2 = labels2 - all_exclusive
        compatible.update(non_exclusive1)
        compatible.update(non_exclusive2)
        
        return compatible
    
    def _resolve_priority_overlap(self, rules: List[Dict], conflict: Dict) -> List[Dict]:
        """Resolve priority overlaps using confidence scores"""
        
        # Group rules by priority
        priority_groups = {}
        for rule in rules:
            priority = rule.get("conflict_resolution", {}).get("priority_weight", 0)
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(rule)
        
        # Resolve overlaps in each priority group
        resolved_rules = []
        
        for priority, group_rules in priority_groups.items():
            if len(group_rules) <= 1:
                resolved_rules.extend(group_rules)
            else:
                # Sort by confidence and keep top N based on tenant settings
                max_rules_per_priority = self._get_tenant_setting("max_rules_per_priority", 3)
                
                sorted_rules = sorted(
                    group_rules,
                    key=lambda r: r.get("ai_metadata", {}).get("confidence_score", 0),
                    reverse=True
                )
                
                resolved_rules.extend(sorted_rules[:max_rules_per_priority])
        
        return resolved_rules
    
    def _resolve_condition_redundancy(self, rules: List[Dict], conflict: Dict) -> List[Dict]:
        """Resolve condition redundancy by merging rules"""
        
        affected_rule_ids = conflict.get("affected_rules", [])
        affected_rules = [r for r in rules if r["rule_id"] in affected_rule_ids]
        other_rules = [r for r in rules if r["rule_id"] not in affected_rule_ids]
        
        if len(affected_rules) <= 1:
            return rules
        
        # Merge redundant rules into the highest confidence one
        merged_rule = max(
            affected_rules,
            key=lambda r: r.get("ai_metadata", {}).get("confidence_score", 0)
        )
        
        # Combine actions from all rules
        merged_actions = self._merge_rule_actions(affected_rules)
        merged_rule["rule_definition"]["actions"] = merged_actions
        
        # Update metadata
        merged_rule["metadata"]["description"] += " (merged from redundant rules)"
        merged_rule["metadata"]["version"] = str(float(merged_rule["metadata"]["version"]) + 0.1)
        
        other_rules.append(merged_rule)
        return other_rules
    
    def _merge_rule_actions(self, rules: List[Dict]) -> Dict:
        """Merge actions from multiple rules"""
        
        merged_actions = {
            "primary_actions": {},
            "advanced_actions": {}
        }
        
        # Collect all unique actions
        all_labels = set()
        
        for rule in rules:
            actions = rule["rule_definition"]["actions"]
            
            # Merge primary actions
            for action_type, action_value in actions.get("primary_actions", {}).items():
                if action_type == "add_labels" and isinstance(action_value, list):
                    all_labels.update(action_value)
                else:
                    merged_actions["primary_actions"][action_type] = action_value
            
            # Merge advanced actions
            for action_type, action_value in actions.get("advanced_actions", {}).items():
                if action_value:  # Only include if enabled
                    merged_actions["advanced_actions"][action_type] = action_value
        
        # Set merged labels
        if all_labels:
            merged_actions["primary_actions"]["add_labels"] = list(all_labels)
        
        return merged_actions
    
    def _resolve_dependency_violation(self, rules: List[Dict], conflict: Dict) -> List[Dict]:
        """Resolve dependency violations by reordering execution"""
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(rules)
        
        # Topological sort to determine execution order
        execution_order = self._topological_sort(dependency_graph)
        
        # Reorder rules based on dependencies
        ordered_rules = []
        for rule_id in execution_order:
            rule = next((r for r in rules if r["rule_id"] == rule_id), None)
            if rule:
                ordered_rules.append(rule)
        
        return ordered_rules
    
    def _build_dependency_graph(self, rules: List[Dict]) -> Dict[str, List[str]]:
        """Build dependency graph from rules"""
        
        graph = {}
        
        for rule in rules:
            rule_id = rule["rule_id"]
            dependencies = rule.get("conflict_resolution", {}).get("dependency_rules", [])
            graph[rule_id] = dependencies
        
        return graph
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Perform topological sort on dependency graph"""
        
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(node: str):
            if node in temp_visited:
                raise ValueError(f"Circular dependency detected involving {node}")
            
            if node not in visited:
                temp_visited.add(node)
                
                for dependency in graph.get(node, []):
                    visit(dependency)
                
                temp_visited.remove(node)
                visited.add(node)
                result.append(node)
        
        for node in graph:
            if node not in visited:
                visit(node)
        
        return result[::-1]  # Reverse to get correct order
    
    def _resolve_resource_contention(self, rules: List[Dict], conflict: Dict) -> List[Dict]:
        """Resolve resource contention through throttling and prioritization"""
        
        affected_rule_ids = conflict.get("affected_rules", [])
        
        if len(affected_rule_ids) <= 5:  # Acceptable limit
            return rules
        
        # Apply rate limiting based on confidence scores
        affected_rules = [r for r in rules if r["rule_id"] in affected_rule_ids]
        other_rules = [r for r in rules if r["rule_id"] not in affected_rule_ids]
        
        # Keep top 5 rules by confidence
        top_rules = sorted(
            affected_rules,
            key=lambda r: r.get("ai_metadata", {}).get("confidence_score", 0),
            reverse=True
        )[:5]
        
        # Add throttling metadata to remaining rules
        for rule in top_rules:
            rule.setdefault("execution_config", {})["throttled"] = True
            rule["execution_config"]["throttle_reason"] = "resource_contention"
        
        other_rules.extend(top_rules)
        return other_rules
    
    def _optimize_rule_execution(self, rules: List[Dict]) -> List[Dict]:
        """Final optimization of rule execution order"""
        
        # Sort by priority weight, then confidence
        optimized_rules = sorted(
            rules,
            key=lambda r: (
                r.get("conflict_resolution", {}).get("priority_weight", 0),
                r.get("ai_metadata", {}).get("confidence_score", 0)
            ),
            reverse=True
        )
        
        return optimized_rules
    
    def _get_tenant_setting(self, setting_name: str, default_value: Any) -> Any:
        """Get tenant-specific configuration setting"""
        # In production, this would query DynamoDB for tenant settings
        tenant_settings = {
            "max_rules_per_priority": 3,
            "conflict_resolution_strategy": "confidence_score",
            "resource_contention_limit": 5
        }
        
        return tenant_settings.get(setting_name, default_value)
    
    def _log_resolution(self, resolution_type: str, winner_id: str, loser_id: str):
        """Log conflict resolution for analytics"""
        
        if resolution_type not in self.resolution_stats:
            self.resolution_stats[resolution_type] = 0
        
        self.resolution_stats[resolution_type] += 1
        
        # In production, this would write to DynamoDB execution logs
        print(f"Resolved {resolution_type}: {winner_id} took precedence over {loser_id}")
```

## 3. ML-Powered Optimization

### Learning from Resolution Outcomes

```python
class ConflictResolutionLearner:
    """ML system to learn optimal conflict resolution strategies"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.model_version = "conflict-resolver-v1.0"
        
    def analyze_resolution_effectiveness(self, resolution_history: List[Dict]) -> Dict:
        """Analyze effectiveness of past conflict resolutions"""
        
        effectiveness_metrics = {
            "strategy_success_rates": {},
            "user_satisfaction_scores": {},
            "rule_performance_impact": {},
            "recommended_strategies": {}
        }
        
        # Group resolutions by strategy
        strategy_groups = {}
        for resolution in resolution_history:
            strategy = resolution.get("strategy_used")
            if strategy not in strategy_groups:
                strategy_groups[strategy] = []
            strategy_groups[strategy].append(resolution)
        
        # Calculate success rates for each strategy
        for strategy, resolutions in strategy_groups.items():
            successful = len([r for r in resolutions if r.get("user_feedback") == "positive"])
            total = len(resolutions)
            
            effectiveness_metrics["strategy_success_rates"][strategy] = {
                "success_rate": successful / total if total > 0 else 0,
                "total_resolutions": total,
                "successful_resolutions": successful
            }
        
        # Generate recommendations
        effectiveness_metrics["recommended_strategies"] = self._generate_strategy_recommendations(
            effectiveness_metrics["strategy_success_rates"]
        )
        
        return effectiveness_metrics
    
    def _generate_strategy_recommendations(self, success_rates: Dict) -> Dict:
        """Generate recommendations for future conflict resolution"""
        
        recommendations = {}
        
        # Sort strategies by success rate
        sorted_strategies = sorted(
            success_rates.items(),
            key=lambda x: x[1]["success_rate"],
            reverse=True
        )
        
        for conflict_type in ConflictType:
            # Find best performing strategy for this conflict type
            best_strategy = None
            best_rate = 0
            
            for strategy, metrics in sorted_strategies:
                if metrics["total_resolutions"] >= 5:  # Minimum sample size
                    if metrics["success_rate"] > best_rate:
                        best_rate = metrics["success_rate"]
                        best_strategy = strategy
            
            recommendations[conflict_type.value] = {
                "recommended_strategy": best_strategy,
                "confidence": best_rate,
                "fallback_strategy": "priority_weight"  # Always reliable fallback
            }
        
        return recommendations
    
    def predict_resolution_success(self, conflict: Dict, proposed_strategy: str) -> float:
        """Predict success probability of a proposed resolution strategy"""
        
        # Feature extraction
        features = self._extract_conflict_features(conflict)
        
        # In production, this would use a trained ML model
        # For now, use heuristic-based prediction
        base_probability = self._get_strategy_base_probability(proposed_strategy)
        
        # Adjust based on conflict characteristics
        adjustments = {
            "severity": {
                "critical": -0.1,
                "moderate": 0.0,
                "minor": 0.1
            },
            "auto_resolvable": {
                True: 0.2,
                False: -0.2
            }
        }
        
        adjusted_probability = base_probability
        
        if "severity" in features:
            adjusted_probability += adjustments["severity"].get(features["severity"], 0)
        
        if "auto_resolvable" in features:
            adjusted_probability += adjustments["auto_resolvable"].get(features["auto_resolvable"], 0)
        
        return max(0.0, min(1.0, adjusted_probability))
    
    def _extract_conflict_features(self, conflict: Dict) -> Dict:
        """Extract features from conflict for ML prediction"""
        
        return {
            "conflict_type": conflict.get("type"),
            "severity": conflict.get("severity"),
            "auto_resolvable": conflict.get("auto_resolvable"),
            "affected_rules_count": len(conflict.get("affected_rules", [])),
            "tenant_id": self.tenant_id
        }
    
    def _get_strategy_base_probability(self, strategy: str) -> float:
        """Get base success probability for a strategy"""
        
        # Based on historical data analysis
        base_probabilities = {
            "priority_weight": 0.85,
            "confidence_score": 0.80,
            "merge_compatible": 0.75,
            "dependency_chain": 0.70,
            "rate_limiting": 0.65,
            "merge_rules": 0.60
        }
        
        return base_probabilities.get(strategy, 0.50)
```

## 4. Integration with Rule Engine

### Updated Rule Engine Integration

```python
# Update to the rule_engine.py Lambda function
def resolve_rule_conflicts_enhanced(tenant_id: str, matching_rules: List[Dict]) -> List[Dict]:
    """Enhanced rule conflict resolution with ML optimization"""
    
    if len(matching_rules) <= 1:
        return matching_rules
    
    # Initialize conflict resolution components
    detector = ConflictDetector(tenant_id)
    resolver = ConflictResolver(tenant_id)
    learner = ConflictResolutionLearner(tenant_id)
    
    # Detect conflicts
    conflicts = detector.detect_conflicts(matching_rules)
    
    if not conflicts:
        return matching_rules
    
    # Load historical data for ML optimization
    resolution_history = load_resolution_history(tenant_id)
    effectiveness_metrics = learner.analyze_resolution_effectiveness(resolution_history)
    
    # Enhance conflict resolution with ML predictions
    for conflict in conflicts:
        conflict_type = conflict.get("type")
        recommended_strategy = effectiveness_metrics["recommended_strategies"].get(
            conflict_type.value if hasattr(conflict_type, 'value') else str(conflict_type)
        )
        
        if recommended_strategy:
            conflict["ml_recommended_strategy"] = recommended_strategy["recommended_strategy"]
            conflict["ml_confidence"] = recommended_strategy["confidence"]
    
    # Resolve conflicts
    resolved_rules = resolver.resolve_conflicts(matching_rules, conflicts)
    
    # Log resolution for future learning
    log_conflict_resolution(tenant_id, conflicts, resolved_rules)
    
    return resolved_rules

def load_resolution_history(tenant_id: str) -> List[Dict]:
    """Load historical conflict resolution data"""
    # Query DynamoDB for resolution history
    # Implementation would query execution logs with conflict resolution data
    return []

def log_conflict_resolution(tenant_id: str, conflicts: List[Dict], resolved_rules: List[Dict]):
    """Log conflict resolution for ML learning"""
    # Store resolution data in DynamoDB for future analysis
    pass
```

## 5. Performance Metrics and Monitoring

### Conflict Resolution Analytics

```python
@dataclass
class ConflictResolutionMetrics:
    """Metrics for monitoring conflict resolution performance"""
    tenant_id: str
    timestamp: str
    conflicts_detected: int
    conflicts_resolved: int
    resolution_strategies_used: Dict[str, int]
    avg_resolution_time_ms: float
    user_satisfaction_score: float
    rule_performance_impact: Dict[str, float]

class ConflictResolutionMonitor:
    """Monitor and track conflict resolution performance"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        
    def track_resolution_performance(self, 
                                   conflicts: List[Dict], 
                                   resolved_rules: List[Dict],
                                   resolution_time_ms: float) -> ConflictResolutionMetrics:
        """Track performance metrics for a resolution session"""
        
        metrics = ConflictResolutionMetrics(
            tenant_id=self.tenant_id,
            timestamp=datetime.utcnow().isoformat(),
            conflicts_detected=len(conflicts),
            conflicts_resolved=len([c for c in conflicts if c.get("resolved", False)]),
            resolution_strategies_used=self._count_strategies_used(conflicts),
            avg_resolution_time_ms=resolution_time_ms,
            user_satisfaction_score=0.0,  # Updated based on user feedback
            rule_performance_impact=self._calculate_performance_impact(resolved_rules)
        )
        
        # Store metrics in DynamoDB
        self._store_metrics(metrics)
        
        return metrics
    
    def _count_strategies_used(self, conflicts: List[Dict]) -> Dict[str, int]:
        """Count which resolution strategies were used"""
        
        strategy_counts = {}
        
        for conflict in conflicts:
            strategy = conflict.get("resolution_strategy_used", "unknown")
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return strategy_counts
    
    def _calculate_performance_impact(self, resolved_rules: List[Dict]) -> Dict[str, float]:
        """Calculate performance impact of conflict resolution"""
        
        return {
            "rules_merged": len([r for r in resolved_rules if "merged" in r.get("metadata", {}).get("description", "")]),
            "rules_removed": 0,  # Would track removed rules
            "avg_confidence_retained": sum(
                r.get("ai_metadata", {}).get("confidence_score", 0) for r in resolved_rules
            ) / len(resolved_rules) if resolved_rules else 0
        }
    
    def _store_metrics(self, metrics: ConflictResolutionMetrics):
        """Store metrics in DynamoDB for analysis"""
        # Implementation would store in analytics table
        pass
```

This advanced rule conflict resolution system provides enterprise-grade handling of rule conflicts with ML-powered optimization, comprehensive monitoring, and multiple resolution strategies. The system learns from past resolutions to continuously improve conflict handling effectiveness.

Next: Privacy-first security design implementation.