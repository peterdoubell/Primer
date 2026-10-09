/* Licensed source-mesh anatomy viewer. Rights and construction differ by manifest. */
(function () {
  "use strict";
  const ATLASES = {
    bodyparts3d: "/app/anatomy/bodyparts3d/",
    "bp3d-sella-4.3": "/app/anatomy/bp3d-sella-4.3/",
    "z-anatomy": "/app/anatomy/msk-atlas/",
    "malaya-mri": "/app/anatomy/msk-mri-knee/",
    "malaya-ankle": "/app/anatomy/msk-mri-ankle/",
    "openknee-oks003": "/app/anatomy/openknee-oks003/",
    "cervical-bones": "/app/anatomy/msk-cervical/",
    "massp2-subcortex": "/app/anatomy/massp2-subcortex/",
    "hvsmr2-pat7": "/app/anatomy/hvsmr2-pat7/",
    "nasalseg-p001": "/app/anatomy/nasalseg-p001/",
    "openear-zeta": "/app/anatomy/openear-zeta/",
    "totalseg-v3-s0358": "/app/anatomy/totalseg-v3-s0358/",
    "totalseg-v3-esophagus-s0358": "/app/anatomy/totalseg-v3-esophagus-s0358/",
    "wt9fc-sub007": "/app/anatomy/wt9fc-sub007/",
    "ispy1-expert1002": "/app/anatomy/ispy1-expert1002/",
    "prostate-biopsy0001": "/app/anatomy/prostate-biopsy0001/",
    "larynx-jasa19629778-phase01": "/app/anatomy/larynx-jasa19629778-phase01/",
    "hra-bladder-female-v1.1": "/app/anatomy/hra-bladder-female-v1.1/",
    "hra-bladder-male-v1.1": "/app/anatomy/hra-bladder-male-v1.1/",
    "fedbca-center1-001": "/app/anatomy/fedbca-center1-001/",
    "fedbca-center2-01": "/app/anatomy/fedbca-center2-01/",
    "fedbca-center3-01": "/app/anatomy/fedbca-center3-01/",
    "fedbca-center4-01": "/app/anatomy/fedbca-center4-01/",
    "verse521": "/app/anatomy/verse521/",
    "liu-lumbosacral-sub03": "/app/anatomy/liu-lumbosacral-sub03/",
  };
  const RANGES = {
    "sella-gross-default": [1518.3900146484375, 1543.3499755859375],
    "gland-source-2011": [1522.5699462890625, 1535.5400390625],
    "gland-source-2014": [1522.6199951171875, 1535.5],
    "optic-reduced-source": [1518.3900146484375, 1543.3499755859375],
    "optic-elongated-source": [1518.3900146484375, 1543.3399658203125],
    "right-ICA-source-2011": [1434.5400390625, 1537.719970703125],
    "right-ICA-source-2014": [1429.06005859375, 1539.219970703125],
    cervical: [150, 157],
    "brain-subcortex": [-25, 35],
    "cardiac-venous-source": [-69.42072296142578, 86.83314514160156],
    "sinonasal-source": [-566, -488],
    "temporal-source": [-2, 78],
    "thyroid-source": [-116.75, 121.5],
    "esophagus-source": [-322.25, 121.5],
    "breast-tumour-source": [-11.71875, 17.28125],
    "prostate-source": [-61.48846435546875, -4.33062744140625],
    "tongue-source": [-106.36968994140625, -49.87583923339844],
    "larynx-phonation-source": [-23.082857131958008, 8.479644298553467],
    "bladder-source": [0, 1],
    "bladder-tumour-source": [-1000, 1000],
    "thoracolumbar-source": [-500, -36],
    "lumbosacral-neural": [-511, -350],
    shoulder: [1140, 1405],
    elbow: [925, 1135],
    hip: [665, 980],
    knee: [250, 500],
    ankle: [-80, 180],
    wrist: [690, 880],
    coronary: [0, 2000],
    prostate: [0, 2000],
    renal: [0, 2000],
    liver: [0, 2000],
    brain: [0, 2000],
  };
  const ALIASES = {
    foot: "ankle",
    hand: "wrist",
    pelvis: "hip",
    heart: "coronary",
    kidney: "renal",
  };
  // A view changes framing only. All source region parts, coordinates and
  // licences remain intact; a narrow ankle acquisition cannot stand in for it.
  function sourceView(options, data, region) {
    if (!options.view) return null;
    if (options.view === "hamstrings") {
      if (options.atlas !== "z-anatomy" || options.family !== "knee"
          || data.coordinate_system?.display_basis !== "native-x-left-y-superior-z-anterior"
          || data.coordinate_system?.unit_meters !== 0.01
          || region.side !== "right" || data.regions.hip?.side !== "right")
        throw new Error("Hamstring framing requires the registered Z-Anatomy muscle source.");
      const muscleIds = ["za-muscles-906368294", "za-muscles-266598907", "za-muscles-312860247", "za-muscles-63886170"];
      const contextIds = ["za-bones-83785534", "za-joints-558314782", "za-nerves-809851269"];
      const divisionIds = ["za-nerves-85997353", "za-nerves-713806063"];
      const framingIds = [...muscleIds, ...contextIds];
      const ids = [...framingIds, ...divisionIds];
      const identities = [
        ["Long head of biceps femoris.r", "muscle"], ["Short head of biceps femoris.r", "muscle"],
        ["Semimembranosus muscle.r", "muscle"], ["Semitendinosus muscle.r", "muscle"],
        ["Hip bone.r", "bone"], ["Sacrotuberous ligament.r", "ligament"], ["Sciatic nerve.r", "nerve"],
        ["Tibial nerve.r", "nerve"], ["Common fibular nerve.r", "nerve"],
      ];
      const parts = ids.map(id => data.parts[id]);
      if (parts.some((p, i) => !p || p.name !== identities[i][0] || p.layer !== identities[i][1]
          || !(i < 4 || i >= 7 ? region.parts.some(r => r.id === ids[i])
          : data.regions.hip?.parts.some(r => r.id === ids[i]))
          || !Array.isArray(p.bounds) || p.bounds.length !== 2
          || p.bounds.some(point => !Array.isArray(point) || point.length !== 3 || !point.every(Number.isFinite))
          || p.bounds[0].some((value, axis) => value > p.bounds[1][axis])))
        throw new Error("All native posterior-thigh muscles and registered pelvic context objects are required.");
      const framingParts = framingIds.map(id => data.parts[id]);
      const focusBounds = [
        [0, 1, 2].map(axis => Math.min(...framingParts.map(p => p.bounds[0][axis])) - 0.5),
        [0, 1, 2].map(axis => Math.max(...framingParts.map(p => p.bounds[1][axis])) + 0.5),
      ];
      return { id: "hamstrings", title: "Adult right posterior thigh", focusBounds,
        range: [focusBounds[0][1], focusBounds[1][1]], camera: { yaw: Math.PI, pitch: 0 },
        boneIds: framingIds, partIds: ids, muscleIds, contextIds, divisionIds, framingIds, initialLayer: "muscle", cropLabel: "Thigh reference extent",
        note: "Four source muscle objects share their original coordinates with the right hip bone, sacrotuberous ligament and separate sciatic, tibial and common fibular nerve objects. No connecting geometry has been invented. Choose Together to inspect relationships; Full structures reveals the tibial nerve beyond the thigh frame. The short head of biceps femoris remains separate. Attachment footprints, tendon volumes, fine aponeuroses, sacral attachment context and nerve fascicular continuity are not established; clinical fidelity remains unverified." };
    }
    if (options.view !== "whole-foot" || options.atlas !== "z-anatomy"
        || (ALIASES[options.family] || options.family) !== "ankle"
        || data.coordinate_system?.display_basis !== "native-x-left-y-superior-z-anterior"
        || data.coordinate_system?.unit_meters !== 0.01)
      throw new Error("The whole-foot view requires the registered Z-Anatomy foot source.");
    const names = new Set([
      "Talus.r", "Calcaneus.r", "Navicular bone.r", "Cuboid bone.r",
      "Medial cuneiform bone.r", "Intermediate cuneiform bone.r", "Lateral cuneiform bone.r",
      "Sesamoid bones of foot.r",
    ]);
    const digits = ["first", "second", "third", "fourth", "fifth"];
    for (const [index, digit] of digits.entries()) {
      names.add(digit[0].toUpperCase() + digit.slice(1) + " metatarsal bone.r");
      for (const level of index ? ["Proximal", "Middle", "Distal"] : ["Proximal", "Distal"])
        names.add(level + " phalanx of " + digit + " finger of foot.r");
    }
    const bones = region.parts.map(part => ({ ...data.parts[part.id], ...part }))
      .filter(part => part.layer === "bone" && !["Tibia.r", "Fibula.r"].includes(part.name));
    if (bones.length !== names.size || new Set(bones.map(part => part.name)).size !== names.size
        || bones.some(part => !names.has(part.name) || !part.bounds?.flat().every(Number.isFinite)))
      throw new Error("The whole-foot view requires every named pedal bone in the source region.");
    const bounds = [
      [0, 1, 2].map(axis => Math.min(...bones.map(part => part.bounds[0][axis]))),
      [0, 1, 2].map(axis => Math.max(...bones.map(part => part.bounds[1][axis]))),
    ];
    // Source units are centimetres. Five millimetres around the complete
    // pedal envelope leaves distal leg context without framing entire shafts.
    const focusBounds = bounds.map((point, end) => point.map(value => value + (end ? 0.5 : -0.5)));
    return { id: "whole-foot", title: "Adult right foot", focusBounds,
      range: [focusBounds[0][1], focusBounds[1][1]],
      camera: { yaw: 0, pitch: Math.PI / 2 },
      boneIds: bones.map(part => part.id),
      note: "Whole-foot framing includes every source tarsal, metatarsal, toe phalanx and the combined hallux sesamoid object. The crop uses their complete source bounds with a 5 mm margin. This adult right-sided surface reference does not supply all plantar plates, tendon sheaths, infection findings or independently validated clinical anatomy.",
    };
  }
  const colors = [
    "#e9d7b5",
    "#b8d9d7",
    "#d8c9a4",
    "#dfb5bd",
    "#9ebfd5",
    "#bcb6da",
    "#acccb9",
    "#dbb388",
  ];
  const manifestPromises = new Map();
  const meshCache = new Map();
  const $ = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  };
  const json = async (url) => {
    const r = await fetch(url);
    if (!r.ok)
      throw new Error("Could not load anatomy data (" + r.status + ").");
    return r.json();
  };
  function manifest(atlas) {
    if (!Object.prototype.hasOwnProperty.call(ATLASES, atlas)) return Promise.reject(new Error("Unknown anatomical atlas."));
    if (!manifestPromises.has(atlas)) manifestPromises.set(atlas,
      json(ATLASES[atlas] + "manifest.json").catch(error => {
        manifestPromises.delete(atlas);
        throw error;
      }));
    return manifestPromises.get(atlas);
  }
  function style() {
    if (document.getElementById("detailed-anatomy-style")) return;
    const s = $("style");
    s.id = "detailed-anatomy-style";
    s.textContent = `
    .detailed-anatomy{margin:1rem 0;border:1px solid var(--border,#344551);border-radius:16px;overflow:hidden;background:#101923;color:#e5edf2}
    .detailed-anatomy-header{padding:1.25rem 1.25rem .85rem;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:start;gap:.6rem}
    .detailed-anatomy h3{margin:0;font-size:1.35rem;color:#f2e9d7}.detailed-anatomy-badge{font:600 .68rem/1.4 system-ui;letter-spacing:.08em;text-transform:uppercase;border:1px solid #507477;border-radius:30px;padding:.35rem .65rem;color:#a8d9d4}
    .detailed-anatomy-instructions{padding:0 1.25rem;margin:0 0 1rem!important;color:#a9b8c6;font-size:.88rem!important;line-height:1.5}
    .detailed-anatomy-toolbar{padding:0 1.25rem .9rem;display:flex;gap:.4rem;flex-wrap:wrap;align-items:center}
    .detailed-anatomy button{min-height:38px;padding:.4rem .7rem;border-radius:7px;background:#192734;border:1px solid #3c5060;color:#e0e8ee;font:500 .8rem/1.4 system-ui;box-shadow:none;cursor:pointer}
    .detailed-anatomy [hidden]{display:none!important}
    .detailed-anatomy button:hover,.detailed-anatomy button[aria-pressed=true]{background:#244451;border-color:#89bebc;color:#fff}
    .detailed-anatomy button:focus-visible,.detailed-anatomy canvas:focus-visible{outline:3px solid #f0bf65;outline-offset:3px}
    .detailed-anatomy-toolbar .detailed-divider{width:1px;height:24px;background:#3b4e5b;margin:0 .3rem}
    .detailed-anatomy-stage{height:480px;position:relative;background:radial-gradient(ellipse at 45% 37%,#263846 0%,#15232f 55%,#0e1821 100%);border-block:1px solid #344754;overflow:hidden}
    .detailed-anatomy canvas{display:block;width:100%;height:100%;touch-action:none;cursor:grab}.detailed-anatomy canvas:active{cursor:grabbing}
    .detailed-anatomy-orientation{position:absolute;top:1rem;left:1rem;pointer-events:none;font:500 .68rem/1.6 system-ui;letter-spacing:.07em;text-transform:uppercase;color:#96afbc}
    .detailed-anatomy-crop-status{position:absolute;top:2.8rem;left:1rem;pointer-events:none;background:#101923e6;color:#c2d4df;padding:.2rem .45rem;border-radius:4px;font:500 .67rem/1.5 system-ui}
    .detailed-anatomy-selected{position:absolute;bottom:1rem;left:1rem;right:1rem;pointer-events:none;display:flex;align-items:center;justify-content:center;gap:.5rem;color:#f0e9db;font:600 .9rem/1.4 system-ui;text-shadow:0 1px 5px #000}
    .detailed-anatomy-status{padding:.85rem 1.25rem;font:.8rem/1.5 system-ui;color:#b2c5cd}.detailed-anatomy-status:empty{display:none}
    .detailed-anatomy-parts{padding:.9rem 1.25rem;display:flex;gap:.4rem;flex-wrap:wrap;border-bottom:1px solid #344754}.detailed-anatomy-parts button{font-size:.72rem;display:flex;gap:.4rem;align-items:center}
    .detailed-anatomy-swatch{width:.55rem;height:.55rem;border-radius:50%;flex-shrink:0}
    .detailed-anatomy-note{padding:.9rem 1.25rem 1.1rem;font:.75rem/1.6 system-ui;color:#a6b7c3}.detailed-anatomy-note p{font:inherit;margin:0 0 .5rem;color:inherit}.detailed-anatomy-note p:last-child{margin:0}.detailed-anatomy-note a{color:#a9d4d6}
    @media(max-width:600px){.detailed-anatomy-stage{height:370px}.detailed-anatomy-header,.detailed-anatomy-parts{padding:1rem}.detailed-anatomy-toolbar{padding:0 1rem .8rem}.detailed-anatomy-toolbar button{flex-grow:1}.detailed-anatomy h3{font-size:1.15rem}.detailed-anatomy-instructions{padding:0 1rem}}
    `;
    document.head.append(s);
  }
  async function readMesh(part) {
    const cacheKey = part.file + ":" + part.sha256;
    if (meshCache.has(cacheKey)) return meshCache.get(cacheKey);
    const task = (async () => {
      const response = await fetch(part.file);
      if (!response.ok) throw new Error("Could not load " + part.name + ".");
      const buffer = await response.arrayBuffer(),
        head = new DataView(buffer);
      if (head.getUint32(0, true) !== 0x44335042)
        throw new Error("Invalid anatomical mesh.");
      const count = head.getUint32(4, true),
        n = head.getUint32(8, true);
      if (buffer.byteLength !== 12 + count * 24 + n * 4)
        throw new Error("Incomplete anatomical mesh.");
      return {
        positions: new Float32Array(buffer, 12, count * 3),
        normals: new Float32Array(buffer, 12 + count * 12, count * 3),
        indices: new Uint32Array(buffer, 12 + count * 24, n),
        count,
      };
    })();
    meshCache.set(cacheKey, task);
    try {
      return await task;
    } catch (e) {
      meshCache.delete(cacheKey);
      throw e;
    }
  }
  function matmul(a, b) {
    const o = new Float32Array(16);
    for (let c = 0; c < 4; c++)
      for (let r = 0; r < 4; r++)
        for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k];
    return o;
  }
  function rotation(x, y) {
    const cx = Math.cos(x),
      sx = Math.sin(x),
      cy = Math.cos(y),
      sy = Math.sin(y);
    return new Float32Array([
      cy,
      sx * sy,
      -cx * sy,
      0,
      0,
      cx,
      sx,
      0,
      sy,
      -sx * cy,
      cx * cy,
      0,
      0,
      0,
      0,
      1,
    ]);
  }
  function viewOrientation(state) {
    const yaw = Math.atan2(Math.sin(state.yaw), Math.cos(state.yaw));
    const near = (a, b) => Math.abs(a - b) < 0.0001;
    if (near(state.pitch, Math.PI / 2)) return "Superior";
    if (near(state.pitch, -Math.PI / 2)) return "Inferior";
    if (near(state.pitch, 0)) {
      if (near(yaw, 0)) return "Anterior";
      if (near(Math.abs(yaw), Math.PI)) return "Posterior";
      if (near(yaw, Math.PI / 2)) return "Right lateral";
      if (near(yaw, -Math.PI / 2)) return "Left lateral";
    }
    return "Rotated view · yaw " + Math.round(yaw * 180 / Math.PI) +
      "° · tilt " + Math.round(state.pitch * 180 / Math.PI) + "°";
  }
  function displayPoint(point, nativeYUp = false, nativeRAS = false) {
    if (nativeYUp) return [...point];
    return nativeRAS ? [-point[0], point[2], point[1]]
      : [point[0], point[2], -point[1]];
  }
  function anatomicalPresets(side) {
    const lateralYaw = side === "left" ? -Math.PI / 2 : Math.PI / 2;
    return [["Anterior", 0, 0], ["Posterior", Math.PI, 0],
      [side === "midline" ? "Right lateral" : "Lateral", lateralYaw, 0], [side === "midline" ? "Left lateral" : "Medial", -lateralYaw, 0],
      ["Superior", 0, Math.PI / 2], ["Inferior", 0, -Math.PI / 2]];
  }
  function shader(gl, type, source) {
    const s = gl.createShader(type);
    gl.shaderSource(s, source);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      const e = gl.getShaderInfoLog(s);
      gl.deleteShader(s);
      throw new Error(e);
    }
    return s;
  }
  function renderer(canvas, parts, range, onView, nativeYUp = false, sourcePreset = null, nativeRAS = false, initialDisplay = {}) {
    const gl = canvas.getContext("webgl", {
      alpha: true,
      antialias: true,
      preserveDrawingBuffer: true,
    });
    if (!gl)
      throw new Error(
        "This browser cannot display WebGL anatomy. The labelled source meshes remain available through the dataset link below.",
      );
    const ext = gl.getExtension("OES_element_index_uint");
    const vert = shader(
      gl,
      gl.VERTEX_SHADER,
      `attribute vec3 aPosition;attribute vec3 aNormal;uniform mat4 uMatrix;uniform mat4 uRotation;uniform vec3 uCenter;uniform float uScale;uniform bool uNativeYUp;uniform bool uNativeRAS;varying vec3 vNormal;varying vec3 vPosition;varying float vSourceZ;vec3 displayPoint(vec3 p){return uNativeYUp?p:(uNativeRAS?vec3(-p.x,p.z,p.y):vec3(p.x,p.z,-p.y));}void main(){vec3 sourcePos=displayPoint(aPosition);vec3 sourceNormal=displayPoint(aNormal);vec3 pos=(sourcePos-uCenter)*uScale;vSourceZ=sourcePos.y;vPosition=(uRotation*vec4(pos,1.0)).xyz;vNormal=mat3(uRotation)*sourceNormal;gl_Position=uMatrix*vec4(pos,1.0);}`,
    );
    const frag = shader(
      gl,
      gl.FRAGMENT_SHADER,
      `precision mediump float;uniform vec3 uColor;uniform float uAlpha;uniform vec2 uClip;varying vec3 vNormal;varying vec3 vPosition;varying float vSourceZ;void main(){if(vSourceZ<uClip.x||vSourceZ>uClip.y)discard;vec3 n=normalize(vNormal);if(!gl_FrontFacing)n=-n;vec3 key=normalize(vec3(-.5,.8,1.2));vec3 fill=normalize(vec3(.8,.2,.4));float diffuse=max(dot(n,key),0.0);float reflected=max(dot(n,fill),0.0);float rim=pow(1.0-abs(n.z),2.8);float spec=pow(max(dot(reflect(-key,n),vec3(0.,0.,1.)),0.),32.);vec3 color=uColor*(.25+.63*diffuse+.23*reflected)+vec3(.13)*rim+vec3(.14)*spec;gl_FragColor=vec4(color,uAlpha);}`,
    );
    const program = gl.createProgram();
    gl.attachShader(program, vert);
    gl.attachShader(program, frag);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS))
      throw new Error("Unable to initialize anatomy rendering.");
    gl.useProgram(program);
    const uniforms = Object.fromEntries(
      [
        "uMatrix",
        "uRotation",
        "uCenter",
        "uScale",
        "uColor",
        "uAlpha",
        "uClip",
        "uNativeYUp",
        "uNativeRAS",
      ].map((x) => [x, gl.getUniformLocation(program, x)]),
    );
    const attrs = {
      position: gl.getAttribLocation(program, "aPosition"),
      normal: gl.getAttribLocation(program, "aNormal"),
    };
    const min = [Infinity, Infinity, Infinity],
      max = [-Infinity, -Infinity, -Infinity];
    function uploadPart(part) {
      const m = part.mesh;
      let sum = [0, 0, 0],
        visible = 0;
      const pmin = [Infinity, Infinity, Infinity],
        pmax = [-Infinity, -Infinity, -Infinity];
      const wholeMin = [Infinity, Infinity, Infinity],
        wholeMax = [-Infinity, -Infinity, -Infinity];
      for (let i = 0; i < m.positions.length; i += 3) {
        const p = displayPoint([m.positions[i], m.positions[i + 1], m.positions[i + 2]], nativeYUp, nativeRAS);
        for (let j = 0; j < 3; j++) {
          wholeMin[j] = Math.min(wholeMin[j], p[j]);
          wholeMax[j] = Math.max(wholeMax[j], p[j]);
        }
        if (p[1] < range[0] || p[1] > range[1]) continue;
        for (let j = 0; j < 3; j++) {
          min[j] = Math.min(min[j], p[j]);
          max[j] = Math.max(max[j], p[j]);
          pmin[j] = Math.min(pmin[j], p[j]);
          pmax[j] = Math.max(pmax[j], p[j]);
          sum[j] += p[j];
        }
        visible++;
      }
      // Long low-resolution source faces may cross the crop even when neither
      // endpoint lies in it. Keep finite conservative bounds in that case.
      const intersectsCrop = wholeMin[1] <= range[1] && wholeMax[1] >= range[0];
      if (!visible && intersectsCrop) {
        for (let j = 0; j < 3; j++) {
          pmin[j] = j === 1 ? Math.max(range[0], wholeMin[j]) : wholeMin[j];
          pmax[j] = j === 1 ? Math.min(range[1], wholeMax[j]) : wholeMax[j];
          min[j] = Math.min(min[j], pmin[j]);
          max[j] = Math.max(max[j], pmax[j]);
        }
      }
      const buffers = [gl.createBuffer(), gl.createBuffer(), gl.createBuffer()];
      gl.bindBuffer(gl.ARRAY_BUFFER, buffers[0]);
      gl.bufferData(gl.ARRAY_BUFFER, m.positions, gl.STATIC_DRAW);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffers[1]);
      gl.bufferData(gl.ARRAY_BUFFER, m.normals, gl.STATIC_DRAW);
      const wide = m.count > 65535;
      if (wide && !ext)
        throw new Error(
          "This device does not support the anatomical mesh resolution.",
        );
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buffers[2]);
      gl.bufferData(
        gl.ELEMENT_ARRAY_BUFFER,
        wide ? m.indices : new Uint16Array(m.indices),
        gl.STATIC_DRAW,
      );
      return {
        ...part,
        buffers,
        indexType: wide ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT,
        center: visible ? sum.map((v) => v / visible) : wholeMin.map((v, j) => (v + wholeMax[j]) / 2),
        bounds: [pmin, pmax],
        wholeBounds: [wholeMin, wholeMax],
        intersectsCrop,
      };
    }
    const loaded = parts.map(uploadPart);
    const fullCenter = min.map((v, i) => (v + max[i]) / 2);
    const state = {
      yaw: sourcePreset?.camera.yaw ?? -0.22,
      pitch: sourcePreset?.camera.pitch ?? 0.1,
      zoom: 1,
      layer: sourcePreset?.initialLayer || initialDisplay.layer || "bone",
      selected: null,
      // Structures a reporting step points to; a user's own selection wins.
      highlight: [],
      isolated: false,
      cropped: initialDisplay.cropped ?? true,
    };
    const focused = () =>
      state.selected ? [state.selected] : state.highlight || [];
    let frame = 0,
      disposed = false;
    const request = () => {
      if (!frame && !disposed) frame = requestAnimationFrame(draw);
    };
    function draw() {
      frame = 0;
      if (disposed) return;
      const ratio = Math.min(window.devicePixelRatio || 1, 2),
        w = Math.max(1, canvas.clientWidth),
        h = Math.max(1, canvas.clientHeight);
      if (
        canvas.width !== Math.round(w * ratio) ||
        canvas.height !== Math.round(h * ratio)
      ) {
        canvas.width = Math.round(w * ratio);
        canvas.height = Math.round(h * ratio);
      }
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.enable(gl.DEPTH_TEST);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.disable(gl.CULL_FACE);
      const focus = focused();
      let visible = loaded.filter(
        (p) => (state.layer === "all" || p.layer === state.layer) && (!state.cropped || p.intersectsCrop),
      );
      if (state.isolated && focus.length)
        visible = visible.filter((p) => focus.includes(p.id));
      const fixedBounds = state.cropped && !state.isolated && ["bone", "all"].includes(state.layer)
        ? sourcePreset?.focusBounds : null;
      const bmin = fixedBounds?.[0] || [0, 1, 2].map((i) =>
          Math.min(...visible.map((p) => (state.cropped ? p.bounds : p.wholeBounds)[0][i])),
        ),
        bmax = fixedBounds?.[1] || [0, 1, 2].map((i) =>
          Math.max(...visible.map((p) => (state.cropped ? p.bounds : p.wholeBounds)[1][i])),
        ),
        center = visible.length
          ? bmin.map((v, i) => (v + bmax[i]) / 2)
          : fullCenter,
        size = Math.max(...bmax.map((v, i) => v - bmin[i])),
        scale = 1.72 / (size || 1);
      const aspect = w / h,
        rot = rotation(state.pitch, state.yaw),
        view = new Float32Array([
          state.zoom / aspect,
          0,
          0,
          0,
          0,
          state.zoom,
          0,
          0,
          0,
          0,
          -0.2,
          0,
          0,
          0,
          0,
          1,
        ]);
      gl.uniformMatrix4fv(uniforms.uMatrix, false, matmul(view, rot));
      gl.uniformMatrix4fv(uniforms.uRotation, false, rot);
      gl.uniform3fv(uniforms.uCenter, center);
      gl.uniform1f(uniforms.uScale, scale);
      gl.uniform2fv(uniforms.uClip, state.cropped ? range : [-1000000, 1000000]);
      gl.uniform1i(uniforms.uNativeYUp, nativeYUp ? 1 : 0);
      gl.uniform1i(uniforms.uNativeRAS, nativeRAS ? 1 : 0);
      // Opaque parts first; dimmed context last, sorted back to front.
      visible.sort((a, b) => {
        const aa = focus.length > 0 && !focus.includes(a.id),
          bb = focus.length > 0 && !focus.includes(b.id);
        return (
          Number(aa) - Number(bb) ||
          rot[2] * a.center[0] +
            rot[6] * a.center[1] +
            rot[10] * a.center[2] -
            (rot[2] * b.center[0] +
              rot[6] * b.center[1] +
              rot[10] * b.center[2])
        );
      });
      for (const p of visible) {
        const dim = focus.length > 0 && !focus.includes(p.id);
        if (p.surface_overlay) {
          gl.enable(gl.POLYGON_OFFSET_FILL);
          gl.polygonOffset(-1, -1);
        } else gl.disable(gl.POLYGON_OFFSET_FILL);
        gl.depthMask(!dim);
        gl.uniform1f(uniforms.uAlpha, dim ? 0.19 : 1);
        gl.uniform3fv(uniforms.uColor, p.color);
        gl.bindBuffer(gl.ARRAY_BUFFER, p.buffers[0]);
        gl.enableVertexAttribArray(attrs.position);
        gl.vertexAttribPointer(attrs.position, 3, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, p.buffers[1]);
        gl.enableVertexAttribArray(attrs.normal);
        gl.vertexAttribPointer(attrs.normal, 3, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, p.buffers[2]);
        gl.drawElements(gl.TRIANGLES, p.mesh.indices.length, p.indexType, 0);
      }
      gl.depthMask(true);
      gl.disable(gl.POLYGON_OFFSET_FILL);
      canvas.dataset.rendered = "true";
      canvas.dataset.layer = state.layer;
      canvas.dataset.cropped = String(state.cropped);
      canvas.dataset.view = state.yaw.toFixed(2) + "," + state.pitch.toFixed(2);
      if (onView) onView(state);
    }
    const pointers = new Map();
    let previous = null;
    canvas.addEventListener("pointerdown", (e) => {
      pointers.set(e.pointerId, [e.clientX, e.clientY]);
      canvas.setPointerCapture(e.pointerId);
      previous = { x: e.clientX, y: e.clientY };
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!pointers.has(e.pointerId)) return;
      const old = [...pointers.values()];
      pointers.set(e.pointerId, [e.clientX, e.clientY]);
      if (pointers.size === 2) {
        const current = [...pointers.values()],
          d0 = Math.hypot(old[0][0] - old[1][0], old[0][1] - old[1][1]),
          d1 = Math.hypot(
            current[0][0] - current[1][0],
            current[0][1] - current[1][1],
          );
        if (d0 > 0)
          state.zoom = Math.min(2.7, Math.max(0.5, (state.zoom * d1) / d0));
      } else if (previous) {
        state.yaw += (e.clientX - previous.x) * 0.009;
        state.pitch = Math.min(
          Math.PI / 2,
          Math.max(-Math.PI / 2, state.pitch + (e.clientY - previous.y) * 0.009),
        );
      }
      previous = { x: e.clientX, y: e.clientY };
      request();
    });
    const end = (e) => {
      pointers.delete(e.pointerId);
      previous = null;
    };
    canvas.addEventListener("pointerup", end);
    canvas.addEventListener("pointercancel", end);
    canvas.addEventListener(
      "wheel",
      (e) => {
        e.preventDefault();
        state.zoom = Math.min(
          2.7,
          Math.max(0.5, state.zoom * Math.exp(-e.deltaY * 0.001)),
        );
        request();
      },
      { passive: false },
    );
    canvas.addEventListener("keydown", (e) => {
      const keys = {
        ArrowLeft: ["yaw", -0.15],
        ArrowRight: ["yaw", 0.15],
        ArrowUp: ["pitch", -0.15],
        ArrowDown: ["pitch", 0.15],
        "+": ["zoom", 0.1],
        "=": ["zoom", 0.1],
        "-": ["zoom", -0.1],
      };
      if (keys[e.key]) {
        e.preventDefault();
        const [key, v] = keys[e.key];
        state[key] += v;
        state.zoom = Math.max(0.5, Math.min(2.7, state.zoom));
        state.pitch = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, state.pitch));
        request();
      }
    });
    const observer = new ResizeObserver(request);
    observer.observe(canvas);
    request();
    return {
      state,
      focused,
      update(values) {
        Object.assign(state, values);
        request();
      },
      addParts(parts) {
        if (disposed) return;
        for (const part of parts) {
          if (!loaded.some(existing => existing.id === part.id)) loaded.push(uploadPart(part));
        }
        request();
      },
      dispose() {
        disposed = true;
        cancelAnimationFrame(frame);
        observer.disconnect();
        for (const p of loaded) for (const b of p.buffers) gl.deleteBuffer(b);
        gl.deleteProgram(program);
        gl.deleteShader(vert);
        gl.deleteShader(frag);
        gl.getExtension("WEBGL_lose_context")?.loseContext();
      },
    };
  }
  function render(options = {}) {
    const family = ALIASES[options.family] || options.family;
    if (!RANGES[family]) return null;
    const atlas = options.atlas || "bodyparts3d";
    if (!Object.prototype.hasOwnProperty.call(ATLASES, atlas)) return null;
    style();
    const root = $("section", "detailed-anatomy");
    root.dataset.family = family;
    root.dataset.atlas = atlas;
    root.setAttribute("aria-label", "Detailed anatomical model");
    const header = $("div", "detailed-anatomy-header"),
      title = $("h3", null, "3D anatomical atlas"),
      badge = $("span", "detailed-anatomy-badge", "Source anatomical meshes");
    header.append(title, badge);
    if (options.populationNote) {
      const population = $("p", "detailed-anatomy-instructions", options.populationNote);
      population.setAttribute("role", "note");
      header.append(population);
    }
    const instructions = $(
      "p",
      "detailed-anatomy-instructions",
      "Rotate to inspect the anatomy. Select a structure to highlight it; switch layers or isolate the selection. Drag, pinch or scroll to explore. Arrow keys rotate; + and − zoom.",
    );
    const toolbar = $("div", "detailed-anatomy-toolbar");
    toolbar.setAttribute("aria-label", "Anatomy view controls");
    const stage = $("div", "detailed-anatomy-stage"),
      canvas = $("canvas");
    canvas.tabIndex = 0;
    canvas.setAttribute(
      "aria-label",
      "Interactive 3D anatomy. Arrow keys rotate; plus and minus zoom.",
    );
    const orientation = $(
        "div",
        "detailed-anatomy-orientation",
        "Loading anatomical orientation…",
      ),
      selected = $("div", "detailed-anatomy-selected"),
      cropStatus = $("div", "detailed-anatomy-crop-status", "Cropped to region");
    stage.append(canvas, orientation, cropStatus, selected);
    const status = $(
      "div",
      "detailed-anatomy-status",
      "Loading anatomical meshes…",
    );
    status.setAttribute("role", "status");
    const partsUI = $("div", "detailed-anatomy-parts");
    partsUI.setAttribute("aria-label", "Anatomical structures");
    const note = $("div", "detailed-anatomy-note");
    note.innerHTML =
      '<p>Registered surface anatomy from an adult male reference model. Bone shapes and spatial relationships come from the source dataset. Shafts and neighbouring structures are cropped to the selected region. Colours distinguish structures.</p><p>This surface atlas does not depict every ligament, labrum, meniscus, articular cartilage layer or MRI finding. Use the clinical images alongside the model.</p><p><a href="https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html" target="_blank" rel="noopener noreferrer">BodyParts3D</a>, © The Database Center for Life Science · <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener noreferrer">CC BY 4.0</a>. Selected polygon-reduced source meshes; display normals recalculated. <a href="/app/anatomy/bodyparts3d/manifest.json" target="_blank" rel="noopener noreferrer">Mesh provenance</a>.</p>';
    if (atlas !== "bodyparts3d") note.replaceChildren($("p", null,
      "Loading this source's own construction, licence and limitations. Registered geometry is not clinical or complete anatomical approval."));
    root.append(header, instructions, toolbar, stage, status, partsUI, note);
    let engine = null,
      cancelled = false;
    let wasConnected = root.isConnected;
    const cleanup = new MutationObserver(() => {
      if (root.isConnected) wasConnected = true;
      else if (wasConnected) root.dispose();
    });
    cleanup.observe(document.body, { childList: true, subtree: true });
    root.dispose = () => {
      cancelled = true;
      cleanup.disconnect();
      engine?.dispose();
    };
    // Reporting steps point at the structures they concern. Requests made while
    // meshes are still loading are applied once the model is ready.
    let applyHighlight = null,
      pendingHighlight = null;
    root.highlight = (ids) => {
      const wanted = Array.isArray(ids)
        ? ids.filter((id) => typeof id === "string")
        : [];
      if (applyHighlight) applyHighlight(wanted);
      else pendingHighlight = wanted;
    };
    function button(label, action, pressed) {
      const b = $("button", null, label);
      b.type = "button";
      if (pressed !== undefined)
        b.setAttribute("aria-pressed", String(pressed));
      b.addEventListener("click", action);
      return b;
    }
    manifest(atlas)
      .then(async (data) => {
        const region = data.regions[family];
        if (!region) throw new Error("No anatomical mesh set for this region.");
        const view = sourceView({ ...options, atlas }, data, region);
        title.textContent = (view?.title || region.title) + " · 3D anatomy";
        if (view) {
          root.dataset.viewPreset = view.id;
          root.dataset.cropRange = JSON.stringify(view.range);
          root.dataset.focusBounds = JSON.stringify(view.focusBounds);
          root.dataset.focusPartIds = JSON.stringify(view.boneIds);
        }
        if (data.viewer_notes) {
          note.replaceChildren();
          for (const text of data.viewer_notes) note.append($("p", null, text));
          const credit = $("p");
          const sourceLink = $("a", null, data.dataset);
          sourceLink.href = data.source_url;
          sourceLink.target = "_blank";
          sourceLink.rel = "noopener noreferrer";
          const licenseLink = $("a", null, data.license);
          licenseLink.href = data.license_url;
          licenseLink.target = "_blank";
          licenseLink.rel = "noopener noreferrer";
          credit.append(sourceLink, document.createTextNode(" · "), licenseLink);
          note.append(credit);
        }
        if (view) note.prepend($("p", null, view.note));
        if (
          atlas === "bodyparts3d" && !["shoulder", "elbow", "hip", "knee", "ankle", "wrist"].includes(
            family,
          )
        ) {
          note.firstElementChild.textContent =
            "Registered surface anatomy from an adult male reference model. Organ shapes and spatial relationships come from the source dataset. Colours distinguish structures.";
          note.children[1].textContent =
            family === "prostate"
              ? "The source provides the external prostate surface and neighbouring organs. It does not resolve peripheral / transition zones, urethra, neurovascular bundles or PI-RADS lesions."
              : family === "brain"
                ? "The cerebral hemispheres include source surface and internal components. Ventricles are separate selectable structures. This model does not simulate disease or MRI signal."
                : "Only the labelled source structures are included. This reference anatomy does not simulate disease, flow or contrast enhancement.";
        }
        const initialLayer = view?.initialLayer || options.initialLayer || "bone";
        const initialCropped = options.initialCropped ?? true;
        if (!region.parts.some(p => (p.layer || data.parts[p.id]?.layer) === initialLayer))
          throw new Error("Requested initial tissue layer is unavailable in this source.");
        const loaded = (view?.partIds ? view.partIds.map(id => ({ id })) : region.parts).flatMap(p => {
          const source = { ...data.parts[p.id], ...p };
          // Reviewed native disconnected components replace their combined
          // display entry. The original parent remains in provenance only;
          // rendering both would duplicate overlapping anatomical surfaces.
          return source.components?.length ? source.components : [source];
        }).map((p, i) => ({
            ...p,
            color: (p.color || colors[i % colors.length])
              .match(/\w\w/g)
              .map((x) => parseInt(x, 16) / 255),
          }));
        const initialParts = await Promise.all(loaded
          .filter(p => !region.lazy_layers || p.layer === initialLayer)
          .map(async p => ({ ...p, mesh: await readMesh(p) })));
        if (cancelled) return;
        const labels = new Map();
        const displayName = (name) =>
          region.side === "right" ? name.replace(/^right /, "").replace(/\.r$/, "") : name;
        const nativeYUp = ["native-x-left-y-superior-z-anterior", "native-gltf-y-up"].includes(data.coordinate_system?.display_basis);
        const nativeRAS = data.coordinate_system?.display_basis === "native-ras-to-x-left-y-superior-z-anterior";
        engine = renderer(canvas, initialParts, view?.range || region.source_up_range || RANGES[family], (state) => {
          orientation.textContent =
            (region.side === "right" ? "Right side" : region.side) +
            " · " +
            (region.source_coordinate_cameras ? "Source coordinates · yaw " + Math.round(state.yaw * 180 / Math.PI) + "° · tilt " + Math.round(state.pitch * 180 / Math.PI) + "°" : viewOrientation(state));
          cropStatus.textContent = state.cropped ? (view?.cropLabel || (view ? "Whole-foot region" : "Cropped to region")) : (region.uncropped_label || "Uncropped source");
          const focus = state.selected ? [state.selected] : state.highlight;
          for (const [id, el] of labels) {
            el.setAttribute("aria-pressed", String(focus.includes(id)));
            el.hidden =
              state.layer !== "all" &&
              loaded.find((p) => p.id === id).layer !== state.layer;
          }
          selected.textContent = loaded
            .filter((p) => focus.includes(p.id))
            .map((p) => displayName(p.name))
            .join(" · ");
          root.dataset.highlight = focus.join(",");
          root.dispatchEvent(new CustomEvent("anatomy-selection", { detail: { partIds: focus.slice() } }));
        }, nativeYUp, view, nativeRAS, { layer: initialLayer, cropped: initialCropped });
        const presets = region.source_coordinate_cameras ? [["Source view A",0,0],["Source view B",Math.PI,0],["Source view C",Math.PI/2,0],["Source view D",-Math.PI/2,0],["Source tilt +90°",0,Math.PI/2],["Source tilt −90°",0,-Math.PI/2]] : anatomicalPresets(region.side);
        for (const [label, yaw, pitch] of presets)
          toolbar.append(
            button(label, () => {
              engine.update({ yaw, pitch });
            }),
          );
        toolbar.append($("span", "detailed-divider"));
        const layerButtons = new Map();
        const showLayer = (value) => {
          for (const [v, el] of layerButtons)
            el.setAttribute("aria-pressed", String(v === value));
        };
        let layerRequest = 0;
        const layers = (region.layers || [
          ["bone", region.labels?.[0] || "Bones"],
          ["soft", region.labels?.[1] || "Soft tissue"],
        ]).filter(([value]) => !view?.partIds || loaded.some(p => p.layer === value));
        for (const [value, label] of [...layers, ["all", "Together"]]) {
          const b = button(
            label,
            async () => {
              const request = ++layerRequest;
              if (region.lazy_layers) {
                status.textContent = "Loading " + label.toLowerCase() + " source geometry…";
                try {
                  const added = await Promise.all(loaded.filter(p => value === "all" || p.layer === value)
                    .map(async p => ({ ...p, mesh: await readMesh(p) })));
                  if (cancelled || request !== layerRequest) return;
                  engine.addParts(added);
                } catch (error) {
                  if (!cancelled && request === layerRequest) status.textContent = error.message;
                  return;
                }
              }
              engine.update({ layer: value, selected: null, highlight: [], isolated: false });
              for (const [v, el] of layerButtons)
                el.setAttribute("aria-pressed", String(v === value));
              isolate.setAttribute("aria-pressed", "false");
              status.textContent = "";
            },
            value === initialLayer,
          );
          layerButtons.set(value, b);
          toolbar.append(b);
        }
        const isolate = button(
          "Isolate",
          () => {
            if (!engine.focused().length) {
              status.textContent =
                "Select a labelled structure below, then choose Isolate.";
              return;
            }
            const value = !engine.state.isolated;
            engine.update({ isolated: value, cropped: value ? false : engine.state.cropped });
            fullStructures.setAttribute("aria-pressed", String(!engine.state.cropped));
            isolate.setAttribute("aria-pressed", String(value));
          },
          false,
        );
        const fullStructures = button("Full structures", () => {
          const cropped = !engine.state.cropped;
          engine.update({ cropped });
          fullStructures.setAttribute("aria-pressed", String(!cropped));
        }, !initialCropped);
        toolbar.append(
          isolate,
          fullStructures,
          button("Reset", () => {
            layerRequest++;
            engine.update({
              yaw: view?.camera.yaw ?? -0.22,
              pitch: view?.camera.pitch ?? 0.1,
              zoom: 1,
              selected: null,
              highlight: [],
              isolated: false,
              layer: initialLayer,
              cropped: initialCropped,
            });
            showLayer(initialLayer);
            isolate.setAttribute("aria-pressed", "false");
            fullStructures.setAttribute("aria-pressed", String(!initialCropped));
            status.textContent = "";
          }),
        );
        for (const [i, p] of loaded.entries()) {
          const b = button(
            displayName(p.name),
            () => {
              engine.update({
                selected: engine.state.selected === p.id ? null : p.id,
                highlight: [],
              });
              status.textContent = "";
            },
            false,
          );
          const swatch = $("span", "detailed-anatomy-swatch");
          swatch.style.background = p.color.map(c => Math.round(c * 255)).reduce((s, c) => s + c.toString(16).padStart(2, "0"), "#");
          b.prepend(swatch);
          b.dataset.part = p.id;
          labels.set(p.id, b);
          partsUI.append(b);
        }
        applyHighlight = (ids) => {
          const parts = loaded.filter((p) => ids.includes(p.id));
          const layers = new Set(parts.map((p) => p.layer));
          const layer = !parts.length
            ? engine.state.layer
            : layers.size === 1
              ? parts[0].layer
              : "all";
          engine.update({
            highlight: parts.map((p) => p.id),
            selected: null,
            isolated: false,
            layer,
          });
          showLayer(layer);
          isolate.setAttribute("aria-pressed", "false");
        };
        if (pendingHighlight) applyHighlight(pendingHighlight);
        status.textContent = "";
        root.dataset.ready = "true";
        root.dataset.meshes = String(loaded.length);
        root.dataset.triangles = String(
          loaded.reduce((n, p) => n + p.triangles, 0),
        );
      })
      .catch((error) => {
        status.textContent =
          error.message ||
          "Anatomy could not be loaded. Open the credited dataset below.";
        stage.hidden = true;
        root.dataset.error = "true";
      });
    return root;
  }
  window.PrimerDetailedAnatomy = {
    render,
    supported: (family) => !!RANGES[ALIASES[family] || family],
    families: Object.keys(RANGES),
    viewOrientation,
    sourceView,
    displayPoint,
    anatomicalPresets,
  };
})();
