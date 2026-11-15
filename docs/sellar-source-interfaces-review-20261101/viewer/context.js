import {sha, decode, verified} from './transport.js';

const EXPECTED = '0bb1c06120f6b358a1d44391da64cfcf5bd2820aa2164560afe2159b3c276db4';
const ATLASES = new Set(['spl-nac-limbic', 'spl-nac-reporting', 'spl-additional-source']);
const IDENTITY = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]];

export function installContext(gl, redraw) {
  const status = document.getElementById('context-status');
  let configPromise, program, uniforms, attribute, epoch = 0, generation = 0;
  let current = [], lastCamera = null;
  const cache = new Map();

  async function fetchBytes(url, maximum) {
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 45000);
    try {
      const response = await fetch(url, {signal: controller.signal, credentials: 'same-origin'});
      if (!response.ok) throw Error('Source context request returned HTTP ' + response.status);
      const reader=response.body.getReader(),chunks=[];let total=0;
      try {
        while(true){const {value,done}=await reader.read();if(done)break;total+=value.length;
          if(total>maximum)throw Error('Source context exceeds declared bounds');chunks.push(value);}
      } finally {await reader.cancel();}
      const bytes=new Uint8Array(total);let offset=0;
      for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
      return bytes;
    } finally {clearTimeout(timer);}
  }

  async function configuration() {
    if (configPromise) return configPromise;
    configPromise = (async () => {
      const bytes = await fetchBytes('context-source.json', 4*1024*1024);
      if (await sha(bytes) !== EXPECTED) throw Error('Source context metadata identity differs');
      const data = JSON.parse(new TextDecoder().decode(bytes));
      if (data.schemaVersion !== 1 || data.sourceCommit !== 'bec24db25aad5f7600e2df3becfb1f883e61ff56' ||
          data.clinicalApproval !== false || data.sourceCoordinatesFitted !== false ||
          data.meshes.length !== 21 || new Set(data.meshes.map(r => r.code)).size !== 21) throw Error('Source context scope differs');
      for (const [atlas, row] of Object.entries(data.sourceManifests)) {
        if (!ATLASES.has(atlas) || row.file !== '/app/anatomy/' + atlas + '/manifest.json') throw Error('Source context address differs');
        const originalBytes = await fetchBytes(row.file,4*1024*1024);
        if (await sha(originalBytes) !== row.sha256) throw Error('Original source metadata changed');
        const original = JSON.parse(new TextDecoder().decode(originalBytes));
        for (const mesh of data.meshes.filter(r => r.sourceAtlas === atlas)) {
          const {sourceAtlas, ...fields} = mesh;
          const expected = original.labelMeshes.find(r => r.code === mesh.code);
          if (JSON.stringify(fields) !== JSON.stringify(expected)) throw Error('Source context descriptor changed');
        }
      }
      for (const row of data.meshes) {
        if (!ATLASES.has(row.sourceAtlas) || !/^label-\d+\.mesh\.gz$/.test(row.file) ||
            row.positionsAlreadyRAS !== true || row.coordinateSystem !== 'RAS' || row.spaceUnits !== 'mm' ||
            JSON.stringify(row.sourceAffine) !== JSON.stringify(IDENTITY)) throw Error('Source context geometry convention differs');
      }
      return data;
    })().catch(error => { configPromise = null; throw error; });
    return configPromise;
  }

  function setup() {
    if (!gl) return;
    const vertex = `#version 300 es
in vec3 position;uniform vec3 center,basisRight,basisUp,basisDepth;uniform float radius,aspect;out vec3 p;
void main(){vec3 q=position-center,b=vec3(q.x,q.z,-q.y);p=vec3(dot(basisRight,b),dot(basisUp,b),dot(basisDepth,b));gl_Position=vec4(p.x/(radius*aspect),p.y/radius,-p.z/(4.0*radius),1.0);}`;
    const fragment = `#version 300 es
precision highp float;in vec3 p;uniform vec3 tint;out vec4 color;
void main(){vec3 n=normalize(cross(dFdx(p),dFdy(p)));float light=.48+.52*abs(dot(n,normalize(vec3(.3,.5,1.0))));color=vec4(tint*light,.15);}`;
    program = gl.createProgram();
    for (const [type, text] of [[gl.VERTEX_SHADER, vertex], [gl.FRAGMENT_SHADER, fragment]]) {
      const shader = gl.createShader(type); gl.shaderSource(shader, text); gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw Error('Source context shader unavailable');
      gl.attachShader(program, shader); gl.deleteShader(shader);
    }
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw Error('Source context program unavailable');
    attribute = gl.getAttribLocation(program, 'position');
    uniforms = Object.fromEntries(['center','basisRight','basisUp','basisDepth','radius','aspect','tint'].map(k => [k, gl.getUniformLocation(program,k)]));
  }

  async function load(code) {
    if (cache.has(code)) return cache.get(code);
    const startingEpoch = epoch;
    const pending = (async () => {
      const config = await configuration(), row = config.meshes.find(r => r.code === code);
      if (!row) throw Error('Selected class has no source context');
      const packed = await fetchBytes('/app/anatomy/' + row.sourceAtlas + '/' + row.file,Math.max(row.byteLength,row.gzipBytes));
      const identity = await sha(packed);
      const raw = identity === row.decodedSHA256 ? await verified(packed,row.byteLength,row.decodedSHA256)
        : await verified(packed,row.gzipBytes,row.gzipSHA256).then(p => decode(p,row.byteLength,row.decodedSHA256));
      const view = new DataView(raw.buffer,raw.byteOffset,raw.byteLength), n = view.getUint32(4,true), t = view.getUint32(8,true);
      if (String.fromCharCode(...raw.slice(0,4)) !== 'HVX1' || n !== row.vertexCount || t !== row.triangleCount ||
          view.getUint32(12,true) !== 0 || raw.length !== 16+n*12+t*12) throw Error('Source context layout differs');
      const xyz = new Float32Array(n*3), indices = new Uint32Array(t*3);
      for (let i=0;i<xyz.length;i++) xyz[i]=view.getFloat32(16+i*4,true);
      for (let i=0;i<indices.length;i++) indices[i]=view.getUint32(16+n*12+i*4,true);
      if (xyz.some(v=>!Number.isFinite(v)) || indices.some(v=>v>=n) ||
          await sha(xyz) !== row.positionByteSHA256 || await sha(indices) !== row.indexByteSHA256) throw Error('Source context vectors or indices differ');
      const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
      for(let i=0;i<n;i++)for(let a=0;a<3;a++){lo[a]=Math.min(lo[a],xyz[i*3+a]);hi[a]=Math.max(hi[a],xyz[i*3+a]);}
      if (startingEpoch !== epoch || gl.isContextLost()) throw Error('Superseded source context');
      const positions=gl.createBuffer(),elements=gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER,positions);gl.bufferData(gl.ARRAY_BUFFER,xyz,gl.STATIC_DRAW);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,elements);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,indices,gl.STATIC_DRAW);
      if(gl.getError()!==gl.NO_ERROR){gl.deleteBuffer(positions);gl.deleteBuffer(elements);throw Error('Source context upload failed');}
      return {row,positions,indices:elements,triangles:t,bounds:[lo,hi],epoch:startingEpoch};
    })();
    cache.set(code,pending);
    pending.catch(()=>{if(cache.get(code)===pending)cache.delete(code);});
    return pending;
  }

  async function select(group) {
    const ticket=++generation;
    document.getElementById('retry-context').disabled=true;
    current=[];delete status.dataset.ready;
    if (!group) {status.textContent='Choose a source pair to inspect its complete source-label context.';document.getElementById('retry-context').disabled=false;redraw();return;}
    if (!gl) {status.textContent='3D source context requires WebGL 2.';return;}
    status.textContent='Loading complete source-label boundaries…';
    try {
      const meshes=await Promise.all([load(group.firstCode),load(group.secondCode)]);
      if(ticket!==generation)return;
      current=meshes;status.dataset.ready=group.firstCode+':'+group.secondCode;
      status.textContent='Complete provided source-label boundaries; all components retained. Transparent context shows spatial relationships, not independently validated biological borders.';
      redraw();
    } catch(error) {if(ticket===generation){status.textContent=error.message+'; use Retry source context.';redraw();}}
    finally {if(ticket===generation)document.getElementById('retry-context').disabled=false;}
  }

  function bounds() {
    if(current.length!==2)return null;
    return [current[0].bounds[0].map((v,i)=>Math.min(v,current[1].bounds[0][i])),
      current[0].bounds[1].map((v,i)=>Math.max(v,current[1].bounds[1][i]))];
  }

  function draw(camera) {
    if(!gl||!program||!current.length||gl.isContextLost())return;
    lastCamera=camera;gl.useProgram(program);
    for(const key of ['center','basisRight','basisUp','basisDepth'])gl.uniform3fv(uniforms[key],camera[key]);
    for(const key of ['radius','aspect'])gl.uniform1f(uniforms[key],camera[key]);
    gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);gl.disable(gl.CULL_FACE);
    for(const [i,mesh]of current.entries()){
      gl.uniform3fv(uniforms.tint,i===0?[100/255,160/255,240/255]:[1,128/255,0]);
      gl.bindBuffer(gl.ARRAY_BUFFER,mesh.positions);gl.vertexAttribPointer(attribute,3,gl.FLOAT,false,0,0);gl.enableVertexAttribArray(attribute);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,mesh.indices);gl.drawElements(gl.TRIANGLES,mesh.triangles*3,gl.UNSIGNED_INT,0);
    }
    gl.depthMask(true);gl.disable(gl.BLEND);
  }

  function lost() {++epoch;++generation;current=[];cache.clear();program=null;delete status.dataset.ready;}
  function restored() {setup();}
  setup();
  return {select,bounds,draw,lost,restored,get current(){return current;},get cache(){return cache;},get program(){return program;},get lastCamera(){return lastCamera;}};
}
