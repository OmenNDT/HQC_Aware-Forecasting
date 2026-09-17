set(CORE ${CMAKE_CURRENT_LIST_DIR}/../../core)
if(DEFINED ENV{HQC_BENCH})
    # chế độ bàn thử phase 05 chạy song song với phát lại: ADXL345 + tacho + OLED + LED/còi/servo
    set(HQC_MAIN "main.c" "bench_main.c" "adxl345_spi.c" "ssd1306_i2c.c" "tacho_order.c")
else()
    set(HQC_MAIN "main.c")
endif()
idf_component_register(
    SRCS ${HQC_MAIN} "led_status.c" "${CORE}/sae_int8.c" "${CORE}/stats_util.c" "${CORE}/tier_b_slopes.c" "${CORE}/tier_a_direct.c" "${CORE}/tier_c_phase.c" "${CORE}/hqc_engine.c"
    INCLUDE_DIRS "." "${CORE}"
    REQUIRES driver esp_timer esp_adc)
if(DEFINED ENV{HQC_BENCH})
    target_compile_definitions(${COMPONENT_LIB} PRIVATE HQC_BENCH=1)
endif()
set_source_files_properties(led_status.c PROPERTIES COMPILE_FLAGS "-Wno-missing-field-initializers")
if(DEFINED ENV{HQC_NO_LED})
    target_compile_definitions(${COMPONENT_LIB} PRIVATE HQC_NO_LED=1)
endif()
if(NOT DEFINED ENV{HQC_IO_UART})
    target_compile_definitions(${COMPONENT_LIB} PRIVATE HQC_IO_USB=1)   # mặc định: cổng USB gốc; đặt HQC_IO_UART=1 để dùng UART0
endif()
