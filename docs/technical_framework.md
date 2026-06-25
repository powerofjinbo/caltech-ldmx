# Muon-beam LDMX-like active target: technical framework

## 一句话定位

这个 SURF 项目的核心不是“怎么造出 muon beam”，而是“如果已经有 muon beam，40 层 LYSO active target 能不能同时充当 target 和 detector，把 Standard Model background 产生的额外可见活动 veto 掉”。

## 物理逻辑

LDMX-like missing-momentum 搜索的信号拓扑是：

```text
incoming muon -> outgoing muon with large energy/momentum loss + invisible particle(s)
```

真正的 invisible signal 应该只有一条类似 MIP 的 muon track，并且没有 photon shower、pair-production tracks、hadronic secondaries 等额外可见活动。主要背景不是“看起来完全一样的普通过程”，而是普通 SM 过程在某些角落里也能让 muon 丢很多能量，但通常伴随额外粒子。active target 的任务就是把这些额外粒子抓住。

## 第一版技术栈

```text
Geant4 geometry
  -> muon gun / future beam file
  -> reference physics list
  -> stepping-level scoring
  -> event-level CSV ntuple
  -> cut-based analysis script
  -> later: event display, optimization, ML
```

第一版 pipeline 只解决三件事：

1. 几何真的在 Geant4 中存在。
2. muon 能穿过 LYSO active target，并输出每个 event 的可分析量。
3. 可以立刻定义 toy veto cut，例如 `extra_edep_mev < threshold` 和 `n_extra_hit_layers == 0`。

## 几何模型

当前 scaffold 的默认假设：

- Beam 沿 `+z`。
- LYSO 总厚度 `40 cm`，由 40 层组成，每层厚 `1 cm`；当前 scaffold 加了 39 个 `0.1 mm` 层间 gap，所以几何外包络约 `40.39 cm`。
- 每层 10 根 LYSO crystal bar，每根尺寸 `1 cm x 1 cm x 10 cm`。
- 偶数层 bar 沿 `x`，奇数层 bar 沿 `y`，这样可以提供二维横向 hit 信息。
- LYSO 用 `Lu1.8Y0.2SiO5` 近似，密度 `7.10 g/cm3`。
- 暂时不模拟 optical photons、SiPM response、electronics threshold 或 timing。
- 默认 beam spot 放在 `(0.1 mm, 0.1 mm)`，避免理想几何中 `x=0,y=0` 正好落在 crystal boundary 上导致 Geant4 navigation 变慢。
- scaffold 默认在相邻层之间留 `0.1 mm` air gap，避免早期开发时直接相接的 400 个 crystal volumes 造成边界导航问题；真实机械设计确认后可以再改成实际间距。
- 早期 25-layer debug baseline 已经记录在 `docs/baseline_mip_calibration.md`，当前代码默认使用 proposal-aligned 40-layer geometry。

这个交错方向是一个工程假设，之后应和 Bertrand 确认。如果真实设计是所有层同向或有更复杂的 staggering，只需要改 `DetectorConstruction.cc`。

## 事件变量

第一阶段先用 cut-based variables：

- outgoing muon kinetic energy: 是否发生大能量损失。
- total LYSO energy deposition: target 内总 activity。
- primary-muon energy deposition: MIP-like 轨迹基线。
- extra energy deposition: 非主 muon 造成的可见活动。
- hit crystal/layer multiplicity: shower 或 extra track 的粗粒度 proxy。
- max layer energy deposition: 局部 shower burst 的 proxy。
- secondary counters: gamma、charged secondary 等。

最初的 baseline selection 可以写成：

```text
large muon energy loss
AND extra_edep_mev < E_veto
AND n_extra_hit_layers <= N_layer_veto
```

等 background samples 建好后，真正要画的是 signal efficiency vs background rejection，而不是只报一个 cut 后数字。

## 阶段计划

### Week 1: base pipeline

- 跑通 Geant4/CMake。
- 建好 40-layer LYSO target。
- 生成 8 GeV 和 15 GeV muon smoke samples。
- 输出 CSV ntuple。
- 检查 MIP-like muon 的能量沉积是否在合理量级。

### Week 2: detector observables

- 增加 per-layer profile 输出。
- 做 quick event display 或至少 layer-energy heatmap。
- 扫描 thresholds：`0.05, 0.1, 0.5, 1 MeV`。
- 确认 cut variables 和 Bertrand 的 detector assumptions 对齐。

### Week 3-4: background samples

优先级：

1. Muon bremsstrahlung: `mu N -> mu N gamma`，gamma shower 是 active target veto 的直接目标。
2. Pair production: `mu N -> mu N e+e-`，extra charged tracks 应该较容易被看见。
3. Muon-nuclear / photonuclear-like activity: rare but dangerous, physics-list/systematics 要更小心。

普通 Geant4 unbiased simulation 很难直接给到极低 survival probability，所以 early goal 是理解 topology 和 rejection handles；极低背景尾部之后需要 biased simulation 或 dedicated generation。

### Week 5-6: cut scan and optimization

- 对每类 background 画 survival fraction vs veto threshold。
- 比较不同 target choices：层数、阈值、bar orientation、可能的 gaps。
- 输出一套 defendable baseline cut。

### Week 7+: extension

- 加下游 ECal/HCal/veto 简化体积。
- 加 realistic readout：光产额、SiPM threshold、能量分辨率、dead channels。
- 如果 cut-based baseline 已经稳定，再尝试 BDT/random forest；ML 应该作为 extension，不应该替代物理可解释的 baseline。

## Proposal/report 主线

报告结构可以围绕下面四个问题：

1. 为什么 muon beam 需要 thicker active target。
2. 这个 LYSO target 的几何和读出假设是什么。
3. SM backgrounds 在 active target 中留下什么可见活动。
4. 用哪些 cut 能在保持 signal-like topology 的同时 veto backgrounds。

这样写会自然区分上一届学生的 beam-production feasibility 和你现在的 detector-performance feasibility。
