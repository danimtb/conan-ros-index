/* Minimal zenoh-c API check: default config, open session, read own ZID, close.
 * Uses z_*_move / z_*_loan / z_*_drop (not z_move/z_loan/z_drop) so MSVC C
 * mode works: those macros rely on C11 _Generic, which cl defaults omit. */
#include <stdio.h>
#include <stdlib.h>

#include "zenoh.h"

int main(void) {
    z_owned_config_t config;
    z_owned_session_t session;
    z_owned_string_t zid_str;
    z_id_t zid;
    const z_loaned_string_t *loan;
    size_t len;
    const char *data;

    if (z_config_default(&config) != Z_OK) {
        fprintf(stderr, "z_config_default failed\n");
        return 1;
    }

    if (z_open(&session, z_config_move(&config), NULL) != Z_OK) {
        fprintf(stderr, "z_open failed (is a zenoh router reachable?)\n");
        z_session_drop(z_session_move(&session));
        return 2;
    }

    zid = z_info_zid(z_session_loan(&session));
    z_id_to_string(&zid, &zid_str);

    loan = z_string_loan(&zid_str);
    len = z_string_len(loan);
    data = z_string_data(loan);
    if (len == 0) {
        fprintf(stderr, "unexpected empty ZID string\n");
        z_string_drop(z_string_move(&zid_str));
        z_session_drop(z_session_move(&session));
        return 3;
    }

    if (data[0] == '\0') {
        fprintf(stderr, "unexpected NUL first ZID byte\n");
        z_string_drop(z_string_move(&zid_str));
        z_session_drop(z_session_move(&session));
        return 4;
    }

    z_string_drop(z_string_move(&zid_str));
    z_session_drop(z_session_move(&session));
    return 0;
}
