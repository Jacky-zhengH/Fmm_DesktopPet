"""Time-based behavior; image frame rate is independent of window refresh."""
import math
import random
import time

from PySide6.QtCore import QObject, QRect, QTimer, Qt, Signal
from pet.sprites import CANVAS_SIZE

TICK_MS = 16
HAPPY_SECONDS = 1.5
AUTO_SLEEP_SECONDS = 90.0
WANDER_INTERVAL_SECONDS = 8.25
WANDER_RANGE = 250
WALK_SPEED = 90.0  # pixels/second


class State:
    IDLE = "idle"
    WALK = "walk"
    SLEEP = "sleep"
    HAPPY = "happy"
    DRAG = "drag"


class Character(QObject):
    frame_changed = Signal()
    state_changed = Signal(str)
    walk_step = Signal(float)

    def __init__(self, sprites, *, clock=time.monotonic, rng=None):
        super().__init__()
        self.sprites = sprites
        self._clock = clock
        self._rng = rng or random.Random()
        now = clock()
        self.state = State.IDLE
        self.facing = 1
        self.wander_enabled = True
        self.auto_sleep_seconds = AUTO_SLEEP_SECONDS
        self._last_interaction = self._last_tick = self._state_started = now
        self._phase = 0.0
        self._blink_until = 0.0
        self._next_blink = now + self._rng.uniform(2.0, 6.6)
        self._x = 0.0
        self._window_width = CANVAS_SIZE
        self._walk_target = None
        self._screen = None
        self._frames = {}
        self.reload_sprites()
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._tick)
        self._timer.start(TICK_MS)

    def reload_sprites(self):
        self._frames = {}
        for state in (State.IDLE, State.WALK, State.SLEEP, State.HAPPY, State.DRAG):
            frames = self.sprites.frames(state)
            if frames:
                self._frames[state] = frames
        self._state_started = self._clock()
        self._blink_until = 0.0
        self.frame_changed.emit()

    def set_screen_rect(self, rect: QRect, window_width=None):
        self._screen = rect
        if window_width is not None:
            self._window_width = window_width
        if self._walk_target is not None:
            self._walk_target = max(rect.left(), min(self._walk_target,
                                    rect.left() + rect.width() - self._window_width))

    def set_position(self, x):
        self._x = float(x)

    def notify_x(self, x):
        self._x = float(x)

    def interact(self):
        self._last_interaction = self._clock()

    def _enter_state(self, state):
        self.state = state
        now = self._clock()
        self._state_started = now
        self._blink_until = 0.0
        self._next_blink = now + self._rng.uniform(2.0, 6.6)
        if state != State.WALK:
            self._walk_target = None
        self.state_changed.emit(state)
        self.frame_changed.emit()

    def set_dragging(self, on):
        self.interact()
        self._enter_state(State.DRAG if on else State.IDLE)

    def pet(self):
        self.interact()
        if self.state != State.DRAG:
            self._enter_state(State.IDLE if self.state == State.SLEEP else State.HAPPY)

    def toggle_sleep(self):
        self.interact()
        self._enter_state(State.IDLE if self.state == State.SLEEP else State.SLEEP)

    def set_wandering(self, enabled):
        self.interact()
        self.wander_enabled = bool(enabled)
        if not enabled and self.state == State.WALK:
            self._enter_state(State.IDLE)

    def _options(self):
        return self.sprites.animation_options(self.state)

    def _procedural(self):
        return self.state not in self._frames or self._options().get("procedural", False)

    def current_sprite(self):
        state = self.state
        elapsed = max(0.0, self._clock() - self._state_started)
        if state in (State.IDLE, State.WALK) and self._clock() < self._blink_until:
            return self.sprites.get(f"{state}_blink", fallbacks=("blink", state))
        if state in self._frames:
            frames = self._frames[state]
            options = self._options()
            index = int(elapsed * options["fps"])
            index = index % len(frames) if options.get("loop", True) else min(index, len(frames) - 1)
            return frames[index]
        if state == State.DRAG:
            return self.sprites.get("drag", fallbacks=("idle",))
        return self.sprites.get(state)

    @property
    def scale(self):
        if not self._procedural():
            return 1.0
        if self.state == State.SLEEP:
            return 1.0 + 0.03 * math.sin(self._phase * 0.5)
        if self.state == State.IDLE:
            return 1.0 + 0.02 * math.sin(self._phase)
        return 1.0

    @property
    def hop_offset(self):
        if not self._procedural():
            return 0.0
        if self.state == State.HAPPY:
            return -10 * abs(math.sin((self._clock() - self._state_started) * 9.6))
        if self.state == State.WALK:
            return -3 * abs(math.sin(self._phase * 3))
        return 0.0

    @property
    def zzz_offset(self):
        return (self._phase * 10) % 40 if self.state == State.SLEEP else 0.0

    @property
    def sprite_facing(self):
        return self._options().get("facing", -1 if self.state == State.WALK else 0)

    def pause(self):
        self._timer.stop()

    def resume(self):
        self._last_tick = self._clock()
        self._timer.start()

    def _tick(self):
        now = self._clock()
        elapsed = max(0.0, now - self._last_tick)
        self._last_tick = now
        self._phase = now * 2.4
        if self.state == State.DRAG:
            self.frame_changed.emit()
            return
        # Autonomous activity never resets the human-interaction clock.
        if (self.state in (State.IDLE, State.WALK) and self.auto_sleep_seconds > 0
                and now - self._last_interaction >= self.auto_sleep_seconds):
            self._enter_state(State.SLEEP)
        elif self.state == State.HAPPY:
            if now - self._state_started >= HAPPY_SECONDS:
                self._enter_state(State.IDLE)
        elif self.state == State.WALK:
            if self._walk_target is None or abs(self._walk_target - self._x) < 0.5:
                self._enter_state(State.IDLE)
            else:
                self.facing = 1 if self._walk_target > self._x else -1
                step = min(abs(self._walk_target - self._x), WALK_SPEED * min(elapsed, 0.1))
                self.walk_step.emit(step * self.facing)
        elif (self.state == State.IDLE and self.wander_enabled
              and self._rng.random() < 1.0 - math.exp(-elapsed / WANDER_INTERVAL_SECONDS)):
            self._start_wander()
        if self.state in (State.IDLE, State.WALK) and self.state not in self._frames:
            if now >= self._next_blink:
                self._blink_until = now + 0.132
                self._next_blink = now + self._rng.uniform(2.0, 6.6)
        self.frame_changed.emit()

    def _start_wander(self):
        lo, hi = self._x - WANDER_RANGE, self._x + WANDER_RANGE
        if self._screen is not None:
            lo = max(lo, self._screen.left())
            hi = min(hi, self._screen.left() + self._screen.width() - self._window_width)
        if hi <= lo:
            return
        target = self._rng.uniform(lo, hi)
        self._enter_state(State.WALK)
        self._walk_target = target
        self.facing = 1 if target > self._x else -1
