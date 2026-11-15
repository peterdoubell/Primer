/* Analysis tessellation only: preserve original corner/vertex/face identities.
 * Does not export or modify source geometry. Build against pinned official ufbx. */
#include "ufbx.h"
#include <stdio.h>
#include <stdlib.h>

static long long id(ufbx_element *e) { return e->dom_node->values.data[0].value_int; }
int main(int argc,char **argv) {
 if(argc<3)return 2;
 ufbx_load_opts opts={0};opts.retain_dom=true;opts.ignore_animation=true;opts.ignore_embedded=true;opts.load_external_files=false;
 ufbx_error error;ufbx_scene *scene=ufbx_load_file(argv[1],&opts,&error);if(!scene)return 3;
 printf("{\"geometries\":[");int first=1;
 for(size_t i=0;i<scene->meshes.count;i++) {
  ufbx_mesh *m=scene->meshes.data[i];long long gid=id(&m->element);int selected=0;
  for(int a=2;a<argc;a++)if(gid==atoll(argv[a]))selected=1;
  if(!selected)continue;
  if(!first)putchar(',');first=0;
  printf("{\"geometry_id\":%lld,\"native_faces\":%zu,\"triangles\":[",gid,m->num_faces);
  size_t capacity=m->max_face_triangles*3;uint32_t *corners=malloc(capacity*sizeof(uint32_t));int ft=1;
  for(size_t f=0;f<m->num_faces;f++) {
   ufbx_face face=m->faces.data[f];uint32_t count=ufbx_triangulate_face(corners,capacity,m,face);
   if(count!=face.num_indices-2)return 4;
   for(size_t t=0;t<count;t++) {
    if(!ft)putchar(',');ft=0;
    uint32_t a=corners[t*3],b=corners[t*3+1],c=corners[t*3+2];
    printf("[%zu,%u,%u,%u,%u,%u,%u]",f,a,b,c,m->vertex_indices.data[a],m->vertex_indices.data[b],m->vertex_indices.data[c]);
   }
  }
  printf("]}");free(corners);
 }
 printf("]}\n");ufbx_free_scene(scene);return 0;
}
