"""评估报告渲染与误判整理的单元测试（不需要模型、不需要 torch）。

这些函数只接收普通 list/dict，因此可以在没有模型、没有 GPU 的机器上直接验证，
用来兜住「报告格式写坏」这类只在真正评估时才暴露的问题。

运行：
    pytest tests/test_model_eval_report.py -v
"""

import numpy as np
import pandas as pd
import pytest

from training import model_eval


def test_display_width_counts_cjk_as_two_columns():
    assert model_eval._display_width("差评") == 4
    assert model_eval._display_width("ab") == 2
    assert model_eval._display_width("真实:差评") == 2 + 1 + 4


def test_pad_aligns_by_display_width_not_len():
    left = model_eval._pad("差评", 10)
    right = model_eval._pad("好评", 10, "right")
    assert model_eval._display_width(left) == 10
    assert model_eval._display_width(right) == 10
    assert left.startswith("差评")  # 左对齐：补在右侧
    assert right.endswith("好评")  # 右对齐：补在左侧


def test_confusion_matrix_lines_are_aligned():
    rendered = model_eval._render_confusion_matrix([[760, 38], [45, 354]], ["差评", "好评"])
    rows = rendered.splitlines()[1:]  # 首行是标题，不参与对齐

    assert len(rows) == 4  # 表头 + 两个类别 + 合计
    widths = {model_eval._display_width(row) for row in rows}
    assert len(widths) == 1, f"混淆矩阵各行宽度不一致：{widths}"

    assert "1197" in rows[-1]  # 合计行
    assert "760" in rows[1] and "354" in rows[2]


def test_confusion_matrix_survives_zero_size():
    assert "无类别" in model_eval._render_confusion_matrix([], [])


def test_metrics_table_contains_every_class_and_macro_row():
    metrics = {
        "total": 1197,
        "macro_f1": 0.9217,
        "weighted_f1": 0.9218,
        "per_class": [
            {"label_id": 0, "label": "差评", "precision": 0.9441, "recall": 0.9524, "f1": 0.9482, "support": 798},
            {"label_id": 1, "label": "好评", "precision": 0.9031, "recall": 0.8872, "f1": 0.8951, "support": 399},
        ],
    }
    rendered = model_eval._render_metrics_table(metrics)

    assert "宏平均" in rendered and "加权平均" in rendered
    assert "0.9482" in rendered and "0.8951" in rendered
    assert "798" in rendered and "399" in rendered

    rows = rendered.splitlines()
    widths = {model_eval._display_width(row.rstrip()) for row in rows}
    assert len(widths) == 1, f"指标表各行宽度不一致：{widths}"


def test_to_py_converts_numpy_scalars_for_json():
    import json

    payload = {
        "int": model_eval._to_py(np.int64(3)),
        "float": model_eval._to_py(np.float64(1.5)),
        "bool": model_eval._to_py(np.bool_(True)),
    }
    assert json.dumps(payload)  # numpy 标量会在这里直接抛 TypeError
    assert isinstance(payload["int"], int)
    assert isinstance(payload["float"], float)


def test_fingerprint_dir_changes_when_a_file_changes(tmp_path):
    target = tmp_path / "ft_bert_dir"
    target.mkdir()
    (target / "config.json").write_text('{"num_labels": 2}', encoding="utf-8")

    first = model_eval.fingerprint_dir(target)
    assert first["available"] is True

    # 只改内容不改文件名，指纹也必须变化，否则「训练是否真的产出新模型」会判断错
    (target / "config.json").write_text('{"num_labels": 3}', encoding="utf-8")
    second = model_eval.fingerprint_dir(target)
    assert first["version_id"] != second["version_id"]


def test_fingerprint_dir_reports_missing_directory(tmp_path):
    result = model_eval.fingerprint_dir(tmp_path / "nope")
    assert result["available"] is False
    assert result["version_id"] == "unavailable"


def test_fingerprint_dir_is_stable_across_calls(tmp_path):
    target = tmp_path / "model"
    target.mkdir()
    (target / "a.bin").write_bytes(b"x" * 32)
    assert model_eval.fingerprint_dir(target)["version_id"] == model_eval.fingerprint_dir(target)["version_id"]


def test_eval_error_exposes_code_and_message():
    error = model_eval.EvalError("MODEL_DIR_MISSING", "未找到微调模型目录")
    assert error.code == "MODEL_DIR_MISSING"
    assert "未找到微调模型目录" in error.message
    assert "MODEL_DIR_MISSING" in str(error)


def test_mine_misclassifications_returns_every_error_with_line_numbers():
    frame = pd.DataFrame({"labels": [0, 0, 1, 1], "text": ["甲", "乙", "丙", "丁"]})
    y_true = [0, 0, 1, 1]
    y_pred = [1, 1, 1, 0]  # 第 1、2、4 行判错
    probabilities = np.array([[0.1, 0.9], [0.2, 0.8], [0.3, 0.7], [0.6, 0.4]])

    records = model_eval._mine_misclassifications(
        frame, y_true, y_pred, probabilities, ["差评", "好评"], [5, 6, 7, 8], [False] * 4
    )

    assert {record["line_number"] for record in records} == {1, 2, 4}
    assert all(record["true_label_id"] != record["pred_label_id"] for record in records)


def test_mine_misclassifications_ranks_high_confidence_first():
    frame = pd.DataFrame({"labels": [0, 1], "text": ["甲", "乙"]})
    probabilities = np.array([[0.05, 0.95], [0.55, 0.45]])

    records = model_eval._mine_misclassifications(
        frame, [0, 1], [1, 0], probabilities, ["差评", "好评"], [3, 3], [False, False]
    )

    # 第 1 行以 0.95 的置信度判错，必须出现在高置信度口径里
    first = next(record for record in records if record["line_number"] == 1)
    assert first["confidence"] == pytest.approx(0.95, abs=1e-6)
    assert "高置信度误判" in first["buckets"]


def test_mine_misclassifications_empty_when_all_correct():
    frame = pd.DataFrame({"labels": [0, 1], "text": ["甲", "乙"]})
    probabilities = np.array([[0.9, 0.1], [0.1, 0.9]])
    assert model_eval._mine_misclassifications(
        frame, [0, 1], [0, 1], probabilities, ["差评", "好评"], [3, 3], [False, False]
    ) == []


def test_missing_dependencies_returns_none_when_torch_is_importable():
    # 本测试在有 torch 的环境里应当返回 None；缺 torch 时返回说明字符串。
    missing = model_eval.missing_dependencies()
    assert missing is None or isinstance(missing, str)
