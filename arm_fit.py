#!/usr/bin/env python3
"""
Hiệu chỉnh hình học cánh tay bằng các lần "gắp thử".

Người dùng đưa hai ngón kẹp bao quanh một vật trên tờ giấy rồi ghi lại một mẫu gồm góc 3 servo (đế, vai, khuỷu),
vị trí vật trên tờ giấy (cm) và độ cao điểm kẹp (mm). Vật nằm giữa hai ngón nên điểm kẹp của cánh tay đang trùng vị trí vật,
không phụ thuộc camera nhìn nghiêng hay nhìn thẳng. Từ vài mẫu ở các vị trí khác nhau, khớp lại 5 thông số mà thước đo không
cho biết chính xác:
  - base_x_cm, base_y_cm, base_heading_deg: vị trí trục xoay đế và hướng robot nhìn trên tờ giấy
  - theta2_at_90_deg, theta3_at_90_deg: góc thật của khâu vai và khuỷu khi servo ở 90° (phụ thuộc cách lắp cần servo)
Chiều dài các khâu (d1, L2, L3, L4) vẫn lấy từ ARM_CONFIG vì thước đo được.

Thuần numpy (Levenberg-Marquardt), không biết gì về camera hay Serial: hàm dự đoán đầu kẹp được truyền vào từ bên ngoài.
"""

import math

import numpy as np

# Thông số được khớp (khóa trong ARM_CONFIG)
FIT_KEYS = ("base_x_cm", "base_y_cm", "base_heading_deg", "theta2_at_90_deg", "theta3_at_90_deg")

# Giá trị hiện có là điểm xuất phát; độ lệch chuẩn tiên nghiệm cho biết ta tin chúng tới đâu (cm hoặc độ), để vài mẫu thưa
# hay nhiễu không kéo thông số đi quá xa. Giới hạn cứng là mức dịch tối đa so với điểm xuất phát.
PRIOR_SIGMA = {"base_x_cm": 3.0, "base_y_cm": 3.0, "base_heading_deg": 12.0, "theta2_at_90_deg": 15.0, "theta3_at_90_deg": 15.0}
MAX_SHIFT = {"base_x_cm": 10.0, "base_y_cm": 10.0, "base_heading_deg": 35.0, "theta2_at_90_deg": 45.0, "theta3_at_90_deg": 45.0}
# Bước sai phân (cùng đơn vị với thông số) để tính đạo hàm số. Thêm thông số khớp = thêm khóa vào FIT_KEYS và ba bảng này.
# Đã thử thêm L4_r_mm (độ vươn của kẹp): khi tay thật vươn ngắn hơn mô hình 2-2.5 cm, 5 thông số này vẫn khớp tốt như khi có L4_r_mm.
FIT_STEP = {"base_x_cm": 0.02, "base_y_cm": 0.02, "base_heading_deg": 0.05, "theta2_at_90_deg": 0.05, "theta3_at_90_deg": 0.05}

# Sai số của một mẫu: servo chỉ nhích từng 5° nên người dùng không căn chính xác hơn ~1 cm, độ cao càng lỏng hơn
SIGMA_XY_MM = 10.0
SIGMA_Z_MM = 20.0

MIN_SAMPLES = 2          # Ít nhất ngần này mẫu mới khớp
MIN_SPREAD_CM = 5.0      # Các mẫu phải trải rộng (khoảng cách xa nhất giữa hai vật) tối thiểu ngần này, không thì không đủ thông tin
MAX_ACCEPT_RMS_MM = 30.0  # Sau khi khớp mà sai số trung bình vẫn lớn hơn mức này thì mẫu không nhất quán, không áp dụng


def samples_spread_cm(samples):
    """Khoảng cách xa nhất (cm) giữa hai vị trí vật trong các mẫu."""
    best = 0.0
    for i, a in enumerate(samples):
        for b in samples[i + 1:]:
            best = max(best, math.hypot(a["x_cm"] - b["x_cm"], a["y_cm"] - b["y_cm"]))
    return best


def _residuals(theta, cfg, samples, predict, p0):
    c = dict(cfg)
    c.update(zip(FIT_KEYS, theta))
    res = []
    for s in samples:
        x, y, z = predict(s["servo"], c)
        res.extend(((x - s["x_cm"]) * 10.0 / SIGMA_XY_MM, (y - s["y_cm"]) * 10.0 / SIGMA_XY_MM, (z - s["z_mm"]) / SIGMA_Z_MM))
    for key, value, start in zip(FIT_KEYS, theta, p0):
        res.append((value - start) / PRIOR_SIGMA[key])
    return np.array(res, dtype=float)


def _jacobian(theta, cfg, samples, predict, p0):
    cols = []
    for j, key in enumerate(FIT_KEYS):
        h = FIT_STEP[key]
        up, down = theta.copy(), theta.copy()
        up[j] += h
        down[j] -= h
        cols.append((_residuals(up, cfg, samples, predict, p0) - _residuals(down, cfg, samples, predict, p0)) / (2.0 * h))
    return np.stack(cols, axis=1)


def _xy_errors_mm(theta, cfg, samples, predict):
    c = dict(cfg)
    c.update(zip(FIT_KEYS, theta))
    errors, z_errors = [], []
    for s in samples:
        x, y, z = predict(s["servo"], c)
        errors.append(math.hypot(x - s["x_cm"], y - s["y_cm"]) * 10.0)
        z_errors.append(z - s["z_mm"])
    return np.array(errors), np.array(z_errors)


def fit_geometry(samples, cfg, predict, max_iter=80):
    """
    Khớp FIT_KEYS sao cho điểm kẹp theo mô hình trùng vị trí vật ở mọi mẫu.
      samples: [{"servo": (đế, vai, khuỷu), "x_cm", "y_cm", "z_mm"}]
      cfg: cấu hình hiện tại (dict kiểu ARM_CONFIG), là điểm xuất phát và tiên nghiệm
      predict(servo, cfg) -> (x_cm, y_cm, z_mm): điểm kẹp theo mô hình với cấu hình cfg
    Trả về {"params", "n", "before_rms_xy_mm", "rms_xy_mm", "max_xy_mm", "rms_z_mm", "std", "converged"}.
    """
    p0 = np.array([float(cfg[k]) for k in FIT_KEYS])
    lo = p0 - np.array([MAX_SHIFT[k] for k in FIT_KEYS])
    hi = p0 + np.array([MAX_SHIFT[k] for k in FIT_KEYS])

    theta = p0.copy()
    res = _residuals(theta, cfg, samples, predict, p0)
    cost = float(res @ res)
    lam = 1e-2
    converged = False
    for _ in range(max_iter):
        J = _jacobian(theta, cfg, samples, predict, p0)
        grad = J.T @ res
        hess = J.T @ J
        moved = False
        for _ in range(14):
            step = np.linalg.solve(hess + lam * np.diag(np.diag(hess) + 1e-9), -grad)
            cand = np.clip(theta + step, lo, hi)
            cand_res = _residuals(cand, cfg, samples, predict, p0)
            cand_cost = float(cand_res @ cand_res)
            if cand_cost < cost:
                gain = cost - cand_cost
                theta, res, cost = cand, cand_res, cand_cost
                lam = max(lam / 3.0, 1e-9)
                moved = True
                break
            lam *= 4.0
        if not moved:
            converged = True
            break
        if gain < 1e-10 * (1.0 + cost):
            converged = True
            break

    J = _jacobian(theta, cfg, samples, predict, p0)
    try:
        std = np.sqrt(np.diag(np.linalg.inv(J.T @ J)))
    except np.linalg.LinAlgError:
        std = np.full(len(FIT_KEYS), float("inf"))

    before_xy, _ = _xy_errors_mm(p0, cfg, samples, predict)
    after_xy, after_z = _xy_errors_mm(theta, cfg, samples, predict)
    return {
        "params": {k: float(v) for k, v in zip(FIT_KEYS, theta)},
        "n": len(samples),
        "before_rms_xy_mm": float(np.sqrt(np.mean(before_xy ** 2))),
        "rms_xy_mm": float(np.sqrt(np.mean(after_xy ** 2))),
        "max_xy_mm": float(after_xy.max()),
        "rms_z_mm": float(np.sqrt(np.mean(after_z ** 2))),
        "std": {k: float(v) for k, v in zip(FIT_KEYS, std)},
        "converged": converged,
    }
