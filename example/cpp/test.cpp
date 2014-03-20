#include <stdlib.h>
#include <pthread.h>
#include <string>
#include <map>
#include <iostream>

#include "test.hpp"

using namespace std;
namespace abc {
class E {
public:
    E() {cout << "this is e" << endl;}
    ~E() {}

    void test() {
        map<string, int> tm;
        tm["e123"] = 10;
        tm["e456"] = 20;
        cout << tm["e123"] << endl;
        cout << tm["e456"] << endl;

        F<int> f(100);
        f.test();
    }
};

class D {
public:
    D() {cout << "this is d" << endl;}
    ~D() {}

    void test() {
        map<string, int> tm;
        tm["d123"] = 10;
        tm["d456"] = 20;
        cout << tm["d123"] << endl;
        cout << tm["d456"] << endl;
    }
};

class C {
public:
    C() {cout << "this is c" << endl;}
    ~C() {}

    void test() {
        map<string, int> tm;
        tm["c123"] = 10;
        tm["c456"] = 20;
        cout << tm["c123"] << endl;
        cout << tm["c456"] << endl;
    }
};

class B {
public:
    B() {cout << "this is b" << endl;}
    ~B() {}

    void test(string arg) {
        if (arg == "1") {
            C c;
            c.test();
        } else if (arg == "2") {
            for (int i=0; i<2; i++) {
                D d;
                d.test();

                E e;
                e.test();
            }
        }
    }
};

class A {
public:
    A() {cout << "this is a" << endl;}
    ~A() {}

    void test() {
        B b;
        string arg1 = "1";
        string arg2 = "2";
        b.test(arg1);
        b.test(arg2);
    }
};

}

void* work(void* arg)
{
    for (int i=0; i<=2; i++) {
        abc::A a;
        a.test();
    }
    return NULL;
}

int main(int argc, char** argv)
{
    for (int i=0; i<=2; i++) {
        abc::A a;
        a.test();
    }

    pthread_t t1, t2;
    pthread_create(&t1, NULL, work, NULL);
    pthread_create(&t2, NULL, work, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    return 0;
}
