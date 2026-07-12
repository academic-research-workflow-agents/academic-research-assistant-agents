from __future__ import annotations

try:
    from skill_workspace import DATA_DIR
    from orchestration_manifest import write_manifest
except ModuleNotFoundError:
    from scripts.skill_workspace import DATA_DIR
    from scripts.orchestration_manifest import write_manifest


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = write_manifest("baseline")
    print(f"完成 已生成 baseline manifest：{path}")


if __name__ == "__main__":
    main()
