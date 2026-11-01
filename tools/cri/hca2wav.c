/* hca2wav <in.hca> <out.wav> <key-hex>
 * 用 vgmstream 的 clHCA 解碼 HCA 成 16-bit WAV(去掉 encoder delay / padding)。
 * 編譯前先下載 vgmstream 的 src/coding/libs/clhca.c、clhca.h、clhca_data.h 放在同一資料夾:
 *   gcc -O2 -o hca2wav hca2wav.c clhca.c -lm */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "clhca.h"
static void w32(FILE*f,unsigned v){fputc(v,f);fputc(v>>8,f);fputc(v>>16,f);fputc(v>>24,f);}
static void w16(FILE*f,unsigned v){fputc(v,f);fputc(v>>8,f);}
int main(int argc,char**argv){
  if(argc<4){fprintf(stderr,"usage: hca2wav in.hca out.wav key-hex\n");return 2;}
  FILE*f=fopen(argv[1],"rb"); if(!f) return 3;
  fseek(f,0,SEEK_END); long n=ftell(f); fseek(f,0,SEEK_SET);
  unsigned char*d=malloc(n); if(fread(d,1,n,f)!=(size_t)n) return 3; fclose(f);
  clHCA*h=clHCA_new();
  if(clHCA_DecodeHeader(h,d,(unsigned)n)<0){fprintf(stderr,"bad header\n");return 4;}
  clHCA_stInfo in; clHCA_getInfo(h,&in);
  clHCA_SetKey(h,strtoull(argv[3],NULL,16));
  int tested=0;                                   /* 用前幾個 block 驗證金鑰 */
  for(unsigned b=0;b<in.blockCount && tested<8;b++){
    unsigned char tmp[0x10000]; memcpy(tmp,d+in.headerSize+b*in.blockSize,in.blockSize);
    int r=clHCA_TestBlock(h,tmp,in.blockSize); if(r<0){fprintf(stderr,"wrong key\n");return 5;} if(r>0) tested++;
  }
  clHCA_DecodeReset(h);
  unsigned ch=in.channelCount, spb=in.samplesPerBlock;
  short*buf=malloc(sizeof(short)*spb*ch);
  long total=(long)in.blockCount*spb, keep=total-in.encoderDelay-in.encoderPadding, pos=0, wrote=0;
  if(keep<0) keep=0;
  FILE*o=fopen(argv[2],"wb");
  fwrite("RIFF",1,4,o); w32(o,36+keep*ch*2); fwrite("WAVEfmt ",1,8,o); w32(o,16); w16(o,1); w16(o,ch);
  w32(o,in.samplingRate); w32(o,in.samplingRate*ch*2); w16(o,ch*2); w16(o,16); fwrite("data",1,4,o); w32(o,keep*ch*2);
  for(unsigned b=0;b<in.blockCount;b++){
    if(clHCA_DecodeBlock(h,d+in.headerSize+b*in.blockSize,in.blockSize)<0) break;
    clHCA_ReadSamples16(h,buf);
    for(unsigned s=0;s<spb;s++,pos++){ if(pos<(long)in.encoderDelay||wrote>=keep) continue; fwrite(buf+s*ch,2,ch,o); wrote++; }
  }
  fclose(o);
  printf("%u Hz %u ch %ld samples\n",in.samplingRate,ch,wrote);
  return 0;
}
