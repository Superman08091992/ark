import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent
from config.database import db_manager, DataPackage, Plan
from config.settings import settings
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

class JoeyAgent(BaseAgent):
    """Joey - Planning and Analysis Agent"""
    
    def __init__(self):
        super().__init__(
            name="Joey",
            description="Data analysis and strategic planning agent using ML models for trend identification"
        )
        self.models = {}
        self.scalers = {}
        self.analysis_depth = settings.JOEY_ANALYSIS_DEPTH
        self.confidence_threshold = 0.7
        
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for Joey"""
        required_fields = ["task_type"]
        return all(field in input_data for field in required_fields)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method for analysis and planning"""
        task_type = input_data.get("task_type")
        
        if task_type == "analyze_data":
            return await self._analyze_data(input_data)
        elif task_type == "generate_plans":
            return await self._generate_plans(input_data)
        elif task_type == "trend_analysis":
            return await self._trend_analysis(input_data)
        elif task_type == "risk_assessment":
            return await self._risk_assessment(input_data)
        elif task_type == "opportunity_detection":
            return await self._opportunity_detection(input_data)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _analyze_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze collected data packages"""
        data_package_ids = input_data.get("data_package_ids", [])
        analysis_type = input_data.get("analysis_type", "comprehensive")
        
        # Fetch data packages from database
        data_packages = await self._fetch_data_packages(data_package_ids)
        
        if not data_packages:
            return {
                "status": "error",
                "message": "No data packages found for analysis"
            }
        
        # Prepare data for analysis
        df = await self._prepare_dataframe(data_packages)
        
        # Perform analysis based on type
        if analysis_type == "basic":
            analysis_results = await self._basic_analysis(df)
        elif analysis_type == "standard":
            analysis_results = await self._standard_analysis(df)
        else:  # comprehensive
            analysis_results = await self._comprehensive_analysis(df)
        
        return {
            "status": "completed",
            "analysis_type": analysis_type,
            "data_points_analyzed": len(df),
            "analysis_results": analysis_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_plans(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic plans based on analysis"""
        analysis_results = input_data.get("analysis_results")
        plan_count = input_data.get("plan_count", 3)
        
        if not analysis_results:
            # Fetch recent analysis results
            analysis_results = await self._get_recent_analysis()
        
        plans = []
        
        for i in range(plan_count):
            plan = await self._create_plan(analysis_results, i)
            
            # Calculate success probability using ML models
            success_probability = await self._calculate_success_probability(plan)
            
            # Perform risk assessment
            risk_assessment = await self._assess_plan_risk(plan)
            
            # Calculate expected outcome
            expected_outcome = await self._calculate_expected_outcome(plan, success_probability, risk_assessment)
            
            plan_data = {
                "plan_id": f"plan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{i}",
                "plan_type": plan["type"],
                "actions": plan["actions"],
                "parameters": plan["parameters"],
                "success_probability": success_probability,
                "risk_assessment": risk_assessment,
                "expected_outcome": expected_outcome,
                "confidence_score": plan["confidence_score"],
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store plan in database
            plan_id = await self._store_plan(plan_data, input_data.get("data_package_ids", []))
            plan_data["stored_plan_id"] = plan_id
            
            plans.append(plan_data)
        
        # Rank plans by expected outcome
        ranked_plans = sorted(plans, key=lambda x: x["expected_outcome"]["score"], reverse=True)
        
        return {
            "status": "completed",
            "plans_generated": len(plans),
            "best_plan": ranked_plans[0] if ranked_plans else None,
            "all_plans": ranked_plans,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _trend_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform trend analysis on time series data"""
        data_package_ids = input_data.get("data_package_ids", [])
        trend_window = input_data.get("trend_window", 30)  # days
        
        data_packages = await self._fetch_data_packages(data_package_ids)
        df = await self._prepare_time_series_dataframe(data_packages)
        
        if df.empty:
            return {
                "status": "error",
                "message": "No time series data available for trend analysis"
            }
        
        trends = {}
        
        # Analyze trends for numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if column in df.columns and not df[column].isnull().all():
                trend_data = await self._analyze_column_trend(df[column], column, trend_window)
                trends[column] = trend_data
        
        # Detect pattern changes
        pattern_changes = await self._detect_pattern_changes(df)
        
        # Generate trend summary
        trend_summary = await self._generate_trend_summary(trends, pattern_changes)
        
        return {
            "status": "completed",
            "trend_analysis": trends,
            "pattern_changes": pattern_changes,
            "trend_summary": trend_summary,
            "data_points": len(df),
            "analysis_period": f"{trend_window} days",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _risk_assessment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk assessment"""
        plan_data = input_data.get("plan_data")
        market_data = input_data.get("market_data", {})
        
        if not plan_data:
            return {
                "status": "error",
                "message": "No plan data provided for risk assessment"
            }
        
        risk_factors = {
            "market_volatility": await self._assess_market_volatility(market_data),
            "liquidity_risk": await self._assess_liquidity_risk(plan_data),
            "concentration_risk": await self._assess_concentration_risk(plan_data),
            "execution_risk": await self._assess_execution_risk(plan_data),
            "regulatory_risk": await self._assess_regulatory_risk(plan_data)
        }
        
        # Calculate overall risk score
        risk_weights = {
            "market_volatility": 0.3,
            "liquidity_risk": 0.2,
            "concentration_risk": 0.2,
            "execution_risk": 0.15,
            "regulatory_risk": 0.15
        }
        
        overall_risk_score = sum(
            risk_factors[factor]["score"] * risk_weights[factor]
            for factor in risk_factors
        )
        
        risk_level = "low" if overall_risk_score < 0.3 else "medium" if overall_risk_score < 0.7 else "high"
        
        return {
            "status": "completed",
            "overall_risk_score": overall_risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendations": await self._generate_risk_recommendations(risk_factors, overall_risk_score),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _opportunity_detection(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect opportunities from market data and trends"""
        data_package_ids = input_data.get("data_package_ids", [])
        opportunity_types = input_data.get("opportunity_types", ["arbitrage", "momentum", "mean_reversion"])
        
        data_packages = await self._fetch_data_packages(data_package_ids)
        df = await self._prepare_dataframe(data_packages)
        
        opportunities = []
        
        for opp_type in opportunity_types:
            if opp_type == "arbitrage":
                arb_opportunities = await self._detect_arbitrage_opportunities(df)
                opportunities.extend(arb_opportunities)
            
            elif opp_type == "momentum":
                momentum_opportunities = await self._detect_momentum_opportunities(df)
                opportunities.extend(momentum_opportunities)
            
            elif opp_type == "mean_reversion":
                mean_rev_opportunities = await self._detect_mean_reversion_opportunities(df)
                opportunities.extend(mean_rev_opportunities)
        
        # Rank opportunities by potential return
        ranked_opportunities = sorted(
            opportunities, 
            key=lambda x: x.get("potential_return", 0), 
            reverse=True
        )
        
        return {
            "status": "completed",
            "opportunities_found": len(opportunities),
            "top_opportunities": ranked_opportunities[:5],
            "all_opportunities": ranked_opportunities,
            "detection_methods": opportunity_types,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _fetch_data_packages(self, package_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch data packages from database"""
        try:
            session = db_manager.get_session()
            
            if not package_ids:
                # Fetch recent data packages if no IDs provided
                packages = session.query(DataPackage).order_by(
                    DataPackage.timestamp.desc()
                ).limit(100).all()
            else:
                packages = session.query(DataPackage).filter(
                    DataPackage.id.in_(package_ids)
                ).all()
            
            result = []
            for package in packages:
                result.append({
                    "id": str(package.id),
                    "timestamp": package.timestamp,
                    "source": package.source,
                    "data_type": package.data_type,
                    "raw_data": package.raw_data,
                    "normalized_data": package.normalized_data,
                    "confidence_score": package.confidence_score,
                    "tags": package.tags
                })
            
            session.close()
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to fetch data packages: {e}")
            return []
    
    async def _prepare_dataframe(self, data_packages: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare pandas DataFrame from data packages"""
        data_rows = []
        
        for package in data_packages:
            normalized_data = package.get("normalized_data", {})
            
            row = {
                "package_id": package["id"],
                "timestamp": package["timestamp"],
                "source": package["source"],
                "data_type": package["data_type"],
                "confidence_score": package["confidence_score"]
            }
            
            # Flatten normalized data
            if isinstance(normalized_data, dict):
                for key, value in normalized_data.items():
                    if isinstance(value, (int, float, str)):
                        row[f"data_{key}"] = value
            
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Convert timestamp to datetime
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        return df
    
    async def _prepare_time_series_dataframe(self, data_packages: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare time series DataFrame with proper indexing"""
        df = await self._prepare_dataframe(data_packages)
        
        if "timestamp" in df.columns:
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    async def _basic_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform basic statistical analysis"""
        return {
            "summary_statistics": df.describe().to_dict(),
            "data_types": df.dtypes.to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "correlation_matrix": df.corr().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 1 else {}
        }
    
    async def _standard_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform standard analysis including trends and patterns"""
        basic_analysis = await self._basic_analysis(df)
        
        # Add trend analysis for numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        trends = {}
        
        for column in numeric_columns:
            if not df[column].isnull().all():
                trend_slope = np.polyfit(range(len(df)), df[column].fillna(0), 1)[0]
                trends[column] = {
                    "slope": trend_slope,
                    "direction": "increasing" if trend_slope > 0 else "decreasing" if trend_slope < 0 else "stable"
                }
        
        return {
            **basic_analysis,
            "trends": trends,
            "data_quality_score": await self._calculate_data_quality_score(df)
        }
    
    async def _comprehensive_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive analysis with ML insights"""
        standard_analysis = await self._standard_analysis(df)
        
        # ML-based insights
        ml_insights = {}
        
        if len(df) > 10:  # Minimum data for ML analysis
            # Clustering analysis
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) > 1:
                from sklearn.cluster import KMeans
                
                # Remove NaN values
                clean_df = numeric_df.fillna(numeric_df.mean())
                
                if len(clean_df) > 3:
                    kmeans = KMeans(n_clusters=min(3, len(clean_df)), random_state=42)
                    clusters = kmeans.fit_predict(clean_df)
                    ml_insights["clusters"] = {
                        "cluster_labels": clusters.tolist(),
                        "cluster_centers": kmeans.cluster_centers_.tolist()
                    }
        
        # Anomaly detection
        anomalies = await self._detect_anomalies(df)
        
        return {
            **standard_analysis,
            "ml_insights": ml_insights,
            "anomalies": anomalies,
            "predictive_indicators": await self._calculate_predictive_indicators(df)
        }
    
    async def _create_plan(self, analysis_results: Dict[str, Any], plan_index: int) -> Dict[str, Any]:
        """Create a strategic plan based on analysis results"""
        plan_types = ["conservative", "balanced", "aggressive"]
        plan_type = plan_types[plan_index % len(plan_types)]
        
        base_confidence = 60
        
        if plan_type == "conservative":
            return {
                "type": "conservative",
                "actions": [
                    {"action": "diversify_portfolio", "weight": 0.4},
                    {"action": "hedge_positions", "weight": 0.3},
                    {"action": "maintain_cash_position", "weight": 0.3}
                ],
                "parameters": {
                    "risk_tolerance": 0.2,
                    "max_position_size": 0.05,
                    "stop_loss": 0.02
                },
                "confidence_score": base_confidence + 10
            }
        
        elif plan_type == "balanced":
            return {
                "type": "balanced",
                "actions": [
                    {"action": "strategic_allocation", "weight": 0.5},
                    {"action": "tactical_trading", "weight": 0.3},
                    {"action": "cash_management", "weight": 0.2}
                ],
                "parameters": {
                    "risk_tolerance": 0.5,
                    "max_position_size": 0.1,
                    "stop_loss": 0.05
                },
                "confidence_score": base_confidence
            }
        
        else:  # aggressive
            return {
                "type": "aggressive",
                "actions": [
                    {"action": "momentum_trading", "weight": 0.6},
                    {"action": "leverage_positions", "weight": 0.3},
                    {"action": "options_strategies", "weight": 0.1}
                ],
                "parameters": {
                    "risk_tolerance": 0.8,
                    "max_position_size": 0.2,
                    "stop_loss": 0.1
                },
                "confidence_score": base_confidence - 10
            }
    
    async def _calculate_success_probability(self, plan: Dict[str, Any]) -> float:
        """Calculate success probability using ML models"""
        # Create feature vector from plan
        features = [
            plan["parameters"]["risk_tolerance"],
            plan["parameters"]["max_position_size"],
            plan["parameters"]["stop_loss"],
            plan["confidence_score"] / 100,
            len(plan["actions"])
        ]
        
        # Simple probability calculation (in production, use trained ML model)
        base_probability = 0.6
        
        # Adjust based on risk tolerance
        risk_factor = 1 - plan["parameters"]["risk_tolerance"] * 0.3
        
        # Adjust based on confidence
        confidence_factor = plan["confidence_score"] / 100
        
        probability = base_probability * risk_factor * confidence_factor
        
        return min(max(probability, 0.1), 0.95)  # Clamp between 0.1 and 0.95
    
    async def _assess_plan_risk(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk factors for a plan"""
        risk_tolerance = plan["parameters"]["risk_tolerance"]
        max_position_size = plan["parameters"]["max_position_size"]
        
        return {
            "overall_risk": risk_tolerance,
            "position_risk": max_position_size,
            "strategy_risk": {
                "conservative": 0.2,
                "balanced": 0.5,
                "aggressive": 0.8
            }.get(plan["type"], 0.5),
            "execution_complexity": len(plan["actions"]) * 0.1,
            "market_dependency": 0.6  # Assuming moderate market dependency
        }
    
    async def _calculate_expected_outcome(self, plan: Dict[str, Any], 
                                        success_probability: float, 
                                        risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate expected outcome for a plan"""
        # Base expected return based on plan type
        base_returns = {
            "conservative": 0.05,
            "balanced": 0.08,
            "aggressive": 0.12
        }
        
        base_return = base_returns.get(plan["type"], 0.08)
        
        # Adjust for success probability
        expected_return = base_return * success_probability
        
        # Calculate downside risk
        downside_risk = risk_assessment["overall_risk"] * 0.1
        
        # Risk-adjusted return
        risk_adjusted_return = expected_return - (downside_risk * 0.5)
        
        # Calculate score (combining return and probability)
        score = risk_adjusted_return * success_probability * 100
        
        return {
            "expected_return": expected_return,
            "downside_risk": downside_risk,
            "risk_adjusted_return": risk_adjusted_return,
            "score": score,
            "timeframe": "medium_term"
        }
    
    async def _store_plan(self, plan_data: Dict[str, Any], data_package_ids: List[str]) -> str:
        """Store plan in database"""
        try:
            session = db_manager.get_session()
            plan = Plan(
                plan_data=plan_data,
                success_probability=int(plan_data["success_probability"] * 100),
                risk_assessment=plan_data["risk_assessment"],
                expected_outcome=plan_data["expected_outcome"],
                data_package_ids=data_package_ids,
                status="pending"
            )
            session.add(plan)
            session.commit()
            
            plan_id = str(plan.id)
            session.close()
            
            self.logger.info(f"Stored plan {plan_id}")
            return plan_id
            
        except Exception as e:
            self.logger.error(f"Failed to store plan: {e}")
            raise
    
    async def _get_recent_analysis(self) -> Dict[str, Any]:
        """Get recent analysis results"""
        # In production, fetch from cache or database
        return {
            "summary_statistics": {},
            "trends": {},
            "data_quality_score": 0.8
        }
    
    async def _analyze_column_trend(self, series: pd.Series, column_name: str, window: int) -> Dict[str, Any]:
        """Analyze trend for a specific column"""
        if len(series) < 2:
            return {"trend": "insufficient_data"}
        
        # Calculate trend slope
        x = np.arange(len(series))
        y = series.fillna(series.mean())
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # Calculate trend strength (R-squared)
        correlation = np.corrcoef(x, y)[0, 1]
        r_squared = correlation ** 2
        
        return {
            "slope": slope,
            "trend_direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
            "trend_strength": r_squared,
            "volatility": series.std(),
            "recent_change": series.iloc[-1] - series.iloc[0] if len(series) > 1 else 0
        }
    
    async def _detect_pattern_changes(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect significant pattern changes in data"""
        changes = []
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if column in df.columns and len(df[column].dropna()) > 10:
                series = df[column].dropna()
                
                # Simple change point detection using rolling statistics
                rolling_mean = series.rolling(window=5, min_periods=1).mean()
                rolling_std = series.rolling(window=5, min_periods=1).std()
                
                # Detect where values deviate significantly from rolling statistics
                threshold = 2 * rolling_std
                anomalies = np.abs(series - rolling_mean) > threshold
                
                if anomalies.any():
                    change_points = series[anomalies].index.tolist()
                    changes.append({
                        "column": column,
                        "change_points": len(change_points),
                        "significant_changes": change_points[:5]  # Limit to 5 most recent
                    })
        
        return changes
    
    async def _generate_trend_summary(self, trends: Dict[str, Any], 
                                    pattern_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of trend analysis"""
        if not trends:
            return {"summary": "No trends detected"}
        
        increasing_trends = [k for k, v in trends.items() if v.get("trend_direction") == "increasing"]
        decreasing_trends = [k for k, v in trends.items() if v.get("trend_direction") == "decreasing"]
        
        total_changes = sum(change["change_points"] for change in pattern_changes)
        
        return {
            "total_metrics_analyzed": len(trends),
            "increasing_trends": len(increasing_trends),
            "decreasing_trends": len(decreasing_trends),
            "stable_trends": len(trends) - len(increasing_trends) - len(decreasing_trends),
            "pattern_changes_detected": total_changes,
            "market_sentiment": "bullish" if len(increasing_trends) > len(decreasing_trends) else "bearish" if len(decreasing_trends) > len(increasing_trends) else "neutral"
        }
    
    async def _assess_market_volatility(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess market volatility risk factor"""
        # Simple volatility assessment based on available data
        volatility_score = market_data.get("volatility", 0.5)  # Default moderate volatility
        
        return {
            "score": volatility_score,
            "level": "high" if volatility_score > 0.7 else "medium" if volatility_score > 0.3 else "low",
            "description": "Market volatility assessment based on recent price movements"
        }
    
    async def _assess_liquidity_risk(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess liquidity risk factor"""
        position_size = plan_data["parameters"]["max_position_size"]
        liquidity_score = min(position_size * 2, 1.0)  # Higher position size = higher liquidity risk
        
        return {
            "score": liquidity_score,
            "level": "high" if liquidity_score > 0.7 else "medium" if liquidity_score > 0.3 else "low",
            "description": "Liquidity risk based on position sizing and market depth"
        }
    
    async def _assess_concentration_risk(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess concentration risk factor"""
        # Number of different actions indicates diversification
        action_count = len(plan_data["actions"])
        concentration_score = max(0, 1 - (action_count - 1) * 0.2)
        
        return {
            "score": concentration_score,
            "level": "high" if concentration_score > 0.7 else "medium" if concentration_score > 0.3 else "low",
            "description": "Concentration risk based on strategy diversification"
        }
    
    async def _assess_execution_risk(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess execution risk factor"""
        complexity = len(plan_data["actions"]) * 0.15
        execution_score = min(complexity, 1.0)
        
        return {
            "score": execution_score,
            "level": "high" if execution_score > 0.7 else "medium" if execution_score > 0.3 else "low",
            "description": "Execution risk based on strategy complexity"
        }
    
    async def _assess_regulatory_risk(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess regulatory risk factor"""
        # Aggressive strategies may have higher regulatory risk
        regulatory_score = {"conservative": 0.1, "balanced": 0.3, "aggressive": 0.6}.get(plan_data["type"], 0.3)
        
        return {
            "score": regulatory_score,
            "level": "high" if regulatory_score > 0.7 else "medium" if regulatory_score > 0.3 else "low",
            "description": "Regulatory risk based on strategy type and compliance requirements"
        }
    
    async def _generate_risk_recommendations(self, risk_factors: Dict[str, Any], 
                                           overall_risk_score: float) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if overall_risk_score > 0.7:
            recommendations.append("Consider reducing overall position sizes")
            recommendations.append("Implement additional hedging strategies")
        
        if risk_factors["market_volatility"]["score"] > 0.7:
            recommendations.append("Increase stop-loss protection during high volatility periods")
        
        if risk_factors["concentration_risk"]["score"] > 0.7:
            recommendations.append("Diversify across more strategies and asset classes")
        
        if risk_factors["liquidity_risk"]["score"] > 0.7:
            recommendations.append("Ensure adequate cash reserves for position management")
        
        return recommendations
    
    async def _detect_arbitrage_opportunities(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect arbitrage opportunities"""
        opportunities = []
        
        # Simple price spread detection between sources
        price_columns = [col for col in df.columns if "price" in col.lower() or "close" in col.lower()]
        
        if len(price_columns) >= 2:
            for i in range(len(price_columns)):
                for j in range(i + 1, len(price_columns)):
                    col1, col2 = price_columns[i], price_columns[j]
                    
                    # Calculate price differences
                    price_diff = df[col1] - df[col2]
                    avg_diff = price_diff.mean()
                    
                    if abs(avg_diff) > 0.01:  # Threshold for significant difference
                        opportunities.append({
                            "type": "arbitrage",
                            "sources": [col1, col2],
                            "price_difference": avg_diff,
                            "potential_return": abs(avg_diff) * 0.8,  # Assuming 80% capture rate
                            "confidence": 0.7
                        })
        
        return opportunities
    
    async def _detect_momentum_opportunities(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect momentum opportunities"""
        opportunities = []
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if len(df[column].dropna()) > 5:
                series = df[column].dropna()
                
                # Calculate momentum (rate of change)
                momentum = (series.iloc[-1] - series.iloc[0]) / series.iloc[0] if series.iloc[0] != 0 else 0
                
                if abs(momentum) > 0.05:  # 5% threshold
                    opportunities.append({
                        "type": "momentum",
                        "metric": column,
                        "momentum_score": momentum,
                        "direction": "bullish" if momentum > 0 else "bearish",
                        "potential_return": abs(momentum) * 0.5,
                        "confidence": 0.6
                    })
        
        return opportunities
    
    async def _detect_mean_reversion_opportunities(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect mean reversion opportunities"""
        opportunities = []
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if len(df[column].dropna()) > 10:
                series = df[column].dropna()
                
                # Calculate deviation from moving average
                moving_avg = series.rolling(window=5, min_periods=1).mean()
                current_value = series.iloc[-1]
                avg_value = moving_avg.iloc[-1]
                
                deviation = (current_value - avg_value) / avg_value if avg_value != 0 else 0
                
                if abs(deviation) > 0.1:  # 10% deviation threshold
                    opportunities.append({
                        "type": "mean_reversion",
                        "metric": column,
                        "deviation": deviation,
                        "current_value": current_value,
                        "mean_value": avg_value,
                        "potential_return": abs(deviation) * 0.3,
                        "confidence": 0.5
                    })
        
        return opportunities
    
    async def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate overall data quality score"""
        if df.empty:
            return 0.0
        
        # Factors affecting data quality
        completeness = 1 - (df.isnull().sum().sum() / (len(df) * len(df.columns)))
        consistency = 1.0  # Placeholder - would implement consistency checks
        timeliness = 1.0   # Placeholder - would check data freshness
        accuracy = 1.0     # Placeholder - would implement accuracy checks
        
        # Weighted average
        quality_score = (completeness * 0.4 + consistency * 0.2 + timeliness * 0.2 + accuracy * 0.2)
        
        return round(quality_score, 2)
    
    async def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in the data"""
        anomalies = []
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if not df[column].isnull().all():
                series = df[column].dropna()
                
                # Simple outlier detection using IQR
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = series[(series < lower_bound) | (series > upper_bound)]
                
                if len(outliers) > 0:
                    anomalies.append({
                        "column": column,
                        "outlier_count": len(outliers),
                        "outlier_percentage": len(outliers) / len(series) * 100,
                        "outlier_values": outliers.head(5).tolist()
                    })
        
        return anomalies
    
    async def _calculate_predictive_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate predictive indicators"""
        indicators = {}
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if len(df[column].dropna()) > 3:
                series = df[column].dropna()
                
                # Simple predictive indicators
                indicators[column] = {
                    "trend_strength": abs(np.corrcoef(np.arange(len(series)), series)[0, 1]) if len(series) > 1 else 0,
                    "volatility": series.std(),
                    "momentum": (series.iloc[-1] - series.iloc[0]) / series.iloc[0] if series.iloc[0] != 0 else 0,
                    "recent_direction": "up" if len(series) > 1 and series.iloc[-1] > series.iloc[-2] else "down"
                }
        
        return indicators

# Global Joey instance
joey_agent = JoeyAgent()

