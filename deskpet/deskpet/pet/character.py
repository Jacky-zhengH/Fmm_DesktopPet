"""角色状态机与动画/行为逻辑。

状态：
  IDLE  待机 —— 呼吸起伏（或播放 idle 序列帧）；随机眨眼；随机漫游；久置入睡
  WALK  走路 —— 朝目标点移动，窗口随动；到达后回 IDLE
  SLEEP 睡觉 —— 慢速呼吸 + 漂浮 Zzz；点击/拖动可唤醒
  HAPPY 互动 —— 点击宠物触发，开心跳跃 1.5s
  DRAG  被拖动 —— 由窗口通知进入/退出，期间暂停自主行为

眨眼是叠加层（可叠加在 IDLE/WALK 上），素材回退链：walk_blink → blink → 占位。

扩展新状态：
  1. State 加常量  2. _tick() 加迁移逻辑
  3. current_sprite() 映射同名素材  4. assets/sprites/ 放对应 PNG
"""
import math
import random

from PySide6.QtCore import QObject, QRect, QTimer, Signal

from pet.sprites import CANVAS_SIZE

TICK_MS = 33              # ~30fps
BLINK_TICKS = 4           # 眨眼持续 ~0.13s
HAPPY_TICKS = 45          # 开心 1.5s
IDLE_SLEEP_TICKS = 2700   # 待机 90s 无交互入睡
WANDER_CHANCE = 0.004     # 每 tick 漫游概率（平均 ~8s 一次）
WANDER_RANGE = 250        # 漫游半径 px
WALK_SPEED = 3            # px/tick ≈ 90px/s
ANIM_FRAME_DIV = 4        # 序列帧每 4 tick 换一帧（~7.5fps）
SPRITE_FACING = 0         # 素材朝向：1=朝右，-1=朝左，0=正面素材（永不镜像）
WALK_SPRITE_FACING = -1   # 走路素材原生朝向：-1=朝左 / 1=朝右 / 0=正面（走路的镜像单独配置）
DRAG_MODE = "idle"        # 拖拽时显示什么："idle"=待机原图（被拎着静止） / "none"=不显示任何图片


class State:
    IDLE = "idle"
    WALK = "walk"
    SLEEP = "sleep"
    HAPPY = "happy"
    DRAG = "drag"


class Character(QObject):
    frame_changed = Signal()   # 需要重绘
    walk_step = Signal(int)    # 请求窗口移动 dx px（由窗口执行并回写位置）

    def __init__(self, sprites):
        super().__init__()
        self.sprites = sprites
        self.state = State.IDLE
        self.facing = 1            # 1 朝右 / -1 朝左

        self._phase = 0.0          # 动画相位
        self._blink = 0            # 眨眼剩余 tick（叠加层）
        self._next_blink = self._rand_blink_gap()
        self._state_ticks = 0      # HAPPY 倒计时
        self._awake_ticks = 0      # 连续无交互时长（用于入睡）
        self._x = 0                # 当前窗口 x（由窗口回写）
        self._walk_target: float | None = None
        self._screen: QRect | None = None
        # 各状态序列帧（<状态>_0.png...）：有则轮播，代替程序化动效
        self._frames: dict[str, list] = {}
        for s in (State.IDLE, State.WALK, State.SLEEP, State.HAPPY):
            fs = sprites.frames(s)
            if fs:
                self._frames[s] = fs
        self._anim_tick = 0        # 降帧计数
        self._anim_idx = 0         # 序列帧索引（全局相位）

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(TICK_MS)

    # -------------------------------------------------- 窗口协作接口
    def set_screen_rect(self, rect: QRect):
        self._screen = rect

    def set_position(self, x: int):
        """初始化位置（窗口创建后调用一次）。"""
        self._x = x

    def notify_x(self, x: int):
        """窗口实际移动后回写。"""
        self._x = x

    # -------------------------------------------------- 交互入口
    def set_dragging(self, on: bool):
        self.state = State.DRAG if on else State.IDLE
        self._awake_ticks = 0
        self.frame_changed.emit()

    def pet(self):
        """点击互动：睡觉则唤醒，否则开心。"""
        self._awake_ticks = 0
        if self.state == State.DRAG:
            return
        self.state = State.HAPPY
        self._state_ticks = HAPPY_TICKS
        self.frame_changed.emit()

    def toggle_sleep(self):
        self._awake_ticks = 0
        self.state = State.IDLE if self.state == State.SLEEP else State.SLEEP
        self.frame_changed.emit()

    # -------------------------------------------------- 渲染接口
    def current_sprite(self):
        s = self.state
        if s == State.DRAG:
            if DRAG_MODE == "none":
                return None  # 拖拽时不显示任何图片
            return self.sprites.get(State.IDLE)  # 拖拽用待机原图（静止，不眨眼不轮播）
        if self._blink > 0:
            # 回退链：<状态>_blink → blink → <状态> 本身（有真实素材时宁可不眨眼，也不闪占位图）
            return self.sprites.get(f"{s}_blink", fallbacks=("blink", s))
        if s in self._frames:
            return self._frames[s][self._anim_idx % len(self._frames[s])]
        return self.sprites.get(s)

    @property
    def scale(self) -> float:
        if self.state == State.SLEEP:
            return 1.0 + 0.03 * math.sin(self._phase * 0.5)  # 睡觉时慢深呼吸
        if self.state == State.IDLE and State.IDLE not in self._frames:
            return 1.0 + 0.02 * math.sin(self._phase)
        return 1.0

    @property
    def hop_offset(self) -> float:
        """垂直位移：开心大跳，走路小颠。"""
        if self.state == State.HAPPY:
            return -10 * abs(math.sin(self._phase * 4))
        if self.state == State.WALK:
            return -3 * abs(math.sin(self._phase * 3))
        return 0.0

    @property
    def zzz_offset(self) -> float:
        """睡觉 Zzz 的漂浮相位（窗口绘制用）。"""
        return (self._phase * 10) % 40 if self.state == State.SLEEP else 0.0

    # ---------------------------------------------------------- 主循环
    def _tick(self):
        self._phase += 0.08

        self._anim_tick += 1
        if self._anim_tick >= ANIM_FRAME_DIV:
            self._anim_tick = 0
            self._anim_idx += 1

        if self.state != State.DRAG:
            self._tick_blink()
            handler = {
                State.IDLE: self._tick_idle,
                State.WALK: self._tick_walk,
                State.HAPPY: self._tick_countdown,
            }.get(self.state)
            if handler:
                handler()
            # SLEEP：无逻辑，慢呼吸由 scale 负责

        self.frame_changed.emit()

    def _tick_blink(self):
        if self._blink > 0:
            self._blink -= 1
        elif self.state in (State.IDLE, State.WALK):
            if self.state in self._frames:
                return  # 有序列帧素材时眨眼由素材自行负责
            self._next_blink -= 1
            if self._next_blink <= 0:
                self._blink = BLINK_TICKS
                self._next_blink = self._rand_blink_gap()

    def _tick_idle(self):
        self._awake_ticks += 1
        if self._awake_ticks >= IDLE_SLEEP_TICKS:
            self.state = State.SLEEP
            return
        if random.random() < WANDER_CHANCE:
            self._start_wander()

    def _tick_walk(self):
        self._awake_ticks = 0
        if self._walk_target is None or abs(self._walk_target - self._x) <= WALK_SPEED:
            self._walk_target = None
            self.state = State.IDLE
            return
        self.walk_step.emit(WALK_SPEED * self.facing)

    def _tick_countdown(self):
        self._awake_ticks = 0
        self._state_ticks -= 1
        if self._state_ticks <= 0:
            self.state = State.IDLE

    def _start_wander(self):
        lo, hi = self._x - WANDER_RANGE, self._x + WANDER_RANGE
        if self._screen is not None:
            lo = max(lo, self._screen.left())
            hi = min(hi, self._screen.right() - CANVAS_SIZE)
        if hi <= lo:
            return
        self._walk_target = random.uniform(lo, hi)
        self.facing = 1 if self._walk_target > self._x else -1
        self.state = State.WALK

    @staticmethod
    def _rand_blink_gap() -> int:
        return random.randint(60, 200)  # 2~6.6 秒
