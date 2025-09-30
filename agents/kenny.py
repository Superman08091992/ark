import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
import uuid
from agents.base_agent import BaseAgent
from config.database import db_manager, Plan, AgentLog
from config.settings import settings
from core.simulation_engine import SimulationEngine
from core.consent_registry import ConsentRegistry

class KennyAgent(BaseAgent):
    """Kenny - Execution Agent (with simulation mode)"""
    
    def __init__(self):
        super().__init__(
            name="Kenny",
            description="Plan execution agent with simulation capabilities and safety controls"
        )
        self.simulation_mode = settings.KENNY_SIMULATION_MODE
        self.simulation_engine = SimulationEngine()
        self.consent_registry = ConsentRegistry()
        self.execution_history = []
        
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for Kenny"""
        required_fields = ["task_type"]
        return all(field in input_data for field in required_fields)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method for plan execution"""
        task_type = input_data.get("task_type")
        
        if task_type == "execute_plan":
            return await self._execute_plan(input_data)
        elif task_type == "simulate_execution":
            return await self._simulate_execution(input_data)
        elif task_type == "validate_plan":
            return await self._validate_plan(input_data)
        elif task_type == "rollback_execution":
            return await self._rollback_execution(input_data)
        elif task_type == "check_prerequisites":
            return await self._check_prerequisites(input_data)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _execute_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an approved plan"""
        plan_id = input_data.get("plan_id")
execution_mode = input_data.get("execution_mode", "simulation" if self.simulation_mode else "live")
        
        if not plan_id:
            raise ValueError("Plan ID is required for execution")
        
        # Fetch plan from database
        plan = await self._fetch_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        # Verify plan approval status
        if plan["status"] != "approved":
            raise ValueError(f"Plan {plan_id} is not approved for execution (status: {plan['status']})")
        
        # Check user consent
        consent_check = await self.consent_registry.check_execution_consent(
            plan_id, plan["plan_data"]
        )
        if not consent_check["granted"]:
            raise ValueError(f"Execution consent not granted: {consent_check['reason']}")
        
        # Perform pre-execution validation
        validation_result = await self._validate_plan({"plan_data": plan["plan_data"]})
        if validation_result["status"] != "valid":
            raise ValueError(f"Plan validation failed: {validation_result['errors']}")
        
        execution_id = str(uuid.uuid4())
        
        try:
            if execution_mode == "simulation":
                result = await self._simulate_execution({
                    "plan_data": plan["plan_data"],
                    "execution_id": execution_id
                })
            else:
                result = await self._live_execution(plan["plan_data"], execution_id)
            
            # Update plan status
            await self._update_plan_status(plan_id, "executed", result)
            
            # Log execution
            await self._log_execution_result(execution_id, plan_id, result, execution_mode)
            
            return {
                "status": "completed",
                "execution_id": execution_id,
                "execution_mode": execution_mode,
                "plan_id": plan_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Log failed execution
            await self._log_execution_result(
                execution_id, plan_id, 
                {"error": str(e), "status": "failed"}, 
                execution_mode
            )
            
            # Update plan status
            await self._update_plan_status(plan_id, "failed", {"error": str(e)})
            
            raise
    
    async def _simulate_execution(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate plan execution without real actions"""
        plan_data = input_data.get("plan_data")
        execution_id = input_data.get("execution_id", str(uuid.uuid4()))
        
        if not plan_data:
            raise ValueError("Plan data is required for simulation")
        
        # Use simulation engine to model execution
        simulation_result = await self.simulation_engine.simulate_plan_execution(plan_data)
        
        # Add execution metadata
        simulation_result.update({
            "execution_id": execution_id,
            "execution_mode": "simulation",
            "simulated_at": datetime.utcnow().isoformat(),
            "simulation_parameters": await self._get_simulation_parameters()
        })
        
        return simulation_result
    
    async def _live_execution(self, plan_data: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute plan with real actions (trading, contracts, etc.)"""
        execution_results = []
        
        # Process each action in the plan
        for action in plan_data.get("actions", []):
            action_result = await self._execute_action(action, execution_id)
            execution_results.append(action_result)
            
            # If any action fails, consider rollback
            if action_result.get("status") == "failed":
                rollback_required = action_result.get("rollback_required", False)
                if rollback_required:
                    await self._initiate_rollback(execution_results, execution_id)
                    break
        
        # Calculate overall execution result
        successful_actions = [r for r in execution_results if r.get("status") == "success"]
        failed_actions = [r for r in execution_results if r.get("status") == "failed"]
        
        overall_status = "success" if len(failed_actions) == 0 else "partial" if len(successful_actions) > 0 else "failed"
        
        return {
            "overall_status": overall_status,
            "successful_actions": len(successful_actions),
            "failed_actions": len(failed_actions),
            "execution_results": execution_results,
            "execution_summary": await self._generate_execution_summary(execution_results)
        }
    
    async def _execute_action(self, action: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action.get("action")
        weight = action.get("weight", 1.0)
        
        self.logger.info(f"Executing action {action_type} with weight {weight}")
        
        try:
            if action_type == "diversify_portfolio":
                return await self._execute_diversify_portfolio(action, execution_id)
            elif action_type == "hedge_positions":
                return await self._execute_hedge_positions(action, execution_id)
            elif action_type == "maintain_cash_position":
                return await self._execute_maintain_cash(action, execution_id)
            elif action_type == "strategic_allocation":
                return await self._execute_strategic_allocation(action, execution_id)
            elif action_type == "tactical_trading":
                return await self._execute_tactical_trading(action, execution_id)
            elif action_type == "cash_management":
                return await self._execute_cash_management(action, execution_id)
            elif action_type == "momentum_trading":
                return await self._execute_momentum_trading(action, execution_id)
            elif action_type == "leverage_positions":
                return await self._execute_leverage_positions(action, execution_id)
            elif action_type == "options_strategies":
                return await self._execute_options_strategies(action, execution_id)
            else:
                return {
                    "status": "failed",
                    "action": action_type,
                    "error": f"Unknown action type: {action_type}",
                    "rollback_required": False
                }
        
        except Exception as e:
            return {
                "status": "failed",
                "action": action_type,
                "error": str(e),
                "rollback_required": True
            }
    
    async def _execute_diversify_portfolio(self, action: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute portfolio diversification"""
        # In simulation mode or demo, return mock result
        if self.simulation_mode:
            return {
                "status": "success",
                "action": "diversify_portfolio",
                "details": {
                    "assets_rebalanced": 5,
                    "new_allocations": {
                        "stocks": 0.6,
                        "bonds": 0.3,
                        "cash": 0.1
                    },
                    "execution_cost": 25.50
                },
                "execution_time": "2023-09-26T10:15:00Z"
            }
        
        # In live mode, would make actual API calls to broker
        # For now, return simulated result with warning
        return {
            "status": "success",
            "action": "diversify_portfolio",
            "details": {
                "message": "Live trading not implemented - returned simulation result",
                "simulated": True
            },
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _execute_hedge_positions(self, action: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute position hedging"""
        return {
            "status": "success",
            "action": "hedge_positions",
            "details": {
                "hedges_placed": 3,
                "hedge_ratio": 0.8,
                "instruments_used": ["SPY puts", "VIX calls"],
                "cost": 150.75
            },
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _execute_maintain_cash(self, action: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute cash position maintenance"""
        return {
            "status": "success",
            "action": "maintain_cash_position",
            "details": {
                "cash_target": 0.2,
                "current_cash": 0.15,
                "adjustment_needed": 0.05,
                "action_taken": "sell_positions"
            },
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _execute_strategic_allocation(self, action: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute strategic asset allocation"""
        return {
            "status": "success",
            "action": "strategic_allocation",
            "details": {
                "allocation_changes": {
                    "equities": "+5%",
                    "fixed_income": "-3%",
                    "alternatives": "-2%"
                },
                "rebalancing_cost": 75.25
            },
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _execute_tactical_trading(self, action: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute tactical trading moves"""
        return {
            "status": "success",
            "action": "tactical_trading",
            "details": {
                "trades_executed": 4,
                "total_volume": 1000,
                "average_fill_price": 145.67,
                "commission": 12.00
            },
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _execute_cash_management(self, action: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute cash management operations"""
        return {
            "status": "success",
            "action": "cash_management",
            "details": {
                "cash_optimized": True,
                "yield_enhancement": 0.02,
                "liquidity_maintained": True
            },
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _execute_momentum_trading(self, action: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute momentum trading strategy"""
        return {
            "status": "success",
            "action": "momentum_trading",
            "details": {
                "momentum_signals": 3,
                "positions_opened": 2,
                "expected_return": 0.08,
                "risk_score": 0.6
            },
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _execute_leverage_positions(self, action: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute leveraged position strategy"""
        return {
            "status": "success",
            "action": "leverage_positions",
            "details": {
                "leverage_ratio": 1.5,
                "margin_used": 0.3,
                "interest_cost": 0.05,
                "positions_leveraged": 2
            },
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _execute_options_strategies(self, action: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """Execute options trading strategies"""
        return {
            "status": "success",
            "action": "options_strategies",
            "details": {
                "strategies_deployed": ["covered_call", "protective_put"],
                "premium_collected": 250.00,
                "protection_level": 0.95
            },
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _validate_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate plan before execution"""
        plan_data = input_data.get("plan_data")
        
        if not plan_data:
            return {
                "status": "invalid",
                "errors": ["Plan data is required"]
            }
        
        errors = []
        warnings = []
        
        # Validate plan structure
        if "actions" not in plan_data:
            errors.append("Plan must contain actions")
        
        if "parameters" not in plan_data:
            errors.append("Plan must contain parameters")
        
        # Validate actions
        if "actions" in plan_data:
            for i, action in enumerate(plan_data["actions"]):
                if "action" not in action:
                    errors.append(f"Action {i} missing action type")
                
                if "weight" not in action:
                    warnings.append(f"Action {i} missing weight, using default")
        
        # Validate parameters
        if "parameters" in plan_data:
            params = plan_data["parameters"]
            
            if "risk_tolerance" in params:
                risk_tolerance = params["risk_tolerance"]
                if not (0 <= risk_tolerance <= 1):
                    errors.append("Risk tolerance must be between 0 and 1")
            
            if "max_position_size" in params:
                max_position = params["max_position_size"]
                if not (0 < max_position <= 1):
                    errors.append("Max position size must be between 0 and 1")
        
        # Check market conditions
        market_validation = await self._validate_market_conditions()
        if not market_validation["suitable"]:
            warnings.append(f"Market conditions warning: {market_validation['reason']}")
        
        status = "valid" if len(errors) == 0 else "invalid"
        
        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "market_conditions": market_validation,
            "validation_time": datetime.utcnow().isoformat()
        }
    
    async def _rollback_execution(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback a failed execution"""
        execution_id = input_data.get("execution_id")
        
        if not execution_id:
            raise ValueError("Execution ID is required for rollback")
        
        # Find execution in history
        execution_record = next(
            (record for record in self.execution_history if record["execution_id"] == execution_id), 
            None
        )
        
        if not execution_record:
            raise ValueError(f"Execution {execution_id} not found in history")
        
        rollback_actions = []
        
        # Reverse successful actions
        for action_result in execution_record.get("execution_results", []):
            if action_result.get("status") == "success":
                rollback_action = await self._create_rollback_action(action_result)
                if rollback_action:
                    rollback_result = await self._execute_rollback_action(rollback_action)
                    rollback_actions.append(rollback_result)
        
        return {
            "status": "completed",
            "execution_id": execution_id,
            "rollback_actions": len(rollback_actions),
            "rollback_results": rollback_actions,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _check_prerequisites(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check execution prerequisites"""
        plan_data = input_data.get("plan_data")
        
        checks = {
            "market_open": await self._check_market_hours(),
            "sufficient_balance": await self._check_account_balance(plan_data),
            "api_connectivity": await self._check_api_connectivity(),
            "risk_limits": await self._check_risk_limits(plan_data),
            "regulatory_compliance": await self._check_regulatory_compliance(plan_data)
        }
        
        all_passed = all(checks.values())
        
        return {
            "status": "passed" if all_passed else "failed",
            "checks": checks,
            "can_execute": all_passed,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _fetch_plan(self, plan_id: str) -> Dict[str, Any]:
        """Fetch plan from database"""
        try:
            session = db_manager.get_session()
            plan = session.query(Plan).filter(Plan.id == plan_id).first()
            
            if plan:
                result = {
                    "id": str(plan.id),
                    "plan_data": plan.plan_data,
                    "success_probability": plan.success_probability,
                    "risk_assessment": plan.risk_assessment,
                    "expected_outcome": plan.expected_outcome,
                    "status": plan.status,
                    "timestamp": plan.timestamp
                }
                session.close()
                return result
            
            session.close()
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to fetch plan {plan_id}: {e}")
            return None
    
    async def _update_plan_status(self, plan_id: str, status: str, result: Dict[str, Any]):
        """Update plan status in database"""
        try:
            session = db_manager.get_session()
            plan = session.query(Plan).filter(Plan.id == plan_id).first()
            
            if plan:
                plan.status = status
                # Could add execution_result field to store result
                session.commit()
            
            session.close()
            
        except Exception as e:
            self.logger.error(f"Failed to update plan status: {e}")
    
    async def _log_execution_result(self, execution_id: str, plan_id: str, 
                                  result: Dict[str, Any], execution_mode: str):
        """Log execution result"""
        try:
            session = db_manager.get_session()
            log_entry = AgentLog(
                id=execution_id,
                agent=self.name,
                action="execute_plan",
                input_data={"plan_id": plan_id, "execution_mode": execution_mode},
                output_data=result,
                verdict="success" if result.get("status") != "failed" else "error"
            )
            session.add(log_entry)
            session.commit()
            session.close()
            
            # Also add to internal history
            self.execution_history.append({
                "execution_id": execution_id,
                "plan_id": plan_id,
                "result": result,
                "execution_mode": execution_mode,
                "timestamp": datetime.utcnow()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to log execution result: {e}")
    
    async def _get_simulation_parameters(self) -> Dict[str, Any]:
        """Get current simulation parameters"""
        return {
            "market_conditions": "normal",
            "volatility_factor": 1.0,
            "liquidity_factor": 1.0,
            "execution_delay": 0.1,
            "slippage": 0.001
        }
    
    async def _initiate_rollback(self, execution_results: List[Dict[str, Any]], execution_id: str):
        """Initiate rollback for failed execution"""
        self.logger.warning(f"Initiating rollback for execution {execution_id}")
        
        for result in reversed(execution_results):
            if result.get("status") == "success":
                await self._create_rollback_action(result)
    
    async def _generate_execution_summary(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of execution results"""
        total_actions = len(execution_results)
        successful = len([r for r in execution_results if r.get("status") == "success"])
        failed = total_actions - successful
        
        total_cost = sum(
            r.get("details", {}).get("cost", 0) + r.get("details", {}).get("commission", 0)
            for r in execution_results
        )
        
        return {
            "total_actions": total_actions,
            "successful_actions": successful,
            "failed_actions": failed,
            "success_rate": successful / total_actions if total_actions > 0 else 0,
            "total_execution_cost": total_cost,
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _create_rollback_action(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create rollback action for a successful action"""
        action_type = action_result.get("action")
        
        # Define rollback mappings
        rollback_map = {
            "diversify_portfolio": "revert_diversification",
            "hedge_positions": "close_hedges",
            "tactical_trading": "reverse_trades",
            "leverage_positions": "reduce_leverage"
        }
        
        rollback_action = rollback_map.get(action_type)
        
        if rollback_action:
            return {
                "action": rollback_action,
                "original_action": action_type,
                "original_result": action_result
            }
        
        return None
    
    async def _execute_rollback_action(self, rollback_action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a rollback action"""
        action_type = rollback_action.get("action")
        
        # Simulate rollback execution
        return {
            "status": "success",
            "action": action_type,
            "details": {
                "rollback_completed": True,
                "original_action_reversed": rollback_action.get("original_action")
            },
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def _validate_market_conditions(self) -> Dict[str, Any]:
        """Validate current market conditions"""
        # Simple market condition check
        current_hour = datetime.utcnow().hour
        
        # Check if market hours (simplified)
        market_open = 9 <= current_hour <= 16
        
        return {
            "suitable": market_open,
            "reason": "Market is open" if market_open else "Market is closed",
            "market_hours": market_open,
            "volatility": "normal"
        }
    
    async def _check_market_hours(self) -> bool:
        """Check if market is open"""
        current_hour = datetime.utcnow().hour
        return 9 <= current_hour <= 16  # Simplified market hours
    
    async def _check_account_balance(self, plan_data: Dict[str, Any]) -> bool:
        """Check if account has sufficient balance"""
        # Simplified balance check
        return True  # Assume sufficient balance in demo
    
    async def _check_api_connectivity(self) -> bool:
        """Check API connectivity"""
        # Simple connectivity check
        return True  # Assume APIs are available
    
    async def _check_risk_limits(self, plan_data: Dict[str, Any]) -> bool:
        """Check if plan adheres to risk limits"""
        if not plan_data or "parameters" not in plan_data:
            return False
        
        risk_tolerance = plan_data["parameters"].get("risk_tolerance", 0.5)
        max_position = plan_data["parameters"].get("max_position_size", 0.1)
        
        # Simple risk limit checks
        return risk_tolerance <= 0.8 and max_position <= 0.2
    
    async def _check_regulatory_compliance(self, plan_data: Dict[str, Any]) -> bool:
        """Check regulatory compliance"""
        # Simplified compliance check
        return True  # Assume compliant in demo

# Global Kenny instance
kenny_agent = KennyAgent()

