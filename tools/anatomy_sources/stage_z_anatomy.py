#!/usr/bin/env python3
"""Stage selected Z-Anatomy meshes in their native common world coordinates.

No asset is published. Model names and source-defined material regions are
whitelisted explicitly. The source's .j/.i labels and insertion markers are
not anatomy and are never selected as bones.
"""
import hashlib, json, pathlib, subprocess, struct

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = pathlib.Path('/tmp/primer-msk-sources')
OUT = CACHE / 'staged'
SOURCES = {'bones':'SkeletalSystem100','joints':'Joints100','muscles':'MuscularSystem100','nerves':'NervousSystem100'}
JOINT_GROUPS = {
 'shoulder':['Glenohumeral joint.g','Acromioclavicular joint.g','Fibrous joints of pectoral girdle.g'],
 'elbow':['Elbow joint.g','Radio-ulnar syndesmoses.g'],
 'wrist':['Distal radio-ulnar joint.g','Radiocarpal joint.g','Intercarpal joints.g','Carpometacarpal joints.g','Intermetacarpal joints.g','Metacarpophalangeal joints.g','Interphalangeal joints of hand.g'],
 'hip':['Hip joint.g','Sacro-iliac joint.g','Fibrous joints of pelvic girdle.g'],
 'knee':['Knee joint.g','Superior tibiofibular joint.g'],
 'ankle':['Tibiofibular syndesmosis.g','Medial collateral ligament of ankle.g','Lateral collateral ligament of ankle.g','Intertarsal joints.g','Tarsometatarsal joints.g','Intermetatarsal joints.g','Metatarsophalangeal joints.g','Interphalangeal joints of foot.g'],
}
BONES = {
 'shoulder':['Scapula.r','Clavicle.r','Humerus.r'],
 'elbow':['Humerus.r','Radius.r','Ulna.r'],
 'wrist':['Radius.r','Ulna.r','Scaphoid bone.r','Lunate bone.r','Triquetrum bone.r','Pisiform bone.r','Trapezium bone.r','Trapezoid bone.r','Capitate bone.r','Hamate bone.r'],
 'hip':['Hip bone.r','Sacrum','Femur.r'],
 'knee':['Femur.r','Tibia.r','Fibula.r','Patella.r'],
 'ankle':['Tibia.r','Fibula.r','Talus.r','Calcaneus.r','Navicular bone.r','Cuboid bone.r','Medial cuneiform bone.r','Intermediate cuneiform bone.r','Lateral cuneiform bone.r','Sesamoid bones of foot.r'],
}
MUSCLES = {
 'shoulder':['Supraspinatus muscle.r','Infraspinatus muscle.r','Subscapularis muscle.r','Teres minor muscle.r','Teres major muscle.r','Long head of biceps brachii.r','Short head of biceps brachii.r','Intertubercular tendon sheath.r','Acromial part of deltoid muscle.r','Clavicular part of deltoid muscle.r','Scapular spinal part of deltoid muscle.r','Subacromial bursa.r','Subdeltoid bursa.r','Subcoracoid bursa.r'],
 'elbow':['Long head of biceps brachii.r','Short head of biceps brachii.r','Medial head of triceps brachii.r','Lateral head of triceps brachii.r','Long head of triceps brachii.r','Brachialis muscle.r','Brachioradialis muscle.r','Anconeus muscle.r','Supinator.r','Superficial head of pronator teres.r','Deep head of pronator teres.r','Humeral head of flexor carpi ulnaris.r','Ulnar head of flexor carpi ulnaris.r','Flexor carpi radialis.r','Extensor carpi radialis longus.r','Extensor carpi radialis brevis.r','Bicipitoradial bursa.r','Subtendinous bursa of triceps brachii muscle.r'],
 'wrist':['Flexor retinaculum of wrist.r','Extensor retinaculum of wrist.r','Flexor carpi radialis.r','Humeral head of flexor carpi ulnaris.r','Ulnar head of flexor carpi ulnaris.r','Humero-ulnar head of flexor digitorum superficialis.r','Radial head of flexor digitorum superficialis.r','Flexor digitorum profundus.r','Flexor pollicis longus.r','Palmaris longus muscle.r','Extensor digitorum.r','Ulnar head of extensor carpi ulnaris.r','Humeral head of extensor carpi ulnaris.r','Extensor carpi radialis longus.r','Extensor carpi radialis brevis.r','Extensor digiti minimi.r','Abductor pollicis longus.r','Extensor indicis.r','Extensor pollicis brevis.r','Extensor pollicis longus.r','Common flexor tendon sheath.r','Tendon sheath of flexor carpi radialis.r','Tendon sheath of flexor pollicis longus.r','Tendon sheath of extensor carpi ulnaris.r','Tendon sheath of extensors carpi radialis.r','Tendon sheath of extensor pollicis longus.r','Tendon sheath of extensor digitorum and extensor indicis.r','Tendon sheath - abd. pollicis longus - ext. pollicis brevis.r','Palmar aponeurosis.r'],
 'hip':['Gluteus medius muscle.r','Gluteus minimus muscle.r','Gluteus maximus muscle.r','Iliacus muscle.r','Psoas major.r','Rectus femoris muscle.r','Sartorius muscle.r','Tensor fasciae latae.r','Piriformis muscle.r','Quadratus femoris muscle.r','Obturator internus.r','Obturator externus.r','Superior gemellus muscle.r','Inferior gemellus muscle.r','Pectineus muscle.r','Adductor longus.r','Adductor brevis.r','Adductor magnus.r','Trochanteric bursa of gluteus medius muscle.r','Trochanteric bursa of gluteus minimus muscle.r','(Iliopectineal bursa).r'],
 'knee':['Rectus femoris muscle.r','Vastus medialis muscle.r','Vastus lateralis muscle.r','Vastus intermedius muscle.r','Sartorius muscle.r','Gracilis muscle.r','Semimembranosus muscle.r','Semitendinosus muscle.r','Long head of biceps femoris.r','Short head of biceps femoris.r','Popliteus muscle.r','Medial head of gastrocnemius.r','Lateral head of gastrocnemius.r','Iliotibial tract.r','Medial patellar retinaculum.r','Lateral patellar retinaculum.r','Suprapatellar bursa.r','Anserine bursa.r','Deep infrapatellar bursa.r','Subcutaneous prepatellar bursa.r','Semimembranosus bursa.r'],
 'ankle':['Calcaneal tendon.r','Tibialis posterior muscle.r','Tibialis anterior muscle.r','Fibularis longus muscle.r','Fibularis brevis muscle.r','Fibularis tertius muscle.r','Flexor hallucis longus.r','Flexor digitorum longus.r','Extensor hallucis longus.r','Extensor digitorum longus.r','Tendon of extensor digitorum longus.r','Superior extensor retinaculum of ankle.r','Inferior extensor retinaculum of ankle.r','Flexor retinaculum of ankle.r','Superior fibular retinaculum.r','Inferior fibular retinaculum.r','Plantar aponeurosis.r','Tendon sheath of tibialis anterior.r','Tendon sheath of tibialis posterior muscle.r','Tendon sheath of flexor hallucis longus.r','Tendon sheath of flexor digitorum longus.r','Tendon sheath of extensor hallucis longus.r','Tendon sheath of extensor digitorum longus.r','Common tendon sheath of fibularis muscles.r','Plantar tendon sheath of fibularis longus muscle.r','Subcutaneous calcaneal bursa.r','Subtendinous calcaneal bursa.r'],
}
NERVES = {
 'shoulder':['Axillary nerve.r','Suprascapular nerve.r','Musculocutaneous nerve.r'],
 'elbow':['Median nerve.r','Radial nerve.r','Ulnar nerve.r','Deep branch of radial nerve.r','Superficial branch of radial nerve.r'],
 'wrist':['Median nerve.r','Ulnar nerve.r','Superficial branch of radial nerve.r','Deep branch of ulnar nerve.r','Superficial branch of ulnar nerve.r','Palmar branch of median nerve.r'],
 'hip':['Sciatic nerve.r','Femoral nerve.r','Obturator nerve.r','Superior gluteal nerve.r','Inferior gluteal nerve.r'],
 'knee':['Tibial nerve.r','Common fibular nerve.r','Saphenous nerve.r'],
 'ankle':['Tibial nerve.r','Superficial fibular nerve.r','Deep fibular nerve.r','Sural nerve.r','Medial plantar nerve.r','Lateral plantar nerve.r'],
}
FOCUS = {
 'shoulder':['Glenoid labrum.r','Articular capsule of glenohumeral joint.r'],
 'elbow':['Articular capsule of elbow joint.r'],
 'wrist':['Articular capsule of radiocarpal joint.r','Articular disc of distal radio-ulnar joint.r'],
 'hip':['Acetabular labrum.r','Articular capsule of hip joint.r'],
 'knee':['Articular capsule of knee joint.r','Medial meniscus.r','Lateral meniscus.r'],
 'ankle':['Anterior talofibular ligament.r','Posterior talofibular ligament.r','Calcaneofibular ligament.r','Posterior tibiotalar ligament.r','Tibiocalcaneal ligament.r','Tibionavicular ligament.r'],
}

def union(items):
 return [[min(x['bounds'][0][a] for x in items) for a in range(3)],[max(x['bounds'][1][a] for x in items) for a in range(3)]]

def main():
 OUT.mkdir(exist_ok=True)
 inventories={c:json.loads((CACHE/(c+'-world-inventory.json')).read_text()) for c in SOURCES}
 selection={c:{} for c in SOURCES};missing=[]
 for region,groups in JOINT_GROUPS.items():
  for m in inventories['joints']['meshes']:
   if m['name'].endswith('.r') and any(g in m['ancestors'] for g in groups):selection['joints'].setdefault(m['name'],set()).add(region)
 for category,by_region in [('bones',BONES),('muscles',MUSCLES),('nerves',NERVES)]:
  known={m['name'] for m in inventories[category]['meshes']}
  for region,names in by_region.items():
   for name in names:
    if name not in known:missing.append({'category':category,'region':region,'name':name});continue
    selection[category].setdefault(name,set()).add(region)
 for m in inventories['bones']['meshes']:
  name=m['name']
  if name.endswith('.r') and ('metacarpal bone' in name or 'finger of hand' in name):selection['bones'].setdefault(name,set()).add('wrist')
  if name.endswith('.r') and ('metatarsal bone' in name or 'finger of foot' in name):selection['bones'].setdefault(name,set()).add('ankle')
 parts={}
 for category,source in SOURCES.items():
  dest=OUT/category;dest.mkdir(exist_ok=True);names=OUT/(category+'-selected.txt');names.write_text('\n'.join(sorted(selection[category]))+'\n')
  result=subprocess.run([str(CACHE/'export_ufbx'),str(CACHE/('z-anatomy-'+source+'.fbx')),str(dest),str(names)],check=True,capture_output=True,text=True)
  data=json.loads(result.stdout);(OUT/(category+'-export.json')).write_text(json.dumps(data,indent=2)+'\n')
  source_path=CACHE/('z-anatomy-'+source+'.fbx');source_hash=hashlib.sha256(source_path.read_bytes()).hexdigest()
  for m in data['meshes']:
   if 'file' not in m:continue
   identifier='za-'+category+'-'+str(m['source_model_id']);name=m['name'];record={**m,'id':identifier,'regions':sorted(selection[category][name]),'source_category':category,'source_file':source_path.name,'source_sha256':source_hash,'license':'CC BY-SA 4.0','sha256':hashlib.sha256(pathlib.Path(m['file']).read_bytes()).hexdigest(),'bytes':pathlib.Path(m['file']).stat().st_size}
   raw=pathlib.Path(record['file']).read_bytes();nv,ni=struct.unpack_from('<II',raw,4);positions=struct.unpack_from('<'+'f'*(nv*3),raw,12);indices=struct.unpack_from('<'+'I'*ni,raw,12+nv*24)
   record['source_bounds_all_vertices']=record['bounds']
   record['bounds']=[[min(positions[i*3+a] for i in indices) for a in range(3)],[max(positions[i*3+a] for i in indices) for a in range(3)]]
   if category=='bones':layer='bone'
   elif category=='nerves':layer='nerve'
   elif 'bursa' in name.lower():layer='bursa'
   elif 'fat pad' in name.lower():layer='fat'
   elif 'articular disc' in name.lower():layer='fibrocartilage'
   elif 'tendon sheath' in name.lower():layer='tendon-sheath'
   elif 'fascia' in name.lower() or 'aponeurosis' in name.lower():layer='fascia'
   elif 'meniscus' in name.lower() and 'ligament' not in name.lower():layer='meniscus'
   elif 'labrum' in name.lower():layer='labrum'
   elif 'capsule' in name.lower():layer='capsule'
   elif category=='joints' or 'retinacul' in name.lower():layer='ligament'
   elif 'tendon' in name.lower():layer='tendon'
   else:layer='muscle'
   record['layer']=layer
   for sub in record.get('material_submeshes',[]):
    raw=pathlib.Path(sub['file']).read_bytes();sub['sha256']=hashlib.sha256(raw).hexdigest();sub['bytes']=len(raw)
    nv,ni=struct.unpack_from('<II',raw,4);positions=struct.unpack_from('<'+'f'*(nv*3),raw,12);indices=struct.unpack_from('<'+'I'*ni,raw,12+nv*24)
    sub['bounds']=[[min(positions[i*3+a] for i in indices) for a in range(3)],[max(positions[i*3+a] for i in indices) for a in range(3)]]
   parts[identifier]=record
 regions={}
 for region,names in FOCUS.items():
  objects=[p for p in parts.values() if p['name'] in names]
  assert len(objects)==len(names),(region,names)
  regions[region]={'title':region.title(),'side':'right','parts':[p['id'] for p in parts.values() if region in p['regions']], 'focus_bounds':union(objects),'focus_bounds_source_objects':names}
 result={'schema_version':1,'status':'research candidates; not published or clinically certified','dataset':'Z-Anatomy','source_commit':'6c7f9016bd5899ac8edafd31b9900c151df42ed6','coordinate_system':{'units':'centimeters','unit_meters':.01,'x_positive':'patient left','y_positive':'superior','z_positive':'anterior','registration':'Source FBX geometry_to_world evaluated by ufbx; no fit or translation to BodyParts3D','display_basis':'Native [x,y,z] already maps to [patient-left,superior,anterior]. Multiply by10 only if millimeters are needed.'},'license':'CC BY-SA 4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/','source_license_file':str(CACHE/'z-anatomy-License.txt'),'attribution':['BodyParts3D — The Database Center for Life Science — upstream lineage CC BY-SA 2.1 Japan','Z-Anatomy — The open source atlas of anatomy — CC BY-SA 4.0'],'adaptations':'Source world transforms baked, native polygon faces triangulated using ufbx, source normal seams retained, mirrored-instance winding corrected. No decimation or inferred anatomy. Material submeshes retain source-assigned material face groups.','parts':parts,'regions':regions,'requested_but_absent':missing}
 (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Candidate parts',len(parts),'bytes',sum(p['bytes'] for p in parts.values()),'region memberships',{r:len(v['parts']) for r,v in regions.items()},'missing requests',missing)

if __name__=='__main__':main()
