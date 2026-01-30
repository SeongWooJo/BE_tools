# 🩺 Medical Image Analysis Pipeline System Manual

본 문서는 Multi-container 아키텍처를 기반으로 Multi-phase CT(N, A, P, D) 데이터를 분석하여 신장, 종양, 혈관, 요관을 세그멘테이션하고 3D 시각화 데이터(GLB)를 생성하는 인공지능 파이프라인의 사양과 워크플로우를 기술합니다.

---

## 1. AI Model Zoo

각 장기 및 조직의 특성에 맞춰 설계된 4가지 핵심 세그멘테이션 모델입니다.

| 모델명 | 입력 데이터 (Input) | 출력 라벨 (Output Labels) | 주요 특징 |
| :--- | :--- | :--- | :--- |
| **Tumor Model** | 특정 Phase Series | Kidney, Tumor | N, A, P, D 각 시기별 데이터로 별도 훈련 (정밀도 특화) |
| **Vessel Model** | **A, P Phase 동시 입력** | Artery, Vein, Kidney | A Phase 기준 결과 생성. A 또는 P 누락 시 추론 불가 |
| **Ureter Model** | D Phase Series | Ureter, Kidney | D Phase 전용. 요관 및 신장 추출. D 누락 시 추론 불가 |
| **Arna_v1 Model** | 특정 Phase Series | K, T, A, V, U (All) | 전 라벨 통합 추론(저화질). 전 페이즈 단일 모델 훈련 |

---

## 2. API Workflow 상세

### 📍 `/demo` API (Rapid Prototyping Mode)
시연을 목적으로 가용한 페이즈를 탐색하여 빠르게 3D 결과물을 생성합니다.

#### **(1) DemoTumorEvent** (Container: `nnunet`)
* **시리즈 선택:** 케이스 내 이미지 중 `D → A → P → N` 우선순위로 탐색하여 가장 먼저 발견된 시리즈 하나를 선택.
* **모델 추론:** 선택된 시리즈로 `Tumor Model` 실행하여 Kidney, Tumor 마스크 생성.

#### **(2) DemoEvent** (Container: `postprocess`)
* **무게중심 계산:** 생성된 마스크 내 두 신장의 무게중심(Center of Mass) 산출.
* **Template Transform:** 표준 템플릿 이미지의 신장 무게중심에 맞추어 현재 마스크를 이동(Transform) 및 정렬.
* **결과 병합:** 템플릿의 기존 신장/종양 영역을 제거하고 이동시킨 Segmentation 마스크를 부착.
* **⚠️ 예외 처리:** 신장이 2개가 아닌 경우 로직 작동 불가 (Error 발생).

#### **(3) DemoSmoothEvent** (Container: `smooth`)
* **Smoothing:** 전달받은 Segmentation 경로를 기반으로 스무딩 알고리즘 적용.
* **결과 생성:** 시각화용 **GLB 파일** 생성 (모든 라벨이 없는 경우 제외).

---

### 📍 `/auto` API (Full Analysis Mode)
모든 데이터를 활용하여 정밀한 통합 세그멘테이션 및 후처리를 수행합니다. (이미지 0개 시 예외 처리)

#### **(1) VesselEvent** (Container: `nnunet`)
* **전처리:** A, P Phase에 대해 `TotalSegmentator` 실행 후 `total_A`, `total_P` 저장.
* **Feature 추출:** 원본 이미지와 Total 결과를 기반으로 Feature Image 생성.
* **추론:** A Phase 이미지와 Feature Image를 입력으로 `Vessel Model` 실행 (Artery, Vein, Kidney 획득).
* **결합 및 보정:** - A Phase `Tumor Model` 결과(Tumor) 병합.
    - **Registration 보정:** P Phase에서 획득한 중심부 정맥(Vein) 부분을 **Registration 알고리즘을 통해 A Phase 위치로 전이(Transformation)** 시켜 정밀도 보정.
* **최종 결과:** 보정된 데이터를 합쳐 `segment_A`, `segment_P` 생성.

#### **(2) UreterEvent** (Container: `nnunet`)
* **추론:** D Phase 입력 기반 `Ureter Model`(U, K), `Arna_v1`(A, V), `Tumor Model`(T) 실행 및 병합하여 `segment_D` 생성.

#### **(3) ArnaV1Event** (Container: `nnunet`)
* **보완 추론:** 앞선 이벤트에서 누락된 나머지 이미지들에 대해 `Arna_v1` 및 `Tumor Model` 실행 후 각 시리즈별 segment 생성.

#### **(4) FatEvent** (Container: `postprocess`)
* **지방 분석:** 우선순위(Prior)가 가장 높은 이미지에 대해 `TotalSegmentator` 결과 기반 Fat 알고리즘 적용 및 라벨 병합.

#### **(5) SmoothEvent** (Container: `smooth`)
* **라벨 통합:** 최우선순위 이미지에 없는 라벨을 타 Phase 결과에서 **Resample**을 통해 가져와 합침 (`segment_combined` 저장).
* **3D 생성:** 통합 마스크 기반으로 스무딩 처리가 된 최종 **GLB 파일** 생성.

#### **(6) GenImageEvent** (Container: `othermodel`)
* **페이즈 생성:** A, P, D 중 누락된 페이즈가 있을 경우, 기존 이미지로부터 `A→P`, `P→D`, `D→A` 변환 모델을 적용하여 이미지 생성.
* **후속 작업:** 새로 생성된 이미지가 있다면 즉시 `TumorEvent` 트리거.

---

## 3. 시스템 운영 정책
* **우선순위 관리:** 각 모델 결과 및 페이즈별 우선순위(Prior) 정보를 JSON 형식으로 저장하여 통합 단계에서 참조.
* **컨테이너 격리:** 연산 부하에 따라 `nnunet`, `postprocess`, `smooth`, `othermodel` 컨테이너로 역할을 분리하여 운영 효율화.