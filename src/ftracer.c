#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>
#include <signal.h>

#define TRACE_FILE "/tmp/trace.txt"
#define FTRACER_FUNC_ENTRY "FTRACER_FUNC_ENTRY"
#define FTRACER_SIG_NUM "FTRACER_SIG_NUM"
#define TRACE_NULL "0x0"

static FILE* __fp = NULL;
static int __tracer_start = 0;

static uintptr_t __func_entry = 0;

void __cyg_profile_func_enter(void* this, void* callsite)
                             __attribute__((no_instrument_function));
void __cyg_profile_func_exit(void* this, void* callsite)
                             __attribute__((no_instrument_function));

void __cyg_profile_func_enter(void* function, void* caller)
{
    // enable tracer when the function == user specific func address
    if (!__tracer_start) {
        if (__func_entry && __func_entry == (uintptr_t)function) {
            __tracer_start = 1;
            printf("enter in function(%p), tracer start\n", function);
        } else {
            return;
        }
    }

    if (!__fp) {
        return;
    }

    /* Function Entry Address */
    int n = fprintf(__fp, "E|%p|%p\n", function, caller);
    if (n < 0) {
        printf("dump entrance trace info failed: %s\n", strerror(errno));
    }
}

void __cyg_profile_func_exit(void* function, void* caller)
{
    if (!__tracer_start) {
        return;
    }

    if (!__fp) {
        return;
    }

    /* Function Exit Address */
    int n = fprintf(__fp, "X|%s|%s\n", TRACE_NULL, TRACE_NULL);
    if (n < 0) {
        printf("dump exit trace info failed: %s\n", strerror(errno));
    }
}

void main_constructor(void)
        __attribute__ ((no_instrument_function, constructor));
void main_destructor(void)
        __attribute__ ((no_instrument_function, destructor));

static
void tracer_sighandler(int sig)
{
    __tracer_start = 1;
}

void main_constructor(void)
{
    __fp = fopen(TRACE_FILE, "w");
    if (__fp == NULL) {
        printf("can not open trace.txt\n");
    } else {
        printf("open trace file: %s success\n", TRACE_FILE);

        // setup tracer according to env
        // 1. setup by function address
        char* func_entry = getenv(FTRACER_FUNC_ENTRY);
        if (func_entry) {
            __func_entry = strtoul(func_entry, NULL, 16);
            if (!__func_entry) {
                printf("Warning: %s is invalid, tracer is disabled: %s\n", FTRACER_FUNC_ENTRY, strerror(errno));
            } else {
                printf("tracer will start when function(%p) is called\n", (void*)__func_entry);
            }

            return;
        }

        // 2. setup by signal
        char* sig_num_str = getenv(FTRACER_SIG_NUM);
        if (sig_num_str) {
            int sig_num = (int)strtoul(sig_num_str, NULL, 10);
            if (sig_num <= 0 ) {
                printf("Warning: %s is invalid, tracer is disabled: sig_num = %d\n", FTRACER_SIG_NUM, sig_num);
                return;
            }

            struct sigaction sa;
            sa.sa_handler = tracer_sighandler;
            sigemptyset(&sa.sa_mask);
            sa.sa_flags = 0;

            sigaction(sig_num, &sa, NULL);

            printf("tracer will start when receive signal number = %d\n", sig_num);
            return;
        }

        __tracer_start = 1;
        printf("tracer start\n");
    }
}

void main_deconstructor(void)
{
    if (__fp) {
        fclose(__fp);
        printf("close trace file: %s\n", TRACE_FILE);
    }
}
