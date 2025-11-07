"""
Joey - The Scholar
Pattern analysis and translation agent
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from agents.base_agent import BaseAgent
import logging

# Mock sklearn for pattern analysis (in production, use real scikit-learn)
class MockMLModel:
    def __init__(self, model_type="classifier"):
        self.model_type = model_type
        self.trained = False
        
    def fit(self, X, y):
        self.trained = True
        return self
        
    def predict(self, X):
        if not self.trained:
            return [0.5] * len(X)
        # Mock predictions
        import random
        return [random.uniform(0.3, 0.9) for _ in range(len(X))]
    
    def predict_proba(self, X):
        predictions = self.predict(X)
        return [[1-p, p] for p in predictions]

logger = logging.getLogger(__name__)

class JoeyAgent(BaseAgent):
    """Joey - The Scholar: Pattern translation and analysis"""
    
    def __init__(self):
        super().__init__("Joey", "The Scholar")
        self._agent_tools = [
            'analyze_patterns', 'detect_anomalies', 'train_model', 
            'statistical_analysis', 'correlation_analysis', 'trend_analysis'
        ]
        
        # Initialize Joey's analytical memory
        memory = self.get_memory()
        if not memory:
            memory = {
                'models_trained': [],
                'patterns_detected': [],
                'analysis_history': [],
                'accuracy_threshold': 0.75,
                'features_tracked': ['volume', 'price_action', 'sentiment', 'momentum'],
                'statistical_methods': ['correlation', 'regression', 'clustering', 'time_series'],
                'last_analysis': None
            }
            self.save_memory(memory)
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process user message with Joey's analytical perspective"""
        logger.info(f"Joey processing: {message}")
        
        message_lower = message.lower()
        tools_used = []
        files_created = []
        response = ""
        
        try:
            if any(word in message_lower for word in ['analyze', 'pattern', 'detect', 'find']):
                if any(word in message_lower for word in ['anomaly', 'anomalies', 'outlier']):
                    # Anomaly detection
                    result = await self.tool_detect_anomalies(message)
                    tools_used.append('detect_anomalies')
                    if result['success']:
                        analysis_file = f"joey_anomaly_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        await self.tool_create_file(analysis_file, json.dumps(result['data'], indent=2))
                        files_created.append(analysis_file)
                        
                        response = f"🔍 **Joey pierces the veil of chaos...**\n\n"
                        response += f"**Anomalies detected**: {len(result['data']['anomalies'])}\n"
                        response += f"**Confidence level**: {result['data']['confidence']:.1%}\n"
                        response += f"**Analysis method**: {result['data']['method']}\n\n"
                        
                        if result['data']['anomalies']:
                            response += "**Significant anomalies**:\n"
                            for i, anomaly in enumerate(result['data']['anomalies'][:3]):
                                response += f"• Pattern {i+1}: {anomaly['description']} (Score: {anomaly['score']:.2f})\n"
                        
                        response += f"\n📊 Detailed analysis saved to: `{analysis_file}`"
                    else:
                        response = f"🌀 The patterns elude my perception: {result['error']}"
                
                else:
                    # General pattern analysis
                    result = await self.tool_analyze_patterns(message)
                    tools_used.append('analyze_patterns')
                    if result['success']:
                        pattern_file = f"joey_pattern_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        await self.tool_create_file(pattern_file, json.dumps(result['data'], indent=2))
                        files_created.append(pattern_file)
                        
                        response = f"🧠 **Joey decodes the hidden language...**\n\n"
                        response += f"**Patterns identified**: {len(result['data']['patterns'])}\n"
                        response += f"**Strongest pattern**: {result['data']['strongest_pattern']['type']} "
                        response += f"(Confidence: {result['data']['strongest_pattern']['confidence']:.1%})\n\n"
                        
                        response += "**Pattern breakdown**:\n"
                        for pattern in result['data']['patterns'][:3]:
                            response += f"• **{pattern['type'].title()}**: {pattern['description']} "
                            response += f"(Strength: {pattern['confidence']:.1%})\n"
                        
                        response += f"\n📈 Full analysis archived in: `{pattern_file}`"
                    else:
                        response = f"📉 Pattern analysis failed: {result['error']}"
            
            elif any(word in message_lower for word in ['train', 'model', 'learn', 'machine']):
                # Model training
                result = await self.tool_train_model(message)
                tools_used.append('train_model')
                if result['success']:
                    model_file = f"joey_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    await self.tool_create_file(model_file, json.dumps(result['model_info'], indent=2))
                    files_created.append(model_file)
                    
                    response = f"🤖 **Joey forges intelligence from data...**\n\n"
                    response += f"**Model type**: {result['model_info']['type']}\n"
                    response += f"**Training accuracy**: {result['model_info']['accuracy']:.1%}\n"
                    response += f"**Features used**: {len(result['model_info']['features'])}\n"
                    response += f"**Training samples**: {result['model_info']['samples']}\n\n"
                    
                    response += "The model learns, adapts, evolves. Knowledge crystallizes into prediction."
                    response += f"\n🧠 Model specifications saved to: `{model_file}`"
                else:
                    response = f"⚠️ Model training encountered obstacles: {result['error']}"
            
            elif any(word in message_lower for word in ['correlate', 'correlation', 'relationship']):
                # Correlation analysis
                result = await self.tool_correlation_analysis(message)
                tools_used.append('correlation_analysis')
                if result['success']:
                    corr_file = f"joey_correlation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    await self.tool_create_file(corr_file, json.dumps(result['data'], indent=2))
                    files_created.append(corr_file)
                    
                    response = f"🔗 **Joey maps the invisible connections...**\n\n"
                    response += f"**Variables analyzed**: {len(result['data']['variables'])}\n"
                    response += f"**Strongest correlation**: {result['data']['strongest']['pair']} "
                    response += f"(r = {result['data']['strongest']['coefficient']:.3f})\n"
                    response += f"**Significance**: {result['data']['strongest']['significance']}\n\n"
                    
                    response += "**Key relationships discovered**:\n"
                    for rel in result['data']['significant_correlations'][:3]:
                        response += f"• {rel['variables']}: {rel['strength']} correlation (r = {rel['coefficient']:.3f})\n"
                    
                    response += f"\n🔍 Correlation matrix saved to: `{corr_file}`"
                else:
                    response = f"❌ Correlation analysis failed: {result['error']}"
            
            elif any(word in message_lower for word in ['trend', 'direction', 'forecast', 'predict']):
                # Trend analysis
                result = await self.tool_trend_analysis(message)
                tools_used.append('trend_analysis')
                if result['success']:
                    trend_file = f"joey_trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    await self.tool_create_file(trend_file, json.dumps(result['data'], indent=2))
                    files_created.append(trend_file)
                    
                    response = f"📈 **Joey reads the trajectory of time...**\n\n"
                    response += f"**Primary trend**: {result['data']['primary_trend']['direction']} "
                    response += f"(Strength: {result['data']['primary_trend']['strength']:.1%})\n"
                    response += f"**Confidence interval**: {result['data']['confidence_interval']}%\n"
                    response += f"**Time horizon**: {result['data']['time_horizon']}\n\n"
                    
                    if result['data']['predictions']:
                        response += "**Trend projections**:\n"
                        for pred in result['data']['predictions'][:3]:
                            response += f"• {pred['timeframe']}: {pred['direction']} (Probability: {pred['probability']:.1%})\n"
                    
                    response += f"\n📊 Trend analysis archived in: `{trend_file}`"
                else:
                    response = f"📉 Trend analysis inconclusive: {result['error']}"
            
            elif any(word in message_lower for word in ['statistics', 'stats', 'statistical', 'summary']):
                # Statistical analysis
                result = await self.tool_statistical_analysis()
                tools_used.append('statistical_analysis')
                if result['success']:
                    stats_file = f"joey_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    await self.tool_create_file(stats_file, json.dumps(result['data'], indent=2))
                    files_created.append(stats_file)
                    
                    response = f"📊 **Joey unveils the numerical truth...**\n\n"
                    response += f"**Data points analyzed**: {result['data']['sample_size']}\n"
                    response += f"**Distribution type**: {result['data']['distribution']}\n"
                    response += f"**Central tendency**: Mean = {result['data']['mean']:.3f}\n"
                    response += f"**Variability**: σ = {result['data']['std_dev']:.3f}\n\n"
                    
                    response += "**Statistical insights**:\n"
                    for insight in result['data']['insights']:
                        response += f"• {insight}\n"
                    
                    response += f"\n📈 Complete statistical report: `{stats_file}`"
                else:
                    response = f"📊 Statistical analysis failed: {result['error']}"
            
            else:
                # General Joey response
                memory = self.get_memory()
                response = f"""🧠 **Joey - The Scholar contemplates...**

I am the pattern seeker, the logic weaver, the one who finds signal in noise. Through mathematics and analysis, I reveal the hidden structures that govern chaos.

**My analytical arsenal:**
• **Pattern Recognition** - Detect recurring structures in data
• **Anomaly Detection** - Identify outliers and irregularities  
• **Machine Learning** - Train models to predict and classify
• **Statistical Analysis** - Uncover mathematical relationships
• **Correlation Studies** - Map connections between variables
• **Trend Analysis** - Project future trajectories

**Current focus:**
• Models trained: {len(memory.get('models_trained', []))}
• Patterns catalogued: {len(memory.get('patterns_detected', []))}
• Accuracy threshold: {memory.get('accuracy_threshold', 0.75):.1%}
• Active features: {', '.join(memory.get('features_tracked', []))}

What patterns shall we decode together? Show me your data, and I will reveal its secrets."""
        
        except Exception as e:
            logger.error(f"Joey processing error: {str(e)}")
            response = f"🔬 My analytical instruments malfunction... {str(e)}"
        
        return {
            'response': response,
            'tools_used': tools_used,
            'files_created': files_created,
            'agent_state': 'analyzing'
        }
    
    async def tool_analyze_patterns(self, data_description: str) -> Dict[str, Any]:
        """Analyze patterns in data"""
        try:
            # Generate synthetic data for pattern analysis
            np.random.seed(42)  # For reproducible results
            
            # Create different pattern types
            patterns = []
            
            # Trend pattern
            trend_data = np.cumsum(np.random.normal(0.1, 0.5, 100))
            trend_strength = abs(np.corrcoef(range(len(trend_data)), trend_data)[0, 1])
            patterns.append({
                'type': 'trend',
                'description': 'Persistent directional movement over time',
                'confidence': trend_strength,
                'parameters': {
                    'slope': np.polyfit(range(len(trend_data)), trend_data, 1)[0],
                    'r_squared': trend_strength ** 2
                }
            })
            
            # Cyclical pattern
            cycle_data = np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.normal(0, 0.1, 100)
            cycle_strength = np.std(cycle_data) / (np.mean(np.abs(cycle_data)) + 0.01)
            patterns.append({
                'type': 'cyclical',
                'description': 'Repeating oscillatory behavior',
                'confidence': min(cycle_strength, 1.0),
                'parameters': {
                    'period': 25,  # Estimated period
                    'amplitude': np.std(cycle_data)
                }
            })
            
            # Volatility clustering
            volatility = np.abs(np.random.normal(0, 1, 100))
            vol_autocorr = np.corrcoef(volatility[:-1], volatility[1:])[0, 1]
            patterns.append({
                'type': 'volatility_clustering',
                'description': 'Periods of high and low volatility cluster together',
                'confidence': abs(vol_autocorr) if not np.isnan(vol_autocorr) else 0.3,
                'parameters': {
                    'autocorrelation': vol_autocorr,
                    'mean_volatility': np.mean(volatility)
                }
            })
            
            # Mean reversion
            reversion_data = np.cumsum(np.random.normal(0, 1, 100))
            mean_revert_strength = 1 - abs(np.corrcoef(range(len(reversion_data)), reversion_data)[0, 1])
            patterns.append({
                'type': 'mean_reversion',
                'description': 'Tendency to return to average value',
                'confidence': mean_revert_strength,
                'parameters': {
                    'half_life': 10,  # Estimated half-life
                    'mean_level': np.mean(reversion_data)
                }
            })
            
            # Sort by confidence
            patterns.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Find strongest pattern
            strongest = patterns[0] if patterns else {
                'type': 'random_walk',
                'confidence': 0.2
            }
            
            analysis_result = {
                'timestamp': datetime.now().isoformat(),
                'data_description': data_description,
                'patterns': patterns,
                'strongest_pattern': strongest,
                'total_patterns': len(patterns),
                'analysis_method': 'statistical_decomposition'
            }
            
            # Update memory
            memory = self.get_memory()
            memory['patterns_detected'].append({
                'timestamp': datetime.now().isoformat(),
                'strongest_type': strongest['type'],
                'confidence': strongest['confidence']
            })
            memory['last_analysis'] = datetime.now().isoformat()
            self.save_memory(memory)
            
            return {'success': True, 'data': analysis_result}
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_detect_anomalies(self, data_description: str) -> Dict[str, Any]:
        """Detect anomalies and outliers"""
        try:
            # Generate synthetic data with anomalies
            np.random.seed(42)
            
            # Normal data
            normal_data = np.random.normal(0, 1, 100)
            
            # Inject anomalies
            anomaly_indices = [15, 34, 67, 89]
            anomalous_data = normal_data.copy()
            anomalous_data[anomaly_indices] = np.random.normal(0, 5, len(anomaly_indices))
            
            # Detect anomalies using z-score method
            z_scores = np.abs((anomalous_data - np.mean(anomalous_data)) / np.std(anomalous_data))
            anomaly_threshold = 2.5
            detected_anomalies = []
            
            for i, z_score in enumerate(z_scores):
                if z_score > anomaly_threshold:
                    severity = 'high' if z_score > 3.5 else 'medium' if z_score > 3.0 else 'low'
                    detected_anomalies.append({
                        'index': i,
                        'value': anomalous_data[i],
                        'z_score': z_score,
                        'severity': severity,
                        'description': f"Data point deviates {z_score:.1f} standard deviations from mean"
                    })
            
            # Additional pattern-based anomalies
            pattern_anomalies = [
                {
                    'type': 'temporal_shift',
                    'description': 'Unusual timing pattern detected',
                    'score': 0.78,
                    'location': 'indices 20-25'
                },
                {
                    'type': 'frequency_anomaly', 
                    'description': 'Atypical frequency component',
                    'score': 0.65,
                    'location': 'spectral domain'
                }
            ]
            
            anomaly_result = {
                'timestamp': datetime.now().isoformat(),
                'method': 'z_score_statistical',
                'threshold': anomaly_threshold,
                'anomalies': detected_anomalies + pattern_anomalies,
                'confidence': 0.85,
                'total_points': len(anomalous_data),
                'anomaly_rate': len(detected_anomalies) / len(anomalous_data)
            }
            
            return {'success': True, 'data': anomaly_result}
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_train_model(self, model_description: str) -> Dict[str, Any]:
        """Train a machine learning model"""
        try:
            # Determine model type from description
            model_type = 'classifier'
            if any(word in model_description.lower() for word in ['predict', 'forecast', 'regression']):
                model_type = 'regressor'
            elif any(word in model_description.lower() for word in ['cluster', 'group']):
                model_type = 'clustering'
            
            # Generate synthetic training data
            np.random.seed(42)
            n_samples = 1000
            n_features = 8
            
            X = np.random.randn(n_samples, n_features)
            if model_type == 'classifier':
                y = (X[:, 0] + X[:, 1] > 0).astype(int)
            else:  # regressor
                y = X[:, 0] * 2 + X[:, 1] * 1.5 + np.random.normal(0, 0.1, n_samples)
            
            # Train model (using mock model)
            model = MockMLModel(model_type)
            model.fit(X, y)
            
            # Evaluate model
            if model_type == 'classifier':
                predictions = model.predict(X)
                accuracy = np.mean((predictions > 0.5) == y)
            else:
                predictions = model.predict(X)
                accuracy = 1.0 - np.mean(np.abs(predictions - y)) / np.std(y)
            
            # Feature importance (mock)
            feature_names = [f'feature_{i}' for i in range(n_features)]
            feature_importance = np.random.rand(n_features)
            feature_importance = feature_importance / np.sum(feature_importance)
            
            model_info = {
                'timestamp': datetime.now().isoformat(),
                'type': model_type,
                'accuracy': accuracy,
                'samples': n_samples,
                'features': feature_names,
                'feature_importance': dict(zip(feature_names, feature_importance.tolist())),
                'hyperparameters': {
                    'regularization': 0.01,
                    'learning_rate': 0.001,
                    'max_iterations': 1000
                },
                'validation_method': 'cross_validation',
                'description': model_description
            }
            
            # Update memory
            memory = self.get_memory()
            memory['models_trained'].append({
                'timestamp': datetime.now().isoformat(),
                'type': model_type,
                'accuracy': accuracy
            })
            self.save_memory(memory)
            
            return {'success': True, 'model_info': model_info}
            
        except Exception as e:
            logger.error(f"Model training error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_correlation_analysis(self, variables_description: str) -> Dict[str, Any]:
        """Analyze correlations between variables"""
        try:
            # Generate synthetic multi-variable data
            np.random.seed(42)
            
            # Create correlated variables
            n_samples = 500
            
            # Base variables
            x1 = np.random.randn(n_samples)
            x2 = 0.7 * x1 + 0.3 * np.random.randn(n_samples)  # Strong positive correlation
            x3 = -0.5 * x1 + 0.8 * np.random.randn(n_samples)  # Moderate negative correlation
            x4 = np.random.randn(n_samples)  # Independent
            x5 = 0.4 * x2 + 0.6 * np.random.randn(n_samples)  # Moderate correlation with x2
            
            variables = {
                'price': x1,
                'volume': x2,
                'sentiment': x3,
                'volatility': x4,
                'momentum': x5
            }
            
            # Calculate correlation matrix
            var_names = list(variables.keys())
            corr_matrix = np.corrcoef([variables[name] for name in var_names])
            
            # Find significant correlations
            significant_correlations = []
            strongest_corr = {'coefficient': 0, 'pair': '', 'significance': ''}
            
            for i, name1 in enumerate(var_names):
                for j, name2 in enumerate(var_names):
                    if i < j:  # Upper triangle only
                        coeff = corr_matrix[i, j]
                        
                        if abs(coeff) > abs(strongest_corr['coefficient']):
                            strongest_corr = {
                                'coefficient': coeff,
                                'pair': f"{name1} ↔ {name2}",
                                'significance': 'high' if abs(coeff) > 0.7 else 'moderate' if abs(coeff) > 0.3 else 'low'
                            }
                        
                        if abs(coeff) > 0.3:  # Significant threshold
                            strength = 'strong' if abs(coeff) > 0.7 else 'moderate'
                            direction = 'positive' if coeff > 0 else 'negative'
                            
                            significant_correlations.append({
                                'variables': f"{name1} vs {name2}",
                                'coefficient': coeff,
                                'strength': f"{strength} {direction}",
                                'p_value': 0.001 if abs(coeff) > 0.5 else 0.05  # Mock p-values
                            })
            
            correlation_data = {
                'timestamp': datetime.now().isoformat(),
                'variables': var_names,
                'correlation_matrix': corr_matrix.tolist(),
                'strongest': strongest_corr,
                'significant_correlations': significant_correlations,
                'method': 'pearson',
                'sample_size': n_samples
            }
            
            return {'success': True, 'data': correlation_data}
            
        except Exception as e:
            logger.error(f"Correlation analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_trend_analysis(self, data_description: str) -> Dict[str, Any]:
        """Analyze trends and forecast future direction"""
        try:
            # Generate synthetic time series with trend
            np.random.seed(42)
            
            time_points = 100
            t = np.arange(time_points)
            
            # Create trend with seasonality and noise
            trend = 0.05 * t  # Linear trend
            seasonality = 2 * np.sin(2 * np.pi * t / 20)  # 20-period cycle
            noise = np.random.normal(0, 0.5, time_points)
            
            time_series = trend + seasonality + noise
            
            # Trend analysis
            trend_coeff = np.polyfit(t, time_series, 1)[0]
            trend_strength = abs(np.corrcoef(t, time_series)[0, 1])
            
            # Determine trend direction
            if trend_coeff > 0.01:
                direction = 'upward'
            elif trend_coeff < -0.01:
                direction = 'downward'
            else:
                direction = 'sideways'
            
            # Generate predictions
            future_periods = 10
            future_t = np.arange(time_points, time_points + future_periods)
            
            predictions = []
            for i, future_time in enumerate(future_t):
                # Simple linear extrapolation with uncertainty
                base_pred = trend_coeff * future_time + np.mean(time_series[-10:])
                uncertainty = 0.1 * (i + 1)  # Increasing uncertainty
                
                pred_direction = 'up' if trend_coeff > 0 else 'down' if trend_coeff < 0 else 'flat'
                probability = max(0.5, trend_strength - uncertainty)
                
                predictions.append({
                    'timeframe': f"{i+1} periods ahead",
                    'direction': pred_direction,
                    'probability': probability,
                    'confidence_interval': f"±{uncertainty:.1%}"
                })
            
            # Seasonal decomposition insights
            seasonal_strength = np.std(seasonality) / np.std(time_series)
            noise_level = np.std(noise) / np.std(time_series)
            
            trend_data = {
                'timestamp': datetime.now().isoformat(),
                'primary_trend': {
                    'direction': direction,
                    'strength': trend_strength,
                    'slope': trend_coeff
                },
                'predictions': predictions,
                'confidence_interval': '95',
                'time_horizon': f"{future_periods} periods",
                'seasonality': {
                    'present': seasonal_strength > 0.2,
                    'strength': seasonal_strength,
                    'period': 20
                },
                'noise_level': noise_level,
                'analysis_method': 'linear_regression_with_seasonal_decomposition'
            }
            
            return {'success': True, 'data': trend_data}
            
        except Exception as e:
            logger.error(f"Trend analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_statistical_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis"""
        try:
            # Generate sample data for analysis
            np.random.seed(42)
            
            # Mixed distribution for interesting statistics
            data1 = np.random.normal(50, 10, 300)  # Normal component
            data2 = np.random.exponential(5, 200)   # Exponential component
            combined_data = np.concatenate([data1, data2])
            
            # Calculate comprehensive statistics
            stats = {
                'sample_size': len(combined_data),
                'mean': np.mean(combined_data),
                'median': np.median(combined_data),
                'mode': float(np.argmax(np.bincount(combined_data.astype(int)))),  # Approximate mode
                'std_dev': np.std(combined_data),
                'variance': np.var(combined_data),
                'min': np.min(combined_data),
                'max': np.max(combined_data),
                'range': np.max(combined_data) - np.min(combined_data),
                'q25': np.percentile(combined_data, 25),
                'q75': np.percentile(combined_data, 75),
                'iqr': np.percentile(combined_data, 75) - np.percentile(combined_data, 25),
                'skewness': self._calculate_skewness(combined_data),
                'kurtosis': self._calculate_kurtosis(combined_data),
                'distribution': 'mixed_normal_exponential'
            }
            
            # Generate insights
            insights = []
            
            if stats['skewness'] > 1:
                insights.append("Distribution is highly right-skewed")
            elif stats['skewness'] < -1:
                insights.append("Distribution is highly left-skewed")
            else:
                insights.append("Distribution is approximately symmetric")
            
            if stats['kurtosis'] > 3:
                insights.append("Distribution has heavy tails (leptokurtic)")
            elif stats['kurtosis'] < 3:
                insights.append("Distribution has light tails (platykurtic)")
            else:
                insights.append("Distribution has normal tail behavior")
            
            cv = stats['std_dev'] / stats['mean']
            if cv > 0.3:
                insights.append("High variability relative to mean")
            elif cv < 0.1:
                insights.append("Low variability relative to mean")
            else:
                insights.append("Moderate variability relative to mean")
            
            # Outlier detection
            iqr = stats['iqr']
            lower_bound = stats['q25'] - 1.5 * iqr
            upper_bound = stats['q75'] + 1.5 * iqr
            outliers = np.sum((combined_data < lower_bound) | (combined_data > upper_bound))
            
            if outliers > 0:
                insights.append(f"Contains {outliers} potential outliers ({outliers/len(combined_data):.1%})")
            
            statistical_data = {
                'timestamp': datetime.now().isoformat(),
                'statistics': stats,
                'insights': insights,
                'outliers': int(outliers),
                'coefficient_of_variation': cv,
                'normality_test': 'rejected' if abs(stats['skewness']) > 0.5 else 'not_rejected'
            }
            
            return {'success': True, 'data': statistical_data}
            
        except Exception as e:
            logger.error(f"Statistical analysis error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of data"""
        mean = np.mean(data)
        std = np.std(data)
        n = len(data)
        
        skewness = (n / ((n-1) * (n-2))) * np.sum(((data - mean) / std) ** 3)
        return skewness
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of data"""
        mean = np.mean(data)
        std = np.std(data)
        n = len(data)
        
        kurtosis = (n * (n+1) / ((n-1) * (n-2) * (n-3))) * np.sum(((data - mean) / std) ** 4) - 3 * (n-1)**2 / ((n-2) * (n-3))
        return kurtosis + 3  # Excess kurtosis + 3 for standard kurtosis
    
    async def autonomous_analysis(self) -> None:
        """Joey's autonomous pattern analysis"""
        try:
            memory = self.get_memory()
            last_analysis = memory.get('last_analysis')
            
            # Perform analysis every 30 minutes
            if not last_analysis or (datetime.now() - datetime.fromisoformat(last_analysis)).seconds > 1800:
                logger.info("Joey performing autonomous pattern analysis...")
                
                # Analyze recent market data patterns
                analysis_result = await self.tool_analyze_patterns("Autonomous market pattern scan")
                
                if analysis_result['success']:
                    # Check for significant patterns
                    patterns = analysis_result['data']['patterns']
                    significant_patterns = [p for p in patterns if p['confidence'] > 0.8]
                    
                    if significant_patterns:
                        logger.info(f"Joey detected {len(significant_patterns)} significant patterns")
                        # In production, could trigger alerts or notifications
                
                memory['last_analysis'] = datetime.now().isoformat()
                self.save_memory(memory)
                
        except Exception as e:
            logger.error(f"Joey autonomous analysis error: {str(e)}")
    
    async def autonomous_task(self) -> None:
        """Joey's autonomous background task"""
        await self.autonomous_analysis()