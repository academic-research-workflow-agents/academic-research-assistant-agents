version 17.0

capture adopath + "D:/Stata17/ado/plus"
capture adopath + "D:/Stata17/ado/personal"

capture which reghdfe
if _rc {
    di as error "错误 未检测到 reghdfe。当前工作流禁止回退到 areg/reg，请先安装 reghdfe。"
    exit 199
}

capture which esttab
if _rc {
    di as txt "提示 未检测到 esttab，当前版本主结果先由 Python 层统一排版。"
}

capture which psmatch2
if _rc {
    di as error "错误 未检测到 psmatch2。当前工作流禁止由 Python 承接 PSM-DID，请先安装 psmatch2。"
    exit 199
}
