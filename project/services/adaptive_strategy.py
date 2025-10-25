"""
🧠 Adaptive Strategy Selector

Automatically selects the best checking method based on historical success rates.

Features:
- Tracks success/failure of different check methods
- Adaptive strategy selection (epsilon-greedy)
- Persistent learning (survives restarts)
- Per-user strategy optimization
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import random


class AdaptiveStrategySelector:
    """
    Intelligent strategy selection based on success history
    
    Strategies:
    - playwright_advanced: Advanced Playwright with stealth
    - mobile_bypass: Mobile emulation bypass
    - hybrid_proxy: Hybrid API + Proxy
    - bypass_403: 403 bypass methods
    - undetected_chrome: Undetected chromedriver
    """
    
    STRATEGIES = [
        "playwright_advanced",
        "mobile_bypass",
        "hybrid_proxy",
        "bypass_403",
        "undetected_chrome"
    ]
    
    def __init__(self, history_file: str = "data/strategy_history.json"):
        """
        Initialize AdaptiveStrategySelector
        
        Args:
            history_file: Path to history JSON file
        """
        self.history_file = history_file
        self.history = self.load_history()
        
        # Weights for each strategy (0-1 scale)
        self.weights = {s: 1.0 for s in self.STRATEGIES}
        self.update_weights()
        
        print(f"[ADAPTIVE] 🧠 Initialized with {len(self.history)} historical records")
    
    def load_history(self) -> List[Dict]:
        """Load history from file"""
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.history_file) if os.path.dirname(self.history_file) else "data", exist_ok=True)
        
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ADAPTIVE] ⚠️ Error loading history: {e}")
            return []
    
    def save_history(self):
        """Save history to file"""
        try:
            # Keep only last 1000 records to avoid file bloat
            recent_history = self.history[-1000:]
            
            with open(self.history_file, 'w') as f:
                json.dump(recent_history, f, indent=2)
        except Exception as e:
            print(f"[ADAPTIVE] ⚠️ Error saving history: {e}")
    
    def record_attempt(
        self, 
        strategy: str, 
        success: bool, 
        username: str = None,
        error: Optional[str] = None,
        response_time: float = 0,
        proxy_used: bool = False,
        user_id: Optional[int] = None
    ):
        """
        Record result of a check attempt
        
        Args:
            strategy: Strategy used
            success: Whether check was successful
            username: Instagram username checked
            error: Error message if failed
            response_time: Time taken in seconds
            proxy_used: Whether proxy was used
            user_id: User ID (for per-user optimization)
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy,
            "success": success,
            "username": username,
            "error": error,
            "response_time": response_time,
            "proxy_used": proxy_used,
            "user_id": user_id
        }
        
        self.history.append(record)
        
        # Update weights every 10 records
        if len(self.history) % 10 == 0:
            self.update_weights()
            self.save_history()
        
        result_emoji = "✅" if success else "❌"
        print(f"[ADAPTIVE] {result_emoji} Recorded: {strategy} - {success} ({response_time:.2f}s)")
    
    def update_weights(self):
        """
        Update strategy weights based on recent history
        
        Algorithm:
        - Analyze last 100 attempts
        - Calculate success rate for each strategy
        - Calculate average response time
        - Combine into weighted score
        """
        # Need at least 20 records to start learning
        if len(self.history) < 20:
            return
        
        recent_history = self.history[-100:]
        
        # Statistics per strategy
        stats = defaultdict(lambda: {
            "attempts": 0,
            "successes": 0,
            "total_time": 0
        })
        
        for record in recent_history:
            strategy = record["strategy"]
            stats[strategy]["attempts"] += 1
            
            if record["success"]:
                stats[strategy]["successes"] += 1
            
            stats[strategy]["total_time"] += record.get("response_time", 0)
        
        # Calculate weights
        for strategy in self.STRATEGIES:
            if stats[strategy]["attempts"] == 0:
                # No data - keep neutral weight
                continue
            
            # Success rate (0-1)
            success_rate = stats[strategy]["successes"] / stats[strategy]["attempts"]
            
            # Average response time (normalized 0-1, faster = better)
            avg_time = stats[strategy]["total_time"] / stats[strategy]["attempts"]
            time_score = max(0, min(1, 1 - (avg_time / 60)))  # 60s = score 0
            
            # Combined score (70% success rate, 30% speed)
            self.weights[strategy] = (success_rate * 0.7) + (time_score * 0.3)
        
        print(f"[ADAPTIVE] 📊 Updated weights: {self.format_weights()}")
    
    def format_weights(self) -> Dict[str, float]:
        """Format weights for display"""
        return {k: round(v, 3) for k, v in self.weights.items()}
    
    def select_strategy(self, epsilon: float = 0.1) -> str:
        """
        Select best strategy using epsilon-greedy algorithm
        
        Args:
            epsilon: Exploration rate (0-1, default 0.1 = 10% random)
            
        Returns:
            Selected strategy name
        """
        # If not enough data, return random
        if len(self.history) < 20:
            strategy = random.choice(self.STRATEGIES)
            print(f"[ADAPTIVE] 🎲 Random selection (insufficient data): {strategy}")
            return strategy
        
        # Epsilon-greedy: explore vs exploit
        if random.random() < epsilon:
            # Exploration: random selection
            strategy = random.choice(self.STRATEGIES)
            print(f"[ADAPTIVE] 🔍 Exploration: {strategy}")
            return strategy
        else:
            # Exploitation: select best weighted strategy
            # Use softmax for probabilistic selection
            import math
            
            # Softmax with temperature
            temperature = 2.0
            exp_weights = {
                s: math.exp(w * temperature) 
                for s, w in self.weights.items()
            }
            
            total = sum(exp_weights.values())
            probabilities = {
                s: exp_w / total 
                for s, exp_w in exp_weights.items()
            }
            
            # Weighted random choice
            strategies = list(probabilities.keys())
            probs = list(probabilities.values())
            
            strategy = random.choices(strategies, weights=probs)[0]
            
            weight = self.weights.get(strategy, 0)
            print(f"[ADAPTIVE] 🎯 Selected: {strategy} (weight: {weight:.3f})")
            return strategy
    
    def get_best_strategy(self) -> str:
        """Get best strategy without randomness"""
        if not self.weights:
            return "playwright_advanced"
        
        best = max(self.weights.items(), key=lambda x: x[1])
        return best[0]
    
    def get_statistics(self, last_n: int = 100) -> Dict:
        """
        Get statistics for recent attempts
        
        Args:
            last_n: Number of recent attempts to analyze
            
        Returns:
            Statistics dict
        """
        if not self.history:
            return {
                "total_attempts": 0,
                "success_rate": 0,
                "strategies": {}
            }
        
        recent = self.history[-last_n:]
        
        total = len(recent)
        successes = sum(1 for r in recent if r["success"])
        success_rate = (successes / total * 100) if total > 0 else 0
        
        # Per-strategy stats
        strategy_stats = {}
        
        for strategy in self.STRATEGIES:
            strategy_records = [r for r in recent if r["strategy"] == strategy]
            
            if strategy_records:
                s_total = len(strategy_records)
                s_successes = sum(1 for r in strategy_records if r["success"])
                s_success_rate = (s_successes / s_total * 100) if s_total > 0 else 0
                
                avg_time = sum(r.get("response_time", 0) for r in strategy_records) / s_total
                
                strategy_stats[strategy] = {
                    "attempts": s_total,
                    "successes": s_successes,
                    "success_rate": round(s_success_rate, 2),
                    "avg_response_time": round(avg_time, 2),
                    "weight": round(self.weights.get(strategy, 0), 3)
                }
        
        return {
            "total_attempts": total,
            "total_successes": successes,
            "success_rate": round(success_rate, 2),
            "strategies": strategy_stats
        }
    
    def print_statistics(self, last_n: int = 100):
        """Print formatted statistics"""
        stats = self.get_statistics(last_n)
        
        print("\n" + "=" * 70)
        print(f"📊 ADAPTIVE STRATEGY STATISTICS (last {last_n} attempts)")
        print("=" * 70)
        print(f"Total Attempts: {stats['total_attempts']}")
        print(f"Success Rate: {stats['success_rate']}%")
        print("\nPer-Strategy Performance:")
        print("-" * 70)
        print(f"{'Strategy':<25} {'Attempts':<10} {'Success':<10} {'Avg Time':<12} {'Weight':<10}")
        print("-" * 70)
        
        for strategy, s_stats in stats['strategies'].items():
            print(
                f"{strategy:<25} "
                f"{s_stats['attempts']:<10} "
                f"{s_stats['success_rate']:>6.2f}% "
                f"{s_stats['avg_response_time']:>8.2f}s "
                f"{s_stats['weight']:>8.3f}"
            )
        
        print("=" * 70 + "\n")
    
    def reset_weights(self):
        """Reset all weights to neutral (1.0)"""
        self.weights = {s: 1.0 for s in self.STRATEGIES}
        print(f"[ADAPTIVE] 🔄 Reset all weights to 1.0")
    
    def clear_history(self):
        """Clear all history"""
        self.history = []
        self.save_history()
        self.reset_weights()
        print(f"[ADAPTIVE] 🗑️ Cleared all history")


# ========================================================================
# GLOBAL INSTANCE
# ========================================================================

_selector_instance: Optional[AdaptiveStrategySelector] = None


def get_strategy_selector() -> AdaptiveStrategySelector:
    """Get global AdaptiveStrategySelector instance"""
    global _selector_instance
    
    if _selector_instance is None:
        _selector_instance = AdaptiveStrategySelector()
    
    return _selector_instance


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

def select_best_strategy() -> str:
    """Select best strategy (convenience function)"""
    selector = get_strategy_selector()
    return selector.select_strategy()


def record_check_result(
    strategy: str,
    success: bool,
    username: str = None,
    error: str = None,
    response_time: float = 0,
    proxy_used: bool = False,
    user_id: int = None
):
    """Record check result (convenience function)"""
    selector = get_strategy_selector()
    selector.record_attempt(
        strategy=strategy,
        success=success,
        username=username,
        error=error,
        response_time=response_time,
        proxy_used=proxy_used,
        user_id=user_id
    )


def print_adaptive_stats(last_n: int = 100):
    """Print adaptive statistics (convenience function)"""
    selector = get_strategy_selector()
    selector.print_statistics(last_n)




