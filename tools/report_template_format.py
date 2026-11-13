"""Versioned formatting and authored normal summaries for reporting templates."""

KNEE_NORMAL_GROUPS = (
    (
        tuple(f'{side}-meniscus-{segment}' for segment in ('anterior-horn', 'body', 'posterior-horn')),
        f'No tear of the {side} meniscal anterior horn, body or posterior horn.',
    )
    for side in ('medial', 'lateral')
)
KNEE_NORMAL_GROUPS = tuple(KNEE_NORMAL_GROUPS) + (
    (('acl', 'pcl'), 'The ACL and PCL are intact with normal signal.'),
    (('quadriceps', 'patellar-tendon'), 'The quadriceps and patellar tendons are intact with normal signal.'),
    (('medial-femoral-cartilage', 'medial-tibial-cartilage'), 'Medial femoral and tibial cartilage is preserved.'),
    (('lateral-femoral-cartilage', 'lateral-tibial-cartilage'), 'Lateral femoral and tibial cartilage is preserved.'),
    (
        ('patellar-medial-cartilage', 'patellar-lateral-cartilage', 'patellar-ridge-cartilage', 'trochlear-cartilage'),
        'Cartilage at both patellar facets, the median ridge and the trochlea is preserved.',
    ),
)


def apply_report_format(forms, digest):
    for form in forms.values():
        for exam in form['investigations']:
            exam['report_format'] = 2
            if exam['id'] != 'ra.mri-knee':
                continue
            rows = {row['anatomy_id']: row for row in exam['sections']}
            exam['normal_summaries'] = []
            for keys, text in KNEE_NORMAL_GROUPS:
                members = [rows[key] for key in keys]
                if (any(not row['normal'] or row['normal']['slots']
                        or row.get('repeatable') or row.get('requires_scope') for row in members)
                        or len({row['report_section_id'] for row in members}) != 1):
                    raise ValueError(f'Unsafe normal summary membership: {keys}')
                exam['normal_summaries'].append({
                    'section_ids': [row['id'] for row in members],
                    'text': text,
                })
        form['schema_hash'] = digest({key: value for key, value in form.items() if key != 'schema_hash'})
