#include <stdio.h>
#include <stdlib.h>
#include <setjmp.h>
#include <pthread.h>

static jmp_buf thread1_jumpbuf;
static int loop_cnt = 0;

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

        loop_cnt++;
        if (loop_cnt == 2) {
            longjmp(thread1_jumpbuf, 2);
        }

        e(); // this will never be excuted
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
    int val = setjmp(thread1_jumpbuf);
    if (val == 0) {
        for (int i=0; i<=2; i++) {
            a();
        }
    } else {
        printf("return from longjmp() val=%d\n", val);
    }

    return NULL;
}


int main(int argc, char** argv)
{
    pthread_t t1;
    pthread_create(&t1, NULL, work, NULL);

    pthread_join(t1, NULL);
    return 0;
}
