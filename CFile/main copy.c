#include <stdio.h>
#define A 1
#define myMacro_impl(x,y) x##y = 1
#define myMacro(x,y) myMacro_impl(x,y)
#define Loop(x,n) \
for(int i = 0; i < n; i++) {\
	x+=i;\
}

int main(){
	int myMacro(x,A);
	Loop(x1,5)
	printf("%d\n", x1);
}