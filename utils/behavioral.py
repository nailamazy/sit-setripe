"""
Behavioral Analysis - Human-like timing simulation
Simplified version: 2-5s random delay per field
"""

import random
import time
from enum import Enum
from typing import Optional


class TypingSpeed(Enum):
    """Kecepatan mengetik manusia"""
    SLOW = "slow"       # 20-35 WPM
    NORMAL = "normal"   # 35-55 WPM  
    FAST = "fast"       # 55-80 WPM


class HumanBehavior:
    """
    Simulasi perilaku manusia yang sederhana tapi efektif
    """
    
    # Timing constants (dalam milliseconds)
    FIELD_INPUT_MIN = 1500   # 1.5 detik minimum (untuk field cepat seperti CVC)
    FIELD_INPUT_MAX = 5500   # 5.5 detik maximum (untuk field panjang seperti CC)
    
    TRANSITION_MIN = 300     # 0.3s antar field
    TRANSITION_MAX = 1200    # 1.2s antar field
    
    DISTRACTION_CHANCE = 0.08  # 8% chance berpikir/terdistraksi
    DISTRACTION_MIN = 800      # 0.8s
    DISTRACTION_MAX = 3000     # 3s
    
    def __init__(self, speed: TypingSpeed = TypingSpeed.NORMAL):
        self.speed = speed
        self._set_speed_params()
        
    def _set_speed_params(self):
        """Set parameter berdasarkan kecepatan (dalam ms)"""
        if self.speed == TypingSpeed.SLOW:
            self.input_range = (3000, 5000)      # 3-5s (cautious user)
            self.transition_range = (600, 1500)   # Slow transition
        elif self.speed == TypingSpeed.FAST:
            self.input_range = (1500, 3000)      # 1.5-3s (experienced user)
            self.transition_range = (200, 600)    # Quick transition
        else:  # NORMAL
            self.input_range = (2000, 4500)      # 2-4.5s (average user)
            self.transition_range = (300, 1000)   # Normal transition
    
    @staticmethod
    def gaussian_clamp(mean: float, std: float, min_val: float, max_val: float) -> float:
        """
        Generate random number dengan Gaussian distribution, lalu clamp ke range
        Lebih natural dari uniform random
        """
        value = random.gauss(mean, std)
        return max(min_val, min(max_val, value))
    
    def get_field_input_time(self, field_type: str = "text") -> float:
        """
        Get waktu mengisi satu field (dalam detik)
        
        Args:
            field_type: "cc", "expiry", "cvc", "zip", "name", "email"
            
        Returns:
            Waktu dalam detik (float)
        """
        min_ms, max_ms = self.input_range
        mean = (min_ms + max_ms) / 2
        std = (max_ms - min_ms) / 4  # 68% data dalam range
        
        # Field-specific adjustments
        multipliers = {
            "cc": 1.0,      # CC number - standard
            "expiry": 0.6,  # Expiry - cepat (4 digit)
            "cvc": 0.5,     # CVC - sangat cepat (3-4 digit)
            "zip": 0.5,     # ZIP - cepat (5 digit)
            "name": 0.8,    # Name - medium (biasanya auto-fill)
            "email": 0.7,   # Email - medium (biasanya auto-fill)
        }
        
        multiplier = multipliers.get(field_type, 1.0)
        
        # Apply Gaussian randomness lalu multiply
        delay_ms = self.gaussian_clamp(mean, std, min_ms, max_ms)
        delay_ms *= random.gauss(multiplier, 0.1)  # Variation pada multiplier
        
        return round(delay_ms / 1000, 2)  # Convert ke detik, 2 decimal
    
    def get_transition_time(self) -> float:
        """
        Waktu berpindah antar field (mouse movement + think)
        
        Returns:
            Waktu dalam detik
        """
        min_ms, max_ms = self.transition_range
        mean = (min_ms + max_ms) / 2
        std = (max_ms - min_ms) / 3
        
        delay_ms = self.gaussian_clamp(mean, std, min_ms, max_ms)
        return round(delay_ms / 1000, 2)
    
    def get_distraction_pause(self) -> float:
        """
        Simulasi distraksi/berpikir (seperti cek HP, ragu-ragu)
        
        Returns:
            Waktu dalam detik, atau 0 jika tidak distracted
        """
        if random.random() > self.DISTRACTION_CHANCE:
            return 0.0
        
        # Distracted! Add pause
        delay_ms = random.uniform(self.DISTRACTION_MIN, self.DISTRACTION_MAX)
        return round(delay_ms / 1000, 2)
    
    def simulate_field_entry(self, field_type: str, field_value: str = "") -> dict:
        """
        Simulasi lengkap entry satu field
        
        Returns:
            {
                "field_type": "cc",
                "input_time": 3.45,
                "distraction": 0.0,
                "total_time": 3.45,
                "wpm": 45.2  # simulated
            }
        """
        input_time = self.get_field_input_time(field_type)
        distraction = self.get_distraction_pause()
        
        # Kalkulasi fake WPM untuk logging
        if field_value:
            char_count = len(field_value)
            # WPM = (chars / 5) / (time in minutes)
            time_minutes = input_time / 60
            wpm = round((char_count / 5) / time_minutes) if time_minutes > 0 else 0
        else:
            wpm = random.randint(30, 60)
        
        return {
            "field_type": field_type,
            "input_time": input_time,
            "distraction": distraction,
            "total_time": round(input_time + distraction, 2),
            "wpm": wpm
        }
    
    def get_full_checkout_timing(self, fields: list[str]) -> dict:
        """
        Kalkulasi timing untuk full checkout sequence
        
        Args:
            fields: List field yang diisi, e.g., ["cc", "expiry", "cvc"]
            
        Returns:
            {
                "total_time": 12.34,
                "field_timings": [...],
                "breakdown": {
                    "cc": {...},
                    "expiry": {...},
                    ...
                }
            }
        """
        field_timings = []
        total_time = 0
        breakdown = {}
        
        for i, field in enumerate(fields):
            # Waktu input field
            field_time = self.simulate_field_entry(field)
            
            # Waktu transisi ke field berikutnya (kecuali field terakhir)
            if i < len(fields) - 1:
                transition = self.get_transition_time()
                field_time["transition_to_next"] = transition
                total_time += transition
            
            field_timings.append(field_time)
            total_time += field_time["total_time"]
            breakdown[field] = field_time
        
        return {
            "total_time": round(total_time, 2),
            "field_timings": field_timings,
            "breakdown": breakdown,
            "speed_profile": self.speed.value
        }


class SessionBehavior:
    """
    Behavior untuk session warming dan browsing
    """
    
    @staticmethod
    def get_page_reading_time() -> float:
        """
        Waktu "membaca" halaman sebelum interaksi
        
        Returns:
            Detik (1.5 - 8 detik)
        """
        # Gaussian: mean 4s, std 1.5s
        return round(random.gauss(4.0, 1.5), 2)
    
    @staticmethod
    def get_scroll_behavior() -> list[dict]:
        """
        Simulasi scroll behavior
        
        Returns:
            List scroll events
        """
        num_scrolls = random.randint(1, 4)
        scrolls = []
        
        for _ in range(num_scrolls):
            scrolls.append({
                "direction": random.choice(["down", "up"]),
                "amount": random.randint(100, 600),
                "delay_after": round(random.uniform(0.5, 2.0), 2)
            })
        
        return scrolls
    
    @staticmethod
    def get_hover_elements() -> list[dict]:
        """
        Simulasi hover mouse ke element tertentu
        
        Returns:
            List hover events
        """
        elements = ["logo", "product_image", "price", "description", "form"]
        selected = random.sample(elements, random.randint(1, 3))
        
        hovers = []
        for el in selected:
            hovers.append({
                "element": el,
                "duration": round(random.uniform(0.3, 1.5), 2)
            })
        
        return hovers


# Pre-instantiated untuk convenience
slow_behavior = HumanBehavior(TypingSpeed.SLOW)
normal_behavior = HumanBehavior(TypingSpeed.NORMAL)
fast_behavior = HumanBehavior(TypingSpeed.FAST)


def simulate_checkout_input(
    card_number: str,
    expiry: str,
    cvc: str,
    zip_code: str = "",
    speed: TypingSpeed = TypingSpeed.NORMAL
) -> dict:
    """
    Helper function untuk simulasi lengkap input checkout
    
    Returns timing info yang bisa digunakan untuk asyncio.sleep()
    """
    behavior = HumanBehavior(speed)
    
    fields = [
        ("cc", card_number),
        ("expiry", expiry),
        ("cvc", cvc),
    ]
    if zip_code:
        fields.append(("zip", zip_code))
    
    field_types = [f[0] for f in fields]
    timing = behavior.get_full_checkout_timing(field_types)
    
    # Add per-field value info
    for field_type, value in fields:
        if field_type in timing["breakdown"]:
            timing["breakdown"][field_type]["value_length"] = len(value)
    
    return timing


async def execute_with_timing(timing: dict, verbose: bool = True):
    """
    Execute delays berdasarkan timing dict
    Gunakan ini di charge_card()
    """
    import asyncio
    
    breakdown = timing.get("breakdown", {})
    field_order = ["cc", "expiry", "cvc", "zip"]
    
    for field in field_order:
        if field not in breakdown:
            continue
            
        info = breakdown[field]
        
        # Input time
        if verbose:
            print(f"[BEHAVIOR] Typing {field}: {info['input_time']:.2f}s (simulated {info['wpm']} WPM)")
        await asyncio.sleep(info["input_time"])
        
        # Distraction if any
        if info["distraction"] > 0:
            if verbose:
                print(f"[BEHAVIOR] Brief pause: {info['distraction']:.2f}s")
            await asyncio.sleep(info["distraction"])
        
        # Transition to next field
        if "transition_to_next" in info:
            if verbose:
                print(f"[BEHAVIOR] Moving to next: {info['transition_to_next']:.2f}s")
            await asyncio.sleep(info["transition_to_next"])


if __name__ == "__main__":
    # Test
    test_card = "4242424242424242"
    test_expiry = "1225"
    test_cvc = "123"
    
    print("=== SLOW TYPING ===")
    timing = simulate_checkout_input(test_card, test_expiry, test_cvc, speed=TypingSpeed.SLOW)
    print(f"Total time: {timing['total_time']:.2f}s")
    for field, info in timing["breakdown"].items():
        print(f"  {field}: {info['total_time']:.2f}s (input: {info['input_time']:.2f}s, WPM: {info['wpm']})")
    
    print("\n=== NORMAL TYPING ===")
    timing = simulate_checkout_input(test_card, test_expiry, test_cvc, speed=TypingSpeed.NORMAL)
    print(f"Total time: {timing['total_time']:.2f}s")
    
    print("\n=== FAST TYPING ===")
    timing = simulate_checkout_input(test_card, test_expiry, test_cvc, speed=TypingSpeed.FAST)
    print(f"Total time: {timing['total_time']:.2f}s")
