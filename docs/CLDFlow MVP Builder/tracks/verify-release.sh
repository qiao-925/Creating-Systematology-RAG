#!/usr/bin/env bash
# CLDFlow MVP 可发布性统一校验
set -uo pipefail

TRACK_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$TRACK_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"

PASS=0
FAIL=0
WARN=0

gate() {
    local id="$1" desc="$2" cmd="$3" level="${4:-hard}"
    if eval "$cmd" >/dev/null 2>&1; then
        echo "  ✅ $id $desc"
        PASS=$((PASS + 1))
    else
        if [ "$level" = "hard" ]; then
            echo "  ❌ $id $desc  [BLOCK]"
            FAIL=$((FAIL + 1))
        else
            echo "  ⚠️  $id $desc  [WARN]"
            WARN=$((WARN + 1))
        fi
    fi
}

echo "╔═══════════════════════════════════════════╗"
echo "║ CLDFlow MVP 可发布性校验                    ║"
echo "║ $(date '+%Y-%m-%d %H:%M')                  ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ── Gate 1：后端代码完整 ──
echo "▶ Gate 1：后端代码完整"
echo "─────────────────────────────────────────"
gate "G1.1" "CLD 模块" \
    "test -f backend/core/modules/cld/module.py && grep -q 'def ' backend/core/modules/cld/module.py"
gate "G1.2" "FCM 模块" \
    "test -f backend/core/modules/fcm/simulator.py && grep -q 'def ' backend/core/modules/fcm/simulator.py"
gate "G1.3" "D2D 模块" \
    "test -f backend/core/modules/d2d/sensitivity.py && grep -q 'def ' backend/core/modules/d2d/sensitivity.py"
gate "G1.4" "Lead Agent" \
    "test -f backend/core/orchestration/lead_agent.py && grep -q 'def ' backend/core/orchestration/lead_agent.py"
gate "G1.5" "API 路由" \
    "test -f backend/core/api.py && grep -q 'router\|APIRouter' backend/core/api.py"
echo ""

# ── Gate 2：测试文件存在 ──
echo "▶ Gate 2：测试体系"
echo "─────────────────────────────────────────"
gate "G2.1" "单元测试文件" \
    "test -f backend/tests/test_cldflow_unit.py && grep -q 'def test_' backend/tests/test_cldflow_unit.py"
gate "G2.2" "集成测试文件" \
    "test -f backend/tests/test_cldflow_integration.py && grep -q 'def test_' backend/tests/test_cldflow_integration.py"
gate "G2.3" "黄金样例 fixtures" \
    "test -f backend/tests/fixtures/cldflow_fixtures.py"
gate "G2.4" "pytest 配置" \
    "test -f pytest.ini && grep -q 'testpaths' pytest.ini"
echo ""

# ── Gate 3：前端构建 ──
echo "▶ Gate 3：前端构建"
echo "─────────────────────────────────────────"
gate "G3.1" "Next.js 项目" \
    "test -f web/package.json && test -d web/src/app" \
    "warn"
gate "G3.2" "CLDFlow 组件" \
    "test -f web/src/components/cldflow/cldflow-panel.tsx" \
    "warn"
gate "G3.3" "API 对接层" \
    "test -f web/src/lib/api.ts" \
    "warn"
echo ""

# ── Gate 4：部署就绪 ──
echo "▶ Gate 4：部署就绪"
echo "─────────────────────────────────────────"
gate "G4.1" "Dockerfile（多阶段）" \
    "test -f Dockerfile && grep -q 'FROM' Dockerfile && grep -q 'node\|Node' Dockerfile"
gate "G4.2" "启动脚本（双进程）" \
    "test -f start.sh && grep -q 'uvicorn' start.sh && grep -q 'next\|node' start.sh"
gate "G4.3" "HF Spaces frontmatter" \
    "grep -q 'sdk: docker' README.md" \
    "warn"
echo ""

# ── Gate 5：文档完整 ──
echo "▶ Gate 5：文档完整"
echo "─────────────────────────────────────────"
gate "G5.1" "README 含安装说明" \
    "grep -qi 'install\|安装\|quick\|快速' README.md"
gate "G5.2" "ARCHITECTURE 存在且 >200 行" \
    "test -f ARCHITECTURE.md && [ \$(wc -l < ARCHITECTURE.md) -gt 200 ]"
echo ""

# ── 汇总 ──
echo "╔═══════════════════════════════════════════╗"
echo "║ 结果                                       "
echo "║   ✅ 通过: $PASS                            "
echo "║   ❌ 阻塞: $FAIL                            "
echo "║   ⚠️  警告: $WARN                            "
echo "╠═══════════════════════════════════════════╣"
if [ $FAIL -eq 0 ]; then
    echo "║ 🟢 可发布（代码层面就绪）                    "
else
    echo "║ 🔴 不可发布（$FAIL 个阻塞项）                "
fi
echo "╚═══════════════════════════════════════════╝"

exit $FAIL
