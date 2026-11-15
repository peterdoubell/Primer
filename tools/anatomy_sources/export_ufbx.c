/* Research staging exporter: native FBX world positions, source normals, native
 * triangulation. No decimation, guessed registration, remote resources or code.
 * Build against pinned official ufbx source; see acquire_z_anatomy.py. */
#include "ufbx.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <float.h>

static void text(ufbx_string s) {putchar('"');for(size_t i=0;i<s.length;i++){unsigned char c=s.data[i];if(c=='"'||c=='\\')printf("\\%c",c);else if(c<32)printf("\\u%04x",c);else putchar(c);}putchar('"');}
static int cmp_u64(const void*a,const void*b){uint64_t x=*(const uint64_t*)a,y=*(const uint64_t*)b;return(x>y)-(x<y);}
static uint32_t lookup(uint64_t *keys,size_t n,uint64_t key){size_t lo=0,hi=n;while(lo<hi){size_t mid=(lo+hi)/2;if(keys[mid]<key)lo=mid+1;else hi=mid;}if(lo>=n||keys[lo]!=key){fprintf(stderr,"Missing vertex key\n");exit(2);}return(uint32_t)lo;}
static uint64_t vertex_key(ufbx_mesh*m,size_t i){return ((uint64_t)m->vertex_indices.data[i]<<32)|(m->vertex_normal.exists?m->vertex_normal.indices.data[i]:0);}
static long long source_id(ufbx_element*e){return e->dom_node&&e->dom_node->values.count?(long long)e->dom_node->values.data[0].value_int:-1;}
static int selected(ufbx_string name,char **names,size_t count){for(size_t i=0;i<count;i++)if(strlen(names[i])==name.length&&!memcmp(names[i],name.data,name.length))return 1;return 0;}
int main(int argc,char**argv){
 if(argc<2){fprintf(stderr,"usage: export_ufbx source.fbx [output-dir names.txt]\n");return 2;}
 char **names=NULL;size_t count=0;if(argc==4){FILE*f=fopen(argv[3],"r");if(!f)return 2;char line[2048];while(fgets(line,sizeof line,f)){line[strcspn(line,"\r\n")]=0;if(!line[0])continue;names=realloc(names,(count+1)*sizeof(char*));names[count++]=strdup(line);}fclose(f);}
 ufbx_load_opts opts={0};opts.ignore_animation=true;opts.ignore_embedded=true;opts.load_external_files=false;opts.retain_dom=true;opts.generate_missing_normals=true;
 ufbx_error error;ufbx_scene *scene=ufbx_load_file(argv[1],&opts,&error);if(!scene){char buf[2048];ufbx_format_error(buf,sizeof buf,&error);fprintf(stderr,"%s\n",buf);return 1;}
 printf("{\"unit_meters\":%.17g,\"axes\":{\"right\":%d,\"up\":%d,\"front\":%d},\"meshes\":[",scene->settings.unit_meters,scene->settings.axes.right,scene->settings.axes.up,scene->settings.axes.front);
 int first=1;for(size_t ni=0;ni<scene->nodes.count;ni++){
  ufbx_node*node=scene->nodes.data[ni];ufbx_mesh*mesh=node->mesh;if(!mesh)continue;
  int write=argc==4&&selected(node->name,names,count);
  ufbx_matrix matrix=node->geometry_to_world,norm_matrix=ufbx_matrix_for_normals(&matrix);
  double bounds[2][3]={{DBL_MAX,DBL_MAX,DBL_MAX},{-DBL_MAX,-DBL_MAX,-DBL_MAX}};
  for(size_t i=0;i<mesh->vertices.count;i++){ufbx_vec3 p=ufbx_transform_position(&matrix,mesh->vertices.data[i]);for(int a=0;a<3;a++){double v=p.v[a];if(!isfinite(v))return 3;if(v<bounds[0][a])bounds[0][a]=v;if(v>bounds[1][a])bounds[1][a]=v;}}
  if(!first)putchar(',');first=0;printf("{\"name\":");text(node->name);printf(",\"mesh_name\":");text(mesh->name);
  printf(",\"source_model_id\":%lld,\"source_geometry_id\":%lld,\"source_vertices\":%zu,\"triangles\":%zu,\"world_transform_columns\":[",source_id(&node->element),source_id(&mesh->element),mesh->num_vertices,mesh->num_triangles);
  for(int c=0;c<4;c++)printf("%s[%.17g,%.17g,%.17g]",c?",":"",matrix.cols[c].x,matrix.cols[c].y,matrix.cols[c].z);
  printf("],\"bounds\":[[%.17g,%.17g,%.17g],[%.17g,%.17g,%.17g]],\"ancestors\":[",bounds[0][0],bounds[0][1],bounds[0][2],bounds[1][0],bounds[1][1],bounds[1][2]);
  int fp=1;for(ufbx_node*p=node->parent;p;p=p->parent){if(!fp)putchar(',');fp=0;text(p->name);}putchar(']');printf(",\"materials\":[");for(size_t mi=0;mi<node->materials.count;mi++){if(mi)putchar(',');text(node->materials.data[mi]->name);}putchar(']');
  if(write){
   size_t corners=mesh->num_indices;uint64_t *keys=malloc(corners*sizeof(uint64_t));for(size_t i=0;i<corners;i++)keys[i]=vertex_key(mesh,i);qsort(keys,corners,sizeof(uint64_t),cmp_u64);size_t n=0;for(size_t i=0;i<corners;i++)if(i==0||keys[i]!=keys[i-1])keys[n++]=keys[i];
   uint32_t vertices=(uint32_t)n,index_count=(uint32_t)(mesh->num_triangles*3);float *positions=malloc(n*3*sizeof(float)),*normals=malloc(n*3*sizeof(float));uint32_t *indices=malloc(index_count*sizeof(uint32_t)),*triangle_material=malloc(mesh->num_triangles*sizeof(uint32_t));
   for(size_t i=0;i<n;i++){uint32_t vi=keys[i]>>32,normal_index=(uint32_t)keys[i];ufbx_vec3 p=ufbx_transform_position(&matrix,mesh->vertices.data[vi]);ufbx_vec3 normal=mesh->vertex_normal.exists?mesh->vertex_normal.values.data[normal_index]:(ufbx_vec3){0,1,0};normal=ufbx_transform_direction(&norm_matrix,normal);double length=sqrt(normal.x*normal.x+normal.y*normal.y+normal.z*normal.z);for(int a=0;a<3;a++){positions[i*3+a]=(float)p.v[a];normals[i*3+a]=(float)(length>1e-12?normal.v[a]/length:0);}}
   size_t offset=0,capacity=mesh->max_face_triangles*3;uint32_t *tri=malloc(capacity*sizeof(uint32_t));int mirror=ufbx_matrix_determinant(&matrix)<0;
   for(size_t fi=0;fi<mesh->num_faces;fi++){ufbx_face face=mesh->faces.data[fi];uint32_t tc=ufbx_triangulate_face(tri,capacity,mesh,face);for(size_t t=0;t<tc;t++){uint32_t v[3];for(int j=0;j<3;j++)v[j]=lookup(keys,n,vertex_key(mesh,tri[t*3+j]));triangle_material[offset/3]=mesh->face_material.count?mesh->face_material.data[fi]:0;indices[offset++]=v[0];indices[offset++]=v[mirror?2:1];indices[offset++]=v[mirror?1:2];}}
   if(offset!=index_count){fprintf(stderr,"Triangulation mismatch\n");return 4;}
   char filename[2048];snprintf(filename,sizeof filename,"%s/%lld.bin",argv[2],source_id(&node->element));FILE*out=fopen(filename,"wb");if(!out)return 5;fwrite("BP3D",1,4,out);fwrite(&vertices,4,1,out);fwrite(&index_count,4,1,out);fwrite(positions,4,n*3,out);fwrite(normals,4,n*3,out);fwrite(indices,4,index_count,out);fclose(out);
   printf(",\"export_vertices\":%u,\"mirrored_winding_corrected\":%s,\"file\":",vertices,mirror?"true":"false");ufbx_string name={filename,strlen(filename)};text(name);
   printf(",\"material_submeshes\":[");int first_material=1;
   if(node->materials.count>1)for(size_t mi=0;mi<node->materials.count;mi++){
    uint32_t material_indices=0;for(size_t i=0;i<mesh->num_triangles;i++)if(triangle_material[i]==mi)material_indices+=3;
    if(!material_indices)continue;
    snprintf(filename,sizeof filename,"%s/%lld-material-%zu.bin",argv[2],source_id(&node->element),mi);out=fopen(filename,"wb");if(!out)return 6;
    fwrite("BP3D",1,4,out);fwrite(&vertices,4,1,out);fwrite(&material_indices,4,1,out);fwrite(positions,4,n*3,out);fwrite(normals,4,n*3,out);
    for(size_t i=0;i<mesh->num_triangles;i++)if(triangle_material[i]==mi)fwrite(indices+i*3,4,3,out);fclose(out);
    if(!first_material)putchar(',');first_material=0;printf("{\"material_index\":%zu,\"name\":",mi);text(node->materials.data[mi]->name);printf(",\"triangles\":%u,\"file\":",material_indices/3);name.data=filename;name.length=strlen(filename);text(name);putchar('}');
   }
   printf("]");free(triangle_material);free(tri);free(indices);free(normals);free(positions);free(keys);
  }
  putchar('}');
 }
 printf("]}\n");ufbx_free_scene(scene);for(size_t i=0;i<count;i++)free(names[i]);free(names);return 0;
}
