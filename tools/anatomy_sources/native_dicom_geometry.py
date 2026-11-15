"""Construct a native slice/row/column transform without resampling a CT stack."""
import math


def vector(values, length):
    result = [float(v) for v in values]
    if len(result) != length or not all(math.isfinite(v) for v in result):
        raise ValueError('Invalid source geometry vector')
    return result


def dot(a, b):
    return sum(x*y for x,y in zip(a,b))


def close(a, b, tolerance):
    return len(a) == len(b) and all(abs(x-y) <= tolerance for x,y in zip(a,b))


def validate_geometry(frames, tolerance_mm=1e-5):
    if len(frames) < 2:
        raise ValueError('A 3D stack needs at least two source planes')
    first = frames[0]
    orientation = vector(first['orientation'], 6)
    spacing = vector(first['pixel_spacing_mm'], 2)
    if any(v <= 0 for v in spacing):
        raise ValueError('Invalid pixel spacing')
    if any(type(first[k]) is not int or first[k] <= 0 for k in ('rows','columns')):
        raise ValueError('Invalid matrix size')
    column_axis, row_axis = orientation[:3], orientation[3:]
    if (abs(dot(column_axis,column_axis)-1) > 1e-6
            or abs(dot(row_axis,row_axis)-1) > 1e-6
            or abs(dot(column_axis,row_axis)) > 1e-6):
        raise ValueError('DICOM direction cosines are not orthonormal')
    a,b = column_axis,row_axis
    normal = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    # DICOM direction cosines may be rounded. Normalize the derived normal
    # for physical distances; retain the supplied in-plane direction values.
    normal_length = math.sqrt(dot(normal,normal))
    normal = [v/normal_length for v in normal]
    positions = []
    for frame in frames:
        if (frame['rows'],frame['columns']) != (first['rows'],first['columns']):
            raise ValueError('Matrix size changes within the series')
        if not close(vector(frame['orientation'],6),orientation,1e-6):
            raise ValueError('Orientation changes within the series')
        if not close(vector(frame['pixel_spacing_mm'],2),spacing,1e-8):
            raise ValueError('Pixel spacing changes within the series')
        positions.append(vector(frame['position_mm'],3))
    order = sorted(range(len(frames)),key=lambda i:dot(positions[i],normal))
    ordered = [positions[i] for i in order]
    projections = [dot(p,normal) for p in ordered]
    steps = [b-a for a,b in zip(projections,projections[1:])]
    if min(steps) <= tolerance_mm:
        raise ValueError('Duplicate or indistinguishable source planes')
    if any(abs(step-steps[0]) > tolerance_mm for step in steps):
        raise ValueError('Irregular plane spacing; resampling is not permitted')
    step = (projections[-1]-projections[0])/(len(ordered)-1)
    affine_errors = [abs(position-(projections[0]+index*step))
                     for index,position in enumerate(projections)]
    if max(affine_errors) > tolerance_mm:
        raise ValueError('Plane positions cannot be represented by one native affine')
    for position in ordered:
        displacement = [x-y for x,y in zip(position,ordered[0])]
        projection = dot(displacement,normal)
        drift = [x-projection*n for x,n in zip(displacement,normal)]
        if math.sqrt(dot(drift,drift)) > tolerance_mm:
            raise ValueError('In-plane origins drift; do not silently shear the volume')
    # Matrix maps [slice, row, column, 1] to the original DICOM LPS coordinates.
    affine = [[normal[i]*step,row_axis[i]*spacing[0],column_axis[i]*spacing[1],ordered[0][i]] for i in range(3)]
    affine.append([0,0,0,1])
    return {
        'source_frame_order': order,
        'array_axis_order': ['slice','row','column'],
        'shape': [len(frames),first['rows'],first['columns']],
        'index_to_dicom_lps_mm': affine,
        'slice_step_mm': step,
        'maximum_plane_affine_error_mm': max(affine_errors),
        'resampled': False,
        'anatomical_orientation_independently_verified': False,
        'complete_anatomical_extent_proven': False,
    }
