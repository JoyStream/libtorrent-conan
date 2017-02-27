#include <iostream>
#include <libtorrent/session.hpp>
#include <boost/asio.hpp>

#ifndef BOOST_ASIO_HEADER_ONLY
    #include <boost/asio/impl/src.hpp>
#endif

int main() {
    libtorrent::session s;
    boost::asio::io_service io;
    return 0;
}
