/*
 * Availability Zone Constraints for MiniZinc
 * -------------------------------------------
 * Includes:
 * 1. az_dispersion: Ensures at most 1 replica of a component per AZ
 *    (Anti-affinity across zones with dynamic VMZone decision variables).
 * 2. latency_sla: Ensures inter-component communication respects
 *    maximum allowed network latency based on host VM zones.
 */

/*
 * Ensures that at most 1 replica of a component is placed per Availability Zone.
 * If two distinct VMs k1 < k2 host compID, they must be assigned to different zones.
 */
predicate az_dispersion(array[int, int] of var 0..1: AssignmentMatrix,
                        array[int] of var int: VMZone,
                        int: NoZones,
                        int: VM,
                        int: compID) =
    forall(k1 in 1..VM, k2 in k1+1..VM)(
        (AssignmentMatrix[compID, k1] + AssignmentMatrix[compID, k2] == 2) ->
            (VMZone[k1] != VMZone[k2])
    );

/*
 * Ensures that communication between two component types respects the
 * maximum allowed latency based on their hosting VMs Availability Zones.
 *
 * Efficient forbidden-pair projection: For any zone pair (z1, z2) where
 * ZoneLatency[z1, z2] exceeds MaxAllowedLatency, no VM in z1 and VM in z2
 * can simultaneously host comp1 and comp2.
 */
predicate latency_sla(array[int, int] of var 0..1: AssignmentMatrix,
                      array[int] of var int: VMZone,
                      array[int, int] of int: ZoneLatency,
                      int: MaxAllowedLatency,
                      int: VM,
                      int: comp1,
                      int: comp2) =
    forall(z1 in 1..NoZones, z2 in 1..NoZones where ZoneLatency[z1, z2] > MaxAllowedLatency)(
        forall(k1 in 1..VM, k2 in 1..VM)(
            (VMZone[k1] == z1 /\ VMZone[k2] == z2) ->
                (AssignmentMatrix[comp1, k1] + AssignmentMatrix[comp2, k2] <= 1)
        )
    );
