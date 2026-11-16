// 3D view of the 35 abwab. All linguistic values come from the JSON block that
// tools/build_abwab.py writes into the page; nothing is typed in here.
import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';

const host = document.getElementById('viz');
const data = JSON.parse(document.getElementById('abwab-data').textContent);
const NAVY = '#0A2A45', GOLD = '#C29A52', PAPER = '#FBF8F1';
const AR = '"Amiri","Scheherazade New","Noto Naskh Arabic","Geeza Pro","Traditional Arabic","Times New Roman",serif';
const COL_X = { thulathi: 7.6, mulhaq: 0, rubai: -7.6 };
const FLOOR_H = 5;
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

function cardTexture(b) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 240;
  const g = c.getContext('2d');
  g.beginPath(); g.roundRect(6, 6, 500, 228, 34);
  g.fillStyle = b.ten ? NAVY : '#FFFFFF'; g.fill();
  g.lineWidth = 6; g.strokeStyle = b.ten ? NAVY : GOLD; g.stroke();
  g.direction = 'rtl'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillStyle = b.ten ? '#FFFFFF' : NAVY;
  g.font = `112px ${AR}`; g.fillText(b.past, 256, 96);
  g.fillStyle = b.ten ? '#E9D9B8' : '#8A6A2C';
  g.font = `58px ${AR}`; g.fillText(b.model, 256, 190);
  g.direction = 'ltr'; g.textAlign = 'left';
  g.font = '600 30px system-ui, sans-serif'; g.fillText(String(b.n), 26, 40);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}

function labelTexture(text, size, color) {
  const c = document.createElement('canvas'); c.width = 640; c.height = 128;
  const g = c.getContext('2d');
  g.direction = 'rtl'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillStyle = color; g.font = `${size}px ${AR}`; g.fillText(text, 320, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

function sprite(tex, w, h) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
  s.scale.set(w, h, 1); return s;
}

async function start() {
  if (document.fonts && document.fonts.ready) await document.fonts.ready;
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  host.appendChild(renderer.domElement);
  renderer.domElement.setAttribute('aria-hidden', 'true');
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 400);
  const target = new THREE.Vector3(0, 9.3, 0);

  // floors: one per number of letters of the past form
  const floors = [...new Set(data.abwab.map(b => b.letters))].sort();
  const floorY = n => (n - floors[0]) * FLOOR_H;
  for (const n of floors) {
    const slab = new THREE.Mesh(new THREE.BoxGeometry(22, 0.08, 5),
      new THREE.MeshBasicMaterial({ color: GOLD, transparent: true, opacity: 0.22, depthWrite: false }));
    slab.position.set(0, floorY(n), 0); scene.add(slab);
    const edge = new THREE.LineSegments(new THREE.EdgesGeometry(slab.geometry), new THREE.LineBasicMaterial({ color: GOLD }));
    edge.position.copy(slab.position); scene.add(edge);
    const l = sprite(labelTexture(data.ui.floor.replace('{n}', data.ui.digits[n]), 70, '#8A6A2C'), 4.6, 0.92);
    l.position.set(-8.2, floorY(n) - 0.62, 2.5); scene.add(l);
  }
  for (const [key, x] of Object.entries(COL_X)) {
    const l = sprite(labelTexture(data.ui.columns[key], 84, NAVY), 7, 1.4);
    l.position.set(x, floorY(floors.at(-1)) + 3.9, 0); scene.add(l);
    const pillar = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, floorY(floors.at(-1)), 8),
      new THREE.MeshBasicMaterial({ color: NAVY, transparent: true, opacity: 0.25 }));
    pillar.position.set(x, floorY(floors.at(-1)) / 2, -2.4); scene.add(pillar);
  }

  // cards
  const cells = {};
  for (const b of data.abwab) (cells[b.col + b.letters] ??= []).push(b);
  const cards = [];
  for (const list of Object.values(cells)) {
    const rows = Math.ceil(list.length / 2);
    list.forEach((b, i) => {
      const row = Math.floor(i / 2), alone = list.length === 1 || (i === list.length - 1 && i % 2 === 0);
      const s = sprite(cardTexture(b), 2.5, 1.17);
      s.position.set(COL_X[b.col] + (alone ? 0 : (i % 2 ? -1.4 : 1.4)), floorY(b.letters) + 0.8 + row * 1.3, (row - (rows - 1) / 2) * -1.3);
      s.userData = b; scene.add(s); cards.push(s);
      if (b.col === 'mulhaq' && i === 0) {   // the link "attached to" towards the quadriliteral column
        const y = floorY(b.letters) + 0.8;
        const pts = [new THREE.Vector3(-2.9, y, 0), new THREE.Vector3(-4.7, y, 0)];
        scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: NAVY })));
        const tip = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.4, 12), new THREE.MeshBasicMaterial({ color: NAVY }));
        tip.position.set(-4.9, y, 0); tip.rotation.z = Math.PI / 2; scene.add(tip);
      }
    });
  }

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.copy(target); controls.enablePan = false; controls.enableZoom = false;
  controls.minPolarAngle = 1.05; controls.maxPolarAngle = 1.6;
  controls.minAzimuthAngle = -1.15; controls.maxAzimuthAngle = 1.15;
  renderer.domElement.style.touchAction = 'pan-y';

  let dist = 37, tenOnly = false, selected = null, auto = !reduced, t0 = performance.now();
  const place = az => { camera.position.set(target.x + dist * Math.sin(az) * 0.97, target.y + dist * 0.16, target.z + dist * Math.cos(az) * 0.97); camera.lookAt(target); };
  const render = () => renderer.render(scene, camera);
  function resize() {
    const w = host.clientWidth, h = host.clientHeight; renderer.setSize(w, h, false);
    camera.aspect = w / h; dist = 37 / Math.min(1, camera.aspect / 1.08); camera.updateProjectionMatrix();
    place(auto ? 0 : controls.getAzimuthalAngle()); controls.update(); render();
  }
  new ResizeObserver(resize).observe(host);
  controls.addEventListener('change', render);
  (function loop(now) {
    if (!auto) return;
    place(Math.sin((now - t0) / 2600) * 0.42); controls.update(); render(); requestAnimationFrame(loop);
  })(t0);

  function paint() {
    for (const s of cards) {
      const b = s.userData, dim = (tenOnly && !b.ten) || (selected && selected !== b);
      s.material.opacity = dim ? 0.28 : 1;
      const k = selected === b ? 1.22 : 1; s.scale.set(2.5 * k, 1.17 * k, 1);
    }
    render();
  }
  const panel = document.getElementById('viz-detail');
  function show(b) {
    selected = b; paint();
    panel.replaceChildren();
    const add = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; e.textContent = text; panel.appendChild(e); return e; };
    add('div', 'd-num', data.ui.bab + ' ' + b.n + ' · ' + b.group);
    add('div', 'd-pat ar', b.past + ' ' + b.impf);
    add('div', 'd-model ar', data.ui.model + ' ' + b.model + ' ' + b.modelImpf + (b.masdar ? ' · ' + b.masdar : ''));
    add('div', 'd-use ar', data.ui.use + ' ' + b.use);
    const foot = add('div', 'd-foot', '');
    for (const f of b.forms) { const s = document.createElement('span'); s.className = 'form' + (f.ten ? ' ten' : ''); s.textContent = f.id; s.dir = 'ltr'; foot.appendChild(s); }
    const a = document.createElement('a'); a.href = '#bab-' + b.n; a.textContent = data.ui.more + ' (' + b.page + ')'; foot.appendChild(a);
  }
  const ray = new THREE.Raycaster(), p = new THREE.Vector2(); let down = null;
  const hit = e => { const r = renderer.domElement.getBoundingClientRect(); p.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1); ray.setFromCamera(p, camera); return ray.intersectObjects(cards)[0]?.object.userData; };
  renderer.domElement.addEventListener('pointerdown', e => { auto = false; down = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener('pointerup', e => { if (down && Math.hypot(e.clientX - down[0], e.clientY - down[1]) < 6) { const b = hit(e); if (b) show(b); } down = null; });
  renderer.domElement.addEventListener('pointermove', e => { if (!down) renderer.domElement.style.cursor = hit(e) ? 'pointer' : 'grab'; });
  document.getElementById('viz-ten').addEventListener('click', e => { tenOnly = !tenOnly; e.currentTarget.setAttribute('aria-pressed', tenOnly); auto = false; paint(); });
  host.dataset.ready = '1';
  resize();
}

function fail(err) {   // say why instead of hiding the section
  const reason = String(err && err.message || err);
  host.textContent = 'تعذّر عرض المجسّم في هذا المتصفح. الجدول أدناه يحوي المحتوى نفسه. (' + reason + ')';
  host.style.cssText += ';aspect-ratio:auto;padding:1rem;color:#46586A';
  document.querySelector('.vizbar').hidden = true; document.getElementById('viz-detail').hidden = true;
  console.error('abwab3d:', err);
}
try {
  if (!document.createElement('canvas').getContext('webgl2')) throw new Error('WebGL غير متاح');
  start().catch(fail);
} catch (e) { fail(e); }
