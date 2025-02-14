## Summary of Actions


- The Simulator adds the container to the realm of the Optimizer: 2024-11-14 10:26:30 INFO adding TO TO_CO_TFTU000001, EMT 2024-11-14 10:26:28+01:00
- The Simulator lets your own Vehicle Optimizer run every certain amount of time and the logs show the job sequence per Straddle Carrier per Optimization run:
    - 2024-11-14 10:27:07 INFO SC001 schedule 1:TO_CO_TFTU000018#CO_TFTU000018#PICK,2:TO_CO_TFTU000018#CO_TFTU000018#DROP
    - 2024-11-14 10:27:07 INFO SC002 schedule 1:TO_CO_TFTU000023#CO_TFTU000023#PICK,2:TO_CO_TFTU000023#CO_TFTU000023#DROP

- Additional information regarding what a Straddle Carrier does it listed as follows:
    - 2024-11-14 10:27:07 INFO SC001 starting TO_CO_TFTU000018#CO_TFTU000018#PICK: travel 2024-11-14 10:27:00+01:00
    - 2024-11-14 10:27:30+01:00, action 2024-11-14 10:27:30+01:00 - 2024-11-14 10:28:30+01:00 (to pick up the container, the Straddle Carrier has to travel (30 seconds) and pick up the container (60 seconds).
    - 2024-11-14 10:27:10 INFO SC001 (TO: TO_CO_TFTU000018, CO: CO_TFTU000018, PICK) driving to QC003; 31 s; 172693 mm (Straddle Carrier is driving to a location, driving time and distance is shown – distance is measured in Manhattan Distance)
    - 2024-11-14 10:27:10 DEBUG location QC001: using lane 0 for CO CO_TFTU000001 (shows when a Straddle Carrier is using one of the available and limited spaces in a location)
    - 2024-11-14 10:27:10 INFO SC004 (TO: TO_CO_TFTU000001, CO: CO_TFTU000001, PICK) working at QC001; 60 s (the straddle carrier is picking up the container)
    - 2024-11-14 10:28:07 DEBUG location QC001: freeing lane 0 for CO CO_TFTU000001 (Straddle Carrier has freed up the limited space in a location)
    - 2024-11-14 10:28:07 INFO SC004 (TO: TO_CO_TFTU000001, CO: CO_TFTU000001, PICK) finished at QC001 (Straddle Carrier has finished picking up the container)
    - 2024-11-14 10:28:07 DEBUG finished expected schedule_element TO_CO_TFTU000001#CO_TFTU000001#PICK (Straddle Carrier has finished the logical element of the PICK which we call “schedule_element”)