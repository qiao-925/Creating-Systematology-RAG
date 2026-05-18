#!/usr/bin/env bash
# CLDFlow MVP 全量校验（按交付物组织）
set -uo pipefail

TRACK_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$TRACK_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"

TOTAL_PASS=0
TOTAL_FAIL=0

check() {
    local id="$1" cmd="$2"
    if eval "$cmd" >/dev/null 2>&1; then
        echo "  ✅ $id"; return 0
    else
        echo "  ❌ $id"; return 1
    fi
}

echo "╔═══════════════════════════════════════════╗"
echo "║ CLDFlow MVP 全量校验                       ║"
echo "║ $(date '+%Y-%m-%d %H:%M')                  ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ── A：后端 Pipeline ──
echo "▶ A：后端 Pipeline"
echo "─────────────────────────────────────────"
PASS=0; FAIL=0

check "T2  数据模型" "test -f backend/infrastructure/config/models.py && grep -q 'class.*BaseModel' backend/infrastructure/config/models.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T3  目录骨架" "test -d backend/core/orchestration && test -d backend/core/modules/fcm && test -d backend/core/modules/d2d && test -d backend/core/input" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T4  输入层" "test -f backend/core/input/enhance.py && test -f backend/core/input/retrieve.py && test -f backend/core/input/stop_rules.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T5  护栏" "test -f backend/core/orchestration/guardrails.py && grep -q 'def ' backend/core/orchestration/guardrails.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T6  Lead Agent" "test -f backend/core/orchestration/lead_agent.py && grep -q 'def ' backend/core/orchestration/lead_agent.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T7  视角生成" "test -f backend/core/modules/cld/perspectives/generator.py && grep -q 'def ' backend/core/modules/cld/perspectives/generator.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T8  Specialist" "test -f backend/core/modules/cld/specialist.py && grep -q 'def ' backend/core/modules/cld/specialist.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T9  归并+冲突" "test -f backend/core/modules/cld/merge.py && test -f backend/core/modules/cld/conflict.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T10 裁判" "test -f backend/core/modules/cld/judge.py && grep -q 'def ' backend/core/modules/cld/judge.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T11 CLD 组装" "test -f backend/core/modules/cld/module.py && grep -q 'def ' backend/core/modules/cld/module.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T12 FCM 映射" "test -f backend/core/modules/fcm/mapper.py && grep -q 'def ' backend/core/modules/fcm/mapper.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T13 FCM 评级" "test -f backend/core/modules/fcm/rater.py && grep -q 'def ' backend/core/modules/fcm/rater.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T14 FCM 仿真" "test -f backend/core/modules/fcm/simulator.py && grep -q 'def ' backend/core/modules/fcm/simulator.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T15 D2D 扰动" "test -f backend/core/modules/d2d/sensitivity.py && grep -q 'def ' backend/core/modules/d2d/sensitivity.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T16 D2D 排序" "test -f backend/core/modules/d2d/ranking.py && test -f backend/core/modules/d2d/uncertainty.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T17 报告层" "test -f backend/core/reporting/reporting.py && grep -q 'def ' backend/core/reporting/reporting.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "G2  API 端点" "test -f backend/core/api.py && grep -q 'router\|APIRouter' backend/core/api.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "G3  配置项" "test -f application.yml && grep -q 'cldflow' application.yml" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "G5  instructor" "grep -q 'instructor' backend/core/modules/cld/specialist.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "G6  Judge 降级" "test -f backend/core/modules/cld/judge.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

echo "  → ✅ $PASS · ❌ $FAIL"
TOTAL_PASS=$((TOTAL_PASS + PASS)); TOTAL_FAIL=$((TOTAL_FAIL + FAIL))
echo ""

# ── B：前端 Demo ──
echo "▶ B：前端 Demo"
echo "─────────────────────────────────────────"
PASS=0; FAIL=0

check "B1  项目结构" "test -f web/package.json && test -d web/src/app" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "B2  页面布局" "test -f web/src/app/layout.tsx && test -f web/src/app/page.tsx" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "B4  CLDFlow 组件" "test -f web/src/components/cldflow/cldflow-panel.tsx" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "B5  API 对接" "test -f web/src/lib/api.ts" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

echo "  → ✅ $PASS · ❌ $FAIL"
TOTAL_PASS=$((TOTAL_PASS + PASS)); TOTAL_FAIL=$((TOTAL_FAIL + FAIL))
echo ""

# ── C：测试体系 ──
echo "▶ C：测试体系"
echo "─────────────────────────────────────────"
PASS=0; FAIL=0

check "T18 黄金样例" "test -f backend/tests/fixtures/cldflow_fixtures.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T19 单测" "test -f backend/tests/test_cldflow_unit.py && grep -q 'def test_' backend/tests/test_cldflow_unit.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T19 集成测试" "test -f backend/tests/test_cldflow_integration.py && grep -q 'def test_' backend/tests/test_cldflow_integration.py" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "T20 评估报告" "test -f 'docs/CLDFlow MVP Builder/MVP-releasability-assessment.md'" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

echo "  → ✅ $PASS · ❌ $FAIL"
TOTAL_PASS=$((TOTAL_PASS + PASS)); TOTAL_FAIL=$((TOTAL_FAIL + FAIL))
echo ""

# ── D：部署与文档 ──
echo "▶ D：部署与文档"
echo "─────────────────────────────────────────"
PASS=0; FAIL=0

check "G7  README" "test -f README.md && grep -q 'CLDFlow' README.md" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "G8  预加载" "test -f scripts/preload_models.py || test -f Makefile" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "D6  Dockerfile" "test -f Dockerfile && grep -q 'FROM' Dockerfile && grep -q 'node\|Node' Dockerfile" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "D7  start.sh" "test -f start.sh && grep -q 'uvicorn' start.sh" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "D8  HF 配置" "grep -q 'sdk: docker' README.md" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "D9  ARCHITECTURE" "test -f ARCHITECTURE.md && [ \$(wc -l < ARCHITECTURE.md) -gt 200 ]" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
check "D10 配置说明" "test -f 'docs/CLDFlow MVP Builder/CONFIG_SETUP.md'" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

echo "  → ✅ $PASS · ❌ $FAIL"
TOTAL_PASS=$((TOTAL_PASS + PASS)); TOTAL_FAIL=$((TOTAL_FAIL + FAIL))
echo ""

# ── 汇总 ──
echo "╔═══════════════════════════════════════════╗"
echo "║ 汇总：✅ $TOTAL_PASS 通过 · ❌ $TOTAL_FAIL 失败"
echo "╚═══════════════════════════════════════════╝"

exit $TOTAL_FAIL
