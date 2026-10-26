#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <sys/ioctl.h>
#include <time.h>
#include <errno.h>
#include <string.h>
#include <stdarg.h>
#include <assert.h>
#ifndef _IOC_READ
#define _IOC_READ IOC_OUT /* Host test only: ioctl is mocked, never sent to a device. */
#endif
static ssize_t fake_read(int,void*,size_t);
static int fake_ioctl(int,unsigned long,...);
static int fake_poll(struct pollfd*,nfds_t,int);
static int fake_clock(clockid_t,struct timespec*);
#define read fake_read
#define ioctl fake_ioctl
#define poll fake_poll
#define clock_gettime fake_clock
#define main relay_main
#include "relay.c"
#undef main
static uint64_t now,release_at;
static int queue,heartbeats,command='P',disconnected,device_error,destination;
static int fake_clock(clockid_t id,struct timespec*t){(void)id;t->tv_sec=now/1000;t->tv_nsec=(now%1000)*1000000;return 0;}
static ssize_t fake_read(int fd,void*b,size_t n){
 (void)n;
 if(fd==0){*(char*)b=command;heartbeats++;return 1;}
 if(queue){queue--;memset(b,0,sizeof(struct ev));return sizeof(struct ev);}
 errno=EAGAIN;return -1;
}
static int fake_ioctl(int fd,unsigned long request,...){
 (void)request;if(device_error)return -1;
 va_list args;va_start(args,request);unsigned char*b=va_arg(args,unsigned char*);va_end(args);
 memset(b,0,256);if((fd==startup_in&&now<release_at)||(fd==startup_out&&destination))b[3]=1;return 0;
}
static int fake_poll(struct pollfd*p,nfds_t n,int timeout){(void)n;now+=timeout;p->revents=disconnected?POLLHUP:POLLIN;return 1;}
int main(void){
 startup_in=100;startup_out=101;now=startup_ack=0;release_at=3000;queue=2;
 assert(wait_for_release(ms,startup_keys,startup_pump)==0);assert(queue==0);assert(heartbeats==60);assert(startup_ack==3000);
 now=startup_ack=0;release_at=6000;assert(wait_for_release(ms,startup_keys,startup_pump)==14);
 now=startup_ack=0;release_at=0;destination=1;assert(wait_for_release(ms,startup_keys,startup_pump)==16);destination=0;
 now=startup_ack=0;release_at=3000;command='Q';assert(wait_for_release(ms,startup_keys,startup_pump)==29);
 command='P';disconnected=1;assert(wait_for_release(ms,startup_keys,startup_pump)==24);disconnected=0;
 device_error=1;assert(wait_for_release(ms,startup_keys,startup_pump)==13);device_error=0;
 now=3000;startup_ack=0;assert(startup_pump()==20);
 stop=1;release_at=0;assert(startup_keys()==29);stop=0;
 puts("PASS: actual relay startup drains input, acknowledges heartbeat and preserves stop/error guards");
}
