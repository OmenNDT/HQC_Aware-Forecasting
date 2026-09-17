CC ?= gcc
CFLAGS ?= -O2 -std=c99 -Wall -Wextra -Wno-unused-parameter -D_DEFAULT_SOURCE
SRC = replay_main.c ../core/sae_int8.c ../core/stats_util.c ../core/tier_b_slopes.c ../core/tier_a_direct.c ../core/tier_c_phase.c ../core/hqc_engine.c
replay: $(SRC) ../core/*.h
	$(CC) $(CFLAGS) -o replay $(SRC) -lm
clean:
	rm -f replay
