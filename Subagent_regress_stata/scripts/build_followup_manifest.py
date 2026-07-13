from __future__ import annotations

try:
    from orchestration_manifest import write_manifest
except ModuleNotFoundError:
    from scripts.orchestration_manifest import write_manifest


def main() -> None:
    path = write_manifest("followup")
    print(f"完成 已生成 follow-up manifest：{path}")


if __name__ == "__main__":
    main()
