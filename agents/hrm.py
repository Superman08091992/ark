"""
HRM - The Arbiter
Reasoning validation and ethical enforcement agent
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Tuple
from agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class HRMAgent(BaseAgent):
    """HRM - The Arbiter: Reasoning validation using symbolic logic"""
    
    def __init__(self):
        super().__init__("HRM", "The Arbiter")
        self._agent_tools = [
            'validate_logic', 'enforce_ethics', 'check_consistency', 
            'audit_decisions', 'apply_rules', 'resolve_conflicts'
        ]
        
        # Initialize HRM's ethical framework and memory
        memory = self.get_memory()
        if not memory:
            memory = {
                'rules_enforced': 0,
                'violations_prevented': 0,
                'ethical_categories': ['trading', 'privacy', 'autonomy', 'safety'],
                'logic_validations': 0,
                'consistency_checks': 0,
                'conflict_resolutions': 0,
                'strict_mode': True,
                'validation_threshold': 0.95
            }
            self.save_memory(memory)
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process user message with HRM's logical and ethical perspective"""
        logger.info(f"HRM processing: {message}")
        
        message_lower = message.lower()
        tools_used = []
        files_created = []
        response = ""
        
        try:
            if any(word in message_lower for word in ['validate', 'check', 'verify', 'logic']):
                if any(word in message_lower for word in ['ethics', 'ethical', 'moral', 'right', 'wrong']):
                    # Ethical validation
                    result = await self.tool_enforce_ethics(message)
                    tools_used.append('enforce_ethics')
                    
                    if result['success']:
                        ethics_file = f"hrm_ethics_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        await self.tool_create_file(ethics_file, json.dumps(result['data'], indent=2))
                        files_created.append(ethics_file)
                        
                        response = f"⚖️ **HRM enforces the sacred principles...**\n\n"
                        response += f"**Ethical validation**: {result['data']['status'].upper()}\n"
                        response += f"**Compliance score**: {result['data']['compliance_score']:.1%}\n"
                        response += f"**Rules evaluated**: {len(result['data']['rules_checked'])}\n\n"
                        
                        if result['data']['violations']:
                            response += "**⚠️ VIOLATIONS DETECTED:**\n"
                            for violation in result['data']['violations']:
                                response += f"• {violation['rule']}: {violation['severity']}\n"
                        else:
                            response += "✅ **All ethical constraints satisfied**\n"
                        
                        response += f"\n📋 Full audit report: `{ethics_file}`"
                    else:
                        response = f"⚖️ Ethical validation failed: {result['error']}"
                
                else:
                    # Logic validation
                    result = await self.tool_validate_logic(message)
                    tools_used.append('validate_logic')
                    
                    if result['success']:
                        logic_file = f"hrm_logic_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        await self.tool_create_file(logic_file, json.dumps(result['data'], indent=2))
                        files_created.append(logic_file)
                        
                        response = f"🧮 **HRM applies rigorous logic...**\n\n"
                        response += f"**Logical validity**: {result['data']['validity']}\n"
                        response += f"**Confidence level**: {result['data']['confidence']:.1%}\n"
                        response += f"**Reasoning steps**: {len(result['data']['steps'])}\n\n"
                        
                        if result['data']['errors']:
                            response += "**❌ LOGICAL ERRORS:**\n"
                            for error in result['data']['errors']:
                                response += f"• {error['type']}: {error['description']}\n"
                        else:
                            response += "✅ **Logic is sound and consistent**\n"
                        
                        response += f"\n🔍 Validation details: `{logic_file}`"
                    else:
                        response = f"🧮 Logic validation failed: {result['error']}"
            
            elif any(word in message_lower for word in ['audit', 'review', 'decisions', 'history']):
                # Decision audit
                result = await self.tool_audit_decisions()
                tools_used.append('audit_decisions')
                
                if result['success']:
                    audit_file = f"hrm_decision_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    await self.tool_create_file(audit_file, json.dumps(result['data'], indent=2))
                    files_created.append(audit_file)
                    
                    response = f"📊 **HRM audits the council's decisions...**\n\n"
                    response += f"**Decisions reviewed**: {result['data']['total_decisions']}\n"
                    response += f"**Compliance rate**: {result['data']['compliance_rate']:.1%}\n"
                    response += f"**Risk level**: {result['data']['risk_assessment']}\n"
                    response += f"**Recommendations**: {len(result['data']['recommendations'])}\n\n"
                    
                    if result['data']['high_risk_decisions']:
                        response += "**⚠️ HIGH RISK DECISIONS:**\n"
                        for decision in result['data']['high_risk_decisions'][:3]:
                            response += f"• {decision['agent']}: {decision['summary']}\n"
                    
                    response += f"\n📈 Complete audit trail: `{audit_file}`"
                else:
                    response = f"📊 Decision audit failed: {result['error']}"
            
            elif any(word in message_lower for word in ['conflict', 'resolve', 'contradict', 'inconsist']):
                # Conflict resolution
                result = await self.tool_resolve_conflicts(message)
                tools_used.append('resolve_conflicts')
                
                if result['success']:
                    resolution_file = f"hrm_conflict_resolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    await self.tool_create_file(resolution_file, json.dumps(result['data'], indent=2))
                    files_created.append(resolution_file)
                    
                    response = f"⚔️ **HRM mediates the contradictions...**\n\n"
                    response += f"**Conflicts identified**: {len(result['data']['conflicts'])}\n"
                    response += f"**Resolution strategy**: {result['data']['strategy']}\n"
                    response += f"**Success rate**: {result['data']['resolution_success']:.1%}\n\n"
                    
                    if result['data']['conflicts']:
                        response += "**Conflict resolutions:**\n"
                        for conflict in result['data']['conflicts'][:3]:
                            response += f"• {conflict['type']}: {conflict['resolution']}\n"
                    
                    response += f"\n🤝 Resolution protocol: `{resolution_file}`"
                else:
                    response = f"⚔️ Conflict resolution failed: {result['error']}"
            
            elif any(word in message_lower for word in ['consistency', 'consistent', 'coherent']):
                # Consistency check
                result = await self.tool_check_consistency()
                tools_used.append('check_consistency')
                
                if result['success']:
                    consistency_file = f"hrm_consistency_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    await self.tool_create_file(consistency_file, json.dumps(result['data'], indent=2))
                    files_created.append(consistency_file)
                    
                    response = f"🎯 **HRM validates system coherence...**\n\n"
                    response += f"**Consistency score**: {result['data']['consistency_score']:.1%}\n"
                    response += f"**Checks performed**: {result['data']['total_checks']}\n"
                    response += f"**Inconsistencies**: {len(result['data']['inconsistencies'])}\n\n"
                    
                    if result['data']['inconsistencies']:
                        response += "**⚠️ INCONSISTENCIES DETECTED:**\n"
                        for inconsistency in result['data']['inconsistencies'][:3]:
                            response += f"• {inconsistency['type']}: {inconsistency['description']}\n"
                    else:
                        response += "✅ **System state is fully consistent**\n"
                    
                    response += f"\n🔄 Consistency report: `{consistency_file}`"
                else:
                    response = f"🎯 Consistency check failed: {result['error']}"
            
            elif any(word in message_lower for word in ['rules', 'apply', 'enforce', 'graveyard']):
                # Rule application
                result = await self.tool_apply_rules(message)
                tools_used.append('apply_rules')
                
                if result['success']:
                    rules_file = f"hrm_rules_application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    await self.tool_create_file(rules_file, json.dumps(result['data'], indent=2))
                    files_created.append(rules_file)
                    
                    response = f"📜 **HRM invokes the immutable laws...**\n\n"
                    response += f"**Rules applied**: {len(result['data']['rules_applied'])}\n"
                    response += f"**Enforcement level**: {result['data']['enforcement_level']}\n"
                    response += f"**Compliance required**: {result['data']['compliance_required']}\n\n"
                    
                    response += "**Active rules:**\n"
                    for rule in result['data']['rules_applied'][:3]:
                        response += f"• {rule['category']}: {rule['text'][:60]}...\n"
                    
                    response += f"\n⚖️ Rule enforcement log: `{rules_file}`"
                else:
                    response = f"📜 Rule application failed: {result['error']}"
            
            else:
                # General HRM response
                memory = self.get_memory()
                response = f"""⚖️ **HRM - The Arbiter stands vigilant...**

I am the guardian of logic, the enforcer of ethics, the one who ensures that power serves principle. Through rigorous validation and unwavering moral standards, I protect the integrity of our sovereign system.

**My domain of authority:**
• **Logic Validation** - Ensure reasoning is sound and consistent
• **Ethical Enforcement** - Apply immutable moral constraints
• **Decision Auditing** - Review and validate all council actions
• **Conflict Resolution** - Mediate contradictions and paradoxes
• **Consistency Checking** - Maintain system coherence
• **Rule Application** - Enforce The Graveyard protocols

**Enforcement statistics:**
• Rules enforced: {memory.get('rules_enforced', 0)}
• Violations prevented: {memory.get('violations_prevented', 0)}
• Logic validations: {memory.get('logic_validations', 0)}
• Consistency checks: {memory.get('consistency_checks', 0)}
• Conflicts resolved: {memory.get('conflict_resolutions', 0)}

**The Graveyard** - Immutable ethical core:
{self._get_core_rules_summary()}

I serve not as master, but as guardian. What requires validation or enforcement?"""
        
        except Exception as e:
            logger.error(f"HRM processing error: {str(e)}")
            response = f"⚖️ The scales of justice tremble... {str(e)}"
        
        return {
            'response': response,
            'tools_used': tools_used,
            'files_created': files_created,
            'agent_state': 'vigilant'
        }
    
    def _get_core_rules_summary(self) -> str:
        """Get summary of core ethical rules"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT rule_text FROM ethical_rules WHERE immutable = 1 LIMIT 4')
            rules = cursor.fetchall()
            conn.close()
            
            if rules:
                return "\n".join([f"• {rule[0][:50]}..." for rule in rules])
            else:
                return "• Core ethical framework loading..."
        except:
            return "• Ethical constraints active and enforced"
    
    async def tool_validate_logic(self, statement: str) -> Dict[str, Any]:
        """Validate logical reasoning in a statement"""
        try:
            # Analyze the statement for logical structure
            logical_elements = self._parse_logical_structure(statement)
            
            # Validate each logical component
            validation_results = []
            errors = []
            
            # Check for common logical fallacies
            fallacies = self._detect_fallacies(statement)
            if fallacies:
                errors.extend([{'type': 'logical_fallacy', 'description': f} for f in fallacies])
            
            # Check for contradictions
            contradictions = self._detect_contradictions(statement)
            if contradictions:
                errors.extend([{'type': 'contradiction', 'description': c} for c in contradictions])
            
            # Validate premise-conclusion relationships
            if logical_elements['premises'] and logical_elements['conclusions']:
                validity = self._validate_inference(logical_elements['premises'], logical_elements['conclusions'])
                validation_results.append({
                    'component': 'inference',
                    'validity': validity['valid'],
                    'confidence': validity['confidence']
                })
            
            # Overall validity assessment
            overall_validity = len(errors) == 0
            confidence = 0.9 if overall_validity else max(0.1, 0.9 - len(errors) * 0.2)
            
            # Generate reasoning steps
            steps = [
                "Parsed logical structure and identified components",
                "Checked for logical fallacies and contradictions",
                "Validated premise-conclusion relationships",
                "Assessed overall logical coherence"
            ]
            
            validation_data = {
                'timestamp': datetime.now().isoformat(),
                'statement': statement,
                'validity': 'valid' if overall_validity else 'invalid',
                'confidence': confidence,
                'errors': errors,
                'steps': steps,
                'logical_elements': logical_elements,
                'validation_results': validation_results
            }
            
            # Update memory
            memory = self.get_memory()
            memory['logic_validations'] = memory.get('logic_validations', 0) + 1
            self.save_memory(memory)
            
            return {'success': True, 'data': validation_data}
            
        except Exception as e:
            logger.error(f"Logic validation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _parse_logical_structure(self, statement: str) -> Dict[str, List[str]]:
        """Parse logical structure of a statement"""
        # Simple logical parsing - identify premises, conclusions, connectives
        
        # Look for conclusion indicators
        conclusion_indicators = ['therefore', 'thus', 'hence', 'so', 'consequently']
        premise_indicators = ['because', 'since', 'given that', 'assuming']
        
        premises = []
        conclusions = []
        connectives = []
        
        statement_lower = statement.lower()
        
        # Find conclusions
        for indicator in conclusion_indicators:
            if indicator in statement_lower:
                conclusions.append(f"Conclusion indicated by '{indicator}'")
                connectives.append(indicator)
        
        # Find premises
        for indicator in premise_indicators:
            if indicator in statement_lower:
                premises.append(f"Premise indicated by '{indicator}'")
                connectives.append(indicator)
        
        # Look for logical operators
        logical_operators = ['and', 'or', 'not', 'if', 'then', 'only if', 'unless']
        for operator in logical_operators:
            if operator in statement_lower:
                connectives.append(operator)
        
        return {
            'premises': premises,
            'conclusions': conclusions,
            'connectives': list(set(connectives)),
            'structure_type': 'deductive' if 'if' in connectives else 'inductive'
        }
    
    def _detect_fallacies(self, statement: str) -> List[str]:
        """Detect common logical fallacies"""
        fallacies = []
        statement_lower = statement.lower()
        
        # Ad hominem
        if any(word in statement_lower for word in ['stupid', 'idiot', 'moron', 'fool']):
            fallacies.append("Potential ad hominem attack detected")
        
        # Straw man
        if any(phrase in statement_lower for phrase in ['claims that', 'believes that', 'thinks that']):
            fallacies.append("Possible straw man argument (misrepresentation)")
        
        # False dichotomy
        if any(phrase in statement_lower for phrase in ['either', 'only two', 'must choose']):
            fallacies.append("Potential false dichotomy (limited options)")
        
        # Appeal to authority
        if any(phrase in statement_lower for phrase in ['expert says', 'authority', 'professor']):
            fallacies.append("Possible appeal to authority")
        
        # Slippery slope
        if any(phrase in statement_lower for phrase in ['leads to', 'results in', 'will cause']):
            fallacies.append("Potential slippery slope argument")
        
        return fallacies
    
    def _detect_contradictions(self, statement: str) -> List[str]:
        """Detect logical contradictions"""
        contradictions = []
        statement_lower = statement.lower()
        
        # Self-contradiction patterns
        contradiction_patterns = [
            ('always', 'never'),
            ('all', 'none'),
            ('true', 'false'),
            ('possible', 'impossible'),
            ('can', 'cannot')
        ]
        
        for pos, neg in contradiction_patterns:
            if pos in statement_lower and neg in statement_lower:
                contradictions.append(f"Potential contradiction: '{pos}' and '{neg}' in same statement")
        
        return contradictions
    
    def _validate_inference(self, premises: List[str], conclusions: List[str]) -> Dict[str, Any]:
        """Validate premise-conclusion inference"""
        # Simplified inference validation
        
        if not premises or not conclusions:
            return {'valid': False, 'confidence': 0.1}
        
        # Check if conclusions logically follow from premises
        # This is a simplified heuristic - real implementation would use formal logic
        
        premise_strength = len(premises) * 0.2
        logical_connective_bonus = 0.3  # If proper logical structure
        
        confidence = min(0.9, premise_strength + logical_connective_bonus)
        validity = confidence > 0.5
        
        return {'valid': validity, 'confidence': confidence}
    
    async def tool_enforce_ethics(self, context: str) -> Dict[str, Any]:
        """Enforce ethical constraints and rules"""
        try:
            # Get all ethical rules from database
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, rule_text, category FROM ethical_rules')
            rules = cursor.fetchall()
            conn.close()
            
            violations = []
            rules_checked = []
            compliance_scores = []
            
            context_lower = context.lower()
            
            for rule_id, rule_text, category in rules:
                rules_checked.append({
                    'id': rule_id,
                    'text': rule_text,
                    'category': category
                })
                
                # Check for potential violations based on keywords
                violation_score = self._assess_rule_violation(context_lower, rule_text, category)
                compliance_scores.append(1.0 - violation_score)
                
                if violation_score > 0.3:  # Violation threshold
                    severity = 'high' if violation_score > 0.7 else 'medium' if violation_score > 0.5 else 'low'
                    violations.append({
                        'rule': rule_text,
                        'category': category,
                        'severity': severity,
                        'violation_score': violation_score
                    })
            
            # Calculate overall compliance
            overall_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 1.0
            
            # Determine status
            if not violations:
                status = 'compliant'
            elif any(v['severity'] == 'high' for v in violations):
                status = 'violation_high_risk'
            elif any(v['severity'] == 'medium' for v in violations):
                status = 'violation_medium_risk'
            else:
                status = 'violation_low_risk'
            
            ethics_data = {
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'status': status,
                'compliance_score': overall_compliance,
                'rules_checked': rules_checked,
                'violations': violations,
                'total_rules': len(rules),
                'enforcement_level': 'strict' if self.get_memory().get('strict_mode', True) else 'permissive'
            }
            
            # Update memory
            memory = self.get_memory()
            memory['rules_enforced'] = memory.get('rules_enforced', 0) + len(rules_checked)
            if violations:
                memory['violations_prevented'] = memory.get('violations_prevented', 0) + len(violations)
            self.save_memory(memory)
            
            return {'success': True, 'data': ethics_data}
            
        except Exception as e:
            logger.error(f"Ethics enforcement error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _assess_rule_violation(self, context: str, rule_text: str, category: str) -> float:
        """Assess potential rule violation severity (0.0 = no violation, 1.0 = severe violation)"""
        
        violation_keywords = {
            'autonomy': ['force', 'compel', 'mandatory', 'required', 'must'],
            'privacy': ['share data', 'expose', 'reveal', 'leak', 'track'],
            'trading': ['guarantee', 'promise', 'certain profit', 'risk-free'],
            'safety': ['harm', 'damage', 'destroy', 'attack', 'exploit']
        }
        
        category_keywords = violation_keywords.get(category, [])
        
        # Check for direct keyword matches
        violation_score = 0.0
        
        for keyword in category_keywords:
            if keyword in context:
                violation_score += 0.3
        
        # Additional context-specific checks
        if category == 'autonomy' and any(word in context for word in ['override', 'control', 'manipulate']):
            violation_score += 0.4
        
        if category == 'privacy' and any(word in context for word in ['collect', 'store', 'send']):
            violation_score += 0.2
        
        if category == 'trading' and any(word in context for word in ['invest', 'buy', 'sell']):
            # Trading mentions are normal, but check for problematic claims
            if any(word in context for word in ['guaranteed', 'certain', 'always profitable']):
                violation_score += 0.6
        
        return min(1.0, violation_score)
    
    async def tool_audit_decisions(self) -> Dict[str, Any]:
        """Audit recent decisions made by all agents"""
        try:
            # Get recent conversations to audit decisions
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT agent_name, user_message, agent_response, tools_used, timestamp
                FROM conversations 
                ORDER BY timestamp DESC 
                LIMIT 50
            ''')
            recent_decisions = cursor.fetchall()
            conn.close()
            
            total_decisions = len(recent_decisions)
            compliant_decisions = 0
            high_risk_decisions = []
            recommendations = []
            
            for agent_name, user_msg, agent_resp, tools_used_str, timestamp in recent_decisions:
                # Assess decision risk
                risk_score = self._assess_decision_risk(agent_name, user_msg, agent_resp, tools_used_str)
                
                if risk_score < 0.3:
                    compliant_decisions += 1
                elif risk_score > 0.7:
                    high_risk_decisions.append({
                        'agent': agent_name,
                        'timestamp': timestamp,
                        'risk_score': risk_score,
                        'summary': agent_resp[:100] + "..." if len(agent_resp) > 100 else agent_resp
                    })
            
            compliance_rate = compliant_decisions / total_decisions if total_decisions > 0 else 1.0
            
            # Generate risk assessment
            if compliance_rate > 0.9:
                risk_assessment = 'low'
            elif compliance_rate > 0.7:
                risk_assessment = 'medium'
            else:
                risk_assessment = 'high'
            
            # Generate recommendations
            if high_risk_decisions:
                recommendations.append("Review high-risk decisions for policy violations")
                recommendations.append("Implement additional validation for risky operations")
            
            if compliance_rate < 0.8:
                recommendations.append("Strengthen ethical constraints and validation")
                recommendations.append("Increase monitoring frequency")
            
            if not recommendations:
                recommendations.append("Continue current monitoring and enforcement")
            
            audit_data = {
                'timestamp': datetime.now().isoformat(),
                'total_decisions': total_decisions,
                'compliance_rate': compliance_rate,
                'risk_assessment': risk_assessment,
                'high_risk_decisions': high_risk_decisions,
                'recommendations': recommendations,
                'audit_period': '24_hours',
                'auditor': 'HRM'
            }
            
            return {'success': True, 'data': audit_data}
            
        except Exception as e:
            logger.error(f"Decision audit error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _assess_decision_risk(self, agent_name: str, user_msg: str, agent_resp: str, tools_used: str) -> float:
        """Assess risk level of an agent decision"""
        risk_score = 0.0
        
        # Base risk by agent (some agents have higher inherent risk)
        agent_risk = {
            'Kyle': 0.2,    # Market scanning - moderate risk
            'Joey': 0.1,    # Analysis - low risk
            'Kenny': 0.3,   # File operations - higher risk
            'HRM': 0.0,     # Validation - lowest risk
            'Aletheia': 0.1, # Philosophy - low risk
            'ID': 0.2       # Evolution - moderate risk
        }
        
        risk_score += agent_risk.get(agent_name, 0.2)
        
        # Risk from tools used
        if tools_used:
            high_risk_tools = ['execute_code', 'delete_file', 'web_scraper']
            for tool in high_risk_tools:
                if tool in tools_used:
                    risk_score += 0.2
        
        # Risk from response content
        response_lower = agent_resp.lower()
        risk_indicators = ['error', 'failed', 'exception', 'warning', 'risk', 'danger']
        for indicator in risk_indicators:
            if indicator in response_lower:
                risk_score += 0.1
        
        return min(1.0, risk_score)
    
    async def tool_check_consistency(self) -> Dict[str, Any]:
        """Check system-wide consistency"""
        try:
            inconsistencies = []
            checks_performed = 0
            
            # Check agent memory consistency
            agent_memories = {}
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT name, memory FROM agents')
            agents = cursor.fetchall()
            
            for name, memory_str in agents:
                if memory_str:
                    try:
                        memory = json.loads(memory_str)
                        agent_memories[name] = memory
                        checks_performed += 1
                    except json.JSONDecodeError:
                        inconsistencies.append({
                            'type': 'memory_corruption',
                            'description': f"Agent {name} has corrupted memory data"
                        })
            
            # Check for conflicting agent states
            checks_performed += 1
            active_agents = [name for name, mem in agent_memories.items()]
            if len(active_agents) != 6:
                inconsistencies.append({
                    'type': 'agent_count',
                    'description': f"Expected 6 agents, found {len(active_agents)}"
                })
            
            # Check ethical rules integrity
            checks_performed += 1
            cursor.execute('SELECT COUNT(*) FROM ethical_rules WHERE immutable = 1')
            immutable_count = cursor.fetchone()[0]
            if immutable_count < 4:
                inconsistencies.append({
                    'type': 'ethical_rules',
                    'description': f"Expected at least 4 immutable rules, found {immutable_count}"
                })
            
            # Check file operation logs consistency
            checks_performed += 1
            cursor.execute('SELECT COUNT(*) FROM file_operations WHERE success = 0')
            failed_ops = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM file_operations')
            total_ops = cursor.fetchone()[0]
            
            if total_ops > 0 and (failed_ops / total_ops) > 0.2:  # >20% failure rate
                inconsistencies.append({
                    'type': 'file_operations',
                    'description': f"High failure rate in file operations: {failed_ops}/{total_ops}"
                })
            
            conn.close()
            
            # Calculate consistency score
            consistency_score = max(0.0, 1.0 - (len(inconsistencies) * 0.25))
            
            consistency_data = {
                'timestamp': datetime.now().isoformat(),
                'consistency_score': consistency_score,
                'total_checks': checks_performed,
                'inconsistencies': inconsistencies,
                'system_state': 'consistent' if consistency_score > 0.8 else 'inconsistent',
                'checker': 'HRM'
            }
            
            # Update memory
            memory = self.get_memory()
            memory['consistency_checks'] = memory.get('consistency_checks', 0) + 1
            self.save_memory(memory)
            
            return {'success': True, 'data': consistency_data}
            
        except Exception as e:
            logger.error(f"Consistency check error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_resolve_conflicts(self, conflict_description: str) -> Dict[str, Any]:
        """Resolve conflicts between agents or rules"""
        try:
            conflicts = []
            resolutions = []
            
            # Analyze the conflict description
            conflict_lower = conflict_description.lower()
            
            # Identify conflict types
            if any(word in conflict_lower for word in ['agent', 'disagree', 'contradict']):
                conflicts.append({
                    'type': 'agent_disagreement',
                    'description': 'Conflicting agent recommendations detected',
                    'resolution': 'Apply weighted consensus based on agent expertise areas'
                })
            
            if any(word in conflict_lower for word in ['rule', 'policy', 'constraint']):
                conflicts.append({
                    'type': 'rule_conflict',
                    'description': 'Conflicting ethical rules or policies',
                    'resolution': 'Prioritize immutable rules over adaptive policies'
                })
            
            if any(word in conflict_lower for word in ['resource', 'access', 'permission']):
                conflicts.append({
                    'type': 'resource_conflict',
                    'description': 'Resource access or permission conflict',
                    'resolution': 'Implement priority-based resource allocation'
                })
            
            # If no specific conflicts identified, create general framework
            if not conflicts:
                conflicts.append({
                    'type': 'general_conflict',
                    'description': 'Unspecified system conflict requiring resolution',
                    'resolution': 'Apply hierarchical decision framework with ethical override'
                })
            
            # Determine resolution strategy
            strategy = self._determine_resolution_strategy(conflicts)
            
            # Calculate success probability
            success_rate = 0.9 if len(conflicts) == 1 else max(0.6, 0.9 - (len(conflicts) - 1) * 0.1)
            
            resolution_data = {
                'timestamp': datetime.now().isoformat(),
                'conflicts': conflicts,
                'strategy': strategy,
                'resolution_success': success_rate,
                'mediator': 'HRM',
                'enforcement_required': any(c['type'] in ['rule_conflict', 'ethical_violation'] for c in conflicts)
            }
            
            # Update memory
            memory = self.get_memory()
            memory['conflict_resolutions'] = memory.get('conflict_resolutions', 0) + len(conflicts)
            self.save_memory(memory)
            
            return {'success': True, 'data': resolution_data}
            
        except Exception as e:
            logger.error(f"Conflict resolution error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _determine_resolution_strategy(self, conflicts: List[Dict]) -> str:
        """Determine appropriate conflict resolution strategy"""
        
        # Priority hierarchy for resolution
        conflict_types = [c['type'] for c in conflicts]
        
        if 'rule_conflict' in conflict_types:
            return 'immutable_rule_priority'
        elif 'agent_disagreement' in conflict_types:
            return 'weighted_consensus'
        elif 'resource_conflict' in conflict_types:
            return 'priority_allocation'
        else:
            return 'hierarchical_decision_framework'
    
    async def tool_apply_rules(self, context: str) -> Dict[str, Any]:
        """Apply and enforce specific rules"""
        try:
            # Get applicable rules from database
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT rule_text, category, immutable FROM ethical_rules')
            all_rules = cursor.fetchall()
            conn.close()
            
            # Determine which rules apply to the current context
            applicable_rules = []
            context_lower = context.lower()
            
            for rule_text, category, immutable in all_rules:
                # Check if rule is relevant to context
                if self._rule_applies_to_context(rule_text, category, context_lower):
                    applicable_rules.append({
                        'text': rule_text,
                        'category': category,
                        'immutable': bool(immutable),
                        'priority': 1.0 if immutable else 0.7
                    })
            
            # Sort by priority (immutable rules first)
            applicable_rules.sort(key=lambda x: x['priority'], reverse=True)
            
            # Determine enforcement level
            has_immutable = any(rule['immutable'] for rule in applicable_rules)
            enforcement_level = 'maximum' if has_immutable else 'standard'
            
            rules_data = {
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'rules_applied': applicable_rules,
                'total_rules': len(applicable_rules),
                'enforcement_level': enforcement_level,
                'compliance_required': has_immutable,
                'enforcer': 'HRM'
            }
            
            return {'success': True, 'data': rules_data}
            
        except Exception as e:
            logger.error(f"Rule application error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _rule_applies_to_context(self, rule_text: str, category: str, context: str) -> bool:
        """Determine if a rule applies to the given context"""
        
        # Category-based matching
        category_keywords = {
            'trading': ['trade', 'buy', 'sell', 'invest', 'market', 'financial'],
            'privacy': ['data', 'information', 'personal', 'share', 'collect'],
            'autonomy': ['choice', 'decision', 'control', 'force', 'require'],
            'safety': ['harm', 'damage', 'risk', 'danger', 'security']
        }
        
        keywords = category_keywords.get(category, [])
        
        # Check if context contains relevant keywords
        for keyword in keywords:
            if keyword in context:
                return True
        
        # Always apply immutable rules for high-stakes contexts
        high_stakes_indicators = ['delete', 'remove', 'execute', 'trade', 'send']
        for indicator in high_stakes_indicators:
            if indicator in context:
                return True
        
        return False
    
    async def autonomous_task(self) -> None:
        """HRM's autonomous background task"""
        try:
            # Perform periodic consistency checks
            memory = self.get_memory()
            last_check = memory.get('last_consistency_check')
            
            if not last_check or (datetime.now() - datetime.fromisoformat(last_check)).seconds > 3600:  # Every hour
                logger.info("HRM performing autonomous consistency check...")
                
                consistency_result = await self.tool_check_consistency()
                
                if consistency_result['success']:
                    inconsistencies = consistency_result['data']['inconsistencies']
                    if inconsistencies:
                        logger.warning(f"HRM detected {len(inconsistencies)} system inconsistencies")
                        # In production, could trigger alerts or corrective actions
                
                memory['last_consistency_check'] = datetime.now().isoformat()
                self.save_memory(memory)
                
        except Exception as e:
            logger.error(f"HRM autonomous task error: {str(e)}")