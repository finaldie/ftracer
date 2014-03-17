#include <stdio.h>
#include <stdlib.h>


void e()
{
    printf("this is e\n");
}

void d()
{
    printf("this is d\n");
}

void c()
{
    printf("this is c\n");
}

void b(int i)
{
    printf("this is b\n");

    if (i == 1) {
        c();
    } else {
        for (int i=0; i<2; i++) {
            d();
        }

        e();
    }
}

void a()
{
    printf("this is a\n");
    b(1);
    b(2);
}


int main(int argc, char** argv)
{
    for (int i=0; i<=2; i++) {
        a();
    }
    return 0;
}
