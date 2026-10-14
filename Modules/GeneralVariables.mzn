/*
 * General variables for the Wordpress model
 */

int: VM;
int: NoComponents;
int: HardwareREQ;
int: VMOffers;

array[1..NoComponents, 1..HardwareREQ] of int: CompREQ;
array[1..VMOffers, 1..HardwareREQ] of int: VMSpecs;
array[1..VMOffers] of int: VMPrice;

set of int: S = { i | i in 1..NoComponents};

array[1..NoComponents, 1..VM] of var 0..1: AssignmentMatrix;
array[1..VM] of var 1..VMOffers: VMType;
array[1..VM] of var 0..1: OccupancyVector;
array[1..VM] of var 0..16000: Price;
array[1..VM] of var 0..64: CPU;
array[1..VM] of var 0..1000000: Memory;
array[1..VM] of var 0..16000: Storage;

% --- AZ Extension Variables (Dynamic Solver Decision Variable) ---
int: NoZones;
array[1..VM] of var 1..NoZones: VMZone;

% --- Latency SLA Variables ---
array[1..NoZones, 1..NoZones] of int: ZoneLatency;
int: MaxAllowedLatency;
