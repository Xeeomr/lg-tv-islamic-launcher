#include <stdint.h>
/* Busy keys are temporary, but device errors are not. Pump must service the
 * controller and remain bounded; input has not been grabbed during this wait. */
static int wait_for_release(uint64_t (*clock_ms)(void),int (*keys)(void),int (*pump)(void)){
 uint64_t deadline=clock_ms()+5000;
 for(;;){
  int reason=keys();
  if(reason!=14&&reason!=16)return reason;
  if(clock_ms()>=deadline)return reason;
  reason=pump();if(reason)return reason;
 }
}
