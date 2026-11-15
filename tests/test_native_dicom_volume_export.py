"""Exercise original-voxel export with a small synthetic rotated CT series."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

AVAILABLE = all(importlib.util.find_spec(name) for name in ('numpy','pydicom'))
if AVAILABLE:
    import numpy as np
    import pydicom
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.uid import ExplicitVRLittleEndian, CTImageStorage, generate_uid

ROOT = Path(__file__).resolve().parents[1]
from tools.anatomy_sources.dicom_ct_units import CT_IMAGE_STORAGE, resolve_ct_units


@unittest.skipUnless(AVAILABLE, 'Scientific source dependencies are optional for the app runtime')
class NativeVolumeExport(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='primer-native-volume-test-')
        self.root = Path(self.directory.name)
        self.archive = self.root/'synthetic.zip'
        self.pixels = {}
        self.frames = []
        series_uid = generate_uid()
        with zipfile.ZipFile(self.archive,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for k in (2,0,1):
                meta = FileMetaDataset()
                meta.MediaStorageSOPClassUID = CTImageStorage
                meta.MediaStorageSOPInstanceUID = generate_uid()
                meta.TransferSyntaxUID = ExplicitVRLittleEndian
                ds = FileDataset(None,{},file_meta=meta,preamble=b'\0'*128)
                ds.SOPClassUID = CTImageStorage
                ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
                ds.SeriesInstanceUID = series_uid
                ds.InstanceNumber = k
                ds.Modality = 'CT'
                ds.ImageType = ['ORIGINAL','PRIMARY','AXIAL']
                ds.Rows,ds.Columns = 2,3
                ds.SamplesPerPixel = 1
                ds.PhotometricInterpretation = 'MONOCHROME2'
                ds.BitsAllocated = ds.BitsStored = 16
                ds.HighBit = 15
                ds.PixelRepresentation = 1
                ds.ImageOrientationPatient = [0,1,0,0,0,1]
                ds.ImagePositionPatient = [10+k*.7,20,30]
                ds.PixelSpacing = [.2,.3]
                ds.SliceThickness = .5
                ds.RescaleSlope,ds.RescaleIntercept = 1+k,-1000+k*10
                ds.RescaleType = 'HU'
                pixels = np.array([[-32768,k,32767],[100+k,-100-k,42]],dtype='<i2')
                self.pixels[k] = pixels
                ds.PixelData = pixels.tobytes()
                raw = io.BytesIO();ds.save_as(raw,enforce_file_format=True)
                name=f'plane-{k}.dcm';archive.writestr(name,raw.getvalue())
                self.frames.append(dict(member=name,rows=2,columns=3,orientation=[0,1,0,0,0,1],position_mm=[10+k*.7,20,30],pixel_spacing_mm=[.2,.3],rescale_slope=1+k,rescale_intercept=-1000+k*10,rescale_type='HU',sop_class_uid=CT_IMAGE_STORAGE,image_type=['ORIGINAL','PRIMARY','AXIAL'],multi_energy_ct=None,rescale_units=resolve_ct_units(CT_IMAGE_STORAGE,['ORIGINAL','PRIMARY','AXIAL'],'HU')))
        with zipfile.ZipFile(self.archive) as archive:
            assert archive.testzip() is None
        self.audit = dict(source_doi='synthetic-test-only',archive=dict(bytes=self.archive.stat().st_size,sha256=hashlib.sha256(self.archive.read_bytes()).hexdigest(),all_member_crcs_valid=True),frames=self.frames)

    def tearDown(self):
        self.directory.cleanup()

    def execute(self,audit,optimized=False):
        path=self.root/'audit.json';path.write_text(json.dumps(audit))
        output=self.root/'output'
        result=subprocess.run([sys.executable,*(['-O'] if optimized else []),str(ROOT/'tools/anatomy_sources/export_leeds_spine_native_volume.py'),'--archive',str(self.archive),'--audit',str(path),'--output',str(output)],capture_output=True,text=True)
        return result,output

    def test_exact_signed_voxels_physical_order_and_per_frame_calibration(self):
        result,output=self.execute(self.audit)
        self.assertEqual(result.returncode,0,result.stderr)
        array=np.load(output/'native-int16.npy',allow_pickle=False)
        self.assertTrue(np.array_equal(array,np.stack([self.pixels[i] for i in range(3)])))
        manifest=json.loads((output/'native-volume.json').read_text())
        self.assertEqual([f['rescale_slope'] for f in manifest['frame_records']],[1,2,3])
        self.assertFalse(manifest['geometry']['resampled'])
        self.assertFalse(manifest['geometry']['complete_anatomical_extent_proven'])

    def test_changed_audit_coordinates_cannot_change_source_geometry(self):
        audit=copy.deepcopy(self.audit)
        for frame in audit['frames']:frame['position_mm'][0]+=4
        result,output=self.execute(audit)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Audited position differs from DICOM',result.stderr)
        self.assertFalse((output/'native-int16.npy').exists())

    def test_a_regular_but_decimated_frame_list_is_rejected(self):
        audit=copy.deepcopy(self.audit);audit['frames']=[audit['frames'][0],audit['frames'][1]]
        result,output=self.execute(audit)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((output/'native-int16.npy').exists())

    def test_optimized_python_still_rejects_changed_coordinates(self):
        audit=copy.deepcopy(self.audit)
        for frame in audit['frames']:frame['position_mm'][0]+=4
        result,output=self.execute(audit,optimized=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Audited position differs from DICOM',result.stderr)
        self.assertFalse((output/'native-int16.npy').exists())

    def test_optimized_python_still_rejects_wrong_source_hash(self):
        audit=copy.deepcopy(self.audit);audit['archive']['sha256']='0'*64
        result,output=self.execute(audit,optimized=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Audited archive changed',result.stderr)
        self.assertFalse((output/'native-int16.npy').exists())

    def test_optimized_audit_rejects_an_unrelated_valid_ct_archive(self):
        output=self.root/'unrelated-audit'
        result=subprocess.run([sys.executable,'-O',str(ROOT/'tools/anatomy_sources/audit_leeds_spine_source.py'),
                               '--donor','3','--archive',str(self.archive),'--output',str(output)],
                              capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Archive incomplete or changed',result.stderr)
        self.assertFalse((output/'native-audit.json').exists())

    def test_wrong_unit_metadata_cannot_relabel_identical_voxels(self):
        audit=copy.deepcopy(self.audit)
        for frame in audit['frames']:frame['rescale_units']['units']='MGML'
        result,output=self.execute(audit,optimized=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Audited intensity-unit context differs from DICOM',result.stderr)
        self.assertFalse((output/'native-int16.npy').exists())


if __name__=='__main__':
    unittest.main()
