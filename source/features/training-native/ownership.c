#include "ownership.h"
int training_bag_claimable(const unsigned char bytes[452]) {
 unsigned i,n=0;int uniform=1;
 for(i=1;i<452;i++)if(bytes[i]!=bytes[0]){uniform=0;break;}
 if(uniform)return 1;
 while(n<4&&bytes[n]==(unsigned char)(0x32353242u>>(8*n)))n++;
 if(n==4)return 1;
 if(!n)return 0;
 for(i=n;i<452;i++)if(bytes[i]!=255)return 0;
 return 1;
}
void training_owner_encode(unsigned char out[32]) {
 unsigned i;
 for(i=0;i<32;i++)out[i]=0;
 out[0]='T';out[1]='N';out[2]='O';out[3]='1';out[4]=1;out[6]=32;
 /* Both authorized offsets and lengths, little endian. */
 out[9]=1;out[11]=2;out[13]=1;
 for(i=0;i<16;i++)out[16+i]=(unsigned char)~out[i];
}
int training_owner_valid(const unsigned char bytes[32]) {
 unsigned char expected[32];unsigned i;training_owner_encode(expected);
 for(i=0;i<32;i++)if(bytes[i]!=expected[i])return 0;return 1;
}
int training_record_future(const unsigned char bytes[256]) {
 unsigned i;int tail=0;
 if(bytes[0]!='T'||bytes[1]!='N'||bytes[2]!='R'||bytes[3]!='1')return 0;
 if((bytes[4]==1||bytes[4]==2)&&bytes[5]==0&&bytes[6]==0&&bytes[7]==1)return 0;
 /* With a verified sector lease, a partial FIRST v1/v2 header followed entirely
  * by erased bytes is our interrupted initialization, not a future format.
  * Any explicitly different non-erased version/length still vetoes writes. */
 for(i=4;i<256;i++){
  unsigned char expected=i==4?(bytes[4]==2?2:1):(i==7?1:0);
  if(i>=8||bytes[i]!=expected)tail=1;
  if(tail&&bytes[i]!=255)return 1;
 }
 return 0;
}
