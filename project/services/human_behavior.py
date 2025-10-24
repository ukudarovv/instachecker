"""
🎭 Enhanced Human Behavior Simulator

Realistic human behavior simulation using:
- Markov chains for action sequences
- Bezier curves for smooth mouse movements
- Gaussian distributions for timing
- Reading patterns (F-pattern, Z-pattern)
"""

import asyncio
import random
import math
from typing import List, Tuple, Optional, Dict
from enum import Enum


class ActionType(Enum):
    """Types of human actions"""
    SCROLL_DOWN = "scroll_down"
    SCROLL_UP = "scroll_up"
    MOVE_MOUSE = "move_mouse"
    PAUSE = "pause"
    READ = "read"
    QUICK_GLANCE = "quick_glance"


class HumanBehaviorSimulator:
    """
    Advanced human behavior simulator
    
    Features:
    - Markov chain action sequences
    - Bezier curve mouse movements
    - Gaussian timing distributions
    - Reading patterns (F-pattern, Z-pattern)
    """
    
    def __init__(self):
        """Initialize behavior simulator"""
        
        # Markov chain transition probabilities
        self.transition_matrix = {
            ActionType.SCROLL_DOWN: {
                ActionType.SCROLL_DOWN: 0.35,
                ActionType.SCROLL_UP: 0.05,
                ActionType.PAUSE: 0.30,
                ActionType.MOVE_MOUSE: 0.15,
                ActionType.READ: 0.10,
                ActionType.QUICK_GLANCE: 0.05
            },
            ActionType.SCROLL_UP: {
                ActionType.SCROLL_DOWN: 0.40,
                ActionType.SCROLL_UP: 0.15,
                ActionType.PAUSE: 0.25,
                ActionType.MOVE_MOUSE: 0.10,
                ActionType.READ: 0.05,
                ActionType.QUICK_GLANCE: 0.05
            },
            ActionType.PAUSE: {
                ActionType.SCROLL_DOWN: 0.40,
                ActionType.SCROLL_UP: 0.10,
                ActionType.PAUSE: 0.10,
                ActionType.MOVE_MOUSE: 0.20,
                ActionType.READ: 0.15,
                ActionType.QUICK_GLANCE: 0.05
            },
            ActionType.MOVE_MOUSE: {
                ActionType.SCROLL_DOWN: 0.30,
                ActionType.SCROLL_UP: 0.10,
                ActionType.PAUSE: 0.25,
                ActionType.MOVE_MOUSE: 0.15,
                ActionType.READ: 0.10,
                ActionType.QUICK_GLANCE: 0.10
            },
            ActionType.READ: {
                ActionType.SCROLL_DOWN: 0.50,
                ActionType.SCROLL_UP: 0.05,
                ActionType.PAUSE: 0.20,
                ActionType.MOVE_MOUSE: 0.15,
                ActionType.READ: 0.05,
                ActionType.QUICK_GLANCE: 0.05
            },
            ActionType.QUICK_GLANCE: {
                ActionType.SCROLL_DOWN: 0.45,
                ActionType.SCROLL_UP: 0.10,
                ActionType.PAUSE: 0.15,
                ActionType.MOVE_MOUSE: 0.20,
                ActionType.READ: 0.05,
                ActionType.QUICK_GLANCE: 0.05
            }
        }
        
        self.current_state = ActionType.SCROLL_DOWN
        
        print(f"[BEHAVIOR] 🎭 Initialized human behavior simulator")
    
    # ========================================================================
    # MARKOV CHAIN ACTION SELECTION
    # ========================================================================
    
    def next_action(self) -> ActionType:
        """
        Select next action using Markov chain
        
        Returns:
            Next ActionType
        """
        probs = self.transition_matrix[self.current_state]
        
        actions = list(probs.keys())
        probabilities = list(probs.values())
        
        # Weighted random choice
        self.current_state = random.choices(actions, weights=probabilities)[0]
        
        return self.current_state
    
    # ========================================================================
    # BEZIER CURVE MOUSE MOVEMENTS
    # ========================================================================
    
    def cubic_bezier(self, t: float, p0: float, p1: float, p2: float, p3: float) -> float:
        """
        Cubic Bezier curve calculation
        
        Args:
            t: Parameter (0-1)
            p0, p1, p2, p3: Control points
            
        Returns:
            Point on curve
        """
        return (
            (1 - t) ** 3 * p0 +
            3 * (1 - t) ** 2 * t * p1 +
            3 * (1 - t) * t ** 2 * p2 +
            t ** 3 * p3
        )
    
    async def bezier_mouse_movement(
        self, 
        page,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        duration: float = 1.0,
        steps: int = 20
    ):
        """
        Move mouse along Bezier curve
        
        Args:
            page: Playwright page object
            start_x, start_y: Starting coordinates
            end_x, end_y: Ending coordinates
            duration: Movement duration in seconds
            steps: Number of interpolation steps
        """
        # Generate random control points for natural curve
        ctrl1_x = start_x + (end_x - start_x) * 0.33 + random.randint(-50, 50)
        ctrl1_y = start_y + (end_y - start_y) * 0.33 + random.randint(-50, 50)
        ctrl2_x = start_x + (end_x - start_x) * 0.66 + random.randint(-50, 50)
        ctrl2_y = start_y + (end_y - start_y) * 0.66 + random.randint(-50, 50)
        
        for i in range(steps + 1):
            t = i / steps
            
            # Calculate position on Bezier curve
            x = self.cubic_bezier(t, start_x, ctrl1_x, ctrl2_x, end_x)
            y = self.cubic_bezier(t, start_y, ctrl1_y, ctrl2_y, end_y)
            
            try:
                await page.mouse.move(x, y)
            except Exception:
                pass  # Ignore errors if page is closed
            
            # Variable speed (faster in middle, slower at ends)
            if i < steps * 0.3 or i > steps * 0.7:
                await asyncio.sleep(duration / steps * 1.5)
            else:
                await asyncio.sleep(duration / steps * 0.7)
    
    # ========================================================================
    # REALISTIC SCROLLING
    # ========================================================================
    
    async def realistic_scroll(
        self, 
        page, 
        amount: float,
        acceleration: bool = True
    ):
        """
        Realistic scrolling with acceleration/deceleration
        
        Args:
            page: Playwright page object
            amount: Total scroll amount (positive = down, negative = up)
            acceleration: Use acceleration/deceleration
        """
        steps = random.randint(5, 12)
        
        if acceleration:
            # Acceleration profile (ease-in-out)
            for i in range(steps):
                t = i / steps
                
                # Ease-in-out function
                if t < 0.5:
                    factor = 2 * t * t
                else:
                    factor = -1 + (4 - 2 * t) * t
                
                step_amount = (amount / steps) * (factor + 0.5)
                
                try:
                    await page.mouse.wheel(0, step_amount)
                except Exception:
                    pass
                
                # Variable delay
                await asyncio.sleep(random.uniform(0.05, 0.15))
        else:
            # Linear scroll
            for i in range(steps):
                try:
                    await page.mouse.wheel(0, amount / steps)
                except Exception:
                    pass
                await asyncio.sleep(random.uniform(0.08, 0.12))
    
    # ========================================================================
    # READING PATTERNS
    # ========================================================================
    
    async def f_pattern_reading(self, page):
        """
        Simulate F-pattern reading (common web reading pattern)
        
        Pattern:
        1. Horizontal scan at top
        2. Vertical scan down left side
        3. Shorter horizontal scan in middle
        """
        try:
            viewport = page.viewport_size
            
            # Top horizontal line
            start_x = random.randint(30, 80)
            start_y = random.randint(50, 100)
            end_x = random.randint(int(viewport['width'] * 0.7), int(viewport['width'] * 0.9))
            end_y = start_y + random.randint(-20, 20)
            
            await self.bezier_mouse_movement(
                page, start_x, start_y, end_x, end_y,
                duration=random.uniform(0.5, 1.0)
            )
            
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # Vertical scan down
            start_x = random.randint(30, 80)
            start_y = random.randint(100, 150)
            end_x = start_x + random.randint(-20, 20)
            end_y = random.randint(int(viewport['height'] * 0.4), int(viewport['height'] * 0.6))
            
            await self.bezier_mouse_movement(
                page, start_x, start_y, end_x, end_y,
                duration=random.uniform(0.4, 0.8)
            )
            
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
            # Middle horizontal line (shorter)
            start_x = random.randint(30, 80)
            start_y = end_y + random.randint(-30, 30)
            end_x = random.randint(int(viewport['width'] * 0.4), int(viewport['width'] * 0.6))
            end_y = start_y + random.randint(-20, 20)
            
            await self.bezier_mouse_movement(
                page, start_x, start_y, end_x, end_y,
                duration=random.uniform(0.3, 0.6)
            )
        
        except Exception as e:
            print(f"[BEHAVIOR] ⚠️ F-pattern reading error: {e}")
    
    async def z_pattern_scan(self, page):
        """
        Simulate Z-pattern scanning (quick scan pattern)
        
        Pattern:
        1. Top left to top right
        2. Diagonal to bottom left
        3. Bottom left to bottom right
        """
        try:
            viewport = page.viewport_size
            
            # Top line (left to right)
            await self.bezier_mouse_movement(
                page,
                random.randint(30, 80), random.randint(50, 100),
                random.randint(int(viewport['width'] * 0.7), int(viewport['width'] * 0.9)),
                random.randint(50, 100),
                duration=random.uniform(0.4, 0.7)
            )
            
            await asyncio.sleep(random.uniform(0.2, 0.4))
            
            # Diagonal line
            await self.bezier_mouse_movement(
                page,
                random.randint(int(viewport['width'] * 0.7), int(viewport['width'] * 0.9)),
                random.randint(50, 100),
                random.randint(30, 80),
                random.randint(int(viewport['height'] * 0.6), int(viewport['height'] * 0.8)),
                duration=random.uniform(0.5, 0.9)
            )
            
            await asyncio.sleep(random.uniform(0.2, 0.4))
            
            # Bottom line (left to right)
            await self.bezier_mouse_movement(
                page,
                random.randint(30, 80),
                random.randint(int(viewport['height'] * 0.6), int(viewport['height'] * 0.8)),
                random.randint(int(viewport['width'] * 0.7), int(viewport['width'] * 0.9)),
                random.randint(int(viewport['height'] * 0.6), int(viewport['height'] * 0.8)),
                duration=random.uniform(0.4, 0.7)
            )
        
        except Exception as e:
            print(f"[BEHAVIOR] ⚠️ Z-pattern scan error: {e}")
    
    # ========================================================================
    # MAIN BEHAVIOR SIMULATION
    # ========================================================================
    
    async def simulate_behavior(
        self, 
        page,
        duration: float = 10.0,
        action_count: Optional[int] = None
    ):
        """
        Main behavior simulation function
        
        Args:
            page: Playwright page object
            duration: Total duration in seconds (if action_count not specified)
            action_count: Specific number of actions to perform
        """
        print(f"[BEHAVIOR] 🎭 Starting behavior simulation...")
        
        start_time = asyncio.get_event_loop().time()
        actions_performed = 0
        
        try:
            viewport = page.viewport_size
        except Exception:
            # Default viewport if page is closed
            viewport = {'width': 1920, 'height': 1080}
        
        while True:
            # Check termination conditions
            if action_count and actions_performed >= action_count:
                break
            
            if not action_count and (asyncio.get_event_loop().time() - start_time) >= duration:
                break
            
            # Select next action
            action = self.next_action()
            actions_performed += 1
            
            print(f"[BEHAVIOR] 🎬 Action #{actions_performed}: {action.value}")
            
            try:
                if action == ActionType.SCROLL_DOWN:
                    amount = random.gauss(300, 100)  # Gaussian distribution
                    amount = max(100, min(500, amount))  # Clamp
                    await self.realistic_scroll(page, amount)
                
                elif action == ActionType.SCROLL_UP:
                    amount = random.gauss(-200, 80)
                    amount = max(-400, min(-50, amount))
                    await self.realistic_scroll(page, amount)
                
                elif action == ActionType.MOVE_MOUSE:
                    # Random mouse movement
                    start_x = random.randint(0, viewport['width'])
                    start_y = random.randint(0, viewport['height'])
                    end_x = random.randint(0, viewport['width'])
                    end_y = random.randint(0, viewport['height'])
                    
                    await self.bezier_mouse_movement(
                        page, start_x, start_y, end_x, end_y,
                        duration=random.uniform(0.5, 1.5)
                    )
                
                elif action == ActionType.PAUSE:
                    # Gaussian pause duration
                    pause_time = random.gauss(1.5, 0.5)
                    pause_time = max(0.5, min(3.0, pause_time))
                    await asyncio.sleep(pause_time)
                
                elif action == ActionType.READ:
                    # F-pattern reading
                    await self.f_pattern_reading(page)
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                
                elif action == ActionType.QUICK_GLANCE:
                    # Z-pattern scan
                    await self.z_pattern_scan(page)
                    await asyncio.sleep(random.uniform(0.5, 1.0))
            
            except Exception as e:
                print(f"[BEHAVIOR] ⚠️ Action error: {e}")
            
            # Random delay between actions
            inter_action_delay = random.gauss(0.5, 0.2)
            inter_action_delay = max(0.1, min(1.5, inter_action_delay))
            await asyncio.sleep(inter_action_delay)
        
        print(f"[BEHAVIOR] ✅ Simulation complete ({actions_performed} actions)")


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

async def simulate_human_behavior(
    page,
    duration: float = 10.0,
    action_count: Optional[int] = None
):
    """
    Simulate human behavior on page (convenience function)
    
    Args:
        page: Playwright page object
        duration: Duration in seconds
        action_count: Number of actions to perform
    """
    simulator = HumanBehaviorSimulator()
    await simulator.simulate_behavior(page, duration, action_count)


async def quick_human_actions(page, count: int = 5):
    """Quick human actions (convenience function)"""
    simulator = HumanBehaviorSimulator()
    await simulator.simulate_behavior(page, action_count=count)



