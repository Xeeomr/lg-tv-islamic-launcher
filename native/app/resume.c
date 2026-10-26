#include <unistd.h>
#include <stdlib.h>
#include <signal.h>
int main(int argc,char**argv){if(argc!=2)return 1;pid_t p=atoi(argv[1]);if(p!=getppid())return 2;sleep(4);return kill(p,SIGCONT)<0;}
