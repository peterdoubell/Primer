#!/usr/bin/env python3
"""Render complete original source image objects with PDF colour semantics at native-sized output."""
import argparse,hashlib,io,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from pypdf import PdfReader,PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
from PIL import Image,ImageCms
from tools.anatomy_sources.review_thyroid_pictorial_original import OBJECTS,PAGES

def sha(raw):return hashlib.sha256(raw).hexdigest()
def render(source,proof_dir):
    acquisition=json.loads((proof_dir/'original-source-review.json').read_text());pdf=source/'PMC8864691.1.pdf'
    if sha(pdf.read_bytes())!=acquisition['original_PDF_sha256']:raise ValueError('Original PDF fingerprint differs')
    reader=PdfReader(pdf);destination=source/'PDF-aware-display-review';destination.mkdir(exist_ok=True)
    intent=reader.trailer['/Root']['/OutputIntents'][0];source_profile=intent['/DestOutputProfile'].get_object().get_data()
    display_icc=destination/'display-sRGB.icc'
    display_profile=display_icc.read_bytes() if display_icc.exists() else ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    if ImageCms.getProfileName(ImageCms.ImageCmsProfile(io.BytesIO(display_profile))).strip()!='sRGB built-in':raise ValueError('Reviewed display profile differs')
    source_icc=destination/'source-FOGRA39.icc';source_icc.write_bytes(source_profile);display_icc=destination/'display-sRGB.icc';display_icc.write_bytes(display_profile)
    versions=subprocess.run(['/opt/homebrew/bin/pdftoppm','-v'],capture_output=True,text=True,check=True).stderr.strip();rows=[]
    for number,(ident,page_number) in enumerate(zip(OBJECTS,PAGES),1):
        original=reader.get_object(ident);writer=PdfWriter();page=writer.add_blank_page(width=original['/Width'],height=original['/Height']);clone=original.clone(writer)
        if clone._data!=original._data or clone.get_data()!=original.get_data():raise ValueError('Original image stream changed during isolation')
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Source'):clone.indirect_reference})})
        stream=DecodedStreamObject();stream.set_data(f'q {original["/Width"]} 0 0 {original["/Height"]} 0 0 cm /Source Do Q'.encode());page[NameObject('/Contents')]=writer._add_object(stream)
        # Preserve the original document output intent in addition to explicit renderer profiles.
        writer._root_object[NameObject('/OutputIntents')]=reader.trailer['/Root']['/OutputIntents'].clone(writer)
        isolated=destination/f'figure{number}-source-object.pdf';writer.write(isolated)
        output=destination/f'figure{number}-display';command=['/opt/homebrew/bin/pdftoppm','-r','72','-defaultcmykprofile',str(source_icc),'-displayprofile',str(display_icc),'-png','-singlefile',str(isolated),str(output)]
        subprocess.run(command,check=True,capture_output=True);path=output.with_suffix('.png')
        with Image.open(path) as image:
            image.load();pixels=image.tobytes();size=image.size
            if size!=(original['/Width'],original['/Height']) or image.mode!='RGB':raise ValueError('Native-sized display dimensions/mode differ')
            image.save(path,icc_profile=display_profile)
        with Image.open(path) as check:
            if check.tobytes()!=pixels or check.info.get('icc_profile')!=display_profile:raise ValueError('Lossless display packaging differs')
        rows.append({'figure_number':number,'original_PDF_object':ident,'original_PDF_page':page_number,'original_encoded_image_stream_sha256':sha(original._data),'isolated_source_PDF_sha256':sha(isolated.read_bytes()),'display_file':path.name,'display_sha256':sha(path.read_bytes()),'decoded_display_RGB_sha256':sha(pixels),'dimensions':list(size),'original_image_stream_and_decoded_channels_preserved_in_isolated_PDF':True,'entire_original_image_object_rendered':True,'post_render_resampling_or_anatomical_edits':False,'rendered_RGB_is_unchanged_native_source_samples':False})
    report={'original_PDF_sha256':sha(pdf.read_bytes()),'renderer':versions,'source_output_intent':str(intent['/Info']),'source_CMYK_profile_sha256':sha(source_profile),'display_sRGB_profile_sha256':sha(display_profile),'render_DPI':72,'isolated_page_points_equal_source_pixel_dimensions':True,'rendered_displays_are_derived_PDF_outputs':True,'figures':rows,'direct_ICC_shortcut_matches_PDF_DeviceN_renderer':False,'source_US_acquisition_or_diagnostic_display_calibration_verified':False,'all_display_figures_visually_reviewed':False,'clinical_approval':False,'runtime_promoted':False,'structure_coverage_granted':False}
    (proof_dir/'PDF-display-review.json').write_text(json.dumps(report,indent=2)+'\n');print('21 full source image objects rendered; original streams retained; no post-render spatial resampling')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--proof-dir',type=Path,required=True);a=p.parse_args();render(a.source_root,a.proof_dir)
