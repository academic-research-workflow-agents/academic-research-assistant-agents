from __future__ import annotations

from skill_workspace import DATA_DIR, OUTPUT_RESULTS_DIR, OUTPUT_RUNTIME_DIR, cleanup_script_artifacts, list_supported_data_files, reset_for_new_project


def main() -> None:
    reset_for_new_project()
    data_files = list_supported_data_files()
    cleanup_script_artifacts()
    print(f"完成 已清空 {OUTPUT_RUNTIME_DIR}、执行规格文件、{OUTPUT_RESULTS_DIR} 里的旧产出，以及仓库根目录和 scripts 目录下的临时日志/缓存。")
    print("提示 我没有删除 data 里的文件。")
    if data_files:
        print(f"提示 当前 data 里还有 {len(data_files)} 个数据文件。多文件时新主线会先做分流诊断。")
        for path in data_files:
            print(f"  - {path.name}")
    else:
        print(f"提示 当前 {DATA_DIR} 里还没有数据文件。下次使用时，把本次要分析的 Excel、CSV 或 dta 文件放进去即可。")


if __name__ == "__main__":
    main()
