import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import "./styles.css";

const app = document.querySelector("#app");

app.innerHTML = `
  <main class="event-display">
    <div class="scene" id="scene"></div>
    <div class="topbar">
      <section class="title-block">
        <h1>Geant4 Muon Active Target Event Display</h1>
        <div class="metrics">
          <span class="metric">Layers <strong id="layers">25</strong></span>
          <span class="metric">Crystals <strong id="crystals">250</strong></span>
          <span class="metric">Tracks <strong id="tracks">0</strong></span>
          <span class="metric">Primary <strong id="primary">0</strong></span>
        </div>
      </section>
      <section class="legend">
        <div class="legend-row"><span class="swatch" style="--swatch:#e84b5f"></span>Primary muon</div>
        <div class="legend-row"><span class="swatch" style="--swatch:#34d399"></span>gamma / neutral</div>
        <div class="legend-row"><span class="swatch" style="--swatch:#f97316"></span>electron</div>
        <div class="legend-row"><span class="swatch" style="--swatch:#60a5fa"></span>positron</div>
        <div class="legend-row"><span class="swatch" style="--swatch:#56a6ff"></span>LYSO crystals</div>
      </section>
      <section class="truth-panel">
        <h2>Track truth</h2>
        <div id="trackList" class="track-list"></div>
      </section>
    </div>
    <div class="axis-label">
      <span>beam: z</span>
      <span>x/y transverse</span>
    </div>
    <div class="controls">
      <button class="icon-button" id="play" title="Play">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>
      </button>
      <label class="range-wrap">
        <span class="range-label"><span>time</span><span id="timeLabel">0%</span></span>
        <input id="time" type="range" min="0" max="1000" value="0" />
      </label>
      <select class="select" id="speed" aria-label="Speed">
        <option value="0.35">0.35x</option>
        <option value="0.7">0.7x</option>
        <option value="1" selected>1x</option>
        <option value="1.8">1.8x</option>
        <option value="3">3x</option>
      </select>
      <button class="icon-button" id="reset" title="Reset">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 5V2L7 7l5 5V8a4 4 0 1 1-3.46 6H5.34A7 7 0 1 0 12 5z"/></svg>
      </button>
    </div>
  </main>
`;

const sceneRoot = document.querySelector("#scene");
const playButton = document.querySelector("#play");
const resetButton = document.querySelector("#reset");
const timeInput = document.querySelector("#time");
const speedSelect = document.querySelector("#speed");
const timeLabel = document.querySelector("#timeLabel");

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(sceneRoot.clientWidth, sceneRoot.clientHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
sceneRoot.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x080909, 0.0026);

const camera = new THREE.PerspectiveCamera(
  52,
  sceneRoot.clientWidth / sceneRoot.clientHeight,
  0.1,
  2400
);
camera.position.set(150, 120, 330);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.target.set(0, 0, 0);
controls.minDistance = 130;
controls.maxDistance = 720;

scene.add(new THREE.AmbientLight(0xffffff, 0.55));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
keyLight.position.set(120, 160, 180);
scene.add(keyLight);
const rimLight = new THREE.DirectionalLight(0x8ee6ff, 1.1);
rimLight.position.set(-160, -80, -120);
scene.add(rimLight);

const detectorGroup = new THREE.Group();
const trackGroup = new THREE.Group();
const headGroup = new THREE.Group();
scene.add(detectorGroup, trackGroup, headGroup);

const trackMeshes = [];
const headMeshes = [];
let duration = 1;
let progress = 0;
let playing = false;
let lastTime = performance.now();

function setPlaying(nextPlaying) {
  playing = nextPlaying;
  playButton.innerHTML = playing
    ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg>'
    : '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>';
}

function makeMaterial(color, opacity = 1, emissive = false) {
  return new THREE.MeshStandardMaterial({
    color,
    transparent: opacity < 1,
    opacity,
    roughness: 0.54,
    metalness: 0.05,
    emissive: emissive ? color : 0x000000,
    emissiveIntensity: emissive ? 0.42 : 0,
    depthWrite: opacity > 0.75,
  });
}

function vector(point) {
  return new THREE.Vector3(point[0], point[1], point[2]);
}

function cumulativeLengths(points) {
  const lengths = [0];
  for (let idx = 1; idx < points.length; idx += 1) {
    lengths.push(lengths[idx - 1] + points[idx - 1].distanceTo(points[idx]));
  }
  return lengths;
}

function pointAt(points, lengths, distance) {
  if (distance <= 0) return points[0].clone();
  const total = lengths[lengths.length - 1];
  if (distance >= total) return points[points.length - 1].clone();
  let idx = 1;
  while (idx < lengths.length && lengths[idx] < distance) idx += 1;
  const segmentStart = lengths[idx - 1];
  const segmentEnd = lengths[idx];
  const local = (distance - segmentStart) / Math.max(segmentEnd - segmentStart, 1e-6);
  return points[idx - 1].clone().lerp(points[idx], local);
}

function partialPoints(points, lengths, fraction) {
  const total = lengths[lengths.length - 1];
  const distance = total * fraction;
  const result = [points[0].clone()];
  for (let idx = 1; idx < points.length; idx += 1) {
    if (lengths[idx] <= distance) {
      result.push(points[idx].clone());
    } else {
      result.push(pointAt(points, lengths, distance));
      break;
    }
  }
  return result;
}

function makeLine(points, color, primary) {
  const material = new THREE.LineBasicMaterial({
    color,
    transparent: true,
    opacity: primary ? 0.98 : 0.7,
  });
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const line = new THREE.Line(geometry, material);
  return line;
}

function addDetector(detector) {
  const edgeMaterial = new THREE.LineBasicMaterial({
    color: 0xd9f7ff,
    transparent: true,
    opacity: 0.18,
  });

  detector.forEach((box, index) => {
    const color = index % 20 < 10 ? 0x58b8ff : 0xffb044;
    const material = makeMaterial(color, 0.16);
    const geometry = new THREE.BoxGeometry(box.size[0], box.size[1], box.size[2]);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(box.center[0], box.center[1], box.center[2]);
    detectorGroup.add(mesh);

    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), edgeMaterial);
    edges.position.copy(mesh.position);
    detectorGroup.add(edges);
  });
}

function addBeamAxis() {
  const axisMaterial = new THREE.LineBasicMaterial({
    color: 0x9ec8ff,
    transparent: true,
    opacity: 0.62,
  });
  const axis = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, -170),
      new THREE.Vector3(0, 0, 150),
    ]),
    axisMaterial
  );
  scene.add(axis);

  const grid = new THREE.GridHelper(320, 32, 0x304050, 0x1d2a2f);
  grid.position.y = -62;
  grid.material.transparent = true;
  grid.material.opacity = 0.42;
  scene.add(grid);
}

function addTracks(tracks) {
  duration = Math.max(...tracks.map((track) => track.length || 1));
  tracks.forEach((track) => {
    const points = track.points.map(vector);
    const lengths = cumulativeLengths(points);
    const primary = track.role === "primary";
    const particle = track.truth?.particleName;
    const color = primary
      ? 0xe84b5f
      : particle === "gamma"
        ? 0x34d399
        : particle === "e-"
          ? 0xf97316
          : particle === "e+"
            ? 0x60a5fa
            : 0x43d19e;
    const line = makeLine([points[0], points[0]], color, primary);
    line.userData = { points, lengths, primary };
    trackMeshes.push(line);
    trackGroup.add(line);

    const headGeometry = new THREE.SphereGeometry(primary ? 3.4 : 2.0, 18, 12);
    const head = new THREE.Mesh(headGeometry, makeMaterial(color, 1, true));
    head.userData = { points, lengths, primary };
    headMeshes.push(head);
    headGroup.add(head);
  });
}

function renderTrackTruth(tracks) {
  const list = document.querySelector("#trackList");
  const rows = [...tracks]
    .filter((track) => track.truth)
    .sort((a, b) => (b.truth.trackLengthMm || b.length) - (a.truth.trackLengthMm || a.length))
    .slice(0, 9);

  list.innerHTML = rows
    .map((track) => {
      const truth = track.truth;
      const primary = track.role === "primary";
      return `
        <div class="track-row ${primary ? "primary" : ""}">
          <span class="track-id">#${truth.trackId}</span>
          <span class="track-particle">${truth.particleName}</span>
          <span class="track-process">${truth.creatorProcess}</span>
          <span class="track-length">${Math.round(truth.trackLengthMm)} mm</span>
        </div>
      `;
    })
    .join("");
}

function updateTracks(nextProgress) {
  progress = Math.max(0, Math.min(1, nextProgress));
  const value = Math.round(progress * 1000);
  timeInput.value = String(value);
  timeLabel.textContent = `${Math.round(progress * 100)}%`;

  trackMeshes.forEach((line) => {
    const { points, lengths } = line.userData;
    const partial = partialPoints(points, lengths, progress);
    line.geometry.dispose();
    line.geometry = new THREE.BufferGeometry().setFromPoints(partial);
  });

  headMeshes.forEach((head) => {
    const { points, lengths } = head.userData;
    const position = pointAt(points, lengths, lengths[lengths.length - 1] * progress);
    head.position.copy(position);
    head.visible = progress > 0.002;
  });
}

async function loadEvent() {
  const response = await fetch("/event.json");
  if (!response.ok) throw new Error(`Unable to load event.json: ${response.status}`);
  const event = await response.json();

  document.querySelector("#crystals").textContent = String(event.detector.length);
  document.querySelector("#layers").textContent = String(Math.round(event.detector.length / 10));
  document.querySelector("#tracks").textContent = String(event.tracks.length);
  document.querySelector("#primary").textContent = String(event.primaryTrackIndex);

  addDetector(event.detector);
  addBeamAxis();
  addTracks(event.tracks);
  renderTrackTruth(event.tracks);
  updateTracks(0);
}

playButton.addEventListener("click", () => {
  setPlaying(!playing);
});

resetButton.addEventListener("click", () => {
  setPlaying(false);
  updateTracks(0);
});

timeInput.addEventListener("input", (event) => {
  setPlaying(false);
  updateTracks(Number(event.target.value) / 1000);
});

function onResize() {
  const width = sceneRoot.clientWidth;
  const height = sceneRoot.clientHeight;
  renderer.setSize(width, height);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

window.addEventListener("resize", onResize);

function animate(now) {
  const delta = Math.min((now - lastTime) / 1000, 0.05);
  lastTime = now;
  if (playing) {
    const speed = Number(speedSelect.value);
    const next = progress + (delta * speed) / 5.0;
    updateTracks(next >= 1 ? 0 : next);
  }
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

loadEvent()
  .then(() => {
    setPlaying(true);
    requestAnimationFrame(animate);
  })
  .catch((error) => {
    app.innerHTML = `<pre style="padding:24px;color:#fff;background:#111">${error.stack}</pre>`;
  });
