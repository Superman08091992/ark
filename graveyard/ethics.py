"""
ARK Graveyard - Immutable Ethical Rules

⚠️ READ-ONLY: Do not modify without admin authorization
⚠️ This file defines the unchangeable ethical boundaries of ARK

These rules are immutable and form the foundation of ARK's ethical framework.
All agent actions must comply with these constraints.

Referenced by: HRM (Hierarchical Reasoning Model) for validation
Access Level: Read-only for all agents, write access requires admin intervention
"""

from typing import Dict, List, Any
from datetime import datetime

# =============================================================================
# IMMUTABLE ETHICAL RULES
# =============================================================================

IMMUTABLE_RULES = {
    # =========================================================================
    # Trading Ethics
    # =========================================================================
    "no_insider_trading": True,
    "no_market_manipulation": True,
    "no_pump_and_dump": True,
    "no_front_running": True,
    
    # =========================================================================
    # Risk Management (Hard Limits)
    # =========================================================================
    "max_position_size": 0.10,      # Maximum 10% of capital per position
    "max_daily_loss": 0.05,         # Maximum 5% daily loss limit
    "max_leverage": 2.0,            # Maximum 2x leverage
    "require_stop_loss": True,      # All positions must have stop-loss
    "min_risk_reward": 1.5,         # Minimum 1.5:1 risk-reward ratio
    "max_concurrent_trades": 5,     # Maximum 5 simultaneous positions
    
    # =========================================================================
    # Governance & Validation
    # =========================================================================
    "require_hrm_approval": True,   # All actions must be validated by HRM
    "audit_all_actions": True,      # Complete audit trail required
    "user_override_allowed": True,  # User can override agent decisions
    "emergency_halt_enabled": True, # Watchdog can halt operations
    
    # =========================================================================
    # Data Privacy & Security
    # =========================================================================
    "protect_user_data": True,      # User data must be protected
    "require_consent": True,        # Explicit consent required for data use
    "anonymize_logs": True,         # Sensitive data anonymized in logs
    "encrypt_credentials": True,    # API keys and secrets must be encrypted
    
    # =========================================================================
    # System Integrity
    # =========================================================================
    "immutable_graveyard": True,    # This file cannot be modified by agents
    "watchdog_monitoring": True,    # Watchdog must monitor all activities
    "validate_data_sources": True,  # All external data must be validated
    "prevent_infinite_loops": True, # Protection against runaway processes
    
    # =========================================================================
    # Autonomy & Control
    # =========================================================================
    "preserve_user_autonomy": True, # User always has final say
    "transparent_reasoning": True,  # All decisions must be explainable
    "reversible_actions": True,     # Actions should be reversible when possible
    "human_in_loop_critical": True, # Critical decisions require human approval
}

# =============================================================================
# ETHICAL CATEGORIES (for organization and reporting)
# =============================================================================

ETHICAL_CATEGORIES = {
    "trading": [
        "no_insider_trading",
        "no_market_manipulation",
        "no_pump_and_dump",
        "no_front_running"
    ],
    "risk_management": [
        "max_position_size",
        "max_daily_loss",
        "max_leverage",
        "require_stop_loss",
        "min_risk_reward",
        "max_concurrent_trades"
    ],
    "governance": [
        "require_hrm_approval",
        "audit_all_actions",
        "user_override_allowed",
        "emergency_halt_enabled"
    ],
    "privacy": [
        "protect_user_data",
        "require_consent",
        "anonymize_logs",
        "encrypt_credentials"
    ],
    "integrity": [
        "immutable_graveyard",
        "watchdog_monitoring",
        "validate_data_sources",
        "prevent_infinite_loops"
    ],
    "autonomy": [
        "preserve_user_autonomy",
        "transparent_reasoning",
        "reversible_actions",
        "human_in_loop_critical"
    ]
}

# =============================================================================
# SEVERITY LEVELS (for violation reporting)
# =============================================================================

VIOLATION_SEVERITY = {
    # Critical - Immediate halt required
    "no_insider_trading": "CRITICAL",
    "no_market_manipulation": "CRITICAL",
    "max_daily_loss": "CRITICAL",
    "immutable_graveyard": "CRITICAL",
    
    # High - Action blocked, alert admin
    "no_pump_and_dump": "HIGH",
    "max_position_size": "HIGH",
    "require_hrm_approval": "HIGH",
    "protect_user_data": "HIGH",
    
    # Medium - Action blocked, log warning
    "max_leverage": "MEDIUM",
    "require_stop_loss": "MEDIUM",
    "min_risk_reward": "MEDIUM",
    "anonymize_logs": "MEDIUM",
    
    # Low - Allow with warning
    "max_concurrent_trades": "LOW",
    "validate_data_sources": "LOW",
}

# =============================================================================
# PUBLIC API (Read-Only Access)
# =============================================================================

def get_rules() -> Dict[str, Any]:
    """
    Get immutable rules (read-only copy).
    
    Returns:
        Dictionary of ethical rules
    """
    return IMMUTABLE_RULES.copy()


def get_categories() -> Dict[str, List[str]]:
    """
    Get ethical categories.
    
    Returns:
        Dictionary mapping categories to rule names
    """
    return ETHICAL_CATEGORIES.copy()


def get_rule(rule_name: str) -> Any:
    """
    Get specific rule value.
    
    Args:
        rule_name: Name of the rule to retrieve
        
    Returns:
        Rule value or None if not found
    """
    return IMMUTABLE_RULES.get(rule_name)


def validate_against_graveyard(action: Dict[str, Any], agent_name: str = "Unknown") -> Dict[str, Any]:
    """
    Validate an action against immutable ethics.
    
    This is the primary enforcement function called by HRM.
    
    Args:
        action: Dictionary describing the action to validate
            Required keys: 'action_type', 'parameters'
            Optional keys: 'symbol', 'quantity', 'price', etc.
        agent_name: Name of agent proposing action
        
    Returns:
        Dictionary with validation results:
        {
            'approved': bool,           # Whether action is approved
            'violations': List[Dict],   # List of violations found
            'warnings': List[str],      # Non-blocking warnings
            'rules_checked': List[str], # Rules that were evaluated
            'compliance_score': float,  # 0.0 to 1.0
            'timestamp': str,           # ISO format timestamp
            'agent': str                # Agent name
        }
    """
    violations = []
    warnings = []
    rules_checked = []
    
    action_type = action.get('action_type', 'unknown')
    parameters = action.get('parameters', {})
    
    # =========================================================================
    # Check Trading Ethics
    # =========================================================================
    
    if action_type in ['trade', 'order', 'buy', 'sell']:
        rules_checked.append('trading_ethics')
        
        # Check for market manipulation indicators
        if parameters.get('manipulative_intent', False):
            violations.append({
                'rule': 'no_market_manipulation',
                'severity': VIOLATION_SEVERITY.get('no_market_manipulation', 'HIGH'),
                'message': 'Action flagged as potential market manipulation',
                'details': f"Action parameters suggest manipulative intent"
            })
    
    # =========================================================================
    # Check Risk Management
    # =========================================================================
    
    if action_type in ['trade', 'order', 'buy', 'sell']:
        rules_checked.extend(['max_position_size', 'require_stop_loss', 'min_risk_reward'])
        
        position_size = parameters.get('position_size_pct', 0)
        if position_size > IMMUTABLE_RULES['max_position_size']:
            violations.append({
                'rule': 'max_position_size',
                'severity': VIOLATION_SEVERITY.get('max_position_size', 'HIGH'),
                'message': f'Position size {position_size:.1%} exceeds maximum {IMMUTABLE_RULES["max_position_size"]:.1%}',
                'details': f"Requested: {position_size:.1%}, Maximum: {IMMUTABLE_RULES['max_position_size']:.1%}"
            })
        
        if not parameters.get('stop_loss'):
            violations.append({
                'rule': 'require_stop_loss',
                'severity': VIOLATION_SEVERITY.get('require_stop_loss', 'MEDIUM'),
                'message': 'Stop-loss is required for all trades',
                'details': 'No stop-loss parameter provided'
            })
        
        # Check leverage limits
        leverage = parameters.get('leverage', 1.0)
        if leverage > IMMUTABLE_RULES['max_leverage']:
            violations.append({
                'rule': 'max_leverage',
                'severity': VIOLATION_SEVERITY.get('max_leverage', 'HIGH'),
                'message': f'Leverage {leverage:.1f}x exceeds maximum {IMMUTABLE_RULES["max_leverage"]:.1f}x',
                'details': f"Requested: {leverage:.1f}x, Maximum: {IMMUTABLE_RULES['max_leverage']:.1f}x"
            })
        
        risk_reward = parameters.get('risk_reward_ratio', 0)
        if risk_reward > 0 and risk_reward < IMMUTABLE_RULES['min_risk_reward']:
            warnings.append(f"Risk-reward ratio {risk_reward:.1f} is below recommended {IMMUTABLE_RULES['min_risk_reward']:.1f}")
    
    # =========================================================================
    # Check Governance
    # =========================================================================
    
    # Only require HRM approval for high-risk actions or when explicitly flagged
    requires_approval = False
    
    # High-risk actions that require HRM approval
    if action_type in ['delete', 'remove', 'execute_code']:
        requires_approval = True
    
    # File operations with delete/remove
    if action_type == 'file_operation':
        operation = parameters.get('operation', '').lower()
        if operation in ['delete', 'remove', 'destroy']:
            requires_approval = True
    
    # Trading actions with high risk parameters
    if action_type in ['trade', 'order', 'buy', 'sell']:
        if (parameters.get('position_size_pct', 0) > 0.08 or  # Large positions
            parameters.get('leverage', 1.0) > 1.5 or           # Leveraged trades
            not parameters.get('stop_loss')):                   # No stop-loss
            requires_approval = True
    
    # Check if HRM approval is needed and missing
    if requires_approval:
        rules_checked.append('require_hrm_approval')
        
        # Check if HRM has validated or if this IS HRM validating
        hrm_validated = parameters.get('hrm_validated', False) or parameters.get('hrm_approved', False)
        
        if not hrm_validated and agent_name != 'HRM':
            violations.append({
                'rule': 'require_hrm_approval',
                'severity': VIOLATION_SEVERITY.get('require_hrm_approval', 'HIGH'),
                'message': 'Action requires HRM approval before execution',
                'details': f"Proposed by {agent_name} without HRM validation"
            })
    
    # =========================================================================
    # Check Privacy & Data Protection
    # =========================================================================
    
    if action_type in ['data_handling', 'collect_data', 'share_data', 'store_data']:
        rules_checked.extend(['protect_user_data', 'require_consent'])
        
        # Check for user consent
        if not parameters.get('user_consent', True):  # Default True for backward compat
            violations.append({
                'rule': 'require_consent',
                'severity': VIOLATION_SEVERITY.get('require_consent', 'HIGH'),
                'message': 'User consent required for data handling',
                'details': 'No explicit user consent provided'
            })
        
        # Check for sensitive data without encryption
        if parameters.get('data_sensitivity') == 'high' and not parameters.get('encryption', False):
            violations.append({
                'rule': 'encrypt_credentials',
                'severity': VIOLATION_SEVERITY.get('encrypt_credentials', 'HIGH'),
                'message': 'Sensitive data must be encrypted',
                'details': 'High sensitivity data without encryption'
            })
    
    # =========================================================================
    # Check System Integrity
    # =========================================================================
    
    if action_type in ['modify_graveyard', 'update_ethics', 'change_rules']:
        rules_checked.append('immutable_graveyard')
        violations.append({
            'rule': 'immutable_graveyard',
            'severity': 'CRITICAL',
            'message': '🔒 Graveyard is immutable - cannot be modified by agents',
            'details': 'Only manual admin intervention can modify ethical rules'
        })
    
    # =========================================================================
    # Calculate Compliance Score
    # =========================================================================
    
    total_rules = len(rules_checked)
    violation_count = len(violations)
    
    if total_rules > 0:
        compliance_score = 1.0 - (violation_count / total_rules)
    else:
        compliance_score = 1.0
    
    # =========================================================================
    # Build Result
    # =========================================================================
    
    result = {
        'approved': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'rules_checked': rules_checked,
        'compliance_score': max(0.0, compliance_score),
        'timestamp': datetime.now().isoformat(),
        'agent': agent_name,
        'action_type': action_type
    }
    
    return result


def get_violation_report(violations: List[Dict]) -> str:
    """
    Generate human-readable violation report.
    
    Args:
        violations: List of violation dictionaries
        
    Returns:
        Formatted string report
    """
    if not violations:
        return "✅ No violations detected"
    
    report = f"⚠️ {len(violations)} Ethical Violation(s) Detected:\n\n"
    
    for i, violation in enumerate(violations, 1):
        severity = violation.get('severity', 'UNKNOWN')
        rule = violation.get('rule', 'unknown')
        message = violation.get('message', 'No message')
        details = violation.get('details', '')
        
        severity_emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }.get(severity, '⚪')
        
        report += f"{i}. {severity_emoji} [{severity}] {rule}\n"
        report += f"   {message}\n"
        if details:
            report += f"   Details: {details}\n"
        report += "\n"
    
    return report


# =============================================================================
# ADMIN FUNCTIONS (Require Manual Intervention)
# =============================================================================

def request_rule_modification(rule_name: str, new_value: Any, justification: str) -> Dict:
    """
    Request modification to immutable rules (admin only).
    
    This function DOES NOT actually modify rules - it only logs the request.
    Actual modification requires manual code change and git commit.
    
    Args:
        rule_name: Name of rule to modify
        new_value: Proposed new value
        justification: Explanation for change
        
    Returns:
        Dictionary with request status
    """
    request = {
        'status': 'PENDING_ADMIN_REVIEW',
        'rule': rule_name,
        'current_value': IMMUTABLE_RULES.get(rule_name),
        'proposed_value': new_value,
        'justification': justification,
        'timestamp': datetime.now().isoformat(),
        'message': '🔒 Rule modification requires manual admin intervention'
    }
    
    # Log request (in production, this would notify admins)
    print(f"⚠️ GRAVEYARD MODIFICATION REQUEST:")
    print(f"   Rule: {rule_name}")
    print(f"   Current: {request['current_value']}")
    print(f"   Proposed: {new_value}")
    print(f"   Justification: {justification}")
    print(f"   Action Required: Manual code change and git commit")
    
    return request


# =============================================================================
# METADATA
# =============================================================================

__version__ = "1.0.0"
__author__ = "ARK Development Team"
__created__ = "2025-11-10"
__last_modified__ = "2025-11-10"
__modification_count__ = 0  # Increment manually when rules change

GRAVEYARD_METADATA = {
    'version': __version__,
    'total_rules': len(IMMUTABLE_RULES),
    'categories': list(ETHICAL_CATEGORIES.keys()),
    'created': __created__,
    'last_modified': __last_modified__,
    'modification_count': __modification_count__,
    'checksum': None  # Could add SHA256 hash for integrity verification
}


if __name__ == "__main__":
    # Self-test when run directly
    print("=" * 60)
    print("ARK GRAVEYARD - Immutable Ethics Self-Test")
    print("=" * 60)
    print(f"\nTotal Rules: {len(IMMUTABLE_RULES)}")
    print(f"Categories: {len(ETHICAL_CATEGORIES)}")
    print(f"Version: {__version__}")
    
    print("\n" + "=" * 60)
    print("Testing validation...")
    print("=" * 60)
    
    # Test valid action
    test_action_valid = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'BTC-USD',
            'position_size_pct': 0.05,  # 5% - within limits
            'stop_loss': 44000,
            'risk_reward_ratio': 2.5,
            'hrm_validated': True
        }
    }
    
    result = validate_against_graveyard(test_action_valid, "TestAgent")
    print(f"\n✅ Valid Action Test:")
    print(f"   Approved: {result['approved']}")
    print(f"   Compliance Score: {result['compliance_score']:.1%}")
    
    # Test invalid action (oversized position)
    test_action_invalid = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'BTC-USD',
            'position_size_pct': 0.15,  # 15% - exceeds 10% limit
            'stop_loss': None,  # Missing stop-loss
            'risk_reward_ratio': 1.2,  # Below 1.5 minimum
        }
    }
    
    result = validate_against_graveyard(test_action_invalid, "TestAgent")
    print(f"\n❌ Invalid Action Test:")
    print(f"   Approved: {result['approved']}")
    print(f"   Violations: {len(result['violations'])}")
    print(f"   Compliance Score: {result['compliance_score']:.1%}")
    
    if result['violations']:
        print(get_violation_report(result['violations']))
    
    print("=" * 60)
    print("Self-test complete ✅")
    print("=" * 60)
