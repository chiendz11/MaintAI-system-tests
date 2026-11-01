# MaintAI System Tests & Release Gate Orchestrator

Repository kiểm định chất lượng toàn hệ thống độc lập (Blackbox System Testing), kiểm tra hệ thống giám sát (Observability Verification), kịch bản phục hồi thảm họa (Chaos/Resilience Drills) và điều phối phát hành (Release Gate Pipeline) cho nền tảng MaintAI.

---

## 1. Vị trí trong Kim tự tháp Kiểm thử (Testing Pyramid)

```
        ▲
       / \         Tầng 3: MaintAI-system-tests (Repo này)
      /   \        • E2E System Tests (Luồng Sensor -> Kafka -> ML -> Alert -> UI)
     / E2E \       • Monitoring Verification (Prometheus & Alertmanager API)
    /───────\      • Chaos & Recovery Drills (Kill Pod, Network Partition, RTO/RPO)
   / CIT/INT \     Tầng 2: Cross-Service Integration Tests (PR CI / Docker Compose)
  /───────────\
 /  Unit Tests \   Tầng 1: Unit & Component Tests (Nội bộ từng service)
/───────────────\
```

---

## 2. Cấu trúc Repository

```text
MaintAI-system-tests/
├── .github/workflows/
│   ├── test-ci.yml             # CI lint và dry-run cho chính repo test
│   └── release-gate.yml        # Pipeline điều phối release Staging -> System Tests -> Production
├── config/
│   ├── settings.py             # Quản lý cấu hình tập trung qua Pydantic
│   ├── local-k3d.env           # Cấu hình kiểm thử cụm k3d local (localhost:8001, 8003, 9090...)
│   └── staging.env             # Cấu hình kiểm thử cụm Cloud Staging
├── tests/
│   ├── conftest.py             # Fixtures: HTTP clients, sample telemetry generator, k8s helper
│   ├── e2e/                    # 1. End-to-End Tests
│   │   ├── test_sensor_ingestion_e2e.py    # Ingestion 202 ACK & schema validation
│   │   ├── test_alert_lifecycle_e2e.py     # Alert acknowledge, resolve & feedback
│   │   └── test_rag_brief_e2e.py           # RAG maintenance brief generation
│   ├── monitoring/             # 2. Monitoring Tests
│   │   ├── test_metrics_scrape.py          # Prometheus scrape targets UP & core metrics
│   │   └── test_alertmanager_rules.py      # Alert rules & Alertmanager cluster readiness
│   └── chaos/                  # 3. Chaos & Recovery Drills
│       ├── test_worker_crash_recovery.py   # Live kill worker Pod -> đo thời gian tự hồi sinh (RTO)
│       └── test_rag_down_degradation.py    # Graceful degradation khi AI service offline
└── scripts/
    ├── wait_for_argocd.py      # Chờ Argo CD đồng bộ và kiểm tra trạng thái Healthy
    └── promote_gitops_image.py # Tự động cập nhật image tag vào GitOps Production
```

---

## 3. Hướng dẫn chạy kiểm thử Local (với cụm k3d)

### Cài đặt môi trường
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Chạy kiểm thử theo từng bộ (Markers)

1. **Chạy E2E System Tests:**
   ```bash
   pytest -m e2e
   ```

2. **Chạy Monitoring Verification Tests:**
   ```bash
   pytest -m monitoring
   ```

3. **Chạy Chaos & Recovery Drills:**
   ```bash
   pytest -m chaos
   ```

4. **Chạy toàn bộ kèm báo cáo XML/HTML:**
   ```bash
   pytest --junitxml=reports/system-test-results.xml
   ```

---

## 4. Cơ chế hoạt động của Release Gate Pipeline

Khi một phiên bản ứng dụng mới được build và đẩy lên Container Registry (`ghcr.io/chiendz11/...`):

1. **Staging Rollout:** Release workflow gọi Argo CD để triển khai phiên bản mới lên môi trường Staging.
2. **Quality Gate:** Bộ 3 bài kiểm tra (E2E, Monitoring, Chaos) được tự động thực thi.
3. **Audit Evidence:** Kết quả test (JUnit XML, logs) được đính kèm vào đợt release làm bằng chứng xác minh (Provenance).
4. **Production Promotion:** Chỉ khi **100% bài test bắt buộc vượt qua**, workflow mới kích hoạt script `promote_gitops_image.py` để commit tag mới vào môi trường Production của `MaintAI-gitops`.
