#ifndef test_hpp_
#define test_hpp_

#include <iostream>

namespace abc {

void throw_ex(int ex)
{
    throw ex;
}

void unreachable_func()
{
    std::cout << "unreachable_func" << std::endl;
}

template<typename T>
class F {
public:
    F(T v) {_v = v; std::cout << "this is F" << std::endl;}
    ~F() {}

public:
    void test()
    {
        std::cout << "F's value = " << _v << std::endl;
        throw_ex(20);
    }

private:
    T _v;
};

inline void G()
{
    std::cout << "this is G(inline)" << std::endl;
}

}

#endif
