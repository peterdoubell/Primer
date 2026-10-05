#!/usr/bin/env python3
"""Project every original native wall polygon and source edge finding without repair."""
import argparse
import array
import base64
import gzip
import hashlib
import json
from pathlib import Path


def decode(record):
    raw = base64.b64decode(record['base64'], validate=True)
    if hashlib.sha256(raw).hexdigest() != record['sha256']:
        raise ValueError('Preserved original array changed')
    a = array.array(record['typecode']); a.frombytes(raw)
    if len(a) != record['count'] or record['byte_order'] != 'little':
        raise ValueError('Native array type/count differs')
    return a


def render(output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
    from tools.anatomy_sources.review_zanatomy_wall_source import native_polygons
    path = output / 'native-wall-review.json'; raw = path.read_bytes(); report = json.loads(raw)
    figures = []
    for geometry in report['geometries']:
        packed = (output / geometry['file']).read_bytes(); payload = gzip.decompress(packed)
        if hashlib.sha256(packed).hexdigest() != geometry['compressed_sha256'] or hashlib.sha256(payload).hexdigest() != geometry['uncompressed_sha256']:
            raise ValueError('Native source evidence changed')
        source = json.loads(payload); local = np.asarray(decode(source['positions'])).reshape(-1, 3)
        polygons = native_polygons(decode(source['polygon_vertex_index']), len(local))
        instances = [i for i in report['instances'] if i['source_geometry_id'] == geometry['geometry_id']]
        fig = plt.figure(figsize=(14, 6.5 if len(instances)==1 else 5 * len(instances)))
        panels = []
        for row, part in enumerate(instances):
            matrix = np.asarray(part['world_transform_columns']).T
            world = np.column_stack([local, np.ones(len(local))]) @ matrix.T
            if hashlib.sha256(world.astype('<f8').tobytes()).hexdigest() != part['world_positions_float64_cm_sha256']:
                raise ValueError('Original source instance transform differs')
            points = world * 10
            face_points = [points[p] for p in polygons]
            native_normals=np.asarray(decode(source['original_layers']['LayerElementNormal']['Normals'])).reshape(-1,3)
            normal_matrix=np.linalg.inv(matrix[:,:3]).T
            world_normals=native_normals@normal_matrix.T
            offsets=np.cumsum([0]+[len(p) for p in polygons])
            face_normals=np.asarray([world_normals[offsets[i]:offsets[i+1]].mean(0) for i in range(len(polygons))])
            lengths=np.linalg.norm(face_normals,axis=1)
            face_normals=np.divide(face_normals,lengths[:,None],out=np.zeros_like(face_normals),where=lengths[:,None]>0)
            light=np.array([1,2,1],float);light/=np.linalg.norm(light)
            colours=np.tile([.51,.60,.73,1],(len(polygons),1));colours[:,:3]*=(.55+.45*np.maximum(face_normals@light,0))[:,None]

            lo, hi = points.min(0), points.max(0); extent = np.maximum(hi-lo, .1); pad = extent*.05
            for col, azimuth in enumerate([35, 215]):
                ax = fig.add_subplot(len(instances), 2, row*2+col+1, projection='3d')
                ax.add_collection3d(Poly3DCollection(face_points, facecolors=colours, edgecolors='none', linewidths=0))
                for field, colour in [('boundary', '#c13847'), ('inconsistent_winding', '#dd9421')]:
                    selected = [points[e['source_vertex_indices']] for e in source['source_edge_findings'] if e[field]]
                    if selected: ax.add_collection3d(Line3DCollection(selected, colors=colour, linewidths=1.3))
                unused = source['unreferenced_source_position_indices']
                if unused: ax.scatter(*points[unused].T, color='#171b1f', s=15)
                ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_zlim(lo[2]-pad[2],hi[2]+pad[2])
                ax.view_init(elev=20,azim=azimuth,vertical_axis='y');ax.set_box_aspect(extent);ax.locator_params(nbins=3)
                ax.tick_params(labelsize=7);ax.set_xlabel('Source X mm',fontsize=8);ax.set_ylabel('Source Y mm',fontsize=8,labelpad=30);ax.set_zlabel('\nSource Z mm',fontsize=8)
                if extent.max()/extent[0]>10:ax.set_xlabel('Source X mm',fontsize=8,labelpad=25)
                for axis,short in enumerate(extent.max()/extent>7):
                    if short:[ax.set_xticks,ax.set_yticks,ax.set_zticks][axis]([])
                ax.set_title(part['name'] + (' | source reflected instance' if part['native_reflected_instance'] else '') +
                    '\n' + str(len(polygons)) + ' native faces | azimuth ' + str(azimuth), fontsize=9)
                panels.append({'source_model_id':part['source_model_id'],'source_geometry_id':part['source_geometry_id'],
                    'azimuth':azimuth,'all_native_faces_displayed':len(polygons),
                    'boundary_edges_displayed':sum(e['boundary'] for e in source['source_edge_findings']),
                    'inconsistent_winding_edges_displayed':sum(e['inconsistent_winding'] for e in source['source_edge_findings']),
                    'unused_source_positions_displayed':len(unused),'world_position_sha256':part['world_positions_float64_cm_sha256'],
                    'source_geometry_changed':False})
        fig.suptitle('Original Z-Anatomy wall geometry | every native polygon and source instance\nRed: source boundary edges; amber: inconsistent winding; black: unreferenced positions\nNonplanar faces use projected fill; no tissue thickness, repair, fitting or clinical approval',fontsize=11)
        fig.subplots_adjust(left=.04,right=.95,bottom=.24 if len(instances)==1 else .14,top=.76 if len(instances)==1 else .88,hspace=.38,wspace=.2)
        fig.text(.5,.025,'Z-Anatomy / BodyParts3D DBCLS | CC BY-SA 4.0; original BodyParts3D lineage CC BY-SA 2.1 Japan\nAdaptation: original-array review projections, source instance transforms, display colours and edge markers',ha='center',fontsize=8)
        file = str(geometry['geometry_id']) + '-original-wall-source.png'; target = output / file
        fig.savefig(target,dpi=120);plt.close(fig)
        figures.append({'file':file,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'panels':panels})
    (output/'projection-review.json').write_text(json.dumps({'source_review_sha256':hashlib.sha256(raw).hexdigest(),
        'figures':figures,'source_geometry_changed':False,'clinical_approval':False,'runtime_promoted':False,
        'derived_figure_license':'CC BY-SA 4.0'},indent=2)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    render(p.parse_args().output)
