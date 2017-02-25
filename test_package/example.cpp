#include <iostream>
#include <libtorrent/session.hpp>

#ifdef BOOST_ASIO_SEPARATE_COMPILATION
  #pragma error "BOOST_ASIO_SEPARATE_COMPILATION is defined"
#endif

#ifdef BOOST_ASIO_DYN_LINK
    #pragma error "BOOST_ASIO_DYN_LINK is defined"
#endif

int main() {
    libtorrent::session s;    
    return 0;
}
