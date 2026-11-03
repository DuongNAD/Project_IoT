#!/usr/bin/env python3
"""
NHÓM 2 - SUCCESS: đã tới chưa?

Nhận Plan do NHÓM 1 (control.py) lập ra rồi trả lời một câu hỏi duy nhất: ba servo đế / vai / khuỷu đã tới góc gợi ý chưa?

    Plan (góc hiện tại, góc cần tới, các Move)  -->  check()  -->  Result (XONG hay chưa, còn bao nhiêu lần bấm, từng servo đúng chưa)

Thành công = cả 3 servo lệch không quá TOLERANCE_STEPS bước bấm so với góc gợi ý, và giữ đúng như vậy HOLD_S giây
(giữ đủ lâu mới đếm thêm 1 lần thành công). Kẹp không tính: bản đơn giản chỉ cần đưa đầu kẹp tới đúng chỗ của vật.
"""

import time
from dataclasses import dataclass, field

TOLERANCE_STEPS = 1  # Lệch không quá 1 bước bấm (2° với đế / vai / khuỷu) là "đã tới": mô hình hình học chỉ chính xác cỡ đó
HOLD_S = 1.0         # Giữ đúng liên tục ngần này giây mới tính 1 lần thành công (khỏi đếm khi chỉ lướt qua)

# Trạng thái: done (xong) | moving (còn phải bấm) | no_target (chưa thấy vật) | unreachable (vật ngoài tầm với) | relaxed (tay đang nghỉ)


@dataclass
class Result:
    state: str
    done: bool
    joints_ok: list = field(default_factory=list)   # 3 giá trị True / False: đế, vai, khuỷu đã tới góc gợi ý chưa
    next_move: object = None                        # Move đầu tiên chưa xong theo thứ tự đế -> vai -> khuỷu, None khi không còn gì phải bấm
    remaining: int = 0                              # Tổng số lần bấm còn lại
    count: int = 0                                  # Số lần thành công từ lúc chạy chương trình


def joint_ok(move):
    """Servo đã tới góc gợi ý nếu lệch không quá TOLERANCE_STEPS bước."""
    return move.degrees <= TOLERANCE_STEPS * move.step


def check(plan):
    """Đánh giá một Plan (không nhớ gì giữa hai lần gọi). Số lần thành công do Success.update đếm."""
    joints = [joint_ok(m) for m in plan.moves]
    pending = [m for m, ok in zip(plan.moves, joints) if not ok]
    remaining = sum(m.steps for m in pending)
    if plan.relaxed:
        state = "relaxed"       # Tay đã ngắt xung: góc servo báo về chỉ là góc lệnh cuối, không tin được
    elif not plan.found:
        state = "no_target"
    elif not plan.reachable:
        state = "unreachable"
    elif not pending:
        state = "done"
    else:
        state = "moving"
    return Result(state=state, done=state == "done", joints_ok=joints, next_move=pending[0] if pending else None, remaining=remaining)


class Success:
    """Đánh giá từng khung hình và đếm số lần thành công."""

    def __init__(self):
        self.count = 0
        self._since = None     # Lúc bắt đầu liên tục "done"
        self._counted = False  # Lần "done" hiện tại đã được đếm chưa

    def update(self, plan, now=None):
        now = time.time() if now is None else now
        result = check(plan)
        if result.done:
            if self._since is None:
                self._since = now
            if not self._counted and now - self._since >= HOLD_S:
                self.count += 1
                self._counted = True
        else:
            self._since, self._counted = None, False
        result.count = self.count
        return result
