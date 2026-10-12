"""Freeze an owner intake/technical review; no clinical approval or publishing."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parents[2]
REVIEW=ROOT/'docs/pulmonary-nodule-source-review-20261011'
OUT=ROOT/'web/anatomy/lidc-idri-0525'
PRIVATE=ROOT/'.research/pulmonary-intake-20261011'


def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):return dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
def dump(name,value):(REVIEW/name).write_text(json.dumps(value,indent=2)+'\n')


def main():
    manifest=json.loads((OUT/'manifest.json').read_text());files=[]
    for path in sorted(OUT.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(OUT).as_posix()
        role=('authored-viewer-or-reviewed-manifest' if rel in ('reference.html','reference.js','manifest.json') else
              'unchanged-original-CT-DICOM' if rel.startswith('original-ct/') else
              'lossless-complete-CT-chunk' if rel.startswith('ct.native.') else
              'literal-native-SEG-boundary' if rel.endswith('.mesh.gz') else
              'native-SEG-face-oracle' if rel.endswith('.faces.gz') else
              'lossless-complete-released-SEG-array' if rel.endswith('.mask.gz') else
              'unchanged-released-SEG-SR-archive' if rel.startswith('source-') and rel.endswith('.zip') else
              'source-license-or-attribution' if rel in ('LICENSE','ATTRIBUTION.txt') else
              'unchanged-source-XML-or-checksum-file')
        files.append(dict(path=str(path.relative_to(ROOT)),relative_path=rel,role=role,**pin(path)))
    assert len(files)==483 and max(x['bytes'] for x in files)<100*1024*1024
    names=['current-scope-snapshot.json','native-build-proof.json','source-parity-check.json','original-XML-SR-check.json',
           'original-DICOM-pixel-oracle.json','complete-clinical-question-proposal.json','structure-requirements-proposal.json','reporting-proposal.json','browser-owner/proof.json']
    pins={str((REVIEW/name).relative_to(ROOT)):pin(REVIEW/name) for name in names}
    browser=json.loads((REVIEW/'browser-owner/proof.json').read_text())
    assert browser['manifest_sha256']==sha((OUT/'manifest.json').read_bytes())
    assert browser['js_sha256']==sha((OUT/'reference.js').read_bytes())
    assert browser['html_sha256']==sha((OUT/'reference.html').read_bytes())
    rights=dict(schema_version=1,status='owner_source_reuse_review_GO_subject_to_attribution_and_TCIA_policy; independent_review_pending',
        case=manifest['case'],source_CT_dataset_DOI=manifest['dataset_doi'],released_SEG_SR_dataset_DOI=manifest['annotation_doi'],
        license='CC BY3.0',license_url=manifest['license_url'],archive_license_retained=True,
        full_citations_retained='web/anatomy/lidc-idri-0525/ATTRIBUTION.txt',
        commercial_educational_adaptation_and_redistribution_permitted_under_recorded_CC_BY3=True,
        TCIA_policy_attribution_and_downstream_requirements_retained=True,
        TCIA_DAC_listing_contact_is_suggested_not_redistribution_permission_clause=True,
        no_permission_request_or_external_message_sent=True,no_participant_identification_or_contact_attempt=True,
        article_artwork_included=False,clinical_approval=False,fine_anatomical_approval=False,data_terms_are_not_clinical_approval=True,
        preserved_issue='getImageWithMD5Hash returns MD5 checksums but no LICENSE; actual getImage archives were separately inspected and retain the LICENSE. The standardized analysis is returned under Collection=LIDC-IDRI, with its separate analysis DOI; querying Collection=DICOM-LIDC-IDRI-Nodules returned an empty body. The initial legalcode URL returned403; the canonical English legalcode.en returned200. No source terms were inferred from an access error.',
        primary_rights_file_pins={name:pin(PRIVATE/name) for name in ['lidc-collection.html','dicom-seg-collection.html','CT-LICENSE','seg-getImage-with-license-check.zip','all-0525.json','tcia-usage-policy.html','tcia-dac.html','cc-by-3-legal.html']})
    dump('source-rights-owner-review.json',rights)
    proposal=dict(schema_version=1,base_commit='781ac4e863dda3bcca9002ced356d70aba256657',case=manifest['case'],
        investigation_ids=['ra.ct-pulmonary-nodules'],lesson_ids=['rad.4.pulmonary-nodule'],
        candidate_native_inspector='/app/anatomy/lidc-idri-0525/reference.html',manifest_sha256=sha((OUT/'manifest.json').read_bytes()),
        runtime_files=files,runtime_file_count=len(files),runtime_source_payload_files=len(files)-3,
        runtime_source_payload_bytes=sum(x['bytes'] for x in files if x['role']!='authored-viewer-or-reviewed-manifest'),
        no_runtime_file_over_100MiB=True,largest_runtime_file_bytes=max(x['bytes'] for x in files),
        whole_CT_native_samples=112459776,whole_released_SEG_native_samples=19136512,
        original_XML_reading_sessions=4,original_XML_marks=33,drawn_nodule_annotations=8,small_nodule_loci=8,non_nodule_loci=17,
        original_XML_exclusion_contours=1,complete_released_SEG_objects=8,complete_released_SR_objects=8,
        complete_cell_boundary_triangles=12568,originals_unmodified=True,source_pixels_repainted=False,
        source_resampling=False,source_geometry_smoothing=False,named_fine_anatomy_bindings=[],
        clinical_approval=False,fine_anatomical_approval=False,structure_coverage_granted=False,runtime_integrated=False,
        curriculum_or_shared_reporting_registry_modified=False,no_merge_push_upload_deploy_or_publish=True,proof_pins=pins,
        owner_source_rights_review_sha256=sha((REVIEW/'source-rights-owner-review.json').read_bytes()),
        remaining_gates=[
          'Independent byte/rights/whole-study and scientific review of this candidate',
          'Authenticated reporting and shared-lesson integration with exact pinned case/source bindings',
          'Fixed reviewed source delivery for all480payloads, preserving original license/attribution and MIME/CORS/byte identity',
          'Current whole-module source/rubric correction integration with original13questions preserved',
          'Actual native expert-reviewed lobe/segment/airway/vessel/pleural and diagnostic-feature representations for every required reporting structure',
          'Genuine matched prior/PET source examples and full morphology coverage; no fabricated study or diagnosis',
          'Clinical/fine-anatomical and representative reader review; owner technical parity cannot satisfy these gates'],
        thickness_scope_note='Original SliceThickness0.75mm is nominal reconstructed thickness; reconstructed centres are independently preserved at approximately0.7mm and pixel spacing is0.53710938mm. Actual acquired collimation is not independently verified; SingleCollimationWidth/TotalCollimationWidth are absent.',
        review_commands=['python tools/check_pulmonary_native_source.py','python tools/check_pulmonary_source_sr.py','python tools/anatomy_sources/pulmonary_scope_proposal.py','python tools/anatomy_sources/pulmonary_pixel_oracle.py','node tools/check_pulmonary_native_browser.js'],
        source_intake_archives_private=str(PRIVATE),standalone_browser_fixture='http://127.0.0.1:58271/anatomy/lidc-idri-0525/reference.html')
    dump('integration-proposal.json',proposal)
    print(json.dumps(dict(runtime_files=len(files),source_payload_files=len(files)-3,source_payload_bytes=proposal['runtime_source_payload_bytes'],
                         largest_file_bytes=proposal['largest_runtime_file_bytes'],manifest_sha256=proposal['manifest_sha256'],
                         rights_sha256=proposal['owner_source_rights_review_sha256'],proposal_sha256=sha((REVIEW/'integration-proposal.json').read_bytes()),proof_pins=pins),indent=2))


if __name__=='__main__':main()
