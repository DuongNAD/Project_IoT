#!/usr/bin/env python3
"""
KHỐI SUCCESS: đã tới chưa?
Đọc Plan của control.py rồi trả lời: ba servo đế / vai / khuỷu đã tới góc gợi ý chưa?
Thành công = cả 3 servo lệch không quá 1 bước bấm (2°) và giữ như vậy 1 giây thì đếm thêm 1 lần. Kẹp không tính.
"""

import time
from dataclasses import dataclass, field

TOLERANCE_STEPS = 1  # Lệch không quá 1 bước bấm (2°) là "đã tới": mô hình hình học chỉ chính xác cỡ đó
HOLD_S = 1.0         # Giữ đúng liên tục 1 giây mới đếm 1 lần thành công (khỏi đếm khi chỉ lướt qua)


@dataclass
class Result:
    state: str  # done | moving (còn phải bấm) | no_target (chưa có đích: chưa bấm R) | unreachable (ngoài tầm với)
    done: bool
    joints_ok: list = field(default_factory=list)  # Đế, vai, khuỷu đã tới góc gợi ý chưa
    next_move: object = None                       # Việc đầu tiên còn phải làm, theo thứ tự đế -> vai -> khuỷu
    remaining: int = 0                             # Tổng số lần bấm còn lại
    count: int = 0                                 # Số lần thành công từ lúc chạy chương trình


def check(plan):
    """Đánh giá một Plan (không nhớ gì giữa hai lần gọi)."""
    joints = [m.degrees <= TOLERANCE_STEPS * m.step for m in plan.moves]
    pending = [m for m, ok in zip(plan.moves, joints) if not ok]
    if not plan.found:
        state = "no_target"
    elif not plan.reachable:
        state = "unreachable"
    else:
        state = "moving" if pending else "done"
    return Result(state, state == "done", joints, pending[0] if pending else None, sum(m.steps for m in pending))


class Success:
    """Gọi mỗi khung hình: kết quả check() kèm số lần thành công."""

    def __init__(self):
        self.count = 0
        self.since = None     # Lúc bắt đầu liên tục "done"
        self.counted = False  # Lần "done" này đã được đếm chưa

    def update(self, plan, now=None):
        now = time.time() if now is None else now
        result = check(plan)
        if result.done:
            self.since = now if self.since is None else self.since
            if not self.counted and now - self.since >= HOLD_S:
                self.count, self.counted = self.count + 1, True
        else:
            self.since, self.counted = None, False
        result.count = self.count
        return result
