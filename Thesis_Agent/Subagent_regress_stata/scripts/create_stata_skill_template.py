from __future__ import annotations

try:
    from stata_skill_workflow import write_default_workflow_artifacts
except ModuleNotFoundError:
    from scripts.stata_skill_workflow import write_default_workflow_artifacts


def main() -> None:
    generated = write_default_workflow_artifacts()
    print(f"完成 已生成模板：{generated['template']}")
    print(f"完成 临时任务规格也已写入：{generated['spec']}")
    print(f"完成 当前不会自动塞默认模型；你选好能力后，执行专用 do-file 会写到：{generated['do_file']}")


if __name__ == "__main__":
    main()
