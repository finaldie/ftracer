#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>
#include <signal.h>
#include <pthread.h>

// macros for static values
#define FTRACE_DEFAULT_FILE "/tmp/trace.txt"
#define TRACE_NULL "0x0"

// macros for env variables, the following are all the env keys
#define FTRACER_FUNC_ENTRY "FTRACER_FUNC_ENTRY"
#define FTRACER_SIG_NUM "FTRACER_SIG_NUM"
#define FTRACER_OUTPUT_FILE "FTRACER_FILE"

static FILE* __fp = NULL;
static int __tracer_start = 0;
static uintptr_t __func_entry = 0;

static pthread_mutex_t _fmutex = PTHREAD_MUTEX_INITIALIZER;

void __cyg_profile_func_enter(void* this, void* callsite)
                             __attribute__((no_instrument_function));
void __cyg_profile_func_exit(void* this, void* callsite)
                             __attribute__((no_instrument_function));

static
void _dump_profile_enter_info(void* function, void* caller)
{
    if (!__fp) {
        return;
    }

    pthread_t current = pthread_self();

    pthread_mutex_lock(&_fmutex);

    int n = fprintf(__fp, "%lu|E|%p|%p\n", current, function, caller);
    if (n < 0) {
        printf("dump entrance trace info failed: %s\n", strerror(errno));
    }

    pthread_mutex_unlock(&_fmutex);
}

void _dump_profile_exit_info(void* function, void* caller)
{
    if (!__fp) {
        return;
    }

    pthread_t current = pthread_self();

    pthread_mutex_lock(&_fmutex);

    int n = fprintf(__fp, "%lu|X|%p|%p\n", current, function, caller);
    if (n < 0) {
        printf("dump exit trace info failed: %s\n", strerror(errno));
    }

    pthread_mutex_unlock(&_fmutex);
}

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

    _dump_profile_enter_info(function, caller);
}

void __cyg_profile_func_exit(void* function, void* caller)
{
    if (!__tracer_start) {
        return;
    }

    _dump_profile_exit_info(function, caller);
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
    char* trace_file = getenv(FTRACER_OUTPUT_FILE);
    if (!trace_file) {
        trace_file = FTRACE_DEFAULT_FILE;
    }

    __fp = fopen(trace_file, "w");
    if (__fp == NULL) {
        printf("can not open trace.txt\n");
        return;
    }

    printf("open trace file: %s success\n", trace_file);

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

    // 2. setup by signal, the two options cannot be shown in the same time,
    // if that, the signal option will be no effect
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

void main_deconstructor(void)
{
    if (__fp) {
        fclose(__fp);
        printf("close trace file\n");
    }
}
