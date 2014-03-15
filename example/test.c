#include <stdio.h>
#include <stdlib.h>

int test(int i)
{
	i = i + 1;
	return i;
}


int main(int argc, char** argv)
{
	int i = test(1);
	printf("i = %d\n", i);
	return 0;
}
