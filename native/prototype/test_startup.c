#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "startup.h"
static uint64_t now,release_at;
static int steps,abort_code,source_error,destination_busy;
static uint64_t clock_ms(void){return now;}
static int keys(void){return source_error?13:now<release_at?14:destination_busy?16:0;}
static int pump(void){steps++;now+=50;return abort_code;}
int main(void){
 now=0;release_at=3000;steps=0;assert(wait_for_release(clock_ms,keys,pump)==0);assert(steps==60);
 now=0;release_at=6000;assert(wait_for_release(clock_ms,keys,pump)==14);assert(now==5000);
 now=0;release_at=0;destination_busy=1;assert(wait_for_release(clock_ms,keys,pump)==16);assert(now==5000);
 destination_busy=0;source_error=1;steps=0;assert(wait_for_release(clock_ms,keys,pump)==13);assert(steps==0);
 source_error=0;release_at=3000;now=0;abort_code=24;assert(wait_for_release(clock_ms,keys,pump)==24);
 abort_code=29;assert(wait_for_release(clock_ms,keys,pump)==29);
 abort_code=0;release_at=0;steps=0;assert(wait_for_release(clock_ms,keys,pump)==0);assert(steps==0);
 puts("PASS: startup release wait, deadline, destination, ioctl failure, controller loss and stop");
}
