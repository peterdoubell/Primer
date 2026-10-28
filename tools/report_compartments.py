"""Presentation-only anatomical compartments; descriptor identities stay unchanged.

Existing authored groups remain subgroups. No findings, measurements, normal
statements, scope conditions or calculation bindings are authored here.
"""
import re

VERSION = '2026-10-28'


def compartment(exam, row):
    identifier = exam['id']
    region = identifier + ' ' + exam.get('base_investigation_id', '')
    key = row.get('anatomy_id', row['id'].removeprefix('anatomy-'))
    group = row.get('group') or row.get('report_section_label') or row['label']
    g = group.lower()
    if g in ('technique', 'examination', 'acquisition', 'optional acquisition', 'additional acquisitions', 'additional sequences', 'coverage'):
        return 'Technique'
    if 'knee' in region:
        if g in ('ligament reconstruction', 'postoperative complications', 'meniscal surgery', 'cartilage repair', 'reconstruction tunnels', 'postoperative findings', 'implant identification'):
            return 'Postoperative assessment'
        if any(t in key for t in ('patell', 'trochlear', 'quadriceps', 'hoffa', 'plica')) or g in ('patellofemoral stabilisers', 'patellofemoral cartilage', 'extensor mechanism', 'anterior soft tissues'):
            return 'Patellofemoral compartment and extensor mechanism'
        if key in ('acl','pcl','meniscofemoral-humphrey','meniscofemoral-wrisberg','transverse-meniscal-ligament') or g in ('cruciate ligaments', 'meniscal attachments'):
            return 'Central / intercondylar compartment'
        if g in ('posterior muscles','muscles / nerves') or key in ('baker-cyst', 'knee-muscles','tibial-nerve','common-peroneal-nerve'):
            return 'Posterior soft tissues and neurovascular structures'
        if g in ('medial meniscus','medial stabilisers','posteromedial tendons','pes anserinus','medial cartilage') or key.startswith(('medial-', 'mcl-', 'pes-')):
            return 'Medial compartment'
        if g in ('lateral meniscus','posterolateral corner','lateral stabilisers','lateral cartilage') or key.startswith(('lateral-', 'fibular-head','proximal-tibiofibular')):
            return 'Lateral compartment and posterolateral corner'
        return 'Joint-wide assessment and remaining bone'
    if 'ankle' in region and exam.get('modality') in ('MRI','Ultrasound'):
        if g in ('medial tendons','superficial deltoid','deep deltoid','spring ligament complex') or key in ('flexor-retinaculum','tarsal-tunnel','tibial-nerve-ankle'):
            return 'Medial compartment'
        if g in ('lateral tendons','lateral ligaments') or 'peroneal-retinaculum' in key:
            return 'Lateral compartment'
        if g == 'anterior tendons' or 'extensor-retinaculum' in key:
            return 'Anterior compartment'
        if g == 'posterior tendons' or key in ('posterior-impingement','retrocalcaneal-bursa','superficial-achilles-bursa'):
            return 'Posterior compartment'
        if g == 'syndesmosis': return 'Distal tibiofibular syndesmosis'
        if g in ('midfoot ligaments','sinus tarsi ligaments','sinus tarsi','plantar structures','plantar midfoot ligaments'):
            return 'Hindfoot / midfoot and plantar structures'
        return 'Articular surfaces, bone and joint-wide assessment'
    if 'elbow' in region and exam.get('modality') in ('MRI','Ultrasound'):
        if key.startswith(('ucl-','common-flexor','medial-epicondyle','flexor-pronator','ulnar-nerve')): return 'Medial compartment'
        if key.startswith(('common-extensor','rcl','lucl','annular','lateral-epicondyle','radial-nerve','pin','extensor-supinator','supinator')): return 'Lateral compartment'
        if key.startswith(('distal-biceps','brachialis','biceps-muscle','bicipitoradial','anterior-capsule','median-nerve','pronator-teres')): return 'Anterior compartment'
        if key.startswith(('triceps','olecranon','anconeus','posterior-capsule')): return 'Posterior compartment'
        return 'Articulations, remaining bone and joint contents'
    if 'shoulder' in region and exam.get('modality') in ('MRI','Ultrasound'):
        if 'rotator cuff' in g or g == 'tendon repair': return 'Rotator cuff'
        if 'biceps' in g: return 'Biceps and rotator interval'
        if g in ('labrum','capsule and glenohumeral ligaments','labral repair'): return 'Labrum, capsule and stability'
        if g == 'acromial arch and ac joint' or key in ('acromion-bone','distal-clavicle','sasdb'): return 'Acromial arch, AC joint and subacromial space'
        if g in ('glenohumeral joint','bones'): return 'Glenohumeral articulation and bone'
        return 'Other periarticular and neurovascular structures'
    if 'hip' in region and exam.get('modality') in ('MRI','Ultrasound'):
        if g in ('abductor tendons',) or key.startswith(('gluteus-medius','gluteus-minimus','subgluteus','trochanteric','greater-trochanter')): return 'Lateral / peritrochanteric compartment'
        if g == 'anterior tendons' or key.startswith('iliopsoas'): return 'Anterior compartment'
        if g == 'adductor tendons' or key == 'obturator-externus': return 'Medial / adductor compartment'
        if g == 'hamstring origins' or key in ('gluteus-maximus-muscle','piriformis','quadratus-femoris','obturator-internus','ischial-tuberosity','ischial-bursa','sciatic-nerve'): return 'Posterior / deep gluteal compartment'
        return 'Hip articulation, labrum and remaining bone'
    if 'wrist' in region and exam.get('modality') in ('MRI','Ultrasound'):
        if g.startswith('extensor compartment') or key == 'extensor-retinaculum': return 'Dorsal / extensor compartments'
        if g in ('flexors',) or key in ('flexor-retinaculum','median-nerve','ulnar-nerve'): return 'Volar / flexor and nerve compartments'
        if g.startswith('tfcc') or key in ('distal-radioulnar-joint','distal-ulna','ulnar-variance','ulnar-collateral-ligament'): return 'Ulnar side / TFCC and distal radioulnar joint'
        return 'Radiocarpal / midcarpal articulation and bone'
    if identifier == 'msk.mri-foot':
        if g in ('lisfranc complex','midfoot tendon insertions','plantar midfoot ligaments'): return 'Midfoot / Lisfranc complex'
        if g in ('hallux tendons','hallux sesamoid complex'): return 'Hallux and sesamoid complex'
        if g in ('plantar plates','mtp collateral ligaments','mtp joints','metatarsals','phalanges','lesser toe tendons','intermetatarsal spaces','intermetatarsal ligaments','interphalangeal joints'): return 'Forefoot and digital rays'
        return 'Remaining bone and plantar soft tissues'
    # Non-MSK studies already have authored organs, spaces, sides, vessel
    # territories or spinal levels. Retain these explicit boundaries instead
    # of imposing unrelated joint compartments or guessing from findings.
    return group


def apply_compartments(forms, digest):
    for form in forms.values():
        for exam in form['investigations']:
            buckets = {}
            for row in exam['sections']:
                label = compartment(exam, row)
                row['compartment'] = label
                row['report_section_id'] = 'compartment-' + re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')
                row['report_section_label'] = label.upper()
                buckets.setdefault(label, []).append(row)
            if 'knee' in exam['id']:
                order = ['Technique','Medial compartment','Lateral compartment and posterolateral corner','Patellofemoral compartment and extensor mechanism','Central / intercondylar compartment','Posterior soft tissues and neurovascular structures','Joint-wide assessment and remaining bone','Postoperative assessment']
                buckets = {k:buckets[k] for k in order if k in buckets}
            exam['compartments'] = []
            ordered = []
            for label, rows in buckets.items():
                # Keep each authored subgroup contiguous, including late-added
                # structures. IDs and selections never depend on visual order.
                groups = {}
                for row in rows: groups.setdefault(row.get('group', row['label']), []).append(row)
                rows = [row for items in groups.values() for row in items]
                ordered.extend(rows)
                exam['compartments'].append({'id':re.sub(r'[^a-z0-9]+','-',label.lower()).strip('-'), 'label':label, 'section_ids':[row['id'] for row in rows]})
            if len(ordered) != len(exam['sections']): raise ValueError('Compartment mapping lost rows: '+exam['id'])
            exam['sections'] = ordered
            exam['presentation_revision'] = VERSION
        form['schema_hash'] = digest({k:v for k,v in form.items() if k != 'schema_hash'})
