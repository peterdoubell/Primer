const SOURCE_HOST='ja2lsnp9uca4bivw.public.blob.vercel-storage.com';
export async function readSourceBytes(url,maximum,options={}) {
  if(!Number.isSafeInteger(maximum)||maximum<=0)throw Error('Invalid source response bound');
  const address=new URL(url,location.href);
  if(address.origin!==location.origin&&(address.protocol!=='https:'||address.hostname!==SOURCE_HOST))throw Error('Unexpected source host');
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);
  try {
    const response=await fetch(address,{signal:controller.signal,credentials:address.origin===location.origin?'same-origin':'omit',headers:options.range?{Range:`bytes=${options.range.start}-${options.range.end}`}:{}});
    if(response.status!==(options.range?206:200))throw Error('Source request returned HTTP '+response.status);
    if(options.range&&response.headers.get('Content-Range')!==`bytes ${options.range.start}-${options.range.end}/${options.range.total}`)throw Error('Source Content-Range differs');
    const reader=response.body.getReader(),chunks=[];let total=0;
    try{while(true){const{value,done}=await reader.read();if(done)break;total+=value.length;if(total>maximum)throw Error('Source response exceeds declared length');chunks.push(value);}}finally{await reader.cancel();}
    const result=new Uint8Array(total);let offset=0;for(const chunk of chunks){result.set(chunk,offset);offset+=chunk.length;}
    return result;
  }finally{clearTimeout(timer);controller.abort();}
}
