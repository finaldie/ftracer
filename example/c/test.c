#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

static inline
void f()
{
    printf("this is f(inline)\n");
}

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
        f();
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

void* work(void* arg)
{
    for (int i=0; i<=2; i++) {
        a();
    }
    return NULL;
}


int main(int argc, char** argv)
{
    for (int i=0; i<=2; i++) {
        a();
    }

    pthread_t t1, t2;
    pthread_create(&t1, NULL, work, NULL);
    pthread_create(&t2, NULL, work, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return 0;
}
