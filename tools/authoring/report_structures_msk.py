"""Joints, limbs and soft tissues: the headings report_structures_20261117.py writes."""

CONTENT = r'''
# ---------------------------------------------------------------- wrist and hand

## @WRIST_EXTENSORS
> Extensor tendons
First compartment (APL and EPB) | Normal. | De Quervain tenosynovitis. | [Tendinosis / Tear] of the [abductor pollicis longus / extensor pollicis brevis] [ ].
Second compartment (ECRL and ECRB) | Normal. | [Tenosynovitis / Tendinosis / Tear] of the extensor carpi radialis [longus / brevis] [ ]. | Intersection syndrome.
Third compartment (EPL) | Normal. | [Tenosynovitis / Tendinosis / Rupture] of the extensor pollicis longus [ ].
Fourth compartment (EDC and EIP) | Normal. | [Tenosynovitis / Tendinosis / Tear] of the [extensor digitorum / extensor indicis] [ ].
Fifth compartment (EDM) | Normal. | [Tenosynovitis / Tendinosis / Tear] of the extensor digiti minimi [ ].
Sixth compartment (ECU) | Normal. | [Tenosynovitis / Tendinosis / Tear] of the extensor carpi ulnaris [ ]. | Extensor carpi ulnaris [subluxation / dislocation] with subsheath injury.

## @WRIST_FLEXORS
> Flexor tendons
Flexor carpi radialis and ulnaris | Normal. | [Tenosynovitis / Tendinosis / Tear] of the flexor carpi [radialis / ulnaris] [ ].
Digital flexors and flexor pollicis longus | Normal. | [Tenosynovitis / Tendinosis / Tear] of the [flexor digitorum superficialis / flexor digitorum profundus / flexor pollicis longus] [ ].

## msk.mri-wrist
! Bones
! Intrinsic ligaments
! TFCC
! Tendons
! Nerves and soft tissues
> Bones and alignment
Distal radius and ulna | No distal radius or ulna fracture or bone marrow oedema. Neutral ulnar variance. | [Fracture / Bone marrow oedema] of the distal [radius / ulna] [ ]. | [Positive / Negative] ulnar variance, [ ] mm.
Scaphoid | No scaphoid fracture, nonunion or avascular necrosis. | [Occult fracture / Nonunion / Avascular necrosis] of the scaphoid [waist / proximal pole / distal pole] [ ].
Lunate | Normal lunate marrow signal. | [Kienböck disease / Ulnar impaction change] of the lunate [ ].
Other carpal bones and metacarpal bases | No fracture, oedema or erosion of the other carpal bones or metacarpal bases. | [Fracture / Bone marrow oedema / Cyst / Erosion] of the [ ]. | Hook of hamate fracture.
Carpal alignment | Normal. | [DISI / VISI] deformity; scapholunate angle [ ] degrees; capitolunate angle [ ] degrees. | Scapholunate interval [ ] mm.
> Joints
Distal radioulnar joint | Congruent distal radioulnar joint without effusion. | [Dorsal / Volar] subluxation of the ulnar head. | [Effusion / Synovitis / Osteoarthritis] of the distal radioulnar joint.
Radiocarpal and midcarpal joints | Preserved radiocarpal and midcarpal cartilage, without effusion or synovitis. | [Effusion / Synovitis / Chondral loss / Osteoarthritis] of the [radiocarpal / midcarpal] joint [ ].
Carpometacarpal and pisotriquetral joints | Normal. | [First carpometacarpal / Scaphotrapeziotrapezoid / Pisotriquetral] osteoarthritis [ ].
> Intrinsic ligaments
Scapholunate ligament | Intact. | [Partial / Complete] tear of the [volar / membranous / dorsal] component of the scapholunate ligament.
Lunotriquetral ligament | Intact. | [Partial / Complete] tear of the [volar / membranous / dorsal] component of the lunotriquetral ligament.
> Extrinsic ligaments
Radioscaphocapitate ligament | Intact. | [Sprain / Partial tear / Complete tear] of the radioscaphocapitate ligament.
Long and short radiolunate ligaments | Intact. | [Sprain / Partial tear / Complete tear] of the [long / short] radiolunate ligament.
Ulnolunate and ulnotriquetral ligaments | Intact. | [Sprain / Partial tear / Complete tear] of the [ulnolunate / ulnotriquetral] ligament.
Dorsal radiocarpal ligament | Intact. | [Sprain / Partial tear / Complete tear] of the dorsal radiocarpal ligament.
Dorsal intercarpal ligament | Intact. | [Sprain / Partial tear / Complete tear] of the dorsal intercarpal ligament.
> Triangular fibrocartilage complex
Articular disc | Intact. | [Central perforation / Radial tear / Degenerative thinning] of the articular disc, Palmer class [ ].
Foveal and styloid attachments | Intact. | [Partial / Complete] tear of the [foveal / styloid] attachment.
Dorsal and volar radioulnar ligaments | Intact. | [Dorsal / Volar] radioulnar ligament tear [ ].
@WRIST_EXTENSORS
@WRIST_FLEXORS
> Nerves
Median nerve and carpal tunnel | Normal median nerve. No carpal tunnel mass or bowing of the flexor retinaculum. | Median nerve [swelling / flattening / T2 hyperintensity] in the carpal tunnel. | [Ganglion / Tenosynovitis / Mass] in the carpal tunnel.
Ulnar nerve and Guyon canal | Normal ulnar nerve. No mass in Guyon canal. | [Ganglion / Ulnar artery aneurysm / Mass] in Guyon canal [ ]. | Ulnar nerve [swelling / T2 hyperintensity] [ ].
>
Soft tissues | No ganglion, soft tissue mass or muscle abnormality. | [Dorsal / Volar] ganglion [ ] mm arising from the [ ]. | [Soft tissue mass / Muscle oedema / Muscle atrophy] [ ].

## msk.ultrasound-wrist
! Tendons
! Median and ulnar nerves
! Joints and ganglia
@WRIST_EXTENSORS
@WRIST_FLEXORS
> Nerves
Median nerve and carpal tunnel | Normal median nerve calibre and echotexture at the carpal tunnel. | Median nerve cross-sectional area [ ] mm² at the carpal tunnel inlet. | [Ganglion / Tenosynovitis / Mass] in the carpal tunnel.
Ulnar nerve and Guyon canal | Normal ulnar nerve. No mass in Guyon canal. | [Ganglion / Ulnar artery aneurysm / Mass] in Guyon canal [ ].
>
= Ligaments -> Dorsal scapholunate ligament | Intact.
Radiocarpal, midcarpal and distal radioulnar joints | No joint effusion or synovitis. | [Synovitis / Effusion] of the [ ] joint, Doppler grade [0 / 1 / 2 / 3]. | Erosion of the [ ].
Ganglion and soft tissues | No ganglion or soft tissue mass. | [Dorsal / Volar] ganglion [ ] mm arising from the [ ]. | [Soft tissue mass / Foreign body] [ ].

## ct.wrist-hand
! Fracture
! Alignment
! Bones
> Bones
Distal radius and ulna | No distal radius or ulna fracture. | [Intra-articular / Extra-articular] distal radius fracture; [dorsal / volar] tilt [ ] degrees, articular step [ ] mm. | Ulnar styloid fracture, [base / tip].
Scaphoid | Intact. | Scaphoid [waist / proximal pole / distal pole] fracture, displacement [ ] mm. | [Humpback deformity / Nonunion / Proximal pole sclerosis] [ ].
Other carpal bones | No carpal fracture. | [Triquetral / Hamate / Lunate / Capitate / Trapezium / Pisiform] fracture [ ].
Metacarpals and phalanges | No metacarpal or phalangeal fracture. | [Metacarpal / Phalangeal] fracture of the [ ] ray, [intra-articular / extra-articular], angulation [ ] degrees.
> Joints and alignment
Distal radioulnar joint | Congruent distal radioulnar joint. | [Dorsal / Volar] subluxation of the ulnar head.
Carpal alignment | Normal. | [Perilunate / Lunate] dislocation. | Scapholunate interval [ ] mm; [DISI / VISI] pattern.
Carpometacarpal and finger joints | Normally aligned carpometacarpal, metacarpophalangeal and interphalangeal joints. | [Carpometacarpal / Metacarpophalangeal / Interphalangeal] [subluxation / dislocation] of the [ ] ray.
>
Bone lesion and soft tissues | No focal bone lesion. Normal soft tissues. | [Lytic lesion / Sclerotic lesion / Soft tissue swelling / Foreign body] [ ].

## msk.mri-hand
! Tendons and pulleys
! Ligaments and volar plates
= Bones -> Metacarpals and phalanges
> Joints
Carpometacarpal joints | Normal. | [First carpometacarpal osteoarthritis / Carpometacarpal subluxation / Effusion] [ ].
= Joints -> Metacarpophalangeal and interphalangeal joints | No effusion, synovitis or erosion.
> Ligaments and volar plates
Collateral ligaments | Intact. | [Sprain / Partial tear / Complete tear] of the [radial / ulnar] collateral ligament of the [ ] joint.
Thumb ulnar collateral ligament | Intact. | [Partial / Complete] tear of the thumb ulnar collateral ligament [with / without] a Stener lesion.
Volar plates | Intact. | Volar plate [tear / avulsion] at the [ ] joint.
> Flexor tendons
Flexor digitorum superficialis and profundus | Intact. | [Tenosynovitis / Partial tear / Complete tear] of the [FDS / FDP] of the [ ] finger, retraction [ ] mm.
Flexor pollicis longus | Intact. | [Tenosynovitis / Partial tear / Complete tear] of the flexor pollicis longus.
Annular pulleys | Intact. | [A1 / A2 / A3 / A4 / A5] pulley rupture of the [ ] finger with bowstringing.
> Extensor tendons
Extensor tendons and sagittal bands | Intact. | [Tenosynovitis / Tear] of the extensor tendon of the [ ] finger. | Sagittal band tear with [radial / ulnar] subluxation of the extensor tendon.
Central slip and terminal tendon | Intact. | [Central slip / Terminal tendon] [tear / avulsion] of the [ ] finger.
>
Intrinsic muscles | Normal thenar, hypothenar, interosseous and lumbrical muscles. | Muscle [oedema / atrophy / tear] of the [ ].
Neurovascular bundles | Normal digital nerves and vessels. | [Neuroma / Digital artery thrombosis / Vascular malformation] [ ].
= Soft tissues | No mass, ganglion or collection.

## msk.ultrasound-hand
! Flexor tendons and pulleys
! Ligaments and soft tissues
> Flexor tendons
Flexor digitorum superficialis and profundus | Intact. | [Tenosynovitis / Partial tear / Complete tear] of the [FDS / FDP] of the [ ] finger.
Flexor pollicis longus | Intact. | [Tenosynovitis / Tear] of the flexor pollicis longus.
Annular pulleys | Intact. | Trigger finger: thickened A1 pulley of the [ ] finger. | [A2 / A3 / A4] pulley rupture of the [ ] finger with bowstringing.
>
= Extensor mechanism -> Extensor tendons and sagittal bands | Intact.
= Joints -> Metacarpophalangeal and interphalangeal joints
Collateral ligaments | Intact. | [Thumb ulnar collateral ligament tear / Stener lesion / Collateral ligament tear] at the [ ] joint.
Volar plates | Intact. | Volar plate [tear / avulsion] at the [ ] joint.
Soft tissues | No mass, ganglion or foreign body. | [Ganglion / Giant cell tumour of tendon sheath / Foreign body] [ ].

# ---------------------------------------------------------------- elbow and forearm

## ra.mri-elbow
! Tendons
! Ligaments
! Cartilage and bone
! Nerves
! Joint
> Tendons
Common extensor tendon | Intact. | [Tendinosis / Partial tear / Full-thickness tear] of the common extensor tendon [ ].
Common flexor tendon | Intact. | [Tendinosis / Partial tear / Full-thickness tear] of the common flexor tendon [ ].
Distal biceps and brachialis tendons | Intact. | [Tendinosis / Partial tear / Complete tear] of the distal biceps tendon, retraction [ ] mm. | Bicipitoradial bursitis.
Triceps tendon | Intact. | [Tendinosis / Partial tear / Complete tear] of the triceps tendon [ ].
> Ligaments
Ulnar collateral ligament | Intact anterior, posterior and transverse bundles of the ulnar collateral ligament. | [Sprain / Partial tear / Complete tear] of the anterior bundle of the ulnar collateral ligament [ ].
Radial collateral ligament | Intact. | [Sprain / Partial tear / Complete tear] of the radial collateral ligament.
Lateral ulnar collateral ligament | Intact. | [Sprain / Partial tear / Complete tear] of the lateral ulnar collateral ligament.
Annular ligament | Intact. | Annular ligament [tear / thickening] [ ].
> Joints and cartilage
Radiocapitellar joint | Preserved radiocapitellar cartilage. No osteochondral lesion. | Osteochondral lesion of the capitellum, [ ] mm, [stable / unstable]. | [Chondral loss / Plica / Radial head subluxation] [ ].
Ulnohumeral joint | Preserved ulnohumeral cartilage. | [Chondral loss / Osteophytes / Posteromedial impingement] [ ].
Proximal radioulnar joint | Normal. | Proximal radioulnar joint [subluxation / effusion] [ ].
Effusion and loose bodies | No effusion, synovitis or loose body. | [Effusion / Synovitis / Loose body] [ ].
> Nerves
Ulnar nerve | Normal ulnar nerve in the cubital tunnel. | Ulnar nerve [thickening / T2 hyperintensity / subluxation] at the cubital tunnel. | [Anconeus epitrochlearis / Ganglion / Osteophyte] compressing the ulnar nerve.
Median nerve | Normal. | Median nerve [thickening / T2 hyperintensity] at the [ ].
Radial and posterior interosseous nerves | Normal. | [Radial / Posterior interosseous] nerve [thickening / T2 hyperintensity] at the [ ].
>
Bones | No fracture or bone marrow oedema. | [Bone bruise / Occult fracture / Stress reaction] of the [capitellum / radial head / olecranon / trochlea / coronoid] [ ].
Muscles and bursae | Normal muscles. No olecranon bursitis. | [Olecranon bursitis / Muscle oedema / Denervation change / Soft tissue mass] [ ].

## msk.ultrasound-elbow
! Lateral elbow
! Medial elbow
! Anterior and posterior elbow
! Ulnar nerve and joint
> Lateral elbow
Common extensor tendon | Normal. | [Tendinosis / Partial tear / Full-thickness tear] of the common extensor tendon [ ]. | Neovascularity of the common extensor tendon on Doppler.
Radial collateral ligament | Intact. | [Thickened / Torn] radial collateral ligament.
Radiocapitellar joint | No radiocapitellar effusion or synovitis. | [Effusion / Synovitis / Plica] of the radiocapitellar joint.
> Medial elbow
Common flexor tendon | Normal. | [Tendinosis / Partial tear / Full-thickness tear] of the common flexor tendon [ ].
Ulnar collateral ligament | Intact anterior bundle of the ulnar collateral ligament. | [Thickened / Partially torn / Completely torn] anterior bundle; joint gapping [ ] mm on valgus stress.
Ulnar nerve | Normal ulnar nerve in the cubital tunnel, without subluxation. | Ulnar nerve cross-sectional area [ ] mm² at the cubital tunnel. | Ulnar nerve [subluxation / dislocation] on flexion.
> Anterior elbow
Distal biceps tendon | Intact. | [Partial / Complete] tear of the distal biceps tendon, retraction [ ] mm. | Bicipitoradial bursitis.
Anterior joint recess | No anterior effusion or loose body. | [Effusion / Synovitis / Loose body] in the anterior recess.
Median and radial nerves | Normal. | [Median / Radial / Posterior interosseous] nerve thickening at the [ ].
> Posterior elbow
Triceps tendon | Intact. | [Partial / Complete] tear of the triceps tendon [ ].
Olecranon bursa and posterior recess | No olecranon bursitis or posterior effusion. | [Olecranon bursitis / Posterior recess effusion / Loose body] [ ].

## ct.elbow
! Fracture
! Joint
! Bones
> Bones
Distal humerus | No distal humeral fracture. | [Supracondylar / Intercondylar / Capitellar / Epicondylar] fracture, displacement [ ] mm.
Radial head and neck | Intact. | Radial [head / neck] fracture, Mason type [1 / 2 / 3 / 4], articular step [ ] mm.
Olecranon and coronoid process | Intact. | [Olecranon / Coronoid] fracture, displacement [ ] mm.
> Joints
Radiocapitellar and ulnohumeral joints | Congruent radiocapitellar and ulnohumeral joints. | [Subluxation / Dislocation] of the [radiocapitellar / ulnohumeral] joint.
Proximal radioulnar joint | Congruent proximal radioulnar joint. | Proximal radioulnar [subluxation / dislocation].
Effusion and loose bodies | No effusion or loose body. | [Effusion / Lipohaemarthrosis / Intra-articular fragment] [ ].
>
Bone lesion and soft tissues | No focal bone lesion. Normal soft tissues. | [Lytic lesion / Sclerotic lesion / Soft tissue swelling / Heterotopic ossification] [ ].

## mri.forearm
= Bones -> Radius and ulna
! Muscles
! Soft tissues and nerves
> Muscles
Flexor compartment | Normal flexor muscles. | Muscle [oedema / tear / atrophy / fatty infiltration] of the [ ].
Extensor compartment and mobile wad | Normal extensor muscles and mobile wad. | Muscle [oedema / tear / atrophy / fatty infiltration] of the [ ].
>
Interosseous membrane and joints | Intact interosseous membrane. Normal visualised elbow and wrist. | [Interosseous membrane tear / Distal radioulnar subluxation / Effusion] [ ].
Nerves and vessels | Normal median, ulnar and radial neurovascular bundles. | [Median / Ulnar / Radial / Posterior interosseous] nerve [thickening / T2 hyperintensity] at the [ ].
Soft tissues | No soft tissue mass or collection. | [Soft tissue mass / Collection / Haematoma / Cellulitis] [ ], [ ] mm.

# ---------------------------------------------------------------- shoulder

## ra.mri-shoulder
! Rotator cuff
! Biceps and pulley
! Labrum and capsule
! Bones and joints
! Bursa and soft tissues
> Rotator cuff
Supraspinatus tendon | Intact. | [Tendinosis / Partial-thickness tear / Full-thickness tear] of the supraspinatus, [ ] mm, retraction [ ] mm. | [Bursal / Articular / Intrasubstance] side partial tear [ ]. | Calcific deposit [ ] mm in the supraspinatus tendon.
Infraspinatus tendon | Intact. | [Tendinosis / Partial-thickness tear / Full-thickness tear] of the infraspinatus, [ ] mm.
Subscapularis tendon | Intact. | [Tendinosis / Partial-thickness tear / Full-thickness tear] of the [upper / lower / whole] subscapularis.
Teres minor tendon | Intact. | [Tendinosis / Tear] of the teres minor.
= Muscles -> Rotator cuff muscles
> Biceps
Long head of biceps tendon | Intact long head of biceps tendon in the bicipital groove. | [Tendinosis / Tear / Subluxation / Dislocation] of the long head of biceps [ ].
Biceps pulley and rotator interval | Intact. | [Pulley lesion / Rotator interval synovitis / Capsular thickening] [ ].
> Labrum and capsule
Superior labrum and biceps anchor | Intact. | SLAP lesion, type [1 / 2 / 3 / 4], from [ ] to [ ] o'clock.
Anterior labrum | Intact. | [Bankart / Perthes / ALPSA / GLAD] lesion from [ ] to [ ] o'clock.
Posterior labrum | Intact. | [Posterior labral tear / Reverse Bankart lesion / Paralabral cyst] [ ].
Glenohumeral ligaments and capsule | Intact glenohumeral ligaments. Normal axillary recess. | [HAGL lesion / Capsular thickening / Axillary recess oedema] [ ].
> Joints
Glenohumeral joint | Preserved glenohumeral cartilage. No joint effusion. | [Chondral loss / Osteoarthritis / Effusion / Synovitis / Loose body] [ ].
Acromioclavicular joint | Normal. | [Mild / Moderate / Severe] acromioclavicular osteoarthritis [with / without] inferior osteophytes.
>
Acromion and subacromial space | Normal acromial morphology. No os acromiale. | Bigliani type [1 / 2 / 3] acromion. | [Os acromiale / Subacromial spur / Lateral downsloping] [ ].
Subacromial-subdeltoid bursa | No subacromial-subdeltoid bursitis. | [Bursitis / Bursal effusion] [ ].
Bones | No fracture or bone marrow oedema. | [Hill-Sachs lesion / Bony Bankart lesion / Greater tuberosity fracture / Bone marrow oedema] [ ].
Nerves and soft tissues | Normal suprascapular and spinoglenoid notches and quadrilateral space. | [Paralabral cyst / Ganglion] in the [suprascapular / spinoglenoid] notch. | Denervation change in the [ ].

## ra.ultrasound-shoulder
= Long head of biceps -> Long head of biceps tendon
! Rotator cuff
> Rotator cuff
Subscapularis tendon | Intact. | [Tendinosis / Partial-thickness tear / Full-thickness tear] of the subscapularis [ ].
Supraspinatus tendon | Intact. | [Tendinosis / Partial-thickness tear / Full-thickness tear] of the supraspinatus, [ ] mm. | Calcific deposit [ ] mm in the supraspinatus tendon.
Infraspinatus tendon | Intact. | [Tendinosis / Partial-thickness tear / Full-thickness tear] of the infraspinatus [ ].
Teres minor tendon | Intact. | [Tendinosis / Tear] of the teres minor.
>
= Subacromial bursa -> Subacromial-subdeltoid bursa
! Joints
Acromioclavicular joint | Normal. | [Acromioclavicular effusion / Osteoarthritis / Capsular distension] [ ].
Posterior glenohumeral joint | No glenohumeral effusion. Normal posterior labrum and spinoglenoid notch. | [Glenohumeral effusion / Paralabral cyst] [ ].
Rotator cuff muscles | No muscle atrophy or fatty infiltration. | [Atrophy / Fatty infiltration] of the [supraspinatus / infraspinatus] muscle.

## msk.mri-shoulder-postoperative
= Cuff repair
Remaining rotator cuff tendons | Intact. | [Tendinosis / Partial-thickness tear / Full-thickness tear] of the [supraspinatus / infraspinatus / subscapularis / teres minor].
Long head of biceps tendon | Intact long head of biceps tendon or tenodesis. | [Tenotomy / Tenodesis failure / Tendinosis / Tear] of the long head of biceps.
= Labral repair
= Muscles -> Rotator cuff muscles
Acromion and acromioclavicular joint | No residual subacromial spur or acromial fracture. | [Residual subacromial spur / Acromial fracture / Acromioclavicular arthropathy] [ ].
= Bone and joint -> Glenohumeral joint and bones
Deltoid | Intact deltoid attachment. | Deltoid [dehiscence / atrophy] [ ].
= Soft tissues -> Bursa and soft tissues

## ct.shoulder
! Fracture
> Bones
Proximal humerus | No proximal humeral fracture. | [Two-part / Three-part / Four-part] proximal humeral fracture involving the [ ]. | [Hill-Sachs / Reverse Hill-Sachs] lesion, [ ] mm.
Glenoid and scapula | Intact glenoid rim and scapula. | Glenoid rim fracture involving [ ] percent of the articular surface. | Scapular [body / neck / coracoid / acromion] fracture.
Clavicle and acromion | Intact. | [Clavicle / Acromion] fracture [ ].
> Joints
= Glenohumeral joint | Concentric glenohumeral joint.
= Acromioclavicular joint
>
Lung apex and ribs | Clear lung apex. No rib fracture. | [Pneumothorax / Rib fracture / Apical lesion] [ ].
Soft tissues | Normal. | [Haematoma / Effusion / Calcific tendinopathy / Muscle atrophy] [ ].

# ---------------------------------------------------------------- hip and pelvis

## @HIP_TENDONS
> Tendons and bursae
Gluteus medius and minimus tendons | Intact. | [Tendinosis / Partial tear / Full-thickness tear] of the gluteus [medius / minimus] [ ].
Trochanteric bursa | No trochanteric bursitis. | Trochanteric bursitis [ ].
Iliopsoas tendon and bursa | Normal. | [Iliopsoas tendinosis / Iliopsoas bursitis] [ ].
Hamstring origin | Intact. | [Tendinosis / Partial tear / Complete avulsion] of the hamstring origin, retraction [ ] mm.
Adductor and rectus femoris origins | Intact. | [Adductor / Rectus femoris] [tendinosis / partial tear / avulsion] [ ].

## msk.mri-hip
! Bones
! Labrum and cartilage
! Tendons and bursae
! Joint and soft tissues
> Bones
Femoral head and neck | Normal femoral head and neck marrow signal. No fracture, stress reaction or avascular necrosis. | [Stress fracture / Avascular necrosis / Bone marrow oedema / Insufficiency fracture] of the femoral [head / neck] [ ].
Acetabulum and pelvis | Normal acetabular and visualised pelvic marrow signal. | [Bone marrow oedema / Fracture / Subchondral cyst / Focal lesion] of the [ ].
> Joint
Labrum | Intact. | Labral tear from [ ] to [ ] o'clock [ ]. | Paralabral cyst [ ] mm.
Articular cartilage | Preserved. | [Chondral delamination / Full-thickness cartilage loss] at [ ].
Effusion and synovium | No effusion or synovitis. | [Effusion / Synovitis / Loose body] [ ].
Ligamentum teres | Intact. | [Partial / Complete] tear of the ligamentum teres.
= Morphology
@HIP_TENDONS
> Other structures
Sacroiliac joint and pubic symphysis | Normal. | [Sacroiliitis / Osteitis pubis / Degenerative change] [ ].
Sciatic nerve and muscles | Normal. | [Muscle oedema / Muscle atrophy / Sciatic nerve thickening] [ ].
Soft tissues | No mass or collection. Normal visualised pelvic organs. | [Mass / Collection / Lymphadenopathy] [ ].

## mri.both-hips
> Bones
= Femoral heads
= Bone marrow -> Femoral necks, acetabula and pelvis
> Joints
Labra | Intact. | Labral tear of the [right / left] hip from [ ] to [ ] o'clock.
= Joints -> Cartilage and effusion
! Tendons and bursae
@HIP_TENDONS
> Other structures
Sacroiliac joints and pubic symphysis | Normal. | [Sacroiliitis / Osteitis pubis / Degenerative change] [ ].
Muscles and soft tissues | Normal muscles. No mass or collection. | [Muscle oedema / Muscle atrophy / Mass / Collection] [ ].

## mri.bony-pelvis
! Bone marrow
> Bones
Sacrum and coccyx | No sacral fracture or marrow oedema. | [Sacral insufficiency fracture / Marrow oedema / Focal lesion] [ ].
Iliac bones and acetabula | Normal iliac and acetabular marrow signal. | [Fracture / Marrow oedema / Focal lesion] in the [ ].
Pubic rami and ischia | Intact. | [Fracture / Marrow oedema / Focal lesion] of the [ ].
Proximal femora | Normal femoral heads and necks. No avascular necrosis. | [Fracture / Avascular necrosis / Marrow oedema] of the [right / left] proximal femur.
Lower lumbar spine | Normal visualised lower lumbar vertebrae. | [Fracture / Marrow lesion / Degenerative change] at [ ].
> Joints
= Hip joints | No hip joint effusion or cartilage loss.
Sacroiliac joints | Normal. | [Sacroiliitis / Degenerative change / Ankylosis] of the [right / left] sacroiliac joint.
Pubic symphysis | Normal. | [Osteitis pubis / Diastasis / Degenerative change] [ ].
! Sacroiliac joints and symphysis
! Tendons and muscles
@HIP_TENDONS
> Other structures
Muscles | Normal pelvic and thigh muscles. | Muscle [oedema / tear / atrophy] of the [ ].
Sciatic nerves and soft tissues | Normal sciatic nerves. No mass or collection. | [Sciatic nerve thickening / Mass / Collection / Lymphadenopathy] [ ].
Bladder, bowel and reproductive organs | Normal. | [Bladder / Bowel / Uterine / Adnexal / Prostate] abnormality [ ].

## msk.ultrasound-hip
= Joint -> Hip joint
! Anterior structures
! Lateral structures
> Anterior structures
Iliopsoas tendon and bursa | Normal. | [Iliopsoas bursitis / Snapping iliopsoas tendon / Tendinosis] [ ].
Rectus femoris origin | Intact. | [Tendinosis / Tear / Avulsion] of the rectus femoris origin.
Anterior labrum | Normal. | [Labral tear / Paralabral cyst] [ ].
> Lateral structures
Gluteus medius tendon | Intact. | [Tendinosis / Partial tear / Full-thickness tear] of the gluteus medius.
Gluteus minimus tendon | Intact. | [Tendinosis / Partial tear / Full-thickness tear] of the gluteus minimus.
Trochanteric bursa | No trochanteric bursitis. | Trochanteric bursitis [ ] mm.
Iliotibial band | Normal. | [Thickened iliotibial band / Snapping on dynamic assessment] [ ].
> Posterior and medial structures
Hamstring origin | Intact. | [Tendinosis / Partial tear / Avulsion] of the hamstring origin.
Adductor origin | Intact. | [Tendinosis / Tear] of the adductor origin.
>
= Soft tissues

## ct.hip
> Bones
= Proximal femur
Femoral head | Normal femoral head contour. | [Femoral head fracture / Impaction / Avascular necrosis / Subchondral collapse] [ ].
Acetabulum | Intact acetabular walls and columns. | [Posterior wall / Anterior wall / Posterior column / Anterior column / Transverse] acetabular fracture, displacement [ ] mm.
Pelvis and sacroiliac joint | Intact visualised hemipelvis. Normal sacroiliac joint. | [Pubic ramus fracture / Iliac fracture / Sacral fracture / Sacroiliac diastasis] [ ].
>
= Hip joint
Soft tissues | Normal soft tissues and visualised pelvic organs. | [Haematoma / Effusion / Heterotopic ossification] [ ].

## ct.pelvis-hips
! Pelvic ring and acetabula
> Bones
Pelvic ring | Intact iliac bones, pubic rami and ischia. | [Iliac wing / Superior pubic ramus / Inferior pubic ramus / Ischial] fracture [ ]. | Pelvic ring injury, [lateral compression / anteroposterior compression / vertical shear] pattern.
Sacrum and coccyx | Intact. | Sacral fracture, Denis zone [1 / 2 / 3], [right / left / bilateral].
Acetabula | Intact acetabular walls and columns. | [Posterior wall / Anterior wall / Posterior column / Anterior column / Transverse] acetabular fracture, displacement [ ] mm.
Proximal femora | Normal femoral heads. No proximal femoral fracture. | [Femoral neck / Intertrochanteric / Subtrochanteric / Femoral head] fracture, [right / left].
Lower lumbar spine | Normal visualised lower lumbar vertebrae. | [Fracture / Transverse process fracture / Degenerative change] at [ ].
> Joints
= Hip joints | Congruent hip joints with preserved joint spaces.
= Sacroiliac joints and symphysis -> Sacroiliac joints and pubic symphysis | Normal.
>
= Soft tissues | Normal pelvic soft tissues and visualised pelvic organs.

# ---------------------------------------------------------------- knee

## ra.mri-knee
! Menisci
! Cruciate ligaments
! Collateral ligaments and corners
! Extensor mechanism and patellofemoral joint
! Cartilage and bone
! Joint and soft tissues
> Menisci
Medial meniscus | Intact. | [Horizontal / Vertical / Radial / Complex / Bucket-handle / Root] tear of the medial meniscus [posterior horn / body / anterior horn]. | Meniscal extrusion [ ] mm.
Lateral meniscus | Intact. | [Horizontal / Vertical / Radial / Complex / Bucket-handle / Root] tear of the lateral meniscus [posterior horn / body / anterior horn]. | Discoid lateral meniscus.
> Cruciate ligaments
Anterior cruciate ligament | Intact. | [Sprain / Partial tear / Complete tear] of the anterior cruciate ligament [ ]. | Mucoid degeneration of the anterior cruciate ligament.
Posterior cruciate ligament | Intact. | [Sprain / Partial tear / Complete tear] of the posterior cruciate ligament [ ].
> Collateral ligaments and corners
Medial collateral ligament | Intact superficial and deep medial collateral ligament. | Grade [1 / 2 / 3] injury of the medial collateral ligament at the [femoral / tibial] attachment.
Lateral collateral ligament | Intact. | [Sprain / Partial tear / Complete tear] of the lateral collateral ligament.
Posterolateral corner | Intact popliteus tendon, biceps femoris tendon and popliteofibular ligament. | [Popliteus / Biceps femoris / Popliteofibular ligament] [sprain / partial tear / complete tear].
Posteromedial corner | Intact posterior oblique ligament and semimembranosus tendon. | [Posterior oblique ligament tear / Semimembranosus tendinosis / Semimembranosus bursitis] [ ].
Iliotibial band | Normal. | Iliotibial band friction syndrome.
> Extensor mechanism
Quadriceps tendon | Intact. | [Tendinosis / Partial tear / Complete tear] of the quadriceps tendon [ ].
Patellar tendon | Intact. | [Tendinosis / Partial tear / Complete tear] of the [proximal / mid / distal] patellar tendon.
Patellar retinacula and position | Intact medial patellofemoral ligament and retinacula. Normal patellar position. | [Medial patellofemoral ligament tear / Lateral patellar subluxation / Patella alta / Trochlear dysplasia] [ ].
> Cartilage
Medial compartment | Preserved. | Grade [1 / 2 / 3 / 4] chondral lesion of the medial [femoral condyle / tibial plateau], [ ] mm.
Lateral compartment | Preserved. | Grade [1 / 2 / 3 / 4] chondral lesion of the lateral [femoral condyle / tibial plateau], [ ] mm.
Patellofemoral compartment | Preserved. | Grade [1 / 2 / 3 / 4] chondral lesion of the [patella / trochlea], [ ] mm.
>
Bones | No fracture or bone marrow oedema. | [Bone bruise / Fracture / Osteochondral lesion / Insufficiency fracture] at [ ].
Effusion and synovium | No effusion, synovitis or loose body. | [Small / Moderate / Large] effusion [ ]. | [Synovitis / Loose body / Plica] [ ].
Hoffa fat pad | Normal. | [Hoffa fat pad oedema / Superolateral impingement / Scarring] [ ].
Popliteal fossa | No Baker's cyst. Normal popliteal vessels. | Baker's cyst [ ] x [ ] mm, [intact / ruptured]. | [Popliteal aneurysm / Ganglion / Mass] [ ].
Muscles and soft tissues | Normal muscles and pes anserinus. No soft tissue mass. | [Muscle strain / Pes anserine bursitis / Prepatellar bursitis / Soft tissue mass] [ ].

## msk.mri-knee-postoperative
= Graft -> Anterior cruciate ligament graft
Posterior cruciate ligament | Intact. | [Sprain / Partial tear / Complete tear] of the posterior cruciate ligament.
! Menisci
> Menisci
Medial meniscus | Postoperative medial meniscus without new tear. | [Re-tear / New tear] of the medial meniscus [posterior horn / body / anterior horn]. | [Meniscal repair / Partial meniscectomy] at [ ].
Lateral meniscus | Postoperative lateral meniscus without new tear. | [Re-tear / New tear] of the lateral meniscus [posterior horn / body / anterior horn]. | [Meniscal repair / Partial meniscectomy] at [ ].
>
= Complications
! Cartilage and bone
> Cartilage
Medial compartment | Preserved. | Grade [1 / 2 / 3 / 4] chondral lesion of the medial [femoral condyle / tibial plateau], [ ] mm.
Lateral compartment | Preserved. | Grade [1 / 2 / 3 / 4] chondral lesion of the lateral [femoral condyle / tibial plateau], [ ] mm.
Patellofemoral compartment | Preserved. | Grade [1 / 2 / 3 / 4] chondral lesion of the [patella / trochlea], [ ] mm.
>
Bones and tunnels | No bone marrow oedema, fracture or tunnel widening. | [Bone marrow oedema / Tunnel widening / Tunnel cyst / Hardware loosening] at [ ].
! Ligaments and joint
Collateral ligaments | Intact medial and lateral collateral ligaments. | [Medial / Lateral] collateral ligament [sprain / partial tear / complete tear].
Extensor mechanism | Intact quadriceps and patellar tendons. | [Patellar tendon donor site change / Patellar tendinosis / Quadriceps tendon tear] [ ].
Effusion and soft tissues | No effusion, synovitis or Baker's cyst. | [Effusion / Synovitis / Baker's cyst / Collection] [ ].

## msk.ultrasound-knee
! Extensor mechanism
! Medial and lateral structures
! Joint and bursae
> Anterior knee
Quadriceps tendon | Normal. | [Tendinosis / Partial tear / Full-thickness tear] of the quadriceps tendon [ ].
Patellar tendon | Normal. | [Tendinosis / Partial tear / Full-thickness tear] of the [proximal / distal] patellar tendon [ ].
Suprapatellar recess | No knee effusion or synovitis. | [Small / Moderate / Large] effusion. | Synovitis [ ].
Prepatellar and infrapatellar bursae | No prepatellar or infrapatellar bursitis. | [Prepatellar / Superficial infrapatellar / Deep infrapatellar] bursitis.
> Medial knee
Medial collateral ligament | Normal. | [Thickened / Partially torn / Completely torn] medial collateral ligament.
Medial meniscus and joint line | No meniscal extrusion or parameniscal cyst. | Medial meniscal [extrusion / cyst] [ ] mm.
Pes anserinus | Normal pes anserine tendons and bursa. | Pes anserine bursitis.
> Lateral knee
Lateral collateral ligament and biceps femoris tendon | Normal. | [Lateral collateral ligament / Biceps femoris tendon] [thickening / tear].
Iliotibial band | Normal. | Iliotibial band friction syndrome.
Lateral meniscus and joint line | No lateral meniscal extrusion or cyst. | Lateral meniscal [extrusion / cyst] [ ] mm.
>
= Posterior knee -> Popliteal fossa | No Baker's cyst. Normal popliteal vessels.

## ct.knee
! Fracture
! Joint
! Bones
> Bones
Distal femur | No distal femoral fracture. | [Supracondylar / Condylar / Intercondylar] fracture of the distal femur, displacement [ ] mm.
Tibial plateau | Intact. | Schatzker type [1 / 2 / 3 / 4 / 5 / 6] tibial plateau fracture; articular depression [ ] mm, widening [ ] mm.
Patella | Intact. | [Transverse / Vertical / Comminuted / Osteochondral] patellar fracture, displacement [ ] mm.
Proximal fibula and tibial eminence | Intact. | [Fibular head / Tibial eminence / Segond] fracture.
> Joints
Tibiofemoral and patellofemoral joints | Congruent tibiofemoral and patellofemoral joints. | [Subluxation / Dislocation] of the [tibiofemoral / patellofemoral] joint.
Effusion | No effusion or lipohaemarthrosis. | [Effusion / Lipohaemarthrosis / Intra-articular fragment] [ ].
>
Bone lesion and soft tissues | No focal bone lesion. Normal soft tissues. | [Lytic lesion / Sclerotic lesion / Soft tissue swelling / Extensor mechanism disruption] [ ].

# ---------------------------------------------------------------- thigh and lower leg

## mri.lower-leg
= Bones -> Tibia and fibula
! Muscles
! Soft tissues and vessels
> Muscles
Anterior and lateral compartments | Normal anterior and peroneal muscles. | Muscle [oedema / tear / atrophy / herniation] of the [ ].
Superficial posterior compartment | Normal gastrocnemius, soleus and plantaris. | [Gastrocnemius / Soleus / Plantaris] [strain / tear] at the [ ], [ ] mm.
Deep posterior compartment | Normal deep posterior muscles. | Muscle [oedema / tear / atrophy] of the [ ].
>
Achilles and hamstring tendons | Normal visualised Achilles and distal hamstring tendons. | [Achilles tendinosis / Achilles tear / Tennis leg] [ ].
Nerves and vessels | Normal neurovascular bundles. | [Deep vein thrombosis / Popliteal entrapment / Nerve thickening] [ ].
Soft tissues | No soft tissue mass or collection. | [Soft tissue mass / Collection / Haematoma / Cellulitis] [ ], [ ] mm.

## ra.mri-hamstring
! Proximal tendons
> Proximal tendons
Conjoint tendon | Intact conjoint tendon of biceps femoris and semitendinosus. | [Tendinosis / Partial tear / Complete avulsion] of the conjoint tendon, retraction [ ] mm.
Semimembranosus tendon | Intact. | [Tendinosis / Partial tear / Complete avulsion] of the semimembranosus tendon, retraction [ ] mm.
! Muscles
> Muscles
Biceps femoris | Normal. | British Athletics grade [0 / 1 / 2 / 3 / 4] injury of the biceps femoris, [myofascial / myotendinous / intratendinous], length [ ] mm.
Semitendinosus | Normal. | British Athletics grade [0 / 1 / 2 / 3 / 4] injury of the semitendinosus, [myofascial / myotendinous / intratendinous], length [ ] mm.
Semimembranosus | Normal. | British Athletics grade [0 / 1 / 2 / 3 / 4] injury of the semimembranosus, [myofascial / myotendinous / intratendinous], length [ ] mm.
>
Distal tendons | Intact distal hamstring tendons. | [Tendinosis / Tear] of the distal [biceps femoris / semitendinosus / semimembranosus] tendon.
= Haematoma
= Sciatic nerve
Other muscles and bones | Normal adductor and quadriceps muscles. No ischial marrow oedema or avulsion. | [Adductor strain / Quadriceps strain / Ischial marrow oedema / Avulsion fracture] [ ].

# ---------------------------------------------------------------- ankle and foot

## @ANKLE_TENDONS
> Medial tendons
Tibialis posterior tendon | Intact. | [Tendinosis / Tenosynovitis / Partial tear / Complete tear] of the tibialis posterior tendon [ ].
Flexor digitorum longus tendon | Intact. | [Tenosynovitis / Tear] of the flexor digitorum longus tendon.
Flexor hallucis longus tendon | Intact. | [Tenosynovitis / Tendinosis / Tear] of the flexor hallucis longus tendon [ ].
> Lateral tendons
Peroneus longus tendon | Intact. | [Tendinosis / Tenosynovitis / Split tear / Complete tear] of the peroneus longus tendon [ ].
Peroneus brevis tendon | Intact. | [Tendinosis / Tenosynovitis / Split tear / Complete tear] of the peroneus brevis tendon [ ].
Peroneal retinaculum | Intact. No peroneal tendon subluxation. | Superior peroneal retinaculum injury with tendon [subluxation / dislocation].
> Anterior tendons
Tibialis anterior tendon | Intact. | [Tendinosis / Tenosynovitis / Tear] of the tibialis anterior tendon [ ].
Extensor hallucis and digitorum longus tendons | Intact. | [Tenosynovitis / Tear] of the extensor [hallucis longus / digitorum longus] tendon.
> Posterior structures
Achilles tendon | Intact. | [Tendinosis / Partial tear / Complete tear] of the Achilles tendon [ ] mm from the insertion, gap [ ] mm. | [Retrocalcaneal bursitis / Haglund deformity / Paratenonitis] [ ].
Plantar fascia | Normal. | Plantar fasciitis: fascia [ ] mm thick with perifascial oedema. | [Partial / Complete] tear of the plantar fascia.

## ra.mri-ankle
! Bones and osteochondral surfaces
! Lateral ligaments and syndesmosis
! Medial ligaments and sinus tarsi
! Tendons
! Joints and soft tissues
> Bones
Distal tibia and fibula | No distal tibial or fibular fracture or bone marrow oedema. | [Fracture / Bone bruise / Stress reaction] of the distal [tibia / fibula] [ ].
Talus | Intact talar dome. No osteochondral lesion. | Osteochondral lesion of the [medial / lateral] talar dome, [ ] mm, [stable / unstable]. | [Bone bruise / Avascular necrosis / Os trigonum syndrome] [ ].
Calcaneus | Normal calcaneal marrow signal. | [Stress fracture / Bone marrow oedema / Anterior process fracture] of the calcaneus.
Navicular, cuboid and cuneiforms | Normal. | [Stress fracture / Bone marrow oedema / Accessory navicular oedema] of the [ ].
> Joints
Tibiotalar joint | Preserved tibiotalar cartilage. No joint effusion or synovitis. | [Effusion / Synovitis / Chondral loss / Loose body] [ ]. | [Anterolateral / Anterior / Posterior] impingement.
Subtalar joint | Normal. | [Effusion / Chondral loss / Osteoarthritis / Coalition] of the subtalar joint.
Talonavicular and calcaneocuboid joints | Normal. | [Effusion / Osteoarthritis / Coalition] of the [talonavicular / calcaneocuboid] joint.
> Lateral ligaments
Anterior talofibular ligament | Intact. | [Sprain / Partial tear / Complete tear] of the anterior talofibular ligament.
Calcaneofibular ligament | Intact. | [Sprain / Partial tear / Complete tear] of the calcaneofibular ligament.
Posterior talofibular ligament | Intact. | [Sprain / Partial tear / Complete tear] of the posterior talofibular ligament.
> Syndesmosis
Anterior inferior tibiofibular ligament | Intact. | [Sprain / Partial tear / Complete tear] of the anterior inferior tibiofibular ligament.
Posterior inferior tibiofibular ligament and membrane | Intact posterior inferior tibiofibular ligament and interosseous membrane. | [Sprain / Tear] of the [posterior inferior tibiofibular ligament / interosseous membrane]; tibiofibular clear space [ ] mm.
> Medial ligaments
Deltoid ligament | Intact superficial and deep deltoid ligament. | [Sprain / Partial tear / Complete tear] of the [superficial / deep] deltoid ligament.
Spring ligament | Intact. | [Sprain / Tear] of the [superomedial / inferoplantar] spring ligament.
@ANKLE_TENDONS
> Other structures
Sinus tarsi | Normal sinus tarsi fat and ligaments. | Sinus tarsi [oedema / fibrosis / ganglion] [ ].
Tarsal tunnel | Normal tibial nerve. No tarsal tunnel mass. | [Ganglion / Varicosities / Mass] in the tarsal tunnel [ ].
Soft tissues | No ganglion, mass or collection. | [Ganglion / Soft tissue mass / Collection / Subcutaneous oedema] [ ].

## msk.ultrasound-ankle
! Tendons
! Ligaments
! Joint and soft tissues
> Lateral ligaments
Anterior talofibular ligament | Intact. | [Thickened / Partially torn / Completely torn] anterior talofibular ligament; anterior drawer [positive / negative].
Calcaneofibular ligament | Intact. | [Thickened / Partially torn / Completely torn] calcaneofibular ligament.
Anterior inferior tibiofibular ligament | Intact. | [Thickened / Partially torn / Completely torn] anterior inferior tibiofibular ligament.
>
Deltoid ligament | Intact. | [Thickened / Partially torn / Completely torn] deltoid ligament.
@ANKLE_TENDONS
> Joints and soft tissues
Tibiotalar joint | No tibiotalar effusion or synovitis. | [Effusion / Synovitis / Loose body] in the [anterior / posterior] recess.
Retrocalcaneal bursa | No retrocalcaneal bursitis. | [Retrocalcaneal / Superficial calcaneal] bursitis.
Tarsal tunnel | Normal tibial nerve. No tarsal tunnel mass. | [Ganglion / Varicosities / Mass] in the tarsal tunnel [ ].
Soft tissues | No ganglion, mass or collection. | [Ganglion / Soft tissue mass / Collection] [ ].

## ct.ankle-foot
! Fracture
! Ankle joint
! Hindfoot and midfoot
! Bones
> Bones
Distal tibia and fibula | No malleolar or tibial plafond fracture. | [Medial malleolar / Lateral malleolar / Posterior malleolar / Pilon] fracture, displacement [ ] mm. | Posterior malleolar fragment involving [ ] percent of the plafond.
Talus | Intact talar dome, neck and body. | [Talar dome / Talar neck / Talar body / Lateral process / Posterior process] fracture [ ].
Calcaneus | Intact. Normal Böhler angle. | Intra-articular calcaneal fracture, Sanders type [1 / 2 / 3 / 4]; Böhler angle [ ] degrees. | [Anterior process / Sustentacular / Tuberosity] fracture.
Navicular, cuboid and cuneiforms | No midfoot fracture. | [Navicular / Cuboid / Cuneiform] fracture [ ].
Metatarsals and phalanges | No metatarsal or phalangeal fracture. | [Metatarsal / Phalangeal] fracture of the [ ] ray, displacement [ ] mm.
> Joints and alignment
Ankle mortise and syndesmosis | Congruent ankle mortise. Normal distal tibiofibular relationship. | [Talar shift / Syndesmotic widening / Incongruent mortise] [ ] mm.
Subtalar and Chopart joints | Normally aligned subtalar, talonavicular and calcaneocuboid joints. | [Subluxation / Dislocation / Intra-articular fragment] of the [subtalar / talonavicular / calcaneocuboid] joint.
Lisfranc joint | Normal tarsometatarsal alignment. | Lisfranc injury: [homolateral / divergent / partial] displacement of the [ ] metatarsal bases; fleck sign [present / absent].
>
Bone lesion and soft tissues | No focal bone lesion. Normal soft tissues. | [Lytic lesion / Sclerotic lesion / Soft tissue swelling / Tendon entrapment] [ ].

## msk.mri-foot
! Bones
! Lisfranc and midfoot
! Forefoot
! Tendons and plantar fascia
> Bones
Tarsal bones | No tarsal fracture or bone marrow oedema. | [Stress fracture / Bone marrow oedema / Osteomyelitis] of the [ ].
Metatarsals | No metatarsal stress reaction or fracture. | [Stress reaction / Stress fracture / Freiberg infraction / Osteomyelitis] of the [ ] metatarsal.
Phalanges and sesamoids | Normal. | [Fracture / Bone marrow oedema / Sesamoiditis / Bipartite sesamoid] of the [ ].
> Joints and ligaments
Lisfranc joint and ligament | Intact Lisfranc ligament. Normal tarsometatarsal alignment. | [Partial / Complete] Lisfranc ligament tear; [first / second] intermetatarsal diastasis [ ] mm.
Metatarsophalangeal joints and plantar plates | Intact plantar plates. No metatarsophalangeal effusion or synovitis. | Plantar plate tear of the [ ] metatarsophalangeal joint. | [Synovitis / Effusion / Erosion / Hallux valgus] [ ].
Interphalangeal joints | Normal. | [Effusion / Erosion / Osteoarthritis] of the [ ].
> Tendons and fascia
Flexor tendons | Intact. | [Tenosynovitis / Tendinosis / Tear] of the [flexor hallucis longus / flexor digitorum longus] tendon [ ].
Extensor tendons | Intact. | [Tenosynovitis / Tendinosis / Tear] of the [ ] extensor tendon.
Peroneal and tibialis tendon insertions | Intact. | [Tendinosis / Tear] of the [peroneus brevis / peroneus longus / tibialis anterior / tibialis posterior] insertion.
Plantar fascia | Normal. | Plantar fasciitis: fascia [ ] mm thick. | Plantar fibroma [ ] mm.
>
Intermetatarsal spaces | No Morton neuroma or intermetatarsal bursitis. | Morton neuroma [ ] mm in the [second / third] intermetatarsal space. | Intermetatarsal bursitis in the [ ] space.
Muscles | Normal intrinsic foot muscles. | Muscle [oedema / atrophy / fatty infiltration] of the [ ].
= Soft tissues | No soft tissue mass, ganglion or collection.

## msk.ultrasound-foot
= Plantar fascia
! Forefoot
> Forefoot
Intermetatarsal spaces | No Morton neuroma or intermetatarsal bursitis. | Morton neuroma [ ] mm in the [second / third] intermetatarsal space. | Intermetatarsal bursitis in the [ ] space.
Metatarsophalangeal joints and plantar plates | Intact plantar plates. No metatarsophalangeal effusion or synovitis. | Plantar plate tear of the [ ] metatarsophalangeal joint. | Synovitis of the [ ] joint, Doppler grade [0 / 1 / 2 / 3].
Metatarsals | Smooth metatarsal cortices. | Periosteal reaction of the [ ] metatarsal in keeping with a stress fracture.
! Tendons
> Tendons
Flexor tendons | Normal. | [Tenosynovitis / Tear] of the [ ] flexor tendon.
Extensor tendons | Normal. | [Tenosynovitis / Tear] of the [ ] extensor tendon.
Peroneal and tibialis tendon insertions | Normal. | [Tendinosis / Tear] of the [peroneus brevis / tibialis anterior / tibialis posterior] insertion.
>
= Soft tissues

## ra.mri-diabetic-foot
= Ulcer and sinus tract
! Bone marrow
> Bones
Forefoot bones | No osteomyelitis of the metatarsals or phalanges. Normal T1 marrow signal. | Osteomyelitis of the [ ]: confluent low T1 and high T2 signal. | Reactive marrow oedema without T1 change at the [ ].
Midfoot and hindfoot bones | No osteomyelitis of the tarsal bones or calcaneus. | Osteomyelitis of the [ ]: confluent low T1 and high T2 signal. | Reactive marrow oedema without T1 change at the [ ].
>
= Joints and neuroarthropathy
Tendon sheaths | No septic tenosynovitis. | Tenosynovitis of the [ ] tendon sheath, in continuity with the ulcer.
= Soft tissues and muscles -> Muscles and soft tissues | No abscess, cellulitis or devitalised tissue. No muscle denervation change.
'''
