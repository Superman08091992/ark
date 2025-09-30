import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import sympy as sp
from sympy import symbols, And, Or, Not, Implies, satisfiable
from agents.base_agent import BaseAgent
from config.database import db_manager, EthicsRule
from config.settings import settings
from utils.logger import get_logger

class HRMAgent(BaseAgent):
    """HRM - Human Reasoning & Machine validation agent for logical consistency checking"""
    
    def __init__(self):
        super().__init__(
            name="HRM",
            description="Logic validation and reasoning consistency agent using symbolic reasoning"
        )
        self.reasoning_rules = {}
        self.logic_cache = {}
        self.graveyard_rules = None  # Immutable rule set
        self.load_reasoning_rules()
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for HRM"""
        required_fields = ["task_type"]
        return all(field in input_data for field in required_fields)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method for logical validation"""
        task_type = input_data.get("task_type")
        
        if task_type == "validate_plan":
            return await self._validate_plan_logic(input_data)
        elif task_type == "check_consistency":
            return await self._check_logical_consistency(input_data)
        elif task_type == "verify_reasoning":
            return await self._verify_reasoning_chain(input_data)
        elif task_type == "validate_constraints":
            return await self._validate_constraints(input_data)
        elif task_type == "check_contradictions":
            return await self._check_contradictions(input_data)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _validate_plan_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate logical consistency of a plan"""
        plan_data = input_data.get("plan_data")
        joey_analysis = input_data.get("analysis_data")
        
        if not plan_data:
            return {
                "status": "rejected",
                "verdict": "rejected",
                "reason": "No plan data provided for validation",
                "logical_errors": ["Missing plan data"]
            }
        
        validation_results = {
            "structural_validation": await self._validate_plan_structure(plan_data),
            "parameter_consistency": await self._validate_parameter_consistency(plan_data),
            "action_coherence": await self._validate_action_coherence(plan_data),
            "risk_logic": await self._validate_risk_logic(plan_data),
            "evidence_support": await self._validate_evidence_support(plan_data, joey_analysis),
            "constraint_compliance": await self._validate_constraint_compliance(plan_data)
        }
        
        # Aggregate validation results
        logical_errors = []
        warnings = []
        
        for validation_type, result in validation_results.items():
            if not result["valid"]:
                logical_errors.extend(result.get("errors", []))
            if result.get("warnings"):
                warnings.extend(result["warnings"])
        
        # Determine overall verdict
        has_critical_errors = any(
            not validation_results[check]["valid"] 
            for check in ["structural_validation", "parameter_consistency", "constraint_compliance"]
        )
        
        verdict = "rejected" if has_critical_errors else "approved"
        status = "rejected" if logical_errors else "approved"
        
        # Log validation decision
        await self._log_validation_decision(plan_data, verdict, logical_errors, warnings)
        
        return {
            "status": status,
            "verdict": verdict,
            "logical_errors": logical_errors,
            "warnings": warnings,
            "validation_details": validation_results,
            "reasoning_chain": await self._generate_reasoning_chain(validation_results),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _check_logical_consistency(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check logical consistency of statements or rules"""
        statements = input_data.get("statements", [])
        context = input_data.get("context", {})
        
        if not statements:
            return {
                "status": "error",
                "message": "No statements provided for consistency check"
            }
        
        # Convert statements to logical expressions
        logical_expressions = []
        for i, statement in enumerate(statements):
            try:
                expr = await self._parse_statement_to_logic(statement, context)
                logical_expressions.append({"index": i, "statement": statement, "expression": expr})
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to parse statement {i}: {str(e)}"
                }
        
        # Check for contradictions
        contradictions = await self._find_contradictions(logical_expressions)
        
        # Check for missing implications
        missing_implications = await self._find_missing_implications(logical_expressions)
        
        # Overall consistency assessment
        is_consistent = len(contradictions) == 0
        
        return {
            "status": "completed",
            "is_consistent": is_consistent,
            "contradictions": contradictions,
            "missing_implications": missing_implications,
            "statements_analyzed": len(statements),
            "logical_expressions": [{"index": expr["index"], "statement": expr["statement"]} for expr in logical_expressions],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _verify_reasoning_chain(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a chain of reasoning"""
        premises = input_data.get("premises", [])
        conclusion = input_data.get("conclusion")
        reasoning_steps = input_data.get("reasoning_steps", [])
        
        if not premises or not conclusion:
            return {
                "status": "error",
                "message": "Both premises and conclusion are required"
            }
        
        # Convert premises to logical expressions
        premise_expressions = []
        for premise in premises:
            expr = await self._parse_statement_to_logic(premise, {})
            premise_expressions.append(expr)
        
        # Convert conclusion to logical expression
        conclusion_expr = await self._parse_statement_to_logic(conclusion, {})
        
        # Check if conclusion follows from premises
        validity_check = await self._check_logical_validity(premise_expressions, conclusion_expr)
        
        # Analyze reasoning steps
        step_analysis = await self._analyze_reasoning_steps(reasoning_steps, premise_expressions, conclusion_expr)
        
        return {
            "status": "completed",
            "is_valid": validity_check["valid"],
            "reasoning_quality": validity_check["quality_score"],
            "step_analysis": step_analysis,
            "logical_gaps": validity_check.get("gaps", []),
            "recommendations": await self._generate_reasoning_recommendations(validity_check, step_analysis),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _validate_constraints(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate constraints and business rules"""
        constraints = input_data.get("constraints", [])
        plan_data = input_data.get("plan_data", {})
        
        constraint_violations = []
        satisfied_constraints = []
        
        for constraint in constraints:
            try:
                violation = await self._check_constraint_violation(constraint, plan_data)
                if violation:
                    constraint_violations.append(violation)
                else:
                    satisfied_constraints.append(constraint)
            except Exception as e:
                constraint_violations.append({
                    "constraint": constraint,
                    "error": f"Failed to evaluate constraint: {str(e)}"
                })
        
        return {
            "status": "completed",
            "constraints_satisfied": len(satisfied_constraints),
            "constraints_violated": len(constraint_violations),
            "violations": constraint_violations,
            "all_constraints_met": len(constraint_violations) == 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _check_contradictions(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for logical contradictions in data or rules"""
        rules = input_data.get("rules", [])
        facts = input_data.get("facts", [])
        
        all_statements = rules + facts
        
        # Convert to logical expressions
        expressions = []
        for statement in all_statements:
            expr = await self._parse_statement_to_logic(statement, {})
            expressions.append({"statement": statement, "expression": expr})
        
        # Find contradictions
        contradictions = await self._find_contradictions(expressions)
        
        return {
            "status": "completed",
            "contradictions_found": len(contradictions),
            "contradictions": contradictions,
            "is_consistent": len(contradictions) == 0,
            "statements_analyzed": len(all_statements),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _validate_plan_structure(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate structural integrity of the plan"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["type", "actions", "parameters"]
        for field in required_fields:
            if field not in plan_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate actions structure
        if "actions" in plan_data:
            actions = plan_data["actions"]
            if not isinstance(actions, list):
                errors.append("Actions must be a list")
            else:
                total_weight = 0
                for i, action in enumerate(actions):
                    if not isinstance(action, dict):
                        errors.append(f"Action {i} must be a dictionary")
                        continue
                    
                    if "action" not in action:
                        errors.append(f"Action {i} missing 'action' field")
                    
                    weight = action.get("weight", 0)
                    if not isinstance(weight, (int, float)) or weight < 0:
                        errors.append(f"Action {i} has invalid weight: {weight}")
                    
                    total_weight += weight
                
                if abs(total_weight - 1.0) > 0.01:
                    warnings.append(f"Action weights sum to {total_weight}, should sum to 1.0")
        
        # Validate parameters structure
        if "parameters" in plan_data:
            params = plan_data["parameters"]
            if not isinstance(params, dict):
                errors.append("Parameters must be a dictionary")
            else:
                # Check parameter ranges
                if "risk_tolerance" in params:
                    risk = params["risk_tolerance"]
                    if not (0 <= risk <= 1):
                        errors.append(f"Risk tolerance {risk} must be between 0 and 1")
                
                if "max_position_size" in params:
                    pos_size = params["max_position_size"]
                    if not (0 < pos_size <= 1):
                        errors.append(f"Max position size {pos_size} must be between 0 and 1")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _validate_parameter_consistency(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate internal consistency of parameters"""
        errors = []
        warnings = []
        
        params = plan_data.get("parameters", {})
        plan_type = plan_data.get("type", "unknown")
        
        # Check consistency between plan type and risk tolerance
        if "risk_tolerance" in params:
            risk = params["risk_tolerance"]
            
            if plan_type == "conservative" and risk > 0.4:
                errors.append(f"Conservative plan has high risk tolerance: {risk}")
            elif plan_type == "aggressive" and risk < 0.6:
                warnings.append(f"Aggressive plan has low risk tolerance: {risk}")
        
        # Check consistency between risk tolerance and position size
        if "risk_tolerance" in params and "max_position_size" in params:
            risk = params["risk_tolerance"]
            pos_size = params["max_position_size"]
            
            if risk < 0.3 and pos_size > 0.1:
                warnings.append(f"Low risk tolerance ({risk}) with large position size ({pos_size})")
            elif risk > 0.7 and pos_size < 0.05:
                warnings.append(f"High risk tolerance ({risk}) with small position size ({pos_size})")
        
        # Check stop loss consistency
        if "stop_loss" in params and "risk_tolerance" in params:
            stop_loss = params["stop_loss"]
            risk = params["risk_tolerance"]
            
            if stop_loss > risk * 0.2:
                warnings.append(f"Stop loss ({stop_loss}) seems high for risk tolerance ({risk})")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _validate_action_coherence(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate coherence between actions"""
        errors = []
        warnings = []
        
        actions = plan_data.get("actions", [])
        plan_type = plan_data.get("type", "unknown")
        
        action_types = [action.get("action", "") for action in actions]
        
        # Check for conflicting actions
        conflicting_pairs = [
            ("diversify_portfolio", "leverage_positions"),
            ("hedge_positions", "momentum_trading"),
            ("maintain_cash_position", "leverage_positions")
        ]
        
        for action1, action2 in conflicting_pairs:
            if action1 in action_types and action2 in action_types:
                warnings.append(f"Potentially conflicting actions: {action1} and {action2}")
        
        # Check action appropriateness for plan type
        conservative_actions = {"diversify_portfolio", "hedge_positions", "maintain_cash_position"}
        aggressive_actions = {"momentum_trading", "leverage_positions", "options_strategies"}
        
        if plan_type == "conservative":
            for action_type in action_types:
                if action_type in aggressive_actions:
                    errors.append(f"Aggressive action '{action_type}' in conservative plan")
        
        elif plan_type == "aggressive":
            conservative_count = sum(1 for action in action_types if action in conservative_actions)
            if conservative_count > len(action_types) * 0.7:
                warnings.append("Many conservative actions in aggressive plan")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _validate_risk_logic(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate risk assessment logic"""
        errors = []
        warnings = []
        
        # Get risk-related parameters
        params = plan_data.get("parameters", {})
        actions = plan_data.get("actions", [])
        
        risk_tolerance = params.get("risk_tolerance", 0.5)
        max_position = params.get("max_position_size", 0.1)
        stop_loss = params.get("stop_loss", 0.05)
        
        # Calculate implicit risk from actions
        action_risk_map = {
            "diversify_portfolio": 0.2,
            "hedge_positions": 0.3,
            "maintain_cash_position": 0.1,
            "strategic_allocation": 0.4,
            "tactical_trading": 0.6,
            "momentum_trading": 0.8,
            "leverage_positions": 0.9,
            "options_strategies": 0.7
        }
        
        total_action_risk = 0
        for action in actions:
            action_type = action.get("action", "")
            weight = action.get("weight", 0)
            action_risk = action_risk_map.get(action_type, 0.5)
            total_action_risk += action_risk * weight
        
        # Check consistency between stated risk tolerance and action risk
        risk_gap = abs(total_action_risk - risk_tolerance)
        if risk_gap > 0.3:
            if total_action_risk > risk_tolerance:
                errors.append(f"Actions are riskier ({total_action_risk:.2f}) than risk tolerance ({risk_tolerance:.2f})")
            else:
                warnings.append(f"Actions are more conservative ({total_action_risk:.2f}) than risk tolerance ({risk_tolerance:.2f})")
        
        # Validate stop loss logic
        if stop_loss > max_position * 0.5:
            warnings.append(f"Stop loss ({stop_loss}) is large relative to max position ({max_position})")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "calculated_action_risk": total_action_risk,
            "stated_risk_tolerance": risk_tolerance,
            "risk_gap": risk_gap
        }
    
    async def _validate_evidence_support(self, plan_data: Dict[str, Any], analysis_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that plan is supported by evidence from analysis"""
        errors = []
        warnings = []
        
        if not analysis_data:
            warnings.append("No analysis data provided to validate evidence support")
            return {
                "valid": True,
                "errors": errors,
                "warnings": warnings
            }
        
        plan_type = plan_data.get("type", "unknown")
        actions = plan_data.get("actions", [])
        
        # Check if analysis supports plan direction
        trends = analysis_data.get("trends", {})
        market_sentiment = analysis_data.get("trend_summary", {}).get("market_sentiment", "neutral")
        
        # Validate momentum trading support
        momentum_actions = [a for a in actions if a.get("action") == "momentum_trading"]
        if momentum_actions and market_sentiment == "neutral":
            warnings.append("Momentum trading planned but market sentiment is neutral")
        
        # Validate hedging support
        hedge_actions = [a for a in actions if a.get("action") == "hedge_positions"]
        volatility_indicators = analysis_data.get("volatility", 0.5)
        if hedge_actions and volatility_indicators < 0.3:
            warnings.append("Hedging planned but volatility appears low")
        
        # Check data quality support
        data_quality = analysis_data.get("data_quality_score", 0.5)
        if data_quality < 0.6:
            warnings.append(f"Plan based on low quality data (score: {data_quality})")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "evidence_quality": data_quality,
            "market_alignment": market_sentiment
        }
    
    async def _validate_constraint_compliance(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate compliance with system constraints"""
        errors = []
        warnings = []
        
        # Load system constraints from graveyard rules
        if not self.graveyard_rules:
            await self._load_graveyard_rules()
        
        constraints = self.graveyard_rules.get("constraints", {})
        
        # Check maximum position size constraint
        max_allowed_position = constraints.get("max_position_size", 0.25)
        plan_max_position = plan_data.get("parameters", {}).get("max_position_size", 0.1)
        
        if plan_max_position > max_allowed_position:
            errors.append(f"Plan position size ({plan_max_position}) exceeds limit ({max_allowed_position})")
        
        # Check minimum diversification constraint
        min_actions = constraints.get("min_diversification", 2)
        action_count = len(plan_data.get("actions", []))
        
        if action_count < min_actions:
            errors.append(f"Plan has {action_count} actions, minimum required: {min_actions}")
        
        # Check forbidden action combinations
        forbidden_combinations = constraints.get("forbidden_combinations", [])
        plan_actions = [a.get("action") for a in plan_data.get("actions", [])]
        
        for forbidden in forbidden_combinations:
            if all(action in plan_actions for action in forbidden):
                errors.append(f"Forbidden action combination detected: {forbidden}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _parse_statement_to_logic(self, statement: str, context: Dict[str, Any]) -> sp.Basic:
        """Parse natural language statement to symbolic logic"""
        # Simplified logic parsing - in production would use NLP
        
        # Define common logical patterns
        if "if" in statement.lower() and "then" in statement.lower():
            # Implication: if A then B
            parts = statement.lower().split("then")
            if len(parts) == 2:
                antecedent = symbols("A")  # Simplified
                consequent = symbols("B")
                return Implies(antecedent, consequent)
        
        elif "and" in statement.lower():
            # Conjunction
            parts = statement.lower().split("and")
            vars = [symbols(f"var_{i}") for i in range(len(parts))]
            return And(*vars)
        
        elif "or" in statement.lower():
            # Disjunction
            parts = statement.lower().split("or")
            vars = [symbols(f"var_{i}") for i in range(len(parts))]
            return Or(*vars)
        
        elif "not" in statement.lower():
            # Negation
            var = symbols("var")
            return Not(var)
        
        else:
            # Simple proposition
            return symbols("prop")
    
    async def _find_contradictions(self, logical_expressions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find logical contradictions in expressions"""
        contradictions = []
        
        # Simple contradiction detection
        for i, expr1 in enumerate(logical_expressions):
            for j, expr2 in enumerate(logical_expressions[i+1:], i+1):
                try:
                    # Check if expressions are contradictory
                    combined = And(expr1["expression"], expr2["expression"])
                    if not satisfiable(combined):
                        contradictions.append({
                            "statement1": expr1["statement"],
                            "statement2": expr2["statement"],
                            "index1": expr1.get("index", i),
                            "index2": expr2.get("index", j),
                            "reason": "Statements are logically contradictory"
                        })
                except Exception as e:
                    # If symbolic check fails, use heuristic check
                    if await self._heuristic_contradiction_check(expr1["statement"], expr2["statement"]):
                        contradictions.append({
                            "statement1": expr1["statement"],
                            "statement2": expr2["statement"],
                            "index1": expr1.get("index", i),
                            "index2": expr2.get("index", j),
                            "reason": "Potential contradiction detected heuristically"
                        })
        
        return contradictions
    
    async def _find_missing_implications(self, logical_expressions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find missing logical implications"""
        missing_implications = []
        
        # This is a simplified implementation
        # In production, would use more sophisticated logical reasoning
        
        for expr in logical_expressions:
            statement = expr["statement"].lower()
            
            # Check for common missing implications
            if "risk" in statement and "hedge" not in statement:
                missing_implications.append({
                    "statement": expr["statement"],
                    "missing_implication": "High risk should imply hedging consideration",
                    "type": "risk_management"
                })
            
            if "aggressive" in statement and "stop" not in statement:
                missing_implications.append({
                    "statement": expr["statement"],
                    "missing_implication": "Aggressive strategy should imply stop-loss mechanisms",
                    "type": "risk_control"
                })
        
        return missing_implications
    
    async def _check_logical_validity(self, premises: List[sp.Basic], conclusion: sp.Basic) -> Dict[str, Any]:
        """Check if conclusion logically follows from premises"""
        try:
            # Create implication: premises -> conclusion
            premise_conjunction = And(*premises) if len(premises) > 1 else premises[0]
            implication = Implies(premise_conjunction, conclusion)
            
            # Check if implication is tautology (always true)
            is_tautology = not satisfiable(Not(implication))
            
            # Calculate quality score based on logical strength
            quality_score = 0.9 if is_tautology else 0.6
            
            return {
                "valid": is_tautology,
                "quality_score": quality_score,
                "reasoning": "Conclusion follows logically from premises" if is_tautology else "Conclusion does not necessarily follow from premises"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "quality_score": 0.3,
                "reasoning": f"Unable to verify logical validity: {str(e)}",
                "gaps": ["Logical verification failed"]
            }
    
    async def _analyze_reasoning_steps(self, steps: List[str], premises: List[sp.Basic], conclusion: sp.Basic) -> Dict[str, Any]:
        """Analyze individual reasoning steps"""
        step_analysis = []
        
        for i, step in enumerate(steps):
            analysis = {
                "step_number": i + 1,
                "step_text": step,
                "valid": True,  # Simplified validation
                "reasoning_type": await self._classify_reasoning_type(step),
                "strength": 0.7  # Default strength
            }
            
            # Simple step validation
            if "therefore" in step.lower() or "thus" in step.lower():
                analysis["reasoning_type"] = "conclusion"
                analysis["strength"] = 0.8
            elif "because" in step.lower() or "since" in step.lower():
                analysis["reasoning_type"] = "justification"
                analysis["strength"] = 0.7
            elif "assume" in step.lower() or "suppose" in step.lower():
                analysis["reasoning_type"] = "assumption"
                analysis["strength"] = 0.5
            
            step_analysis.append(analysis)
        
        return {
            "total_steps": len(steps),
            "valid_steps": len([s for s in step_analysis if s["valid"]]),
            "average_strength": sum(s["strength"] for s in step_analysis) / len(step_analysis) if step_analysis else 0,
            "step_details": step_analysis
        }
    
    async def _classify_reasoning_type(self, step: str) -> str:
        """Classify the type of reasoning in a step"""
        step_lower = step.lower()
        
        if any(word in step_lower for word in ["because", "since", "due to"]):
            return "causal"
        elif any(word in step_lower for word in ["therefore", "thus", "hence"]):
            return "deductive"
        elif any(word in step_lower for word in ["probably", "likely", "suggests"]):
            return "inductive"
        elif any(word in step_lower for word in ["similar", "like", "comparable"]):
            return "analogical"
        else:
            return "assertion"
    
    async def _check_constraint_violation(self, constraint: Dict[str, Any], plan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if a specific constraint is violated"""
        constraint_type = constraint.get("type")
        constraint_value = constraint.get("value")
        
        if constraint_type == "max_risk":
            plan_risk = plan_data.get("parameters", {}).get("risk_tolerance", 0.5)
            if plan_risk > constraint_value:
                return {
                    "constraint": constraint,
                    "violation": f"Plan risk ({plan_risk}) exceeds maximum ({constraint_value})",
                    "severity": "critical"
                }
        
        elif constraint_type == "min_diversification":
            action_count = len(plan_data.get("actions", []))
            if action_count < constraint_value:
                return {
                    "constraint": constraint,
                    "violation": f"Plan has {action_count} actions, minimum required: {constraint_value}",
                    "severity": "warning"
                }
        
        elif constraint_type == "forbidden_action":
            forbidden_action = constraint_value
            plan_actions = [a.get("action") for a in plan_data.get("actions", [])]
            if forbidden_action in plan_actions:
                return {
                    "constraint": constraint,
                    "violation": f"Plan contains forbidden action: {forbidden_action}",
                    "severity": "critical"
                }
        
        return None
    
    async def _heuristic_contradiction_check(self, statement1: str, statement2: str) -> bool:
        """Heuristic check for contradictions when symbolic logic fails"""
        s1_lower = statement1.lower()
        s2_lower = statement2.lower()
        
        # Check for obvious contradictions
        positive_negative_pairs = [
            ("increase", "decrease"),
            ("buy", "sell"),
            ("high", "low"),
            ("aggressive", "conservative"),
            ("risk", "safe")
        ]
        
        for pos, neg in positive_negative_pairs:
            if pos in s1_lower and neg in s2_lower:
                return True
            if neg in s1_lower and pos in s2_lower:
                return True
        
        return False
    
    async def _generate_reasoning_chain(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate explanation of reasoning process"""
        reasoning_chain = []
        
        reasoning_chain.append("Beginning logical validation of plan...")
        
        # Structure validation reasoning
        if validation_results["structural_validation"]["valid"]:
            reasoning_chain.append("✓ Plan structure is valid and well-formed")
        else:
            reasoning_chain.append("✗ Plan structure has issues that must be addressed")
        
        # Parameter consistency reasoning
        if validation_results["parameter_consistency"]["valid"]:
            reasoning_chain.append("✓ Plan parameters are internally consistent")
        else:
            reasoning_chain.append("✗ Plan parameters show inconsistencies")
        
        # Action coherence reasoning
        if validation_results["action_coherence"]["valid"]:
            reasoning_chain.append("✓ Plan actions are coherent and compatible")
        else:
            reasoning_chain.append("✗ Plan actions show conflicts or incompatibilities")
        
        # Risk logic reasoning
        if validation_results["risk_logic"]["valid"]:
            reasoning_chain.append("✓ Risk assessment logic is sound")
        else:
            reasoning_chain.append("✗ Risk assessment logic has flaws")
        
        # Evidence support reasoning
        if validation_results["evidence_support"]["valid"]:
            reasoning_chain.append("✓ Plan is adequately supported by evidence")
        else:
            reasoning_chain.append("⚠ Plan lacks sufficient evidence support")
        
        # Constraint compliance reasoning
        if validation_results["constraint_compliance"]["valid"]:
            reasoning_chain.append("✓ Plan complies with all system constraints")
        else:
            reasoning_chain.append("✗ Plan violates system constraints")
        
        reasoning_chain.append("Logical validation complete.")
        
        return reasoning_chain
    
    async def _generate_reasoning_recommendations(self, validity_check: Dict[str, Any], step_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving reasoning"""
        recommendations = []
        
        if not validity_check["valid"]:
            recommendations.append("Review logical connection between premises and conclusion")
            
        if validity_check["quality_score"] < 0.7:
            recommendations.append("Strengthen logical arguments with additional supporting evidence")
        
        if step_analysis["average_strength"] < 0.6:
            recommendations.append("Improve clarity and strength of individual reasoning steps")
        
        weak_steps = [s for s in step_analysis["step_details"] if s["strength"] < 0.5]
        if weak_steps:
            recommendations.append(f"Address weak reasoning in steps: {[s['step_number'] for s in weak_steps]}")
        
        if step_analysis["valid_steps"] < step_analysis["total_steps"]:
            recommendations.append("Remove or fix invalid reasoning steps")
        
        return recommendations
    
    async def _log_validation_decision(self, plan_data: Dict[str, Any], verdict: str, 
                                     logical_errors: List[str], warnings: List[str]):
        """Log HRM validation decision"""
        try:
            session = db_manager.get_session()
            
            # Create log entry for the decision
            from config.database import AgentLog
            log_entry = AgentLog(
                agent=self.name,
                action="validate_plan",
                input_data={"plan_summary": plan_data.get("type", "unknown")},
                output_data={
                    "verdict": verdict,
                    "logical_errors": logical_errors,
                    "warnings": warnings
                },
                verdict=verdict
            )
            session.add(log_entry)
            session.commit()
            session.close()
            
        except Exception as e:
            self.logger.error(f"Failed to log validation decision: {e}")
    
    def load_reasoning_rules(self):
        """Load reasoning rules and logic patterns"""
        self.reasoning_rules = {
            "modus_ponens": "If P implies Q and P is true, then Q is true",
            "modus_tollens": "If P implies Q and Q is false, then P is false",
            "hypothetical_syllogism": "If P implies Q and Q implies R, then P implies R",
            "disjunctive_syllogism": "If P or Q is true and P is false, then Q is true",
            "contradiction": "P and not P cannot both be true"
        }
    
    async def _load_graveyard_rules(self):
        """Load immutable graveyard rules from database"""
        try:
            session = db_manager.get_session()
            graveyard_rules = session.query(EthicsRule).filter(
                EthicsRule.rule_type == "graveyard",
                EthicsRule.is_immutable == True
            ).all()
            
            self.graveyard_rules = {}
            for rule in graveyard_rules:
                self.graveyard_rules.update(rule.rule_data)
            
            # Default constraints if none found
            if not self.graveyard_rules:
                self.graveyard_rules = {
                    "constraints": {
                        "max_position_size": 0.25,
                        "min_diversification": 2,
                        "forbidden_combinations": [
                            ["leverage_positions", "maintain_cash_position"]
                        ]
                    }
                }
            
            session.close()
            
        except Exception as e:
            self.logger.error(f"Failed to load graveyard rules: {e}")
            # Use default rules
            self.graveyard_rules = {
                "constraints": {
                    "max_position_size": 0.25,
                    "min_diversification": 2,
                    "forbidden_combinations": []
                }
            }

# Global HRM instance
hrm_agent = HRMAgent()

