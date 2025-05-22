from case.satellite import SatelliteTestBeam, SatelliteTestUpward

if __name__ == "__main__":
    a = SatelliteTestUpward(start_time="18.05.2025 16:20:00", end_time="18.05.2025 16:20:20", file_name="STARLINK.txt",
                      latitude_dms=(51, 40, 18), longitude_dms=(39, 12, 38),
                      visibility_angle=70, time_stamps_count=5)
    a.visible_at_time_range_name()
    a.visible_at_time_range_closest()

    b = SatelliteTestBeam(start_time="18.05.2025 16:00:00", end_time="18.05.2025 17:00:00", file_name="STARLINK.txt",
                          latitude_dms=(51, 40, 18), longitude_dms=(39, 12, 38),
                          visibility_angle=70, time_stamps_count=30, altitude_deg=60., azimuth_deg=300.)
    b.visible_at_time_range_name()
