// Minimal check: C++ API opens a default session (same idea as zenohc test_package).
#include "zenoh.hxx"

int main() {
    using namespace zenoh;
    Config config = Config::create_default();
    auto session = Session::open(std::move(config));
    (void)session.get_zid();
    return 0;
}
