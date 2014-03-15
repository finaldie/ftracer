#include <stdio.h>
#include <stdlib.h>

#define TRACE_FILE "/tmp/trace.txt"

static FILE *fp = NULL;

void __cyg_profile_func_enter(void* this, void* callsite)
                             __attribute__((no_instrument_function));
void __cyg_profile_func_exit(void* this, void* callsite)
                             __attribute__((no_instrument_function));

void __cyg_profile_func_enter(void* function, void* caller)
{
    /* Function Entry Address */
    fprintf(fp, "E %p %p\n", function, caller);
}

void __cyg_profile_func_exit(void* function, void* caller)
{
    /* Function Exit Address */
    fprintf(fp, "X %p %p\n", function, caller);
}

void main_constructor(void)
        __attribute__ ((no_instrument_function, constructor));
void main_destructor(void)
         __attribute__ ((no_instrument_function, destructor));


void main_constructor(void)
{
    fp = fopen(TRACE_FILE, "w");
    if (fp == NULL) {
        printf("can not open trace.txt\n");
    }
}

void main_deconstructor(void)
{
    if (fp) {
        fclose( fp );
    }
}
